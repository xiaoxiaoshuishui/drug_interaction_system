from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from models.dsas import DSADrugNode, DSASideEffectNode
from models.users import User
from schemas.dsas import (
    DSAPredictionRequest,
    DSAPredictionResult,
    DSAPredictionListResponse,
    DSAPredictionUpdate,
    DSAPredictionResponse
)
from crud.dsas import (
    create_dsa_prediction,
    get_user_dsa_predictions,
    update_dsa_prediction,
    delete_dsa_prediction,
    get_drug_names_by_indices,
    get_se_names_by_indices
)
from utils.auth import get_current_user
from utils.dsas_client import dsas_client, logger
from config.db_config import get_db
from utils.response import success_response

router = APIRouter(prefix="/api/dsa", tags=["药物不良反应预测(MFGNN-DSA)"])


@router.post("/predict", response_model=DSAPredictionResult)
async def predict_dsa(
        request: DSAPredictionRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    预测药物不良反应并保存记录
    """
    try:
        # 1. 根据前端传来的名称，去数据库里查出对应的底层的 index

        # 查药物的 index
        stmt_drug = select(DSADrugNode).where(
            or_(
                DSADrugNode.drug_name_cn == request.drug_identifier,
                DSADrugNode.drug_name == request.drug_identifier,
                DSADrugNode.smiles == request.drug_identifier
            )
        )
        result_drug = await db.execute(stmt_drug)
        drug_node = result_drug.scalars().first()

        if not drug_node:
            raise HTTPException(status_code=400, detail=f"数据库中未找到药物: {request.drug_identifier}")

        # 查副作用的 index
        stmt_se = select(DSASideEffectNode).where(
            or_(
                DSASideEffectNode.se_name_cn == request.se_name,
                DSASideEffectNode.se_name == request.se_name
            )
        )
        result_se = await db.execute(stmt_se)
        se_node = result_se.scalars().first()

        if not se_node:
            raise HTTPException(status_code=400, detail=f"数据库中未找到副作用: {request.se_name}")

        drug_idx = drug_node.model_index
        se_idx = se_node.model_index

        prediction_result = await dsas_client.predict_single(
            se_index=se_idx,
            drug_index=drug_idx
        )

        if isinstance(prediction_result, dict):
            prediction_result["drug_name"] = drug_node.drug_name_cn if drug_node.drug_name_cn else drug_node.drug_name
            prediction_result["se_name"] = se_node.se_name_cn if se_node.se_name_cn else se_node.se_name

            if "graph_data" in prediction_result and "nodes" in prediction_result["graph_data"]:
                similar_drug_indices = []
                similar_se_indices = []

                for node in prediction_result["graph_data"]["nodes"]:
                    node_id = str(node.get("id", ""))

                    if node.get("category") == 0:
                        node["name"] = prediction_result["drug_name"]
                    elif node.get("category") == 1:
                        node["name"] = prediction_result["se_name"]
                    elif node.get("category") == 2:
                        if node_id.startswith("Drug_"):
                            similar_drug_indices.append(int(node_id.split("_")[1]))
                        elif node_id.startswith("SE_"):
                            similar_se_indices.append(int(node_id.split("_")[1]))

                if similar_drug_indices:
                    sim_drug_map = await get_drug_names_by_indices(db, similar_drug_indices)
                    for node in prediction_result["graph_data"]["nodes"]:
                        if node.get("category") == 2 and str(node.get("id", "")).startswith("Drug_"):
                            idx = int(str(node.get("id")).split("_")[1])
                            if idx in sim_drug_map:
                                node["name"] = sim_drug_map[idx]

                if similar_se_indices:
                    sim_se_map = await get_se_names_by_indices(db, similar_se_indices)
                    for node in prediction_result["graph_data"]["nodes"]:
                        if node.get("category") == 2 and str(node.get("id", "")).startswith("SE_"):
                            idx = int(str(node.get("id")).split("_")[1])
                            if idx in sim_se_map:
                                node["name"] = sim_se_map[idx]


        # 👇 3. 结果落库逻辑
        if current_user:
            result_dict = prediction_result.model_dump() if hasattr(prediction_result,
                                                                    'model_dump') else prediction_result
            score = result_dict.get("score", 0.0)
            if score < 0.5:
                db_label = "safe"
            elif score >= 0.5:
                db_label = "risk"
            else:
                db_label = "safe"

            prediction_data = {
                "drug_identifier": request.drug_identifier,
                "se_name": request.se_name,
                "prediction_label": db_label,
                "probability": score
            }

            await create_dsa_prediction(
                db=db,
                user_id=current_user.id,
                prediction_data=prediction_data
            )

        return prediction_result

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"DSA预测失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")

@router.get("/predictions", response_model=DSAPredictionListResponse)
async def get_my_dsa_predictions(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """获取我的 DSA 预测记录"""
    skip = (page - 1) * page_size
    predictions, total = await get_user_dsa_predictions(
        db=db, user_id=current_user.id, skip=skip, limit=page_size
    )
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": predictions
    }

@router.put("/predictions/{prediction_id}", response_model=DSAPredictionResponse)
async def update_dsa_prediction_api(
        prediction_id: int,
        update_data: DSAPredictionUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """更新 DSA 预测记录（如收藏状态）"""
    updated_prediction = await update_dsa_prediction(
        db=db, prediction_id=prediction_id, update_data=update_data.model_dump(exclude_unset=True), user_id=current_user.id
    )
    if not updated_prediction:
        raise HTTPException(status_code=404, detail="预测记录不存在或无权限")
    return updated_prediction

@router.delete("/predictions/{prediction_id}")
async def delete_dsa_prediction_api(
        prediction_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """删除 DSA 预测记录"""
    success = await delete_dsa_prediction(db=db, prediction_id=prediction_id, user_id=current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="预测记录不存在或无权限")
    return success_response(message="删除成功")
