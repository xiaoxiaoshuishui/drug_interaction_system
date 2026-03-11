from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column, Integer, String, Float, Text, DateTime,
    ForeignKey, Enum, JSON, Index, Boolean
)
from sqlalchemy.orm import relationship
from models.users import Base



class DDIPrediction(Base):
    """药物相互作用预测记录表"""
    __tablename__ = 'ddi_predictions'

    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_smiles_pair', 'smiles_a_hash', 'smiles_b_hash'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="预测ID")

    # 用户关联
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User", back_populates="ddi_predictions")

    # 药物信息
    drug_a_name = Column(String(100), nullable=True, comment="药物A名称")
    drug_b_name = Column(String(100), nullable=True, comment="药物B名称")
    smiles_a = Column(Text, nullable=False, comment="药物A的SMILES")
    smiles_b = Column(Text, nullable=False, comment="药物B的SMILES")

    # 哈希值用于快速查找重复预测
    smiles_a_hash = Column(String(64), nullable=False, comment="SMILES A的哈希值")
    smiles_b_hash = Column(String(64), nullable=False, comment="SMILES B的哈希值")

    # 预测结果
    probability = Column(Float, nullable=False, comment="相互作用概率")
    prediction_label = Column(
        Enum('safe', 'risk', name="prediction_label_enum"),
        nullable=False,
        comment="预测标签"
    )
    confidence = Column(
        Enum('low', 'medium', 'high', name="confidence_enum"),
        nullable=False,
        comment="置信度"
    )

    # 模型信息
    model_type = Column(String(50), default='dsn-ddi', comment="使用的模型类型")
    model_version = Column(String(20), nullable=True, comment="模型版本")

    # 额外信息（JSON格式存储）
    drug_a_info = Column(JSON, nullable=True, comment="药物A的详细信息")
    drug_b_info = Column(JSON, nullable=True, comment="药物B的详细信息")
    attention_analysis = Column(JSON, nullable=True, comment="注意力分析结果")
    layer_activations = Column(JSON, nullable=True, comment="层激活信息")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 用户交互字段
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    user_notes = Column(Text, nullable=True, comment="用户备注")
    user_rating = Column(Integer, nullable=True, comment="用户评分（1-5）")

    def __repr__(self):
        return f"<DDIPrediction(id={self.id}, drugs='{self.drug_a_name} & {self.drug_b_name}', prob={self.probability})>"


class InteractionType(Base):
    """相互作用类型表"""
    __tablename__ = 'interaction_types'

    id = Column(Integer, primary_key=True, comment="类型ID")
    type_name = Column(String(100), nullable=False, unique=True, comment="类型名称")
    description = Column(Text, nullable=True, comment="类型描述")
    severity_level = Column(
        Enum('low', 'medium', 'high', 'severe', name="severity_enum"),
        nullable=False,
        comment="严重程度"
    )
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")


class DrugInfo(Base):
    """药物信息缓存表"""
    __tablename__ = 'drug_info_cache'

    __table_args__ = (
        Index('idx_smiles_hash', 'smiles_hash'),
        Index('idx_drug_name', 'drug_name'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True, comment="药物ID")
    smiles = Column(Text, nullable=False, comment="SMILES字符串")
    smiles_hash = Column(String(64), nullable=False, unique=True, comment="SMILES哈希值")
    drug_name = Column(String(200), nullable=True, comment="药物名称")
    drugbank_id = Column(String(20), nullable=True, comment="DrugBank ID")
    cas_number = Column(String(50), nullable=True, comment="CAS号")

    # 分子属性
    molecular_weight = Column(Float, nullable=True, comment="分子量")
    logp = Column(Float, nullable=True, comment="LogP")
    hbd_count = Column(Integer, nullable=True, comment="氢键供体数")
    hba_count = Column(Integer, nullable=True, comment="氢键受体数")

    # 其他信息
    description = Column(Text, nullable=True, comment="药物描述")
    indication = Column(Text, nullable=True, comment="适应症")
    side_effects = Column(Text, nullable=True, comment="副作用")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 来源信息
    source = Column(String(50), default='user_input', comment="数据来源")
    is_verified = Column(Boolean, default=False, comment="是否已验证")

    def __repr__(self):
        return f"<DrugInfo(id={self.id}, name='{self.drug_name}', smiles_hash='{self.smiles_hash}')>"