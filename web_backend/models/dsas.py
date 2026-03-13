from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Index, ForeignKey, Float, Boolean, DateTime
from sqlalchemy.orm import relationship

from models.users import Base

class DSADrugNode(Base):
    """MFGNN-DSA 药物节点映射表"""
    __tablename__ = 'dsa_drug_nodes'

    __table_args__ = (
        Index('idx_dsa_drug_name', 'drug_name'),
        Index('idx_dsa_drug_smiles', 'smiles'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 核心字段：模型底层实际需要的图节点索引 (0 到 ndrug-1)
    model_index = Column(Integer, nullable=False, unique=True, comment="底层图模型中的节点索引")

    drug_name = Column(String(200), nullable=True, comment="药物名称")
    drug_name_cn = Column(String(200), nullable=True, comment="药物中文名称")
    smiles = Column(Text, nullable=True, comment="药物SMILES")


class DSASideEffectNode(Base):
    """MFGNN-DSA 副作用节点映射表"""
    __tablename__ = 'dsa_se_nodes'

    __table_args__ = (
        Index('idx_dsa_se_name', 'se_name'),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    # 核心字段：模型底层实际需要的图节点索引 (0 到 nse-1)
    model_index = Column(Integer, nullable=False, unique=True, comment="底层图模型中的节点索引")

    se_name = Column(String(255), nullable=False, comment="副作用名称/UMLS CUI")
    se_name_cn = Column(String(255), nullable=True, comment="副作用中文名称")

class DSAPrediction(Base):
    """药物不良反应(DSA)预测记录表"""
    __tablename__ = 'dsa_predictions'

    id = Column(Integer, primary_key=True, autoincrement=True, comment="预测ID")

    # 用户关联
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    user = relationship("User", back_populates="dsa_predictions")

    # 预测输入信息
    drug_identifier = Column(String(500), nullable=False, comment="药物标识符(名称或SMILES)")
    se_name = Column(String(255), nullable=False, comment="副作用名称")

    # 预测结果
    probability = Column(Float, nullable=False, comment="关联概率")
    prediction_label = Column(String(50), nullable=False, comment="预测标签(如: risk, safe)")

    # 交互状态
    is_favorite = Column(Boolean, default=False, comment="是否收藏")
    user_notes = Column(String(1000), nullable=True, comment="用户备注")

    # 时间戳
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")