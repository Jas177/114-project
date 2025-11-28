from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator


class TenantCreate(BaseModel):
    """租戶創建模型"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    domain: Optional[str] = None
    plan: str = Field(default="標準版")
    max_users: int = Field(default=10)
    max_documents: int = Field(default=100)
    max_storage_mb: int = Field(default=1000)
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('租戶名稱不能為空')
        return v.strip()


class TenantUpdate(BaseModel):
    """租戶更新模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    domain: Optional[str] = None
    plan: Optional[str] = None
    max_users: Optional[int] = None
    max_documents: Optional[int] = None
    max_storage_mb: Optional[int] = None
    status: Optional[str] = None


class Tenant(BaseModel):
    """租戶模型"""
    id: str
    name: str
    description: Optional[str] = None
    domain: Optional[str] = None
    plan: str = "標準版"
    status: str = "active"  # active, inactive, suspended
    max_users: int = 10
    max_documents: int = 100
    max_storage_mb: int = 1000
    current_users: int = 0
    current_documents: int = 0
    current_storage_mb: float = 0.0
    token_usage: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


def tenant_to_dict(tenant: Tenant) -> dict:
    """將租戶對象轉換為字典"""
    data = tenant.dict()
    data['_id'] = data.pop('id')
    return data


def dict_to_tenant(data: dict) -> Tenant:
    """將字典轉換為租戶對象"""
    if '_id' in data:
        data['id'] = str(data['_id'])
        del data['_id']
    return Tenant(**data)
