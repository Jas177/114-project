import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from config import get_config
from utils.logger import logger

# 導入路由
from routes.auth import auth_bp
from routes.tenants import tenants_bp
from routes.documents import documents_bp
from routes.chat import chat_bp

# 創建應用
app = Flask(__name__)
config = get_config()

# 應用配置
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = config.JWT_ACCESS_TOKEN_EXPIRES
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = config.JWT_REFRESH_TOKEN_EXPIRES
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE

# CORS 配置
CORS(app, origins=config.CORS_ORIGINS, supports_credentials=True)

# JWT 配置
jwt = JWTManager(app)

# 確保必要的目錄存在
os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(os.path.dirname(config.LOG_FILE), exist_ok=True)

# 註冊藍圖
app.register_blueprint(auth_bp)
app.register_blueprint(tenants_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(chat_bp)


@app.route('/')
def index():
    """首頁"""
    return jsonify({
        'message': '114 多企業智能客服平台 API',
        'version': '1.0.0',
        'status': 'running'
    })


@app.route('/health')
def health():
    """健康檢查"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Platform Backend'
    })


# JWT 錯誤處理
@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    return jsonify({
        'success': False,
        'message': 'Token 已過期'
    }), 401


@jwt.invalid_token_loader
def invalid_token_callback(error):
    return jsonify({
        'success': False,
        'message': 'Token 無效'
    }), 401


@jwt.unauthorized_loader
def missing_token_callback(error):
    return jsonify({
        'success': False,
        'message': '缺少 Token'
    }), 401


# 全局錯誤處理
@app.errorhandler(404)
def not_found(error):
    return jsonify({
        'success': False,
        'message': '資源不存在'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"伺服器錯誤: {error}")
    return jsonify({
        'success': False,
        'message': '伺服器內部錯誤'
    }), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    return jsonify({
        'success': False,
        'message': '請求內容過大'
    }), 413


if __name__ == '__main__':
    logger.info("啟動 Flask 應用...")
    logger.info(f"環境: {os.getenv('FLASK_ENV', 'development')}")
    logger.info(f"CORS 允許來源: {config.CORS_ORIGINS}")
    
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=config.DEBUG
    )