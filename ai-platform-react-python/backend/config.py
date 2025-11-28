import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()


class Config:
    """基礎配置"""
    
    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dev-jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
    
    # MongoDB
    MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
    MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME', 'ai_platform')
    
    # Redis
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # Google Cloud
    GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY', '')
    GOOGLE_PROJECT_ID = os.getenv('GOOGLE_PROJECT_ID', '')
    GOOGLE_LOCATION = os.getenv('GOOGLE_LOCATION', 'us-central1')
    
    # Vertex AI Configuration
    VERTEX_AI_API_KEY = os.getenv('VERTEX_AI_API_KEY', '')
    
    # Vertex AI Vector Search
    VERTEX_AI_INDEX_ID = os.getenv('VERTEX_AI_INDEX_ID', '')
    VERTEX_AI_INDEX_ENDPOINT = os.getenv('VERTEX_AI_INDEX_ENDPOINT', '')
    VERTEX_AI_DEPLOYED_INDEX_ID = os.getenv('VERTEX_AI_DEPLOYED_INDEX_ID', '')
    
    # Vertex AI RAG Engine
    USE_RAG_ENGINE = os.getenv('USE_RAG_ENGINE', 'false').lower() == 'true'
    RAG_CORPUS_PREFIX = os.getenv('RAG_CORPUS_PREFIX', 'tenant')
    
    # Cloud Storage (GCS)
    GCS_BUCKET_NAME = os.getenv('GCS_BUCKET_NAME', '')
    GCS_DOCUMENTS_PREFIX = os.getenv('GCS_DOCUMENTS_PREFIX', 'tenants')
    
    # Grounding
    USE_GROUNDING = os.getenv('USE_GROUNDING', 'true').lower() == 'true'
    GROUNDING_SOURCE_TYPE = os.getenv('GROUNDING_SOURCE_TYPE', 'rag_engine')  # or 'vertex_search'
    
    # Gemini LLM
    GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-1.5-flash')
    GEMINI_TEMPERATURE = float(os.getenv('GEMINI_TEMPERATURE', '0.7'))
    GEMINI_MAX_TOKENS = int(os.getenv('GEMINI_MAX_TOKENS', '2048'))
    
    # Gemini Embedding
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'models/embedding-001')
    EMBEDDING_DIMENSION = int(os.getenv('EMBEDDING_DIMENSION', 768))
    
    # File Upload
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 50)) * 1024 * 1024  # Convert to bytes
    ALLOWED_EXTENSIONS = set(os.getenv('ALLOWED_EXTENSIONS', 'pdf,docx,txt,md,csv,xlsx').split(','))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', './uploads')
    
    # RAG
    CHUNK_SIZE = int(os.getenv('CHUNK_SIZE', 500))
    CHUNK_OVERLAP = int(os.getenv('CHUNK_OVERLAP', 50))
    TOP_K_RETRIEVAL = int(os.getenv('TOP_K_RETRIEVAL', 5))
    RERANK_TOP_N = int(os.getenv('RERANK_TOP_N', 3))
    
    # Rate Limiting
    RATE_LIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '100 per hour')
    RATE_LIMIT_CHAT = os.getenv('RATE_LIMIT_CHAT', '50 per hour')
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:3000,http://localhost:5173').split(',')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', './logs/app.log')


class DevelopmentConfig(Config):
    """開發環境配置"""
    DEBUG = True
    TESTING = False


class ProductionConfig(Config):
    """生產環境配置"""
    DEBUG = False
    TESTING = False


class TestingConfig(Config):
    """測試環境配置"""
    DEBUG = True
    TESTING = True
    MONGODB_DB_NAME = 'ai_platform_test'


# 配置字典
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}


def get_config():
    """獲取當前配置"""
    env = os.getenv('FLASK_ENV', 'development')
    return config.get(env, config['default'])
