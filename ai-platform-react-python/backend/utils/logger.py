import logging
import os
from logging.handlers import RotatingFileHandler
from config import get_config

config = get_config()


def setup_logger(name='ai_platform'):
    """設置日誌記錄器"""
    logger = logging.getLogger(name)
    
    # 設置日誌級別
    log_level = getattr(logging, config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 避免重複添加 handler
    if logger.handlers:
        return logger
    
    # 控制台 Handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # 文件 Handler
    log_dir = os.path.dirname(config.LOG_FILE)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)
    
    file_handler = RotatingFileHandler(
        config.LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    return logger


# 創建默認 logger
logger = setup_logger()
