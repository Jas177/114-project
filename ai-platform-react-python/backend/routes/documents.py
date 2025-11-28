from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt, get_jwt_identity
from werkzeug.utils import secure_filename
from services.document_service import DocumentService
from config import get_config
from utils.logger import logger
import os

documents_bp = Blueprint('documents', __name__, url_prefix='/v1/tenants/<tenant_id>/documents')
config = get_config()


def allowed_file(filename):
    """檢查文件類型是否允許"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS


@documents_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_document(tenant_id):
    """上傳文件"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        
        # 檢查權限
        if user_tenant_id != tenant_id:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        # 檢查文件
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'message': '沒有文件'
            }), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({
                'success': False,
                'message': '未選擇文件'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'message': f'不支援的文件類型，允許的類型：{", ".join(config.ALLOWED_EXTENSIONS)}'
            }), 400
        
        # 檢查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > config.MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'message': f'文件過大，最大允許 {config.MAX_FILE_SIZE / 1024 / 1024:.0f}MB'
            }), 400
        
        # 上傳文件
        document = DocumentService.upload_document(file, tenant_id, file.filename)
        
        if document:
            return jsonify({
                'success': True,
                'message': '文件上傳成功',
                'document': document
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '文件上傳失敗'
            }), 500
    except Exception as e:
        logger.error(f"文件上傳錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@documents_bp.route('', methods=['GET'])
@jwt_required()
def get_documents(tenant_id):
    """獲取文件列表"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        
        # 檢查權限
        if user_tenant_id != tenant_id:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        documents = DocumentService.get_documents(tenant_id)
        
        return jsonify({
            'success': True,
            'documents': documents
        }), 200
    except Exception as e:
        logger.error(f"獲取文件列表錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@documents_bp.route('/<document_id>', methods=['DELETE'])
@jwt_required()
def delete_document(tenant_id, document_id):
    """刪除文件"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        role = claims.get('role', '')
        
        # 檢查權限
        if user_tenant_id != tenant_id or role not in ['tenant_admin', 'platform_admin']:
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        success = DocumentService.delete_document(document_id, tenant_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '文件刪除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '文件刪除失敗'
            }), 400
    except Exception as e:
        logger.error(f"刪除文件錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500
