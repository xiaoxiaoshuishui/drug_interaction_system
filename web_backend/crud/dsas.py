from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional, Tuple, Dict, List
from models.dsas import DSADrugNode, DSASideEffectNode


async def get_drug_index(db: AsyncSession, identifier: str) -> Optional[Tuple[int, str]]:
    """根据名称或SMILES查找药物的底层索引及标准名称"""
    stmt = select(DSADrugNode).where(
        or_(
            DSADrugNode.drug_name == identifier,
            DSADrugNode.smiles == identifier
        )
    )
    result = await db.execute(stmt)
    drug_node = result.scalar_one_or_none()

    if drug_node:
        return drug_node.model_index, drug_node.drug_name
    return None


async def get_se_index(db: AsyncSession, se_name: str) -> Optional[Tuple[int, str]]:
    """根据名称查找副作用的底层索引"""
    stmt = select(DSASideEffectNode).where(DSASideEffectNode.se_name == se_name)
    result = await db.execute(stmt)
    se_node = result.scalar_one_or_none()

    if se_node:
        return se_node.model_index, se_node.se_name
    return None

async def get_drug_names_by_indices(db: AsyncSession, indices: List[int]) -> Dict[int, str]:
    """批量根据模型索引查找药物名称"""
    if not indices:
        return {}
    stmt = select(DSADrugNode.model_index, DSADrugNode.drug_name).where(DSADrugNode.model_index.in_(indices))
    result = await db.execute(stmt)
    return {row.model_index: row.drug_name for row in result.all()}

async def get_se_names_by_indices(db: AsyncSession, indices: List[int]) -> Dict[int, str]:
    """批量根据模型索引查找副作用名称"""
    if not indices:
        return {}
    stmt = select(DSASideEffectNode.model_index, DSASideEffectNode.se_name).where(DSASideEffectNode.model_index.in_(indices))
    result = await db.execute(stmt)
    return {row.model_index: row.se_name for row in result.all()}