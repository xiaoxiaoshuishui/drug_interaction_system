from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime
import hashlib

class DDIPredictionBase(BaseModel):
    """DDI预测基础模型"""
    drug_a_name: Optional[str] = Field(None, max_length=100, description="药物A名称")
    drug_b_name: Optional[str] = Field(None, max_length=100, description="药物B名称")
    smiles_a: str = Field(..., description="药物A的SMILES")
    smiles_b: str = Field(..., description="药物B的SMILES")
    model_type: Optional[str] = Field("dsn-ddi", description="使用的模型类型")
    include_attention: Optional[bool] = Field(True, description="是否包含注意力分析")
    include_activations: Optional[bool] = Field(True, description="是否包含层激活信息")

    @field_validator('smiles_a', 'smiles_b')
    @classmethod
    def validate_smiles(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError("SMILES不能为空")
        if len(v) > 1000:
            raise ValueError("SMILES过长")
        return v.strip()


class DDIPredictionRequest(DDIPredictionBase):
    """DDI预测请求模型"""
    interaction_type_id: Optional[int] = Field(0, description="相互作用类型ID")


class DDIPredictionResult(BaseModel):
    """DDI预测结果模型"""
    prediction: str = Field(..., description="预测结果")
    probability: float = Field(..., ge=0, le=1, description="相互作用概率")
    confidence: str = Field(..., description="置信度")

    # 药物信息
    drug_a_info: Optional[Dict[str, Any]] = Field(None, description="药物A信息")
    drug_b_info: Optional[Dict[str, Any]] = Field(None, description="药物B信息")

    # 分析信息
    attention_analysis: Optional[Dict[str, Any]] = Field(None, description="注意力分析")
    layer_activations: Optional[List[Dict[str, Any]]] = Field(None, description="层激活信息")

    # 元数据
    model_used: str = Field(..., description="使用的模型")
    processing_time_ms: Optional[float] = Field(None, description="处理时间(毫秒)")
    timestamp: datetime = Field(..., description="预测时间")


class DDIPredictionResponse(BaseModel):
    """DDI预测响应模型"""
    id: int = Field(..., description="预测记录ID")
    user_id: Optional[int] = Field(None, description="用户ID")

    # 药物信息
    drug_a_name: Optional[str] = Field(None, description="药物A名称")
    drug_b_name: Optional[str] = Field(None, description="药物B名称")
    smiles_a: str = Field(..., description="药物A的SMILES")
    smiles_b: str = Field(..., description="药物B的SMILES")

    interaction_type_id: Optional[int] = Field(None, description="相互作用类型ID")

    # 预测结果
    probability: float = Field(..., description="相互作用概率")
    prediction_label: str = Field(..., description="预测标签")
    confidence: str = Field(..., description="置信度")

    # 模型信息
    model_type: str = Field(..., description="模型类型")

    # 用户交互字段
    is_favorite: bool = Field(False, description="是否收藏")
    user_notes: Optional[str] = Field(None, description="用户备注")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分")

    # 时间戳
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")

    model_config = ConfigDict(from_attributes=True)


class DDIPredictionListResponse(BaseModel):
    """DDI预测列表响应"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    data: List[DDIPredictionResponse] = Field(..., description="预测记录列表")

class DDIPredictionUpdate(BaseModel):
    """DDI预测更新模型"""
    is_favorite: Optional[bool] = Field(None, description="是否收藏")
    user_notes: Optional[str] = Field(None, max_length=1000, description="用户备注")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="用户评分")


class InteractionTypeResponse(BaseModel):
    """相互作用类型响应"""
    id: int = Field(..., description="类型ID")
    type_name: str = Field(..., description="类型名称")
    description: Optional[str] = Field(None, description="类型描述")
    severity_level: str = Field(..., description="严重程度")

    model_config = ConfigDict(from_attributes=True)


def calculate_smiles_hash(smiles: str) -> str:
    """计算SMILES字符串的哈希值"""
    return hashlib.sha256(smiles.encode('utf-8')).hexdigest()