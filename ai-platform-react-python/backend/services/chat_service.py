from datetime import datetime
from typing import Optional, Dict, Generator
from bson import ObjectId
from models.conversation import (
    Conversation, ConversationCreate, ChatRequest, ChatResponse,
    Message, MessageRole, conversation_to_dict, dict_to_conversation
)
from services.retrieval_service import RetrievalService
from services.llm_service import llm_service
from utils.db_manager import get_conversations_collection
from utils.logger import logger


class ChatService:
    """對話服務"""
    
    @staticmethod
    def create_conversation(tenant_id: str, user_id: Optional[str] = None, title: str = "新對話") -> Optional[dict]:
        """創建新對話"""
        try:
            conv_id = str(ObjectId())
            conversation = Conversation(
                id=conv_id,
                tenant_id=tenant_id,
                user_id=user_id,
                title=title
            )
            
            conversations_collection = get_conversations_collection()
            conversations_collection.insert_one(conversation_to_dict(conversation))
            
            logger.info(f"創建新對話: {conv_id}")
            return conversation.dict()
        except Exception as e:
            logger.error(f"創建對話失敗: {e}")
            return None
    
    @staticmethod
    def chat(tenant_id: str, request: ChatRequest, user_id: Optional[str] = None) -> ChatResponse:
        """處理聊天請求"""
        try:
            conversations_collection = get_conversations_collection()
            
            # 獲取或創建對話
            if request.conversation_id:
                conv_data = conversations_collection.find_one({
                    '_id': ObjectId(request.conversation_id),
                    'tenant_id': tenant_id
                })
                
                if not conv_data:
                    logger.warning(f"對話不存在: {request.conversation_id}")
                    conversation = ChatService.create_conversation(tenant_id, user_id)
                    if not conversation:
                        raise Exception("創建對話失敗")
                    conv_id = conversation['id']
                    messages = []
                else:
                    conversation = dict_to_conversation(conv_data)
                    conv_id = conversation.id
                    messages = conversation.messages
            else:
                # 創建新對話
                conversation = ChatService.create_conversation(tenant_id, user_id)
                if not conversation:
                    raise Exception("創建對話失敗")
                conv_id = conversation['id']
                messages = []
            
            # 添加用戶消息
            user_message = Message(
                role=MessageRole.USER,
                content=request.message
            )
            messages.append(user_message)
            
            # RAG 檢索
            logger.info(f"執行 RAG 檢索: {request.message[:50]}...")
            retrieved_docs = RetrievalService.retrieve_with_rerank(
                tenant_id=tenant_id,
                query=request.message
            )
            
            # 構建 RAG 提示詞
            llm_messages = llm_service.build_rag_prompt(
                query=request.message,
                context_docs=retrieved_docs
            )
            
            # 準備 Grounding Sources
            grounding_sources = [{
                'text': doc['text'],
                'source': doc.get('source', doc.get('document_id', '')),
                'score': doc.get('score', 0.0)
            } for doc in retrieved_docs]
            
            # 生成回應（帶 Grounding）
            logger.info("生成 LLM 回應...")
            llm_response = llm_service.generate_response(
                messages=llm_messages,
                stream=request.stream,
                grounding_sources=grounding_sources
            )
            
            # 添加助手消息
            assistant_message = Message(
                role=MessageRole.ASSISTANT,
                content=llm_response['content'],
                sources=[{
                    'text': doc['text'][:200],
                    'document_id': doc['document_id'],
                    'score': doc['score']
                } for doc in retrieved_docs]
            )
            messages.append(assistant_message)
            
            # 更新對話
            conversations_collection.update_one(
                {'_id': ObjectId(conv_id)},
                {
                    '$set': {
                        'messages': [msg.dict() for msg in messages],
                        'message_count': len(messages),
                        'token_usage': llm_response.get('token_usage', {}),
                        'updated_at': datetime.utcnow()
                    }
                }
            )
            
            logger.info(f"對話更新成功: {conv_id}")
            
            # 返回回應
            return ChatResponse(
                conversation_id=conv_id,
                message=llm_response['content'],
                sources=[{
                    'text': doc['text'][:200],
                    'document_id': doc['document_id'],
                    'score': doc['score']
                } for doc in retrieved_docs],
                token_usage=llm_response.get('token_usage', {})
            )
        except Exception as e:
            logger.error(f"聊天處理失敗: {e}")
            raise
    
    @staticmethod
    def chat_stream(tenant_id: str, request: ChatRequest, user_id: Optional[str] = None) -> Generator:
        """處理串流聊天請求"""
        try:
            # 簡化版本：返回完整回應
            # 生產環境應該實作真正的串流
            response = ChatService.chat(tenant_id, request, user_id)
            yield response.message
        except Exception as e:
            logger.error(f"串流聊天失敗: {e}")
            yield f"錯誤：{str(e)}"
    
    @staticmethod
    def get_conversations(tenant_id: str, user_id: Optional[str] = None) -> list:
        """獲取對話列表"""
        try:
            conversations_collection = get_conversations_collection()
            
            query = {'tenant_id': tenant_id}
            if user_id:
                query['user_id'] = user_id
            
            convs = conversations_collection.find(query).sort('updated_at', -1).limit(50)
            
            return [dict_to_conversation(conv).dict() for conv in convs]
        except Exception as e:
            logger.error(f"獲取對話列表失敗: {e}")
            return []
    
    @staticmethod
    def get_conversation(conversation_id: str, tenant_id: str) -> Optional[dict]:
        """獲取對話詳情"""
        try:
            conversations_collection = get_conversations_collection()
            conv_data = conversations_collection.find_one({
                '_id': ObjectId(conversation_id),
                'tenant_id': tenant_id
            })
            
            if not conv_data:
                return None
            
            conversation = dict_to_conversation(conv_data)
            return conversation.dict()
        except Exception as e:
            logger.error(f"獲取對話詳情失敗: {e}")
            return None
