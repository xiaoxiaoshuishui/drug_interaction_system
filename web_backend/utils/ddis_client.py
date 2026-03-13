import aiohttp
import asyncio
import hashlib
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import logging
from fastapi import HTTPException

# 👇 引入缓存配置
from config.cache_config import get_json_cache, set_cache

logger = logging.getLogger(__name__)


class ModelClient:
    """DSN-DDI 模型服务客户端"""

    def __init__(
            self,
            base_url: str = "http://localhost:8001",
            timeout: int = 120
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        if self.session:
            await self.session.close()
            self.session = None

    # 生成短小精悍的 MD5 缓存键
    def _generate_smiles_hash(self, smiles: str) -> str:
        return hashlib.md5(smiles.encode('utf-8')).hexdigest()[:16]

    async def predict_single(
            self,
            smiles_a: str,
            smiles_b: str,
            drug_a_name: Optional[str] = None,
            drug_b_name: Optional[str] = None,
            interaction_type_id: int = 0,
            include_attention: bool = False,
            include_activations: bool = False
    ) -> Dict[str, Any]:
        """调用模型服务进行单个预测 (带 Redis 拦截与动态名称替换)"""

        # 1. 组装缓存 Key (包含 SMILES哈希、反应类型、以及是否需要Attention特征)
        hash_a = self._generate_smiles_hash(smiles_a)
        hash_b = self._generate_smiles_hash(smiles_b)
        cache_key = f"ddi:pred:{hash_a}_{hash_b}_t{interaction_type_id}_att{int(include_attention)}"

        # 2. 尝试读取缓存
        cached_result = await get_json_cache(cache_key)
        if cached_result:
            logger.info(f"DSN-DDI 缓存命中 🎯: {cache_key}")

            # 🌟 核心细节：动态替换名称！
            # 不同的用户可能用不同的名字(比如"阿司匹林"和"Aspirin")搜相同的SMILES。
            # 命中缓存后，我们要把返回结果里的名字替换成当前用户输入的，防止前端显示错乱。
            if "drug_a_info" in cached_result:
                cached_result["drug_a_info"]["name"] = drug_a_name or "Drug A"
            if "drug_b_info" in cached_result:
                cached_result["drug_b_info"]["name"] = drug_b_name or "Drug B"

            # 伪造一下处理时间和时间戳，让前端觉得是新鲜的
            cached_result["processing_time_ms"] = 0.0
            cached_result["timestamp"] = datetime.now().isoformat()
            return cached_result

        # 3. 没命中缓存，发起真实网络请求
        session = await self.get_session()
        request_data = {
            "smiles_a": smiles_a,
            "smiles_b": smiles_b,
            "drug_a_name": drug_a_name or "Drug A",
            "drug_b_name": drug_b_name or "Drug B",
            "interaction_type_id": interaction_type_id,
            "include_attention": include_attention,
            "include_activations": include_activations
        }

        start_time = datetime.now()

        try:
            async with session.post(
                    f"{self.base_url}/predict",
                    json=request_data,
                    timeout=self.timeout
            ) as response:

                processing_time = (datetime.now() - start_time).total_seconds() * 1000
                if response.status == 200:
                    result = await response.json()

                    # 提取关键信息
                    processed_result = {
                        "success": True,
                        "prediction": result.get("prediction"),
                        "probability": result.get("probability"),
                        "confidence": result.get("confidence"),
                        "drug_a_info": result.get("drug_a_info"),
                        "drug_b_info": result.get("drug_b_info"),
                        "attention_analysis": result.get("attention_analysis"),
                        "layer_activations": result.get("layer_activations"),
                        "model_used": "dsn-ddi",
                        "processing_time_ms": processing_time,
                        "timestamp": datetime.now().isoformat()
                    }

                    if processed_result["probability"] > 0.5:
                        processed_result["prediction_label"] = "risk"
                    else:
                        processed_result["prediction_label"] = "safe"

                    # 4. 拿到结果后，静默写入 Redis (缓存7天)
                    await set_cache(cache_key, processed_result, expire=604800)
                    logger.info(f"DSN-DDI 写入缓存 💾: {cache_key}")

                    return processed_result

                elif response.status == 400:
                    error_text = await response.text()
                    logger.warning(f"模型服务输入错误: {error_text}")
                    raise HTTPException(status_code=400, detail=f"模型输入错误: {error_text}")

                else:
                    error_text = await response.text()
                    logger.error(f"模型服务错误: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail=f"模型服务错误: {response.status}")

        except asyncio.TimeoutError:
            logger.error("模型服务请求超时")
            raise HTTPException(status_code=504, detail="模型服务响应超时")
        except aiohttp.ClientError as e:
            logger.error(f"连接模型服务失败: {str(e)}")
            raise HTTPException(status_code=503, detail=f"模型服务暂时不可用: {str(e)}")

    # 这里保留了我们之前加的批量预测接口
    async def predict_batch(self, pairs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """调用模型服务进行批量预测"""
        session = await self.get_session()
        try:
            payload = {"pairs": pairs}
            async with session.post(
                    f"{self.base_url}/predict_batch",
                    json=payload,
                    timeout=self.timeout
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"DSN-DDI 批量预测失败: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail="模型批量预测服务异常")
        except Exception as e:
            logger.error(f"DSN-DDI 请求异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"无法连接到模型服务: {str(e)}")


ddis_client = ModelClient()