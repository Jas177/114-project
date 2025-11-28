from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from pydantic import ValidationError
from models.user import UserCreate, UserLogin
from services.auth_service import AuthService
from utils.logger import logger

auth_bp = Blueprint('auth', __name__, url_prefix='/v1/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """用戶註冊"""
    try:
        data = request.get_json()
        user_data = UserCreate(**data)
        
        result = AuthService.register_user(user_data)
        
        if result:
            return jsonify({
                'success': True,
                'message': '註冊成功',
                'user': result
            }), 201
        else:
            return jsonify({
                'success': False,
                'message': '註冊失敗，用戶可能已存在'
            }), 400
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': '數據驗證失敗',
            'errors': e.errors()
        }), 400
    except Exception as e:
        logger.error(f"註冊錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """用戶登入"""
    try:
        data = request.get_json()
        login_data = UserLogin(**data)
        
        result = AuthService.login_user(login_data)
        
        if result:
            return jsonify({
                'success': True,
                'message': '登入成功',
                'access_token': result['access_token'],
                'refresh_token': result['refresh_token'],
                'user': result['user']
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '登入失敗，請檢查郵箱和密碼'
            }), 401
    except ValidationError as e:
        return jsonify({
            'success': False,
            'message': '數據驗證失敗',
            'errors': e.errors()
        }), 400
    except Exception as e:
        logger.error(f"登入錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """獲取當前用戶資訊"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        
        if user:
            return jsonify({
                'success': True,
                'user': user
            }), 200
        else:
            return jsonify({
                'success': False,
                'message': '用戶不存在'
            }), 404
    except Exception as e:
        logger.error(f"獲取用戶錯誤: {e}")
        return jsonify({
            'success': False,
            'message': '伺服器錯誤'
        }), 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """用戶登出"""
    # JWT 是無狀態的，登出主要在前端處理（刪除 token）
    # 如需實現黑名單，可以將 token 加入 Redis
    return jsonify({
        'success': True,
        'message': '登出成功'
    }), 200
