from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, desc, func, case

from models.ddis import DDIPrediction, InteractionType, DrugInfo
from schemas.ddis import DDIPredictionRequest, DDIPredictionUpdate


def calculate_smiles_hash(smiles: str) -> str:
    """计算SMILES字符串的哈希值"""
    return hashlib.sha256(smiles.encode('utf-8')).hexdigest()


async def get_ddi_prediction(db: AsyncSession, prediction_id: int) -> Optional[DDIPrediction]:
    """获取单个预测记录"""
    query = select(DDIPrediction).where(DDIPrediction.id == prediction_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_user_ddi_predictions(
        db: AsyncSession,
        user_id: int,
        skip: int = 0,
        limit: int = 10,
        is_favorite: Optional[bool] = None,
        search: Optional[str] = None
) -> tuple[List[DDIPrediction], int]:
    """获取用户的预测记录"""
    # 构建查询条件
    conditions = [DDIPrediction.user_id == user_id]

    if is_favorite is not None:
        conditions.append(DDIPrediction.is_favorite == is_favorite)

    if search:
        search_condition = (
                (DDIPrediction.drug_a_name.ilike(f"%{search}%")) |
                (DDIPrediction.drug_b_name.ilike(f"%{search}%")) |
                (DDIPrediction.smiles_a.ilike(f"%{search}%")) |
                (DDIPrediction.smiles_b.ilike(f"%{search}%"))
        )
        conditions.append(search_condition)

    # 查询总数
    count_query = select(func.count()).select_from(DDIPrediction).where(*conditions)
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # 查询数据
    data_query = (
        select(DDIPrediction)
        .where(*conditions)
        .order_by(desc(DDIPrediction.created_at))
        .offset(skip)
        .limit(limit)
    )

    result = await db.execute(data_query)
    predictions = result.scalars().all()

    return predictions, total


async def create_ddi_prediction(
        db: AsyncSession,
        prediction_data: Dict[str, Any],
        user_id: Optional[int] = None
) -> DDIPrediction:
    """创建DDI预测记录"""

    # 计算SMILES哈希值
    smiles_a_hash = calculate_smiles_hash(prediction_data['smiles_a'])
    smiles_b_hash = calculate_smiles_hash(prediction_data['smiles_b'])

    # 创建预测记录
    new_prediction = DDIPrediction(
        user_id=user_id,
        drug_a_name=prediction_data.get('drug_a_name'),
        drug_b_name=prediction_data.get('drug_b_name'),
        smiles_a=prediction_data['smiles_a'],
        smiles_b=prediction_data['smiles_b'],
        interaction_type_id=prediction_data.get("interaction_type_id"),
        smiles_a_hash=smiles_a_hash,
        smiles_b_hash=smiles_b_hash,
        probability=prediction_data['probability'],
        prediction_label=prediction_data['prediction_label'],
        confidence=prediction_data['confidence'],
        model_type=prediction_data.get('model_type', 'dsn-ddi'),
        drug_a_info=prediction_data.get('drug_a_info'),
        drug_b_info=prediction_data.get('drug_b_info'),
        attention_analysis=prediction_data.get('attention_analysis'),
        layer_activations=prediction_data.get('layer_activations'),
        created_at=datetime.now(),
        updated_at=datetime.now()
    )

    db.add(new_prediction)
    await db.commit()
    await db.refresh(new_prediction)

    return new_prediction


async def update_ddi_prediction(
        db: AsyncSession,
        prediction_id: int,
        update_data: DDIPredictionUpdate,
        user_id: Optional[int] = None
) -> Optional[DDIPrediction]:
    """更新DDI预测记录的用户字段"""

    # 构建更新条件
    conditions = [DDIPrediction.id == prediction_id]
    if user_id is not None:
        conditions.append(DDIPrediction.user_id == user_id)

    # 执行更新
    stmt = (
        update(DDIPrediction)
        .where(*conditions)
        .values(
            **update_data.model_dump(exclude_unset=True, exclude_none=True),
            updated_at=datetime.now()
        )
        .returning(DDIPrediction)
    )

    result = await db.execute(stmt)
    await db.commit()

    updated_prediction = result.scalar_one_or_none()

    return updated_prediction


async def delete_ddi_prediction(
        db: AsyncSession,
        prediction_id: int,
        user_id: Optional[int] = None
) -> bool:
    """删除DDI预测记录"""

    # 构建删除条件
    conditions = [DDIPrediction.id == prediction_id]
    if user_id is not None:
        conditions.append(DDIPrediction.user_id == user_id)

    # 执行删除
    stmt = delete(DDIPrediction).where(*conditions)
    result = await db.execute(stmt)
    await db.commit()

    return result.rowcount > 0


async def check_duplicate_prediction(
        db: AsyncSession,
        smiles_a: str,
        smiles_b: str,
        user_id: Optional[int] = None,
        time_window_hours: int = 24
) -> Optional[DDIPrediction]:
    """检查是否存在重复预测（在一定时间内）"""

    smiles_a_hash = calculate_smiles_hash(smiles_a)
    smiles_b_hash = calculate_smiles_hash(smiles_b)

    # 构建查询条件
    conditions = [
        DDIPrediction.smiles_a_hash == smiles_a_hash,
        DDIPrediction.smiles_b_hash == smiles_b_hash,
        DDIPrediction.created_at >= datetime.now() - timedelta(hours=time_window_hours)
    ]

    if user_id is not None:
        conditions.append(DDIPrediction.user_id == user_id)

    # 按时间倒序查找最新的记录
    query = (
        select(DDIPrediction)
        .where(*conditions)
        .order_by(desc(DDIPrediction.created_at))
        .limit(1)
    )

    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_prediction_stats(
        db: AsyncSession,
        user_id: int
) -> Dict[str, Any]:
    """获取用户的预测统计信息"""

    # 1. 总数、风险数、收藏数
    stats_query = select(
        func.count().label("total"),
        func.count().filter(DDIPrediction.prediction_label == 'risk').label("risk_count"),
        func.count().filter(DDIPrediction.is_favorite == True).label("favorite_count")
    ).where(DDIPrediction.user_id == user_id)

    stats_result = await db.execute(stats_query)
    stats_row = stats_result.one()

    total = stats_row.total or 0
    risk_count = stats_row.risk_count or 0
    favorite_count = stats_row.favorite_count or 0

    # 最近7天预测趋势
    week_ago = datetime.now() - timedelta(days=7)
    trend_query = select(
        func.date(DDIPrediction.created_at).label('date'),
        func.count().label('count')
    ).where(
        (DDIPrediction.user_id == user_id) &
        (DDIPrediction.created_at >= week_ago)
    ).group_by(
        func.date(DDIPrediction.created_at)
    ).order_by(
        func.date(DDIPrediction.created_at)
    )

    trend_result = await db.execute(trend_query)
    trend_data = trend_result.all()

    return {
        "total_predictions": total,
        "risk_predictions": risk_count,
        "favorite_predictions": favorite_count,
        "safe_predictions": total - risk_count,
        "trend_last_7_days": [
            {"date": row.date.isoformat(), "count": row.count}
            for row in trend_data
        ]
    }


async def get_interaction_types(db: AsyncSession) -> List[InteractionType]:
    """获取所有相互作用类型"""
    query = select(InteractionType).order_by(InteractionType.id)
    result = await db.execute(query)
    return result.scalars().all()


async def get_drug_info_by_smiles(
        db: AsyncSession,
        smiles: str
) -> Optional[DrugInfo]:
    """根据SMILES获取药物信息"""
    smiles_hash = calculate_smiles_hash(smiles)
    query = select(DrugInfo).where(DrugInfo.smiles_hash == smiles_hash)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_or_update_drug_info(
        db: AsyncSession,
        smiles: str,
        drug_data: Dict[str, Any]
) -> DrugInfo:
    """创建或更新药物信息"""
    smiles_hash = calculate_smiles_hash(smiles)

    # 检查是否存在
    existing_drug = await get_drug_info_by_smiles(db, smiles)

    if existing_drug:
        # 更新现有记录
        for key, value in drug_data.items():
            if hasattr(existing_drug, key):
                setattr(existing_drug, key, value)
        existing_drug.updated_at = datetime.now()
        await db.commit()
        await db.refresh(existing_drug)
        return existing_drug
    else:
        # 创建新记录
        new_drug = DrugInfo(
            smiles=smiles,
            smiles_hash=smiles_hash,
            **drug_data,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db.add(new_drug)
        await db.commit()
        await db.refresh(new_drug)
        return new_drug


async def create_ddi_predictions_bulk(
        db: AsyncSession,
        user_id: int,
        predictions_data: list[dict]
) -> bool:
    """批量创建 DDI 预测记录"""
    if not predictions_data:
        return True

    db_predictions = []
    for data in predictions_data:
        # 同样需要计算哈希值
        smiles_a_hash = calculate_smiles_hash(data['smiles_a'])
        smiles_b_hash = calculate_smiles_hash(data['smiles_b'])

        db_prediction = DDIPrediction(
            user_id=user_id,
            drug_a_name=data.get('drug_a_name'),
            drug_b_name=data.get('drug_b_name'),
            smiles_a=data['smiles_a'],
            smiles_b=data['smiles_b'],
            interaction_type_id=data.get("interaction_type_id", 0),
            smiles_a_hash=smiles_a_hash,
            smiles_b_hash=smiles_b_hash,
            probability=data.get('probability', 0.0),
            prediction_label=data.get('prediction_label', 'safe'),
            confidence=data.get('confidence', 'low'),
            model_type='dsn-ddi',
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        db_predictions.append(db_prediction)

    db.add_all(db_predictions)
    await db.commit()
    return True