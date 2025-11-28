from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import get_config
from utils.logger import logger

config = get_config()


class DatabaseManager:
    """MongoDB 資料庫管理器"""
    
    _instance = None
    _client = None
    _db = None
    
    def __new__(cls):
        """單例模式"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初始化資料庫連接"""
        if self._client is None:
            try:
                self._client = MongoClient(
                    config.MONGODB_URI,
                    serverSelectionTimeoutMS=5000,
                    maxPoolSize=50,
                    minPoolSize=10
                )
                # 測試連接
                self._client.admin.command('ping')
                self._db = self._client[config.MONGODB_DB_NAME]
                logger.info(f"成功連接到 MongoDB: {config.MONGODB_DB_NAME}")
            except (ConnectionFailure, ServerSelectionTimeoutError) as e:
                logger.error(f"MongoDB 連接失敗: {e}")
                raise
    
    @property
    def db(self):
        """獲取資料庫實例"""
        return self._db
    
    @property
    def client(self):
        """獲取客戶端實例"""
        return self._client
    
    def get_collection(self, collection_name):
        """獲取集合"""
        return self._db[collection_name]
    
    def close(self):
        """關閉資料庫連接"""
        if self._client:
            self._client.close()
            logger.info("MongoDB 連接已關閉")


# 創建全局資料庫管理器實例
db_manager = DatabaseManager()


# 常用集合
def get_tenants_collection():
    """獲取租戶集合"""
    return db_manager.get_collection('tenants')


def get_users_collection():
    """獲取用戶集合"""
    return db_manager.get_collection('users')


def get_documents_collection():
    """獲取文件集合"""
    return db_manager.get_collection('documents')


def get_conversations_collection():
    """獲取對話集合"""
    return db_manager.get_collection('conversations')


def get_messages_collection():
    """獲取消息集合"""
    return db_manager.get_collection('messages')


def get_model_providers_collection():
    """獲取模型提供者集合"""
    return db_manager.get_collection('model_providers')
