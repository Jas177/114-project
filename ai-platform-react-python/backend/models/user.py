from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, validator
from passlib.hash import bcrypt


class UserRole:
    """用戶角色常量"""
    PLATFORM_ADMIN = "platform_admin"
    TENANT_ADMIN = "tenant_admin"
    AGENT = "agent"
    END_USER = "end_user"


class UserCreate(BaseModel):
    """用戶創建模型"""
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1, max_length=100)
    tenant_id: str
    role: str = Field(default=UserRole.END_USER)
    
    @validator('role')
    def validate_role(cls, v):
        valid_roles = [UserRole.PLATFORM_ADMIN, UserRole.TENANT_ADMIN, UserRole.AGENT, UserRole.END_USER]
        if v not in valid_roles:
            raise ValueError(f'角色必須是以下之一: {", ".join(valid_roles)}')
        return v


class UserLogin(BaseModel):
    """用戶登入模型"""
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    """用戶更新模型"""
    name: Optional[str] = None
    role: Optional[str] = None
    status: Optional[str] = None


class User(BaseModel):
    """用戶模型"""
    id: str
    email: str
    name: str
    password_hash: str
    tenant_id: str
    role: str = UserRole.END_USER
    status: str = "active"  # active, inactive, suspended
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True
    
    @staticmethod
    def hash_password(password: str) -> str:
        """對密碼進行雜湊"""
        return bcrypt.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """驗證密碼"""
        return bcrypt.verify(password, self.password_hash)


class UserPublic(BaseModel):
    """用戶公開模型（不包含敏感資訊）"""
    id: str
    email: str
    name: str
    tenant_id: str
    role: str
    status: str
    last_login: Optional[datetime] = None
    created_at: datetime


def user_to_dict(user: User) -> dict:
    """將用戶對象轉換為字典"""
    data = user.dict()
    data['_id'] = data.pop('id')
    return data


def dict_to_user(data: dict) -> User:
    """將字典轉換為用戶對象"""
    if '_id' in data:
        data['id'] = str(data['_id'])
        del data['_id']
    return User(**data)


def user_to_public(user: User) -> UserPublic:
    """將用戶轉換為公開模型"""
    return UserPublic(
        id=user.id,
        email=user.email,
        name=user.name,
        tenant_id=user.tenant_id,
        role=user.role,
        status=user.status,
        last_login=user.last_login,
        created_at=user.created_at
    )
