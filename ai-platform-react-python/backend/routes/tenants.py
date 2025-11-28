from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from pydantic import ValidationError
from models.tenant import TenantCreate, TenantUpdate
from services.tenant_service import TenantService
from utils.logger import logger

tenants_bp = Blueprint('tenants', __name__, url_prefix='/v1/tenants')


@tenants_bp.route('', methods=['GET'])
@jwt_required()
def get_tenants():
    """獲取所有租戶（平台管理員）"""
    try:
        claims = get_jwt()
        role = claims.get('role', '')
        
        # 檢查權限
        if role != 'platform_admin':
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        tenants = TenantService.get_all_tenants()
        
        return jsonify({
            'success': True,
            'tenants': tenants
        }), 200
    except Exception as e:
        logger.error(f"獲取租戶列表錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@tenants_bp.route('/<tenant_id>', methods=['GET'])
@jwt_required()
def get_tenant(tenant_id):
    """獲取租戶詳情"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        role = claims.get('role', '')
        
        # 檢查權限：平台管理員或同租戶的租戶管理員
        if role not in ['platform_admin', 'tenant_admin'] or (role == 'tenant_admin' and user_tenant_id != tenant_id):
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        tenant = TenantService.get_tenant(tenant_id)
        
        if tenant:
            return jsonify({
                'success': True,
                'tenant': tenant
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '租戶不存在'
            }), 404
    except Exception as e:
        logger.error(f"獲取租戶錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@tenants_bp.route('', methods=['POST'])
@jwt_required()
def create_tenant():
    """創建租戶（平台管理員）"""
    try:
        claims = get_jwt()
        role = claims.get('role', '')
        
        if role != 'platform_admin':
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        data = request.get_json()
        tenant_data = TenantCreate(**data)
        
        tenant = TenantService.create_tenant(tenant_data)
        
        if tenant:
            return jsonify({
                'success': True,
                'message': '租戶創建成功',
                'tenant': tenant
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '租戶創建失敗，名稱可能已存在'
            }), 400
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': '數據驗證失敗',
            'errors': e.errors()
        }), 400
    except Exception as e:
        logger.error(f"創建租戶錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@tenants_bp.route('/<tenant_id>', methods=['PATCH'])
@jwt_required()
def update_tenant(tenant_id):
    """更新租戶資訊"""
    try:
        claims = get_jwt()
        user_tenant_id = claims.get('tenant_id', '')
        role = claims.get('role', '')
        
        # 檢查權限
        if role not in ['platform_admin', 'tenant_admin'] or (role == 'tenant_admin' and user_tenant_id != tenant_id):
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        data = request.get_json()
        update_data = TenantUpdate(**data)
        
        tenant = TenantService.update_tenant(tenant_id, update_data)
        
        if tenant:
            return jsonify({
                'success': True,
                'message': '租戶更新成功',
                'tenant': tenant
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '租戶更新失敗'
            }), 400
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': '數據驗證失敗',
            'errors': e.errors()
        }), 400
    except Exception as e:
        logger.error(f"更新租戶錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@tenants_bp.route('/<tenant_id>', methods=['DELETE'])
@jwt_required()
def delete_tenant(tenant_id):
    """刪除租戶（平台管理員）"""
    try:
        claims = get_jwt()
        role = claims.get('role', '')
        
        if role != 'platform_admin':
            return jsonify({
                'success': False,
                'message': '權限不足'
            }), 403
        
        success = TenantService.delete_tenant(tenant_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': '租戶刪除成功'
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '租戶刪除失敗'
            }), 400
    except Exception as e:
        logger.error(f"刪除租戶錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500
