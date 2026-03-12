from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from config.db_config import get_db
from models.users import User
from schemas.ddis import (
    DDIPredictionRequest,
    DDIPredictionResponse,
    DDIPredictionResult,
    DDIPredictionListResponse,
    DDIPredictionUpdate,
    InteractionTypeResponse,
    calculate_smiles_hash
)
from crud.ddis import (
    create_ddi_prediction,
    get_user_ddi_predictions,
    get_ddi_prediction,
    update_ddi_prediction,
    delete_ddi_prediction,
    check_duplicate_prediction,
    get_prediction_stats,
    get_interaction_types
)
from utils.auth import get_current_user
from utils.response import success_response
from utils.ddis_client import ddis_client, logger

router = APIRouter(prefix="/api/ddi", tags=["药物相互作用预测"])

@router.post("/predict", response_model=DDIPredictionResult)
async def predict_ddi(
        request: DDIPredictionRequest,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    预测药物相互作用并保存记录到数据库
    """
    try:
        # 2. 调用模型服务进行预测
        prediction_result = await ddis_client.predict_single(
            smiles_a=request.smiles_a,
            smiles_b=request.smiles_b,
            drug_a_name=request.drug_a_name,
            drug_b_name=request.drug_b_name,
            interaction_type_id=request.interaction_type_id,
            include_attention=request.include_attention,
            include_activations=request.include_activations
        )

        # 3. 如果用户已登录，则将预测结果落库保存
        if current_user:
            # 如果 ddis_client 返回的是 Pydantic 模型，先转成字典
            result_dict = prediction_result.model_dump() if hasattr(prediction_result,
                                                                    'model_dump') else prediction_result

            raw_label = str(result_dict.get("prediction", "")).lower()

            if "no interaction" in raw_label or "安全" in raw_label or "safe" in raw_label:
                db_label = "safe"

            elif "interaction" in raw_label or "risk" in raw_label or "风险" in raw_label:
                db_label = "risk"
            else:
                db_label = "safe"

            raw_confidence = str(result_dict.get("confidence", "medium")).lower()
            db_confidence = raw_confidence if raw_confidence in ["low", "medium", "high"] else "medium"
            # 组装入库所需的数据（合并用户输入和模型输出）
            prediction_data = {
                "drug_a_name": request.drug_a_name,
                "drug_b_name": request.drug_b_name,
                "smiles_a": request.smiles_a,
                "smiles_b": request.smiles_b,
                "smiles_a_hash": calculate_smiles_hash(request.smiles_a),
                "smiles_b_hash": calculate_smiles_hash(request.smiles_b),
                "interaction_type_id": request.interaction_type_id,
                "model_type": request.model_type,
                "prediction_label": db_label,
                "probability": result_dict.get("probability", 0.0),
                "confidence": db_confidence,
                "attention_analysis": result_dict.get("attention_analysis"),
                "layer_activations": result_dict.get("layer_activations"),
                "drug_a_info": result_dict.get("drug_a_info"),
                "drug_b_info": result_dict.get("drug_b_info")
            }

            # 调用 CRUD 方法执行数据库写入
            await create_ddi_prediction(
                db=db,
                user_id=current_user.id,
                prediction_data=prediction_data
            )

        # 4. 无论是否登录，最后都将预测结果返回给前端
        return prediction_result

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"预测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"预测失败: {str(e)}"
        )

@router.get("/predictions", response_model=DDIPredictionListResponse)
async def get_my_predictions(
        page: int = Query(1, ge=1, description="页码"),
        page_size: int = Query(10, ge=1, le=100, description="每页数量"),
        is_favorite: Optional[bool] = Query(None, description="是否收藏"),
        search: Optional[str] = Query(None, description="搜索关键词"),
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    获取我的预测记录
    """
    skip = (page - 1) * page_size

    predictions, total = await get_user_ddi_predictions(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=page_size,
        is_favorite=is_favorite,
        search=search
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": predictions
    }


@router.get("/predictions/{prediction_id}", response_model=DDIPredictionResponse)
async def get_prediction_detail(
        prediction_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    获取预测记录详情
    """
    prediction = await get_ddi_prediction(db, prediction_id)

    if not prediction:
        raise HTTPException(status_code=404, detail="预测记录不存在")

    # 检查权限（只能查看自己的记录）
    if prediction.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问此记录")

    return prediction


@router.put("/predictions/{prediction_id}", response_model=DDIPredictionResponse)
async def update_prediction(
        prediction_id: int,
        update_data: DDIPredictionUpdate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    更新预测记录（收藏、备注、评分）
    """
    updated_prediction = await update_ddi_prediction(
        db=db,
        prediction_id=prediction_id,
        update_data=update_data,
        user_id=current_user.id
    )

    if not updated_prediction:
        raise HTTPException(status_code=404, detail="预测记录不存在或无权限")

    return updated_prediction


@router.delete("/predictions/{prediction_id}")
async def delete_prediction(
        prediction_id: int,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    删除预测记录
    """
    success = await delete_ddi_prediction(
        db=db,
        prediction_id=prediction_id,
        user_id=current_user.id
    )

    if not success:
        raise HTTPException(status_code=404, detail="预测记录不存在或无权限")

    return success_response(message="删除成功")


@router.get("/stats")
async def get_my_stats(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db)
):
    """
    获取我的预测统计信息
    """
    stats = await get_prediction_stats(db, current_user.id)
    return success_response(message="统计信息", data=stats)


@router.get("/interaction-types", response_model=List[InteractionTypeResponse])
async def get_interaction_types_list(
        db: AsyncSession = Depends(get_db)
):
    """
    获取所有相互作用类型
    """
    types = await get_interaction_types(db)
    return types