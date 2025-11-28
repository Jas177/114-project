from google.cloud import aiplatform
from google.cloud.aiplatform.matching_engine import MatchingEngineIndexEndpoint
from typing import List, Dict
from config import get_config
from utils.logger import logger
import json

config = get_config()


class VectorStoreManager:
    """Vertex AI Vector Search 管理器"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(VectorStoreManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化連接"""
        if not self._initialized:
            try:
                if not config.GOOGLE_API_KEY or not config.GOOGLE_PROJECT_ID:
                    logger.warning("未配置 Google Cloud，向量搜尋功能將不可用")
                    return
                
                # 初始化 Vertex AI
                aiplatform.init(
                    project=config.GOOGLE_PROJECT_ID,
                    location=config.GOOGLE_LOCATION
                )
                
                self._initialized = True
                logger.info(f"Vertex AI Vector Search 初始化成功")
                
                # 儲存向量數據到內存（簡化版本）
                # 生產環境應該使用 Vertex AI Matching Engine
                self._vector_store = {}  # {tenant_id: [{id, embedding, text, ...}]}
                
            except Exception as e:
                logger.error(f"Vertex AI 初始化失敗: {e}")
                logger.warning("向量搜尋功能將使用簡化的內存存儲")
                self._vector_store = {}
    
    def get_collection_name(self, tenant_id):
        """獲取租戶專屬集合名稱"""
        return f"tenant_{tenant_id}_knowledge"
    
    def create_collection(self, tenant_id):
        """為租戶創建向量集合"""
        collection_name = self.get_collection_name(tenant_id)
        
        # 初始化租戶的向量存儲
        if tenant_id not in self._vector_store:
            self._vector_store[tenant_id] = []
            logger.info(f"創建向量集合: {collection_name}")
        
        return collection_name
    
    def get_collection(self, tenant_id):
        """獲取租戶集合"""
        if tenant_id not in self._vector_store:
            self.create_collection(tenant_id)
        return self._vector_store[tenant_id]
    
    def insert_vectors(self, tenant_id, ids, embeddings, texts, document_ids, chunk_indices, metadata_list):
        """插入向量數據"""
        try:
            if tenant_id not in self._vector_store:
                self.create_collection(tenant_id)
            
            collection = self._vector_store[tenant_id]
            
            for i in range(len(ids)):
                vector_data = {
                    'id': ids[i],
                    'embedding': embeddings[i],
                    'text': texts[i],
                    'document_id': document_ids[i],
                    'chunk_index': chunk_indices[i],
                    'metadata': metadata_list[i] if i < len(metadata_list) else '{}'
                }
                collection.append(vector_data)
            
            logger.info(f"成功插入 {len(ids)} 條向量數據到租戶 {tenant_id}")
            return True
        except Exception as e:
            logger.error(f"插入向量數據失敗: {e}")
            return False
    
    def search(self, tenant_id, query_embedding, top_k=5, filter_expr=None):
        """搜尋相似向量"""
        try:
            if tenant_id not in self._vector_store:
                logger.warning(f"租戶 {tenant_id} 的向量集合不存在")
                return []
            
            collection = self._vector_store[tenant_id]
            
            if not collection:
                logger.warning(f"租戶 {tenant_id} 的向量集合為空")
                return []
            
            # 計算相似度
            results = []
            for vec_data in collection:
                similarity = self._cosine_similarity(query_embedding, vec_data['embedding'])
                results.append({
                    'id': vec_data['id'],
                    'score': similarity,
                    'entity': {
                        'text': vec_data['text'],
                        'document_id': vec_data['document_id'],
                        'chunk_index': vec_data['chunk_index'],
                        'metadata': vec_data.get('metadata', '{}')
                    }
                })
            
            # 排序並返回 top_k
            results.sort(key=lambda x: x['score'], reverse=True)
            top_results = results[:top_k]
            
            # 轉換為類似 Milvus 的結果格式
            class SearchHit:
                def __init__(self, data):
                    self.id = data['id']
                    self.score = data['score']
                    self.entity = data['entity']
            
            return [SearchHit(r) for r in top_results]
        except Exception as e:
            logger.error(f"向量搜尋失敗: {e}")
            return []
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """計算餘弦相似度"""
        try:
            import numpy as np
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except Exception as e:
            logger.error(f"相似度計算失敗: {e}")
            return 0.0
    
    def delete_by_document(self, tenant_id, document_id):
        """刪除文件的所有向量"""
        try:
            if tenant_id not in self._vector_store:
                return False
            
            collection = self._vector_store[tenant_id]
            self._vector_store[tenant_id] = [
                vec for vec in collection 
                if vec['document_id'] != document_id
            ]
            
            logger.info(f"成功刪除文件 {document_id} 的向量數據")
            return True
        except Exception as e:
            logger.error(f"刪除向量數據失敗: {e}")
            return False
    
    def delete_collection(self, tenant_id):
        """刪除租戶集合"""
        try:
            if tenant_id in self._vector_store:
                del self._vector_store[tenant_id]
                logger.info(f"成功刪除租戶 {tenant_id} 的向量集合")
                return True
            return False
        except Exception as e:
            logger.error(f"刪除集合失敗: {e}")
            return False


# 創建全局向量存儲管理器實例
vector_store_manager = VectorStoreManager()

