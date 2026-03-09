import sys
import torch
import numpy as np
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import warnings

warnings.filterwarnings('ignore')

# ---------------------------------------------------------
# 1. 环境与路径配置
# ---------------------------------------------------------
sys.path.append('drugbank_test')

try:
    import models
    from data_preprocessing import (
        get_mol_edge_list_and_feat_mtx,
        get_bipartite_graph,
        BipartiteData
    )
except ImportError as e:
    print("错误：无法导入项目模块。请确保此脚本位于项目根目录，且'drugbank_test'文件夹存在。")
    raise e


# ---------------------------------------------------------
# 2. 修复BipartiteData类
# ---------------------------------------------------------
class FixedBipartiteData:
    """修复的BipartiteData类，添加num_nodes属性"""

    def __init__(self, edge_index, x_s, x_t):
        self.edge_index = edge_index
        self.x_s = x_s
        self.x_t = x_t
        # 计算总节点数
        self.num_nodes = x_s.shape[0] + x_t.shape[0]

    def to(self, device):
        """移动到指定设备"""
        self.edge_index = self.edge_index.to(device)
        self.x_s = self.x_s.to(device)
        self.x_t = self.x_t.to(device)
        return self


# ---------------------------------------------------------
# 3. Hook管理类（修复tuple处理）
# ---------------------------------------------------------
class ActivationHook:
    """用于捕获模型中间层激活的Hook管理器"""

    def __init__(self):
        self.activations = {}
        self.hooks = []

    def __call__(self, module, input, output):
        """存储激活值的Hook函数"""
        module_name = str(module).split('(')[0]
        if module_name not in self.activations:
            self.activations[module_name] = []

        # 处理不同类型的输出
        if isinstance(output, torch.Tensor):
            # 如果是tensor，直接存储
            self.activations[module_name].append(output.detach().cpu())
        elif isinstance(output, tuple):
            # 如果是元组，提取其中的tensor
            tensor_outputs = []
            for item in output:
                if isinstance(item, torch.Tensor):
                    tensor_outputs.append(item.detach().cpu())
                elif hasattr(item, 'x') and isinstance(item.x, torch.Tensor):
                    # 如果是Data对象，存储x
                    tensor_outputs.append(item.x.detach().cpu())
            if tensor_outputs:
                self.activations[module_name].append(tensor_outputs)
        elif hasattr(output, 'x') and isinstance(output.x, torch.Tensor):
            # 如果是Data对象
            self.activations[module_name].append(output.x.detach().cpu())

        return output

    def register(self, model):
        """为模型的不同层注册hook"""
        # 注册co_attention层的hook
        if hasattr(model, 'co_attention'):
            hook = model.co_attention.register_forward_hook(self)
            self.hooks.append(hook)

        # 注册所有blocks的hook
        if hasattr(model, 'blocks'):
            for i, block in enumerate(model.blocks):
                hook = block.register_forward_hook(self)
                self.hooks.append(hook)

    def remove(self):
        """移除所有hooks"""
        for hook in self.hooks:
            hook.remove()
        self.hooks.clear()

    def get_attention_weights(self):
        """获取注意力权重"""
        if 'CoAttentionLayer' in self.activations:
            attentions = self.activations['CoAttentionLayer']
            if attentions and isinstance(attentions[0], torch.Tensor):
                return attentions[0]  # 返回第一个batch的注意力
        return None

    def get_layer_outputs(self):
        """获取各层的输出"""
        return self.activations


# ---------------------------------------------------------
# 4. FastAPI应用初始化
# ---------------------------------------------------------
app = FastAPI(
    title="DSN-DDI 药物相互作用预测API",
    description="基于深度学习的药物-药物相互作用预测模型服务",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # 包括Authorization
)

# 全局变量存储模型
MODEL = None
DEVICE = None


# ---------------------------------------------------------
# 5. 请求/响应模型定义
# ---------------------------------------------------------
class DDIPredictionRequest(BaseModel):
    """药物相互作用预测请求模型"""
    smiles_a: str
    smiles_b: str
    drug_a_name: Optional[str] = "Drug A"
    drug_b_name: Optional[str] = "Drug B"
    interaction_type_id: Optional[int] = 0
    include_attention: Optional[bool] = True
    include_activations: Optional[bool] = True


class AttentionAnalysis(BaseModel):
    """注意力权重分析结果"""
    shape: List[int]
    mean: float
    max: float
    min: float
    std: float
    top_connections: Optional[List[Dict[str, Any]]] = None


class LayerActivation(BaseModel):
    """层激活信息"""
    layer_name: str
    shape: Optional[List[int]] = None
    value_range: Optional[List[float]] = None
    mean: Optional[float] = None
    tensor_count: Optional[int] = None
    tensor_shapes: Optional[List[List[int]]] = None


class DDIPredictionResponse(BaseModel):
    """药物相互作用预测响应模型"""
    success: bool
    prediction: str
    probability: float
    threshold: float = 0.5
    confidence: Optional[str] = None
    drug_a_info: Dict[str, Any]
    drug_b_info: Dict[str, Any]
    attention_analysis: Optional[AttentionAnalysis] = None
    layer_activations: Optional[List[LayerActivation]] = None
    error_message: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    model_loaded: bool
    device: str
    model_path: Optional[str] = None


# ---------------------------------------------------------
# 6. 数据处理函数
# ---------------------------------------------------------
def prepare_input(smiles_a, smiles_b):
    """
    将两个 SMILES 字符串转换为模型所需的 Graph Batch 格式
    """
    from rdkit import Chem
    from torch_geometric.data import Data, Batch

    mol_a = Chem.MolFromSmiles(smiles_a)
    mol_b = Chem.MolFromSmiles(smiles_b)

    if mol_a is None or mol_b is None:
        raise ValueError("无效的 SMILES 字符串，无法解析分子。")

    # 提取分子内特征 (Intra-view)
    edge_index_a, x_a = get_mol_edge_list_and_feat_mtx(mol_a)
    edge_index_b, x_b = get_mol_edge_list_and_feat_mtx(mol_b)

    # 封装为 PyG 的 Data 对象，添加num_nodes
    data_a = Data(x=x_a, edge_index=edge_index_a, num_nodes=x_a.shape[0])
    data_b = Data(x=x_b, edge_index=edge_index_b, num_nodes=x_b.shape[0])

    # 构建分子间关系图 (Inter-view)，使用FixedBipartiteData
    b_edge_index = get_bipartite_graph(mol_a, mol_b)
    b_graph = FixedBipartiteData(edge_index=b_edge_index, x_s=x_a, x_t=x_b)

    # 转换为 Batch
    batch_a = Batch.from_data_list([data_a])
    batch_b = Batch.from_data_list([data_b])

    # 为Batch设置num_nodes
    batch_a.num_nodes = x_a.shape[0]
    batch_b.num_nodes = x_b.shape[0]

    return batch_a, batch_b, b_graph, mol_a, mol_b


def analyze_attention_weights(attentions, drug_a_name="Drug A", drug_b_name="Drug B"):
    """分析注意力权重"""
    if attentions is None:
        return None

    if not isinstance(attentions, torch.Tensor):
        return None

    att = attentions.squeeze().numpy()

    # 计算基本统计信息
    analysis = {
        "shape": list(att.shape),
        "mean": float(att.mean()),
        "max": float(att.max()),
        "min": float(att.min()),
        "std": float(att.std())
    }

    # 找到最重要的连接
    if len(att.shape) == 2:
        # 获取前10个最重要的连接
        flat_indices = np.argsort(att.flatten())[-10:][::-1]
        top_connections = []

        for i, idx in enumerate(flat_indices):
            row, col = np.unravel_index(idx, att.shape)
            top_connections.append({
                "rank": i + 1,
                "drug_a_atom": int(row),
                "drug_b_atom": int(col),
                "weight": float(att[row, col]),
                "description": f"{drug_a_name}[{row}] ↔ {drug_b_name}[{col}]"
            })

        analysis["top_connections"] = top_connections

    return analysis


def analyze_layer_activations(activations):
    """分析层激活信息"""
    if not activations:
        return None

    layer_results = []

    for layer_name, outputs in activations.items():
        if not outputs:
            continue

        output_data = outputs[0]
        layer_info = {"layer_name": layer_name}

        if isinstance(output_data, torch.Tensor):
            layer_info["shape"] = list(output_data.shape)
            layer_info["value_range"] = [
                float(output_data.min()),
                float(output_data.max())
            ]
            layer_info["mean"] = float(output_data.mean())

        elif isinstance(output_data, list):
            layer_info["tensor_count"] = len(output_data)
            tensor_shapes = []
            for tensor in output_data:
                if isinstance(tensor, torch.Tensor):
                    tensor_shapes.append(list(tensor.shape))
            if tensor_shapes:
                layer_info["tensor_shapes"] = tensor_shapes

        layer_results.append(layer_info)

    return layer_results


# ---------------------------------------------------------
# 7. 预测函数
# ---------------------------------------------------------
def predict_with_explanation(model, smiles_a, smiles_b,
                             drug_a_name="Drug A", drug_b_name="Drug B",
                             interaction_type_id=0,
                             include_attention=True, include_activations=True):
    """
    使用Hook机制进行预测并获取解释信息
    """
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # 创建Hook管理器
    hook_manager = None
    if include_attention or include_activations:
        hook_manager = ActivationHook()
        hook_manager.register(model)

    # 准备输入数据
    try:
        h_data, t_data, b_graph, mol_a, mol_b = prepare_input(smiles_a, smiles_b)

        h_data = h_data.to(device)
        t_data = t_data.to(device)
        b_graph = b_graph.to(device)
        rels = torch.LongTensor([interaction_type_id]).to(device)

        # 注意：模型期望b_graph是特定格式，我们需要调整
        triples = (h_data, t_data, rels, b_graph)

    except Exception as e:
        raise ValueError(f"数据处理错误: {str(e)}")

    # 执行预测
    try:
        with torch.no_grad():
            output_scores = model(triples)
            probability = torch.sigmoid(output_scores).item()
    except Exception as e:
        raise RuntimeError(f"预测过程中出错: {str(e)}")

    # 获取Hook收集的信息
    attentions = None
    layer_activations = None

    if hook_manager:
        if include_attention:
            attentions = hook_manager.get_attention_weights()
        if include_activations:
            layer_activations = hook_manager.get_layer_outputs()
        hook_manager.remove()

    # 分析注意力权重
    attention_analysis = None
    if attentions is not None:
        attention_analysis = analyze_attention_weights(
            attentions, drug_a_name, drug_b_name
        )

    # 分析层激活
    layer_analysis = None
    if layer_activations is not None:
        layer_analysis = analyze_layer_activations(layer_activations)

    # 确定置信度
    if probability > 0.8 or probability < 0.2:
        confidence = "high"
    elif probability > 0.6 or probability < 0.4:
        confidence = "medium"
    else:
        confidence = "low"

    result = {
        'success': True,
        'prediction': 'Interaction (风险)' if probability > 0.5 else 'No Interaction (安全)',
        'probability': probability,
        'confidence': confidence,
        'drug_a_info': {
            'smiles': smiles_a,
            'name': drug_a_name,
            'num_atoms': mol_a.GetNumAtoms() if mol_a else 0,
            'num_bonds': mol_a.GetNumBonds() if mol_a else 0
        },
        'drug_b_info': {
            'smiles': smiles_b,
            'name': drug_b_name,
            'num_atoms': mol_b.GetNumAtoms() if mol_b else 0,
            'num_bonds': mol_b.GetNumBonds() if mol_b else 0
        },
        'attention_analysis': attention_analysis,
        'layer_activations': layer_analysis
    }

    return result


# ---------------------------------------------------------
# 8. FastAPI路由
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """启动时加载模型"""
    global MODEL, DEVICE

    try:
        model_path = 'drugbank_test/transductive_drugbank.pkl'
        DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"正在加载模型到设备: {DEVICE}")

        MODEL = torch.load(model_path, map_location=DEVICE)
        MODEL.to(DEVICE)
        MODEL.eval()

        print(f"模型加载成功，设备: {DEVICE}")
    except Exception as e:
        print(f"启动时加载模型失败: {e}")
        MODEL = None


@app.get("/", tags=["根目录"])
async def root():
    """API根目录"""
    return {
        "message": "DSN-DDI 药物相互作用预测API",
        "version": "1.0.0",
        "endpoints": {
            "predict": "/predict (POST)",
            "docs": "/docs"
        }
    }

@app.post("/predict", response_model=DDIPredictionResponse, tags=["预测"])
async def predict_ddi(request: DDIPredictionRequest):
    """单个药物对预测"""
    if MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="模型未加载，请检查服务状态"
        )

    try:
        result = predict_with_explanation(
            model=MODEL,
            smiles_a=request.smiles_a,
            smiles_b=request.smiles_b,
            drug_a_name=request.drug_a_name,
            drug_b_name=request.drug_b_name,
            interaction_type_id=request.interaction_type_id,
            include_attention=request.include_attention,
            include_activations=request.include_activations
        )

        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测过程中发生未知错误: {str(e)}")

@app.post("/predict/simple", tags=["预测"])
async def simple_predict(request: DDIPredictionRequest):
    """简化版预测接口（仅返回关键结果）"""
    if MODEL is None:
        raise HTTPException(
            status_code=503,
            detail="模型未加载，请检查服务状态"
        )

    try:
        result = predict_with_explanation(
            model=MODEL,
            smiles_a=request.smiles_a,
            smiles_b=request.smiles_b,
            interaction_type_id=request.interaction_type_id,
            include_attention=True,
            include_activations=True
        )

        # 返回简化结果
        return {
            "success": True,
            "probability": result["probability"],
            "prediction": result["prediction"],
            "confidence": result["confidence"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------
# 9. 错误处理
# ---------------------------------------------------------
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error_message": exc.detail,
            "detail": str(exc.detail)
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error_message": "服务器内部错误",
            "detail": str(exc)
        }
    )


# ---------------------------------------------------------
# 10. 主函数
# ---------------------------------------------------------
if __name__ == "__main__":

    print("=" * 60)
    print("启动 DSN-DDI 药物相互作用预测API服务")
    print("=" * 60)

    # 启动FastAPI应用
    uvicorn.run(
        "simple_pred:app",
        host="127.0.0.1",
        port=8001,
        reload=True,
        log_level="info"
    )