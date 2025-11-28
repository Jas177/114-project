from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class DocumentStatus:
    """文件狀態常量"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentCreate(BaseModel):
    """文件創建模型"""
    filename: str
    tenant_id: str
    file_size: int
    file_type: str


class Document(BaseModel):
    """文件模型"""
    id: str
    tenant_id: str
    filename: str
    file_path: str
    file_size: int
    file_type: str
    status: str = DocumentStatus.UPLOADING
    chunks_count: int = 0
    text_preview: Optional[str] = None
    language: Optional[str] = None
    keywords: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    error_message: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


def document_to_dict(document: Document) -> dict:
    """將文件對象轉換為字典"""
    data = document.dict()
    data['_id'] = data.pop('id')
    return data


def dict_to_document(data: dict) -> Document:
    """將字典轉換為文件對象"""
    if '_id' in data:
        data['id'] = str(data['_id'])
        del data['_id']
    return Document(**data)
