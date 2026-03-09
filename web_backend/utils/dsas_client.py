import aiohttp
import logging
from typing import Dict, Any, List
from fastapi import HTTPException

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
        """调用模型服务进行单个副作用预测"""
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
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"MFGNN-DSA 单条预测失败: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail="模型预测服务异常")
        except Exception as e:
            logger.error(f"MFGNN-DSA 请求异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"无法连接到模型服务: {str(e)}")

    async def predict_batch(
            self,
            pairs: List[List[int]]
    ) -> Dict[str, Any]:
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
                    logger.error(f"MFGNN-DSA 批量预测失败: {response.status} - {error_text}")
                    raise HTTPException(status_code=500, detail="模型批量预测服务异常")
        except Exception as e:
            logger.error(f"MFGNN-DSA 批量请求异常: {str(e)}")
            raise HTTPException(status_code=500, detail=f"无法连接到模型服务: {str(e)}")

# 实例化全局客户端，供路由使用
dsas_client = ModelClient()