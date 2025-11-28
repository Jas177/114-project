from google.cloud import storage
from typing import Optional
from config import get_config
from utils.logger import logger
import os

config = get_config()


class CloudStorageService:
    """Google Cloud Storage 服務"""
    
    _instance = None
    _initialized = False
    _client = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(CloudStorageService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化 GCS 客戶端"""
        if not self._initialized:
            try:
                if not config.GCS_BUCKET_NAME:
                    logger.warning("未配置 GCS_BUCKET_NAME，文件將存儲在本地")
                    return
                
                self._client = storage.Client(project=config.GOOGLE_PROJECT_ID)
                self._bucket = self._client.bucket(config.GCS_BUCKET_NAME)
                
                # 檢查 bucket 是否存在
                if not self._bucket.exists():
                    logger.warning(f"Bucket {config.GCS_BUCKET_NAME} 不存在")
                    return
                
                self._initialized = True
                logger.info(f"GCS 初始化成功，Bucket: {config.GCS_BUCKET_NAME}")
            except Exception as e:
                logger.error(f"GCS 初始化失敗: {e}")
                self._initialized = False
    
    def upload_file(
        self,
        file_obj,
        tenant_id: str,
        filename: str,
        content_type: Optional[str] = None
    ) -> Optional[str]:
        """上傳文件到 GCS"""
        if not self._initialized:
            logger.warning("GCS 未初始化，無法上傳文件")
            return None
        
        try:
            # 構建 GCS 路徑
            blob_name = f"{config.GCS_DOCUMENTS_PREFIX}/{tenant_id}/documents/{filename}"
            blob = self._bucket.blob(blob_name)
            
            # 上傳文件
            if content_type:
                blob.content_type = content_type
            
            blob.upload_from_file(file_obj, rewind=True)
            
            # 返回 GCS URI
            gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{blob_name}"
            logger.info(f"文件上傳成功: {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"上傳文件到 GCS 失敗: {e}")
            return None
    
    def upload_from_filename(
        self,
        source_file_path: str,
        tenant_id: str,
        destination_filename: str
    ) -> Optional[str]:
        """從本地文件上傳到 GCS"""
        if not self._initialized:
            logger.warning("GCS 未初始化")
            return None
        
        try:
            blob_name = f"{config.GCS_DOCUMENTS_PREFIX}/{tenant_id}/documents/{destination_filename}"
            blob = self._bucket.blob(blob_name)
            
            blob.upload_from_filename(source_file_path)
            
            gcs_uri = f"gs://{config.GCS_BUCKET_NAME}/{blob_name}"
            logger.info(f"文件上傳成功: {gcs_uri}")
            return gcs_uri
        except Exception as e:
            logger.error(f"上傳文件失敗: {e}")
            return None
    
    def delete_file(self, gcs_uri: str) -> bool:
        """刪除 GCS 文件"""
        if not self._initialized:
            return False
        
        try:
            # 從 URI 提取 blob 名稱
            blob_name = gcs_uri.replace(f"gs://{config.GCS_BUCKET_NAME}/", "")
            blob = self._bucket.blob(blob_name)
            blob.delete()
            
            logger.info(f"文件刪除成功: {gcs_uri}")
            return True
        except Exception as e:
            logger.error(f"刪除文件失敗: {e}")
            return False
    
    def list_files(self, tenant_id: str) -> list:
        """列出租戶的所有文件"""
        if not self._initialized:
            return []
        
        try:
            prefix = f"{config.GCS_DOCUMENTS_PREFIX}/{tenant_id}/documents/"
            blobs = self._client.list_blobs(config.GCS_BUCKET_NAME, prefix=prefix)
            
            files = []
            for blob in blobs:
                files.append({
                    'name': blob.name.split('/')[-1],
                    'gcs_uri': f"gs://{config.GCS_BUCKET_NAME}/{blob.name}",
                    'size': blob.size,
                    'updated': blob.updated
                })
            
            return files
        except Exception as e:
            logger.error(f"列出文件失敗: {e}")
            return []


# 創建全局 Cloud Storage 服務實例
cloud_storage_service = CloudStorageService()
