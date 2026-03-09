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
    BatchPredictionRequest,
    BatchPredictionResponse,
    DDIPredictionUpdate,
    InteractionTypeResponse
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
        # ❌ 暂时移除认证和数据库依赖
        # current_user: Optional[User] = Depends(get_current_user),
        # db: AsyncSession = Depends(get_db)
):
    """
    预测药物相互作用（临时版本，不保存数据库）
    """
    try:
        # 直接调用模型服务，不检查缓存，不保存数据库
        prediction_result = await ddis_client.predict_single(
            smiles_a=request.smiles_a,
            smiles_b=request.smiles_b,
            drug_a_name=request.drug_a_name,
            drug_b_name=request.drug_b_name,
            interaction_type_id=request.interaction_type_id,
            include_attention=request.include_attention,
            include_activations=request.include_activations
        )
        print(request)
        return prediction_result

    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"预测失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"预测失败: {str(e)}"
        )


# @router.post("/batch-predict", response_model=BatchPredictionResponse)
# async def batch_predict_ddi(
#         request: BatchPredictionRequest,
#         current_user: Optional[User] = Depends(get_current_user),
#         db: AsyncSession = Depends(get_db)
# ):
#     """
#     批量预测药物相互作用
#     """
#     try:
#         # 调用模型服务进行批量预测
#         batch_result = await ddis_client.predict_batch(
#             predictions=[
#                 {
#                     "smiles_a": pred.smiles_a,
#                     "smiles_b": pred.smiles_b,
#                     "drug_a_name": pred.drug_a_name,
#                     "drug_b_name": pred.drug_b_name,
#                     "interaction_type_id": pred.interaction_type_id,
#                     "include_attention": pred.include_attention,
#                     "include_activations": pred.include_activations
#                 }
#                 for pred in request.predictions
#             ],
#             parallel=request.parallel
#         )
#
#         # 保存成功的预测结果到数据库
#         if current_user and batch_result.get("success"):
#             for i, result in enumerate(batch_result.get("results", [])):
#                 if i < len(request.predictions):
#                     pred_request = request.predictions[i]
#                     await create_ddi_prediction(
#                         db=db,
#                         prediction_data={
#                             **result,
#                             "drug_a_name": pred_request.drug_a_name,
#                             "drug_b_name": pred_request.drug_b_name,
#                             "smiles_a": pred_request.smiles_a,
#                             "smiles_b": pred_request.smiles_b,
#                             "model_type": pred_request.model_type
#                         },
#                         user_id=current_user.id
#                     )
#
#         return batch_result
#
#     except Exception as e:
#         logger.error(f"批量预测失败: {str(e)}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"批量预测失败: {str(e)}"
#         )


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


# @router.post("/simple-predict")
# async def simple_ddi_predict(
#         data: DDIPredictionRequest
# ):
#     """
#     简化版预测（无需登录）
#     """
#     try:
#         result = await ddis_client.simple_predict(
#             smiles_a=data.smiles_a,
#             smiles_b=data.smiles_b,
#             interaction_type_id=data.interaction_type_id or 0
#         )
#         return success_response(message="预测成功", data=result)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))