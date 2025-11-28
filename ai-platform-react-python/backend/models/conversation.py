from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class MessageRole:
    """消息角色常量"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(BaseModel):
    """消息模型"""
    role: str
    content: str
    sources: List[dict] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ConversationCreate(BaseModel):
    """對話創建模型"""
    tenant_id: str
    user_id: Optional[str] = None
    title: Optional[str] = "新對話"


class Conversation(BaseModel):
    """對話模型"""
    id: str
    tenant_id: str
    user_id: Optional[str] = None
    title: str = "新對話"
    messages: List[Message] = Field(default_factory=list)
    message_count: int = 0
    token_usage: dict = Field(default_factory=dict)
    metadata: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """聊天請求模型"""
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    stream: bool = Field(default=False)
    model: Optional[str] = None


class ChatResponse(BaseModel):
    """聊天回應模型"""
    conversation_id: str
    message: str
    sources: List[dict] = Field(default_factory=list)
    token_usage: dict = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


def conversation_to_dict(conversation: Conversation) -> dict:
    """將對話對象轉換為字典"""
    data = conversation.dict()
    data['_id'] = data.pop('id')
    return data


def dict_to_conversation(data: dict) -> Conversation:
    """將字典轉換為對話對象"""
    if '_id' in data:
        data['id'] = str(data['_id'])
        del data['_id']
    return Conversation(**data)
