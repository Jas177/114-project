from datetime import datetime, timedelta
from typing import Optional
from flask_jwt_extended import create_access_token, create_refresh_token
from bson import ObjectId
from models.user import User, UserCreate, UserLogin, dict_to_user, user_to_dict, user_to_public
from utils.db_manager import get_users_collection
from utils.logger import logger


class AuthService:
    """認證服務"""
    
    @staticmethod
    def register_user(user_data: UserCreate) -> Optional[dict]:
        """註冊新用戶"""
        try:
            users_collection = get_users_collection()
            
            # 檢查 email 是否已存在
            existing_user = users_collection.find_one({'email': user_data.email})
            if existing_user:
                logger.warning(f"用戶已存在: {user_data.email}")
                return None
            
            # 創建用戶
            user_id = str(ObjectId())
            user = User(
                id=user_id,
                email=user_data.email,
                name=user_data.name,
                password_hash=User.hash_password(user_data.password),
                tenant_id=user_data.tenant_id,
                role=user_data.role
            )
            
            # 保存到資料庫
            users_collection.insert_one(user_to_dict(user))
            logger.info(f"成功註冊用戶: {user.email}")
            
            return user_to_public(user).dict()
        except Exception as e:
            logger.error(f"用戶註冊失敗: {e}")
            return None
    
    @staticmethod
    def login_user(login_data: UserLogin) -> Optional[dict]:
        """用戶登入"""
        try:
            users_collection = get_users_collection()
            
            # 查找用戶
            user_doc = users_collection.find_one({'email': login_data.email})
            if not user_doc:
                logger.warning(f"用戶不存在: {login_data.email}")
                return None
            
            user = dict_to_user(user_doc)
            
            # 驗證密碼
            if not user.verify_password(login_data.password):
                logger.warning(f"密碼錯誤: {login_data.email}")
                return None
            
            # 檢查用戶狀態
            if user.status != 'active':
                logger.warning(f"用戶狀態異常: {login_data.email} - {user.status}")
                return None
            
            # 更新最後登入時間
            users_collection.update_one(
                {'_id': ObjectId(user.id)},
                {'$set': {'last_login': datetime.utcnow()}}
            )
            
            # 生成 JWT Token
            access_token = create_access_token(
                identity=user.id,
                additional_claims={
                    'email': user.email,
                    'tenant_id': user.tenant_id,
                    'role': user.role
                }
            )
            refresh_token = create_refresh_token(identity=user.id)
            
            logger.info(f"用戶登入成功: {user.email}")
            
            return {
                'access_token': access_token,
                'refresh_token': refresh_token,
                'user': user_to_public(user).dict()
            }
        except Exception as e:
            logger.error(f"用戶登入失敗: {e}")
            return None
    
    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[dict]:
        """根據 ID 獲取用戶"""
        try:
            users_collection = get_users_collection()
            user_doc = users_collection.find_one({'_id': ObjectId(user_id)})
            
            if not user_doc:
                return None
            
            user = dict_to_user(user_doc)
            return user_to_public(user).dict()
        except Exception as e:
            logger.error(f"獲取用戶失敗: {e}")
            return None
