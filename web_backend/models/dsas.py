from sqlalchemy import Column, Integer, String, Text, Index
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

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