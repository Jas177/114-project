from typing import Optional, List
from bson import ObjectId
from models.tenant import Tenant, TenantCreate, TenantUpdate, tenant_to_dict, dict_to_tenant
from utils.db_manager import get_tenants_collection
from utils.vector_store import vector_store_manager
from utils.logger import logger


class TenantService:
    """租戶服務"""
    
    @staticmethod
    def create_tenant(tenant_data: TenantCreate) -> Optional[dict]:
        """創建租戶"""
        try:
            tenants_collection = get_tenants_collection()
            
            # 檢查名稱是否已存在
            existing = tenants_collection.find_one({'name': tenant_data.name})
            if existing:
                logger.warning(f"租戶名稱已存在: {tenant_data.name}")
                return None
            
            # 創建租戶
            tenant_id = str(ObjectId())
            tenant = Tenant(
                id=tenant_id,
                name=tenant_data.name,
                description=tenant_data.description,
                domain=tenant_data.domain,
                plan=tenant_data.plan,
                max_users=tenant_data.max_users,
                max_documents=tenant_data.max_documents,
                max_storage_mb=tenant_data.max_storage_mb
            )
            
            # 保存到資料庫
            tenants_collection.insert_one(tenant_to_dict(tenant))
            
            # 初始化向量集合
            vector_store_manager.create_collection(tenant_id)
            
            logger.info(f"成功創建租戶: {tenant.name}")
            return tenant.dict()
        except Exception as e:
            logger.error(f"創建租戶失敗: {e}")
            return None
    
    @staticmethod
    def get_tenant(tenant_id: str) -> Optional[dict]:
        """獲取租戶資訊"""
        try:
            tenants_collection = get_tenants_collection()
            tenant_data = tenants_collection.find_one({'_id': ObjectId(tenant_id)})
            
            if not tenant_data:
                return None
            
            tenant = dict_to_tenant(tenant_data)
            return tenant.dict()
        except Exception as e:
            logger.error(f"獲取租戶失敗: {e}")
            return None
    
    @staticmethod
    def get_all_tenants() -> List[dict]:
        """獲取所有租戶"""
        try:
            tenants_collection = get_tenants_collection()
            tenants = tenants_collection.find().sort('created_at', -1)
            
            return [dict_to_tenant(t).dict() for t in tenants]
        except Exception as e:
            logger.error(f"獲取租戶列表失敗: {e}")
            return []
    
    @staticmethod
    def update_tenant(tenant_id: str, update_data: TenantUpdate) -> Optional[dict]:
        """更新租戶資訊"""
        try:
            tenants_collection = get_tenants_collection()
            
            # 構建更新數據
            update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
            update_dict['updated_at'] = datetime.utcnow()
            
            result = tenants_collection.update_one(
                {'_id': ObjectId(tenant_id)},
                {'$set': update_dict}
            )
            
            if result.modified_count == 0:
                return None
            
            return TenantService.get_tenant(tenant_id)
        except Exception as e:
            logger.error(f"更新租戶失敗: {e}")
            return None
    
    @staticmethod
    def delete_tenant(tenant_id: str) -> bool:
        """刪除租戶（慎用）"""
        try:
            tenants_collection = get_tenants_collection()
            
            # 刪除向量集合
            vector_store_manager.delete_collection(tenant_id)
            
            # 刪除租戶記錄
            result = tenants_collection.delete_one({'_id': ObjectId(tenant_id)})
            
            if result.deleted_count > 0:
                logger.info(f"成功刪除租戶: {tenant_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"刪除租戶失敗: {e}")
            return False


from datetime import datetime
