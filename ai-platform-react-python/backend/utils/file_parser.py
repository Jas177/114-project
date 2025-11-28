import os
from typing import List
import PyPDF2
import docx
from utils.logger import logger


class FileParser:
    """文件解析器"""
    
    @staticmethod
    def parse_pdf(file_path: str) -> str:
        """解析 PDF 文件"""
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            logger.error(f"解析 PDF 失敗: {e}")
            return ""
    
    @staticmethod
    def parse_docx(file_path: str) -> str:
        """解析 DOCX 文件"""
        try:
            doc = docx.Document(file_path)
            text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
            return text
        except Exception as e:
            logger.error(f"解析 DOCX 失敗: {e}")
            return ""
    
    @staticmethod
    def parse_txt(file_path: str) -> str:
        """解析 TXT 文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # 嘗試其他編碼
            try:
                with open(file_path, 'r', encoding='gbk') as file:
                    return file.read()
            except Exception as e:
                logger.error(f"解析 TXT 失敗: {e}")
                return ""
        except Exception as e:
            logger.error(f"解析 TXT 失敗: {e}")
            return ""
    
    @staticmethod
    def parse_file(file_path: str) -> str:
        """根據文件類型自動解析"""
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return FileParser.parse_pdf(file_path)
        elif file_ext == '.docx':
            return FileParser.parse_docx(file_path)
        elif file_ext in ['.txt', '.md']:
            return FileParser.parse_txt(file_path)
        else:
            logger.warning(f"不支援的文件類型: {file_ext}")
            return ""
    
    @staticmethod
    def get_file_info(file_path: str) -> dict:
        """獲取文件資訊"""
        return {
            'filename': os.path.basename(file_path),
            'size': os.path.getsize(file_path),
            'extension': os.path.splitext(file_path)[1].lower(),
            'path': file_path
        }
