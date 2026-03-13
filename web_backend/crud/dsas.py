from typing import Optional, List, Tuple
from sqlalchemy import select, or_, func, desc, delete
from models.dsas import DSADrugNode, DSASideEffectNode, DSAPrediction
from sqlalchemy.ext.asyncio import AsyncSession

# 1. 根据标识符查药物索引 (支持中文查询)
async def get_drug_index(db: AsyncSession, identifier: str):
    stmt = select(DSADrugNode).where(
        or_(
            DSADrugNode.drug_name.ilike(f"%{identifier}%"),
            DSADrugNode.drug_name_cn.ilike(f"%{identifier}%"),
            DSADrugNode.smiles == identifier
        )
    )
    result = await db.execute(stmt)
    drug = result.scalars().first()
    if drug:
        # 优先返回中文名用于展示，没有中文就回退到英文
        display_name = drug.drug_name_cn if drug.drug_name_cn else drug.drug_name
        return drug.model_index, display_name
    return None

# 2. 根据名称查副作用索引
async def get_se_index(db: AsyncSession, se_name: str):
    stmt = select(DSASideEffectNode).where(
        or_(
            DSASideEffectNode.se_name.ilike(f"%{se_name}%"),
            DSASideEffectNode.se_name_cn.ilike(f"%{se_name}%") # 增加中文列匹配
        )
    )
    result = await db.execute(stmt)
    se = result.scalars().first()
    if se:
        display_name = se.se_name_cn if se.se_name_cn else se.se_name
        return se.model_index, display_name
    return None

# 3. 批量获取药物名称（图谱展示用）
async def get_drug_names_by_indices(db: AsyncSession, indices: list[int]):
    stmt = select(DSADrugNode).where(DSADrugNode.model_index.in_(indices))
    result = await db.execute(stmt)
    drugs = result.scalars().all()
    return {d.model_index: (d.drug_name_cn if d.drug_name_cn else d.drug_name) for d in drugs}

# 4. 批量获取副作用名称（图谱展示用）
async def get_se_names_by_indices(db: AsyncSession, indices: list[int]):
    stmt = select(DSASideEffectNode).where(DSASideEffectNode.model_index.in_(indices))
    result = await db.execute(stmt)
    ses = result.scalars().all()
    return {s.model_index: (s.se_name_cn if s.se_name_cn else s.se_name) for s in ses}

# 1. 创建 DSA 预测记录
async def create_dsa_prediction(db: AsyncSession, user_id: int, prediction_data: dict) -> DSAPrediction:
    db_prediction = DSAPrediction(
        user_id=user_id,
        drug_identifier=prediction_data.get("drug_identifier"),
        se_name=prediction_data.get("se_name"),
        probability=prediction_data.get("probability"),
        prediction_label=prediction_data.get("prediction_label")
    )
    db.add(db_prediction)
    await db.commit()
    await db.refresh(db_prediction)
    return db_prediction


# 2. 获取 DSA 预测历史列表 (带分页)
async def get_user_dsa_predictions(
        db: AsyncSession, user_id: int, skip: int = 0, limit: int = 10
) -> Tuple[List[DSAPrediction], int]:
    query = select(DSAPrediction).where(DSAPrediction.user_id == user_id)

    # 算总数
    count_query = select(func.count(DSAPrediction.id)).where(DSAPrediction.user_id == user_id)
    total = await db.scalar(count_query)

    # 查分页数据
    stmt = query.order_by(desc(DSAPrediction.created_at)).offset(skip).limit(limit)
    result = await db.execute(stmt)
    return result.scalars().all(), total


# 3. 更新 DSA 记录 (收藏/备注)
async def update_dsa_prediction(
        db: AsyncSession, prediction_id: int, user_id: int, update_data: dict
) -> Optional[DSAPrediction]:
    stmt = select(DSAPrediction).where(DSAPrediction.id == prediction_id, DSAPrediction.user_id == user_id)
    result = await db.execute(stmt)
    db_prediction = result.scalars().first()

    if not db_prediction:
        return None

    if "is_favorite" in update_data and update_data["is_favorite"] is not None:
        db_prediction.is_favorite = update_data["is_favorite"]

    await db.commit()
    await db.refresh(db_prediction)
    return db_prediction


# 4. 删除 DSA 记录
async def delete_dsa_prediction(db: AsyncSession, prediction_id: int, user_id: int) -> bool:
    stmt = delete(DSAPrediction).where(DSAPrediction.id == prediction_id, DSAPrediction.user_id == user_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def create_dsa_predictions_bulk(db: AsyncSession, user_id: int, predictions_data: list[dict]) -> bool:
    if not predictions_data:
        return True

    db_predictions = []
    for data in predictions_data:
        db_prediction = DSAPrediction(
            user_id=user_id,
            drug_identifier=data.get("drug_identifier"),
            se_name=data.get("se_name"),
            probability=data.get("probability"),
            prediction_label=data.get("prediction_label")
        )
        db_predictions.append(db_prediction)

    db.add_all(db_predictions)
    await db.commit()
    return True