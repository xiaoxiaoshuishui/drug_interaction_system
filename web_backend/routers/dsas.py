from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.dsas import (
    DSAPredictionRequest,
    DSAPredictionResult
)
from utils.dsas_client import dsas_client
from config.db_config import get_db
from crud.dsas import get_drug_index, get_se_index

router = APIRouter(prefix="/api/dsa", tags=["药物不良反应预测(MFGNN-DSA)"])


@router.post("/predict", response_model=DSAPredictionResult)
async def predict_dsa(
        request: DSAPredictionRequest,
        db: AsyncSession = Depends(get_db)
):
    # 1. 查库：将实体字符串转换为模型底层索引
    drug_info = await get_drug_index(db, request.drug_identifier)
    se_info = await get_se_index(db, request.se_name)

    if not drug_info:
        raise HTTPException(status_code=404, detail=f"数据库中未找到该药物: {request.drug_identifier}")
    if not se_info:
        raise HTTPException(status_code=404, detail=f"数据库中未找到该副作用: {request.se_name}")

    drug_idx, standard_drug_name = drug_info
    se_idx, standard_se_name = se_info

    try:
        # 2. 调用 8002 底层模型微服务
        model_result = await dsas_client.predict_single(
            se_index=se_idx,
            drug_index=drug_idx
        )

        # 3. 组装结果返回给前端 (包含提取出的 radar_data 和 graph_data)
        return DSAPredictionResult(
            success=model_result.get("success", True),
            drug_name=standard_drug_name,
            se_name=standard_se_name,
            score=model_result.get("score", 0.0),
            prediction=model_result.get("prediction", 0),
            risk_level=model_result.get("risk_level", "Unknown"),
            drug_index=drug_idx,
            se_index=se_idx,
            radar_data=model_result.get("radar_data"),  # 透传雷达图数据
            graph_data=model_result.get("graph_data")  # 透传图谱数据
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))