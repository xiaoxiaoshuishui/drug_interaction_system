from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import Optional, Tuple
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