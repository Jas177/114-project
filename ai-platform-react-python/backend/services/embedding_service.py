import google.generativeai as genai
from typing import List
from config import get_config
from utils.logger import logger

config = get_config()


class EmbeddingService:
    """Gemini 向量嵌入服務"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 Gemini API"""
        if not self._initialized:
            try:
                if not config.GOOGLE_API_KEY:
                    logger.warning("未配置 GOOGLE_API_KEY，嵌入功能將不可用")
                    return
                
                genai.configure(api_key=config.GOOGLE_API_KEY)
                self._initialized = True
                logger.info(f"Gemini Embedding 服務初始化成功，模型: {config.EMBEDDING_MODEL}")
            except Exception as e:
                logger.error(f"Gemini Embedding 初始化失敗: {e}")
                raise
    
    def embed_text(self, text: str) -> List[float]:
        """將文本轉換為向量"""
        try:
            if not self._initialized:
                logger.error("Gemini Embedding 服務未初始化")
                return []
            
            result = genai.embed_content(
                model=config.EMBEDDING_MODEL,
                content=text,
                task_type="retrieval_document"
            )
            
            return result['embedding']
        except Exception as e:
            logger.error(f"文本嵌入失敗: {e}")
            return []
    
    def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """批次嵌入文本"""
        try:
            if not self._initialized:
                logger.error("Gemini Embedding 服務未初始化")
                return []
            
            embeddings = []
            
            # Gemini API 批次處理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]
                
                for text in batch:
                    result = genai.embed_content(
                        model=config.EMBEDDING_MODEL,
                        content=text,
                        task_type="retrieval_document"
                    )
                    embeddings.append(result['embedding'])
                
                logger.info(f"已處理 {min(i + batch_size, len(texts))}/{len(texts)} 個文本")
            
            return embeddings
        except Exception as e:
            logger.error(f"批次嵌入失敗: {e}")
            return []
    
    def embed_query(self, query: str) -> List[float]:
        """將查詢轉換為向量（用於檢索）"""
        try:
            if not self._initialized:
                logger.error("Gemini Embedding 服務未初始化")
                return []
            
            result = genai.embed_content(
                model=config.EMBEDDING_MODEL,
                content=query,
                task_type="retrieval_query"
            )
            
            return result['embedding']
        except Exception as e:
            logger.error(f"查詢嵌入失敗: {e}")
            return []


# 創建全局嵌入服務實例
embedding_service = EmbeddingService()

