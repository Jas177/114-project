import os
import uuid
from datetime import datetime
from typing import Optional, List
from bson import ObjectId
from werkzeug.utils import secure_filename
from models.document import Document, DocumentCreate, DocumentStatus, document_to_dict, dict_to_document
from services.embedding_service import embedding_service
from utils.db_manager import get_documents_collection
from utils.file_parser import FileParser
from utils.text_processor import TextProcessor
from utils.vector_store import vector_store_manager
from utils.logger import logger
from config import get_config

config = get_config()


class DocumentService:
    """文件服務"""
    
    @staticmethod
    def upload_document(file, tenant_id: str, filename: str) -> Optional[dict]:
        """上傳文件"""
        try:
            # 確保上傳目錄存在
            upload_dir = os.path.join(config.UPLOAD_FOLDER, tenant_id)
            os.makedirs(upload_dir, exist_ok=True)
            
            # 生成安全的文件名
            safe_filename = secure_filename(filename)
            file_id = str(uuid.uuid4())
            file_ext = os.path.splitext(safe_filename)[1]
            new_filename = f"{file_id}{file_ext}"
            file_path = os.path.join(upload_dir, new_filename)
            
            # 保存文件
            file.save(file_path)
            file_size = os.path.getsize(file_path)
            
            # 創建文件記錄
            doc_id = str(ObjectId())
            document = Document(
                id=doc_id,
                tenant_id=tenant_id,
                filename=safe_filename,
                file_path=file_path,
                file_size=file_size,
                file_type=file_ext.lower(),
                status=DocumentStatus.PROCESSING
            )
            
            # 保存到資料庫
            documents_collection = get_documents_collection()
            documents_collection.insert_one(document_to_dict(document))
            
            logger.info(f"文件上傳成功: {safe_filename}")
            
            # 異步處理文件（這裡同步處理，生產環境應使用 Celery）
            DocumentService.process_document(doc_id, tenant_id)
            
            return document.dict()
        except Exception as e:
            logger.error(f"文件上傳失敗: {e}")
            return None
    
    @staticmethod
    def process_document(document_id: str, tenant_id: str) -> bool:
        """處理文件 - 提取文本、分塊、嵌入"""
        try:
            documents_collection = get_documents_collection()
            doc_data = documents_collection.find_one({'_id': ObjectId(document_id)})
            
            if not doc_data:
                logger.error(f"文件不存在: {document_id}")
                return False
            
            document = dict_to_document(doc_data)
            
            # 1. 提取文本
            logger.info(f"開始處理文件: {document.filename}")
            text = FileParser.parse_file(document.file_path)
            
            if not text or len(text.strip()) < 10:
                documents_collection.update_one(
                    {'_id': ObjectId(document_id)},
                    {'$set': {
                        'status': DocumentStatus.FAILED,
                        'error_message': '文件內容為空或無法解析',
                        'updated_at': datetime.utcnow()
                    }}
                )
                return False
            
            # 2. 文本分塊
            chunks = TextProcessor.split_into_chunks(text)
            logger.info(f"文本已分割為 {len(chunks)} 個塊")
            
            # 3. 生成嵌入向量
            chunk_texts = [chunk['text'] for chunk in chunks]
            embeddings = embedding_service.embed_batch(chunk_texts)
            
            if not embeddings:
                documents_collection.update_one(
                    {'_id': ObjectId(document_id)},
                    {'$set': {
                        'status': DocumentStatus.FAILED,
                        'error_message': '嵌入生成失敗',
                        'updated_at': datetime.utcnow()
                    }}
                )
                return False
            
            # 4. 存入向量資料庫
            ids = [f"{document_id}_{i}" for i in range(len(chunks))]
            document_ids = [document_id] * len(chunks)
            chunk_indices = list(range(len(chunks)))
            metadata_list = ['{}'] * len(chunks)  # 可以添加更多元數據
            
            success = vector_store_manager.insert_vectors(
                tenant_id=tenant_id,
                ids=ids,
                embeddings=embeddings,
                texts=chunk_texts,
                document_ids=document_ids,
                chunk_indices=chunk_indices,
                metadata_list=metadata_list
            )
            
            if not success:
                logger.warning("向量存儲失敗，但文件處理繼續")
            
            # 5. 提取關鍵詞和語言
            keywords = TextProcessor.extract_keywords(text)
            language = TextProcessor.detect_language(text)
            
            # 6. 更新文件狀態
            documents_collection.update_one(
                {'_id': ObjectId(document_id)},
                {'$set': {
                    'status': DocumentStatus.COMPLETED,
                    'chunks_count': len(chunks),
                    'text_preview': text[:500],
                    'language': language,
                    'keywords': keywords,
                    'processed_at': datetime.utcnow(),
                    'updated_at': datetime.utcnow()
                }}
            )
            
            logger.info(f"文件處理完成: {document.filename}")
            return True
        except Exception as e:
            logger.error(f"文件處理失敗: {e}")
            
            # 更新失敗狀態
            documents_collection = get_documents_collection()
            documents_collection.update_one(
                {'_id': ObjectId(document_id)},
                {'$set': {
                    'status': DocumentStatus.FAILED,
                    'error_message': str(e),
                    'updated_at': datetime.utcnow()
                }}
            )
            return False
    
    @staticmethod
    def get_documents(tenant_id: str) -> List[dict]:
        """獲取租戶的所有文件"""
        try:
            documents_collection = get_documents_collection()
            docs = documents_collection.find({'tenant_id': tenant_id}).sort('created_at', -1)
            
            return [dict_to_document(doc).dict() for doc in docs]
        except Exception as e:
            logger.error(f"獲取文件列表失敗: {e}")
            return []
    
    @staticmethod
    def delete_document(document_id: str, tenant_id: str) -> bool:
        """刪除文件"""
        try:
            documents_collection = get_documents_collection()
            doc_data = documents_collection.find_one({'_id': ObjectId(document_id), 'tenant_id': tenant_id})
            
            if not doc_data:
                logger.warning(f"文件不存在或無權限: {document_id}")
                return False
            
            document = dict_to_document(doc_data)
            
            # 刪除向量數據
            vector_store_manager.delete_by_document(tenant_id, document_id)
            
            # 刪除物理文件
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # 刪除資料庫記錄
            documents_collection.delete_one({'_id': ObjectId(document_id)})
            
            logger.info(f"文件已刪除: {document.filename}")
            return True
        except Exception as e:
            logger.error(f"刪除文件失敗: {e}")
            return False
