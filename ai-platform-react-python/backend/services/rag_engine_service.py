from vertexai.preview import rag
from google.cloud import aiplatform
from typing import Optional, List, Dict
from config import get_config
from utils.logger import logger

config = get_config()


class RAGEngineService:
    """Vertex AI RAG Engine 服務"""
    
    _instance = None
    _initialized = False
    _corpuses = {}  # {tenant_id: corpus_name}
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(RAGEngineService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 Vertex AI"""
        if not self._initialized and config.USE_RAG_ENGINE:
            try:
                if not config.GOOGLE_PROJECT_ID:
                    logger.warning("未配置 GOOGLE_PROJECT_ID，RAG Engine 將不可用")
                    return
                
                aiplatform.init(
                    project=config.GOOGLE_PROJECT_ID,
                    location=config.GOOGLE_LOCATION
                )
                
                self._initialized = True
                logger.info("Vertex AI RAG Engine 初始化成功")
            except Exception as e:
                logger.error(f"RAG Engine 初始化失敗: {e}")
                self._initialized = False
    
    def create_or_get_corpus(self, tenant_id: str) -> Optional[str]:
        """為租戶創建或獲取 RAG Corpus"""
        if not self._initialized:
            logger.warning("RAG Engine 未初始化")
            return None
        
        # 檢查快取
        if tenant_id in self._corpuses:
            return self._corpuses[tenant_id]
        
        try:
            corpus_display_name = f"{config.RAG_CORPUS_PREFIX}_{tenant_id}_corpus"
            
            # 嘗試列出現有 corpus
            corpuses = rag.list_corpora()
            for corpus in corpuses:
                if corpus.display_name == corpus_display_name:
                    self._corpuses[tenant_id] = corpus.name
                    logger.info(f"找到現有 Corpus: {corpus.name}")
                    return corpus.name
            
            # 創建新 corpus
            corpus = rag.create_corpus(
                display_name=corpus_display_name,
                description=f"Knowledge base for tenant {tenant_id}"
            )
            
            self._corpuses[tenant_id] = corpus.name
            logger.info(f"成功創建 Corpus: {corpus.name}")
            return corpus.name
        except Exception as e:
            logger.error(f"創建/獲取 Corpus 失敗: {e}")
            return None
    
    def import_files(
        self,
        tenant_id: str,
        gcs_uris: List[str],
        chunk_size: int = 512,
        chunk_overlap: int = 100
    ) -> Optional[List[str]]:
        """匯入文件到 RAG Corpus"""
        if not self._initialized:
            logger.warning("RAG Engine 未初始化")
            return None
        
        try:
            corpus_name = self.create_or_get_corpus(tenant_id)
            if not corpus_name:
                return None
            
            # 匯入文件
            response = rag.import_files(
                corpus_name=corpus_name,
                paths=gcs_uris,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            # 提取 RagFile 名稱
            rag_file_names = [f.name for f in response.imported_rag_files]
            
            logger.info(f"成功匯入 {len(rag_file_names)} 個文件到 Corpus")
            return rag_file_names
        except Exception as e:
            logger.error(f"匯入文件失敗: {e}")
            return None
    
    def retrieval_query(
        self,
        tenant_id: str,
        query: str,
        similarity_top_k: int = 5
    ) -> List[Dict]:
        """使用 RAG Engine 進行檢索"""
        if not self._initialized:
            logger.warning("RAG Engine 未初始化")
            return []
        
        try:
            corpus_name = self.create_or_get_corpus(tenant_id)
            if not corpus_name:
                return []
            
            # 執行檢索
            response = rag.retrieval_query(
                corpus_name=corpus_name,
                text=query,
                similarity_top_k=similarity_top_k
            )
            
            # 格式化結果
            results = []
            for context in response.contexts:
                results.append({
                    'text': context.text,
                    'score': context.score if hasattr(context, 'score') else 0.0,
                    'source': context.source_uri if hasattr(context, 'source_uri') else '',
                    'metadata': {}
                })
            
            logger.info(f"檢索到 {len(results)} 個相關片段")
            return results
        except Exception as e:
            logger.error(f"RAG 檢索失敗: {e}")
            return []
    
    def delete_files(self, tenant_id: str, rag_file_names: List[str]) -> bool:
        """刪除 RAG 文件"""
        if not self._initialized:
            return False
        
        try:
            corpus_name = self.create_or_get_corpus(tenant_id)
            if not corpus_name:
                return False
            
            for file_name in rag_file_names:
                rag.delete_file(name=file_name)
            
            logger.info(f"成功刪除 {len(rag_file_names)} 個 RAG 文件")
            return True
        except Exception as e:
            logger.error(f"刪除 RAG 文件失敗: {e}")
            return False
    
    def delete_corpus(self, tenant_id: str) -> bool:
        """刪除租戶的 Corpus"""
        if not self._initialized:
            return False
        
        try:
            corpus_name = self.create_or_get_corpus(tenant_id)
            if not corpus_name:
                return False
            
            rag.delete_corpus(name=corpus_name)
            
            # 從快取移除
            if tenant_id in self._corpuses:
                del self._corpuses[tenant_id]
            
            logger.info(f"成功刪除 Corpus: {corpus_name}")
            return True
        except Exception as e:
            logger.error(f"刪除 Corpus 失敗: {e}")
            return False


# 創建全局 RAG Engine 服務實例
rag_engine_service = RAGEngineService()
