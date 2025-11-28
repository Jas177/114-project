from typing import List, Dict
from services.embedding_service import embedding_service
from utils.vector_store import vector_store_manager
from utils.logger import logger
from config import get_config

config = get_config()

# 動態導入 RAG Engine（可選）
try:
    from services.rag_engine_service import rag_engine_service
    RAG_ENGINE_AVAILABLE = True
except ImportError:
    RAG_ENGINE_AVAILABLE = False
    logger.warning("RAG Engine 服務不可用，將使用向量存儲")


class RetrievalService:
    """檢索服務（支援 RAG Engine 和 Vector Store）"""
    
    @staticmethod
    def search(tenant_id: str, query: str, top_k: int = None) -> List[Dict]:
        """搜尋相關文檔片段"""
        if top_k is None:
            top_k = config.TOP_K_RETRIEVAL
        
        # 優先使用 RAG Engine
        if config.USE_RAG_ENGINE and RAG_ENGINE_AVAILABLE:
            return RetrievalService._search_with_rag_engine(tenant_id, query, top_k)
        else:
            return RetrievalService._search_with_vector_store(tenant_id, query, top_k)
    
    @staticmethod
    def _search_with_rag_engine(tenant_id: str, query: str, top_k: int) -> List[Dict]:
        """使用 RAG Engine 檢索"""
        try:
            logger.info(f"使用 RAG Engine 檢索: {query[:50]}...")
            
            results = rag_engine_service.retrieval_query(
                tenant_id=tenant_id,
                query=query,
                similarity_top_k=top_k
            )
            
            # 格式化為統一格式
            documents = []
            for i, result in enumerate(results):
                documents.append({
                    'id': f"rag_{i}",
                    'text': result.get('text', ''),
                    'document_id': result.get('source', '').split('/')[-1] if result.get('source') else '',
                    'chunk_index': i,
                    'score': result.get('score', 0.0),
                    'source': result.get('source', ''),
                    'metadata': result.get('metadata', {})
                })
            
            logger.info(f"RAG Engine 檢索到 {len(documents)} 個相關片段")
            return documents
        except Exception as e:
            logger.error(f"RAG Engine 檢索失敗: {e}，回退到向量存儲")
            return RetrievalService._search_with_vector_store(tenant_id, query, top_k)
    
    @staticmethod
    def _search_with_vector_store(tenant_id: str, query: str, top_k: int) -> List[Dict]:
        """使用向量存儲檢索"""
        try:
            logger.info(f"使用向量存儲檢索: {query[:50]}...")
            
            # 將查詢轉換為向量（使用 retrieval_query 任務類型）
            query_embedding = embedding_service.embed_query(query)
            
            if not query_embedding:
                logger.error("查詢嵌入失敗")
                return []
            
            # 向量搜尋
            results = vector_store_manager.search(
                tenant_id=tenant_id,
                query_embedding=query_embedding,
                top_k=top_k
            )
            
            # 格式化結果
            documents = []
            for hit in results:
                documents.append({
                    'id': hit.id,
                    'text': hit.entity.get('text', ''),
                    'document_id': hit.entity.get('document_id', ''),
                    'chunk_index': hit.entity.get('chunk_index', 0),
                    'score': hit.score,
                    'source': '',
                    'metadata': hit.entity.get('metadata', {})
                })
            
            logger.info(f"向量存儲檢索到 {len(documents)} 個相關片段")
            return documents
        except Exception as e:
            logger.error(f"向量存儲檢索失敗: {e}")
            return []
    
    @staticmethod
    def rerank(query: str, documents: List[Dict], top_n: int = None) -> List[Dict]:
        """重排序文檔"""
        if top_n is None:
            top_n = config.RERANK_TOP_N
        
        try:
            # 簡單的重排序邏輯：根據分數排序
            # 在生產環境中，應該使用專門的重排序模型（如 Cross-Encoder）
            sorted_docs = sorted(documents, key=lambda x: x['score'], reverse=True)
            return sorted_docs[:top_n]
        except Exception as e:
            logger.error(f"重排序失敗: {e}")
            return documents[:top_n] if len(documents) >= top_n else documents
    
    @staticmethod
    def retrieve_with_rerank(tenant_id: str, query: str) -> List[Dict]:
        """檢索並重排序"""
        # 先檢索較多的候選
        candidates = RetrievalService.search(
            tenant_id=tenant_id,
            query=query,
            top_k=config.TOP_K_RETRIEVAL
        )
        
        if not candidates:
            return []
        
        # 重排序
        final_docs = RetrievalService.rerank(
            query=query,
            documents=candidates,
            top_n=config.RERANK_TOP_N
        )
        
        return final_docs
