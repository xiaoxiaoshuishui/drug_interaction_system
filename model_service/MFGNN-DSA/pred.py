import torch
import numpy as np
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
from torch.autograd import Variable

# 导入项目自带的模块
from utils import multiomics_data
from model import MultiDeep

# ---------------------------------------------------------
# 1. FastAPI 实例与配置
# ---------------------------------------------------------
app = FastAPI(title="MFGNN-DSA Prediction API", version="1.0.0")

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# 2. 全局变量与模型初始化
# ---------------------------------------------------------
device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
model = None
se_HIN, se_SE, se_adj = None, None, None
drug_HIN, drug_PC, drug_adj = None, None, None

MODEL_WEIGHT_PATH = "./output/model.pkl"


@app.on_event("startup")
async def load_model_and_data():
    global model, se_HIN, se_SE, se_adj, drug_HIN, drug_PC, drug_adj
    print("正在加载图数据与特征矩阵...")
    try:
        # 复用 utils 中的数据加载逻辑
        se_HIN_raw, se_SE_raw, se_adj_raw, drug_HIN_raw, drug_PC_raw, drug_adj_raw, sample_set = multiomics_data()

        # 转换为 Variable 并移动到对应设备
        se_HIN = Variable(se_HIN_raw).to(device)
        se_SE = Variable(se_SE_raw).to(device)
        se_adj = Variable(se_adj_raw).to(device)
        drug_HIN = Variable(drug_HIN_raw).to(device)
        drug_PC = Variable(drug_PC_raw).to(device)
        drug_adj = Variable(drug_adj_raw).to(device)

        print("正在初始化 MFGNN-DSA 模型...")
        # 参数对齐 main.py 中的默认参数
        model = MultiDeep(
            nse=se_SE.shape[0],
            ndrug=drug_PC.shape[0],
            nseHIN=se_HIN.shape[1],
            nseSE=se_SE.shape[1],
            ndrugHIN=drug_HIN.shape[1],
            ndrugPC=drug_PC.shape[1],
            nhid_GAT=128,
            nheads_GAT=1,
            nhid_MHSA=256,
            nheads_MHSA=4,
            alpha=0.2
        ).to(device)

        # 加载预训练权重
        model.load_state_dict(torch.load(MODEL_WEIGHT_PATH, map_location=device))
        model.eval()
        print("模型加载完成，服务已就绪！")

    except Exception as e:
        print(f"初始化失败: {e}")


# ---------------------------------------------------------
# 3. Pydantic 数据模型定义
# ---------------------------------------------------------
class PredictionRequest(BaseModel):
    se_index: int  # 副作用节点的索引 (0 到 nse-1)
    drug_index: int  # 药物节点的索引 (0 到 ndrug-1)


class BatchPredictionRequest(BaseModel):
    pairs: List[List[int]]  # 批量请求：[[se_index_1, drug_index_1], [se_index_2, drug_index_2], ...]


# ---------------------------------------------------------
# 4. 预测接口定义
# ---------------------------------------------------------
@app.get("/")
async def root():
    return {
        "message": "欢迎使用 MFGNN-DSA 药物不良反应预测 API 服务！",
        "docs_url": "请访问 http://127.0.0.1:8002/docs 查看接口文档并进行测试"
    }


@app.post("/predict")
async def predict(request: PredictionRequest):
    """
    单条药物-副作用关联预测 (附带真实的高维可视化特征)
    """
    if model is None:
        raise HTTPException(status_code=503, detail="模型未加载完毕，请稍后再试")

    try:
        # 1. 越界拦截，防止 GPU 崩溃
        if request.drug_index >= drug_PC.shape[0]:
            raise HTTPException(status_code=400, detail=f"药物索引越界！")
        if request.se_index >= se_SE.shape[0]:
            raise HTTPException(status_code=400, detail=f"副作用索引越界！")

        # 2. 模型推理 (使用 Tensor 避免显存上下文丢失)
        idx_tensor = torch.tensor([[request.se_index, request.drug_index]], dtype=torch.long).to(device)

        with torch.no_grad():
            y_pred = model(se_HIN, se_SE, se_adj, drug_HIN, drug_PC, drug_adj, idx_tensor, device)
            score = float(y_pred.cpu().detach().numpy()[0])
            score = max(0.0, min(1.0, score))  # 防止越界负数

        prediction = 1 if score >= 0.5 else 0

        # 3. 提取真实的多视图特征密度 (供雷达图使用)
        # 计算各个特征矩阵在当前输入节点上的 L2 范数（代表信息量大小）
        d_hin_norm = float(torch.norm(drug_HIN[request.drug_index]).cpu())
        d_pc_norm = float(torch.norm(drug_PC[request.drug_index]).cpu())
        s_hin_norm = float(torch.norm(se_HIN[request.se_index]).cpu())
        s_se_norm = float(torch.norm(se_SE[request.se_index]).cpu())

        # 归一化处理，使其适合在 max=1.0 的雷达图中展示
        total_norm = d_hin_norm + d_pc_norm + s_hin_norm + s_se_norm
        if total_norm == 0: total_norm = 1.0

        # 放大一点比例以便于前端雷达图视觉呈现
        radar_data = [
            {"name": "药物HIN网络拓扑特征", "max": 1.0, "value": min(1.0, round((d_hin_norm / total_norm) * 2.5, 4))},
            {"name": "药物自身理化/多视图特征", "max": 1.0,
             "value": min(1.0, round((d_pc_norm / total_norm) * 2.5, 4))},
            {"name": "副作用HIN网络拓扑特征", "max": 1.0, "value": min(1.0, round((s_hin_norm / total_norm) * 2.5, 4))},
            {"name": "副作用语义多视图特征", "max": 1.0, "value": min(1.0, round((s_se_norm / total_norm) * 2.5, 4))}
        ]

        # ==========================================
        # 4. 提取真实的局部知识图谱关联 (供力导向图使用)
        # ==========================================
        nodes = [
            {"id": f"Drug_{request.drug_index}", "name": "当前查询药物", "category": 0, "symbolSize": 50},
            {"id": f"SE_{request.se_index}", "name": "当前查询副作用", "category": 1, "symbolSize": 50}
        ]
        links = [
            {"source": f"Drug_{request.drug_index}", "target": f"SE_{request.se_index}", "value": score,
             "label": "预测关联度"}
        ]

        # 从邻接矩阵 (drug_adj) 中找出和该药物最相似的 Top-3 药物
        k_neighbors = 3
        drug_sim_scores, top_drugs = torch.topk(drug_adj[request.drug_index], k=k_neighbors + 1)
        # 从邻接矩阵 (se_adj) 中找出和该副作用最相似的 Top-3 副作用
        se_sim_scores, top_ses = torch.topk(se_adj[request.se_index], k=k_neighbors + 1)

        # 挂载真实相似药物节点
        for i, d_idx in enumerate(top_drugs.tolist()):
            if d_idx != request.drug_index and drug_sim_scores[i] > 0.01:
                nodes.append({"id": f"Drug_{d_idx}", "name": f"相似药物_{d_idx}", "category": 2, "symbolSize": 30})
                links.append(
                    {"source": f"Drug_{request.drug_index}", "target": f"Drug_{d_idx}", "label": "底层特征相似"})

        # 挂载真实相似副作用节点
        for i, s_idx in enumerate(top_ses.tolist()):
            if s_idx != request.se_index and se_sim_scores[i] > 0.01:
                nodes.append({"id": f"SE_{s_idx}", "name": f"相似副作用_{s_idx}", "category": 2, "symbolSize": 30})
                links.append({"source": f"SE_{request.se_index}", "target": f"SE_{s_idx}", "label": "底层特征相似"})

        # 返回全部结果
        return {
            "success": True,
            "se_index": request.se_index,
            "drug_index": request.drug_index,
            "score": score,
            "prediction": prediction,
            "risk_level": "High" if prediction == 1 else "Low",
            "radar_data": radar_data,  # 真实计算的特征激活范数
            "graph_data": {  # 真实提取的图结构邻居
                "nodes": nodes,
                "links": links
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ---------------------------------------------------------
# 5. 异常处理
# ---------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error_message": exc.detail}
    )


# ---------------------------------------------------------
# 6. 服务启动入口
# ---------------------------------------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("启动 MFGNN-DSA 药物副作用预测 API 服务")
    print("=" * 60)
    # 启动 uvicorn 服务，端口8002
    uvicorn.run("pred:app", host="127.0.0.1", port=8002)