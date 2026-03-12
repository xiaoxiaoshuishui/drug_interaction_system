from datetime import datetime

from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# 可视化图表子数据模型
class RadarDataItem(BaseModel):
    name: str
    max: Optional[float] = None
    value: float


class GraphNode(BaseModel):
    id: str
    name: str
    category: int
    symbolSize: int


class GraphLink(BaseModel):
    source: str
    target: str
    value: Optional[float] = None
    label: Optional[str] = None


class GraphData(BaseModel):
    nodes: List[GraphNode]
    links: List[GraphLink]

# 原始：请求与响应模型
class DSAPredictionRequest(BaseModel):
    drug_identifier: str  # 可以传药物名称、DrugBank ID 或 SMILES
    se_name: str  # 副作用的名称或 UMLS CUI

class DSAPredictionResult(BaseModel):
    success: bool
    drug_name: str
    se_name: str
    score: float
    prediction: int
    risk_level: str
    drug_index: Optional[int] = None
    se_index: Optional[int] = None

    # 新增：用于前端可视化的字段
    radar_data: Optional[List[RadarDataItem]] = None
    graph_data: Optional[GraphData] = None

class DSAPredictionUpdate(BaseModel):
    """DSA预测更新模型"""
    is_favorite: Optional[bool] = None
    user_notes: Optional[str] = None

class DSAPredictionResponse(BaseModel):
    """DSA单条历史记录展示模型"""
    id: int
    user_id: Optional[int]
    drug_identifier: str
    se_name: str
    probability: float
    prediction_label: str
    is_favorite: bool
    user_notes: Optional[str]
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class DSAPredictionListResponse(BaseModel):
    """DSA历史记录列表响应"""
    total: int
    page: int
    page_size: int
    data: List[DSAPredictionResponse]