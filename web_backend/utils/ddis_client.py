import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
import json
from datetime import datetime
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ModelClient:
    """模型服务客户端"""

    def __init__(
            self,
            base_url: str = "http://localhost:8001",
            timeout: int = 120
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
            smiles_a: str,
            smiles_b: str,
            drug_a_name: Optional[str] = None,
            drug_b_name: Optional[str] = None,
            interaction_type_id: int = 0,
            include_attention: bool = False,
            include_activations: bool = False
    ) -> Dict[str, Any]:
        """调用模型服务进行单个预测"""
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

                    # 确定预测标签
                    if processed_result["probability"] > 0.5:
                        processed_result["prediction_label"] = "risk"
                    else:
                        processed_result["prediction_label"] = "safe"

                    return processed_result

                elif response.status == 400:
                    error_text = await response.text()
                    logger.warning(f"模型服务输入错误: {error_text}")
                    raise HTTPException(
                        status_code=400,
                        detail=f"模型输入错误: {error_text}"
                    )

                else:
                    error_text = await response.text()
                    logger.error(f"模型服务错误: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"模型服务错误: {response.status}"
                    )

        except asyncio.TimeoutError:
            logger.error("模型服务请求超时")
            raise HTTPException(
                status_code=504,
                detail="模型服务响应超时"
            )
        except aiohttp.ClientError as e:
            logger.error(f"连接模型服务失败: {str(e)}")
            raise HTTPException(
                status_code=503,
                detail=f"模型服务暂时不可用: {str(e)}"
            )

    async def predict_batch(
            self,
            predictions: List[Dict[str, Any]],
            parallel: bool = False
    ) -> Dict[str, Any]:
        """批量预测"""
        session = await self.get_session()

        request_data = {
            "requests": predictions,
            "parallel": parallel
        }

        try:
            async with session.post(
                    f"{self.base_url}/batch_predict",
                    json=request_data,
                    timeout=self.timeout * len(predictions)  # 根据数量增加超时
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    return {
                        "success": True,
                        "total": result.get("total", 0),
                        "successful": result.get("successful", 0),
                        "failed": result.get("failed", 0),
                        "results": result.get("results", []),
                        "errors": result.get("errors", [])
                    }
                else:
                    error_text = await response.text()
                    logger.error(f"批量预测失败: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail="批量预测失败"
                    )

        except Exception as e:
            logger.error(f"批量预测异常: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"批量预测异常: {str(e)}"
            )

    async def health_check(self) -> Dict[str, Any]:
        """检查模型服务健康状态"""
        session = await self.get_session()

        try:
            async with session.get(
                    f"{self.base_url}/health",
                    timeout=10
            ) as response:

                if response.status == 200:
                    result = await response.json()
                    return {
                        "status": "healthy",
                        "model_loaded": result.get("model_loaded", False),
                        "device": result.get("device", "unknown"),
                        "timestamp": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "detail": f"HTTP {response.status}",
                        "timestamp": datetime.now().isoformat()
                    }

        except Exception as e:
            return {
                "status": "unavailable",
                "detail": str(e),
                "timestamp": datetime.now().isoformat()
            }

    async def simple_predict(
            self,
            smiles_a: str,
            smiles_b: str,
            interaction_type_id: int = 0
    ) -> Dict[str, Any]:
        """简化版预测"""
        session = await self.get_session()

        try:
            payload = {
                "smiles_a": smiles_a,
                "smiles_b": smiles_b,
                "interaction_type_id": interaction_type_id
            }

            async with session.post(
                    f"{self.base_url}/predict/simple",
                    json=payload,  # 改为json参数
                    timeout=self.timeout
            ) as response:

                if response.status == 200:
                    return await response.json()
                else:
                    error_text = await response.text()
                    logger.error(f"简化预测失败: {response.status} - {error_text}")
                    raise HTTPException(
                        status_code=500,
                        detail="简化预测失败"
                    )

        except Exception as e:
            logger.error(f"简化预测异常: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"简化预测异常: {str(e)}"
            )

# 全局模型客户端实例
ddis_client = ModelClient()