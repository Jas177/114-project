from flask import Blueprint, request, jsonify, Response, stream_with_context
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from pydantic import ValidationError
from models.conversation import ChatRequest
from services.chat_service import ChatService
from utils.logger import logger

chat_bp = Blueprint('chat', __name__, url_prefix='/v1/tenants/<tenant_id>/chat')


@chat_bp.route('', methods=['POST'])
@jwt_required()
def chat(tenant_id):
    """發送聊天消息"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        user_id = get_jwt_identity()
        
        # 檢查權限
        if user_tenant_id != tenant_id:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        data = request.get_json()
        chat_request = ChatRequest(**data)
        
        # 處理聊天請求
        response = ChatService.chat(tenant_id, chat_request, user_id)
        
        return jsonify({
            'success': True,
            'conversation_id': response.conversation_id,
            'message': response.message,
            'sources': response.sources,
            'token_usage': response.token_usage,
            'timestamp': response.timestamp.isoformat()
        }), 200
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': '數據驗證失敗',
            'errors': e.errors()
        }), 400
    except Exception as e:
        logger.error(f"聊天錯誤: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@chat_bp.route('/stream', methods=['POST'])
@jwt_required()
def chat_stream(tenant_id):
    """串流聊天消息（Server-Sent Events）"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        user_id = get_jwt_identity()
        
        # 檢查權限
        if user_tenant_id != tenant_id:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        data = request.get_json()
        chat_request = ChatRequest(**data)
        chat_request.stream = True
        
        def generate():
            try:
                for chunk in ChatService.chat_stream(tenant_id, chat_request, user_id):
                    yield f"data: {chunk}\n\n"
            except Exception as e:
                logger.error(f"串流錯誤: {e}")
                yield f"data: [ERROR] {str(e)}\n\n"
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'X-Accel-Buffering': 'no'
            }
        )
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': '數據驗證失敗',
            'errors': e.errors()
        }), 400
    except Exception as e:
        logger.error(f"串流聊天錯誤: {e}")
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500


@chat_bp.route('/conversations', methods=['GET'])
@jwt_required()
def get_conversations(tenant_id):
    """獲取對話列表"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        user_id = get_jwt_identity()
        
        # 檢查權限
        if user_tenant_id != tenant_id:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        conversations = ChatService.get_conversations(tenant_id, user_id)
        
        return jsonify({
            'success': True,
            'conversations': conversations
        }), 200
    except Exception as e:
        logger.error(f"獲取對話列表錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@chat_bp.route('/conversations/<conversation_id>', methods=['GET'])
@jwt_required()
def get_conversation(tenant_id, conversation_id):
    """獲取對話詳情"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        
        # 檢查權限
        if user_tenant_id != tenant_id:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        conversation = ChatService.get_conversation(conversation_id, tenant_id)
        
        if conversation:
            return jsonify({
                'success': True,
                'conversation': conversation
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '對話不存在'
            }), 404
    except Exception as e:
        logger.error(f"獲取對話錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500
