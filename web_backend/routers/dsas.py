from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from schemas.dsas import (
    DSAPredictionRequest,
    DSAPredictionResult
)
from utils.dsas_client import dsas_client
from config.db_config import get_db
from crud.dsas import get_drug_index, get_se_index, get_drug_names_by_indices, get_se_names_by_indices

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

        # 3. 拦截 graph_data，将节点索引替换为数据库中的真实名称
        graph_data = model_result.get("graph_data", {})
        if graph_data and "nodes" in graph_data:
            drug_indices = []
            se_indices = []

            # 遍历并收集返回图谱中所有的药物索引和副作用索引
            for node in graph_data["nodes"]:
                node_id = node.get("id", "")
                if node_id.startswith("Drug_"):
                    drug_indices.append(int(node_id.split("_")[1]))
                elif node_id.startswith("SE_"):
                    se_indices.append(int(node_id.split("_")[1]))

            # 并发去数据库查询对应的真实名称映射字典
            drug_name_map = await get_drug_names_by_indices(db, drug_indices)
            se_name_map = await get_se_names_by_indices(db, se_indices)

            # 更新 node 的 name 属性，保留类别前缀以便于用户区分
            for node in graph_data["nodes"]:
                node_id = node.get("id", "")
                if node_id.startswith("Drug_"):
                    idx = int(node_id.split("_")[1])
                    if idx in drug_name_map:
                        prefix = "相似药物" if "相似" in node["name"] else "查询药物"
                        node["name"] = f"{prefix}: {drug_name_map[idx]}"

                elif node_id.startswith("SE_"):
                    idx = int(node_id.split("_")[1])
                    if idx in se_name_map:
                        prefix = "相似副作用" if "相似" in node["name"] else "查询副作用"
                        node["name"] = f"{prefix}: {se_name_map[idx]}"

        # 4. 组装结果返回给前端
        return DSAPredictionResult(
            success=model_result.get("success", True),
            drug_name=standard_drug_name,
            se_name=standard_se_name,
            score=model_result.get("score", 0.0),
            prediction=model_result.get("prediction", 0),
            risk_level=model_result.get("risk_level", "Unknown"),
            drug_index=drug_idx,
            se_index=se_idx,
            radar_data=model_result.get("radar_data"),
            graph_data=graph_data  # 返回经过名称渲染后的图谱数据
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))