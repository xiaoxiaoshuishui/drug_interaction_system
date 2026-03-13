import aiohttp
import logging
from typing import Dict, Any, List
from fastapi import HTTPException

from config.cache_config import get_json_cache, set_cache

logger = logging.getLogger(__name__)


class ModelClient:
    """MFGNN-DSA 模型服务客户端"""

    def __init__(
            self,
            base_url: str = "http://127.0.0.1:8002",
            timeout: int = 60
    ):
        self.base_url = base_url
        self.timeout = timeout
        self.session = None

    async def get_session(self) -> aiohttp.ClientSession:
        """获取或创建异步会话"""
        if self.session is None:
            self.session = aiohttp.ClientSession()
        return self.session

    async def close_session(self):
        """关闭会话"""
        if self.session:
            await self.session.close()
            self.session = None

    async def predict_single(
            self,
            se_index: int,
            drug_index: int
    ) -> Dict[str, Any]:
        """调用模型服务进行单个副作用预测 (带 Redis 缓存)"""

        # 1. 组装唯一的缓存 Key
        # 例如: "dsa:pred:se_15:drug_120"
        cache_key = f"dsa:pred:se_{se_index}:drug_{drug_index}"

        # 2. 尝试读取缓存
        cached_result = await get_json_cache(cache_key)
        if cached_result:
            logger.info(f"MFGNN-DSA 缓存命中 🎯: {cache_key}")
            return cached_result

        # 3. 没命中缓存，才去真实请求模型底层 8002 端口
        session = await self.get_session()
        try:
            payload = {
                "se_index": se_index,
                "drug_index": drug_index
            }
            async with session.post(
                    f"{self.base_url}/predict",
                    json=payload,
                    timeout=self.timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()

                    # 4. 拿到结果后，静默写入 Redis
                    # 因为模型权重通常不怎么变，这里的缓存可以设为 7 天 (604800 秒)
                    await set_cache(cache_key, result, expire=604800)
                    logger.info(f"MFGNN-DSA 写入缓存 💾: {cache_key}")

                    return result
                else:
                    error_text = await response.text()
                    logger.error(f"MFGNN-DSA 单条预测失败: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail="模型预测服务异常")
        except Exception as e:
            logger.error(f"MFGNN-DSA 请求异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"无法连接到模型服务: {str(e)}")


# 实例化全局客户端，供路由使用
dsas_client = ModelClient()