import re
from typing import List
from langdetect import detect
from config import get_config

config = get_config()


class TextProcessor:
    """文本處理工具"""
    
    @staticmethod
    def clean_text(text: str) -> str:
        """清理文本"""
        if not text:
            return ""
        
        # 移除多餘空白
        text = re.sub(r'\s+', ' ', text)
        
        # 移除特殊字符（保留中文、英文、數字、基本標點）
        text = re.sub(r'[^\w\s\u4e00-\u9fff。，、；：？！""''（）《》\[\]{}.,;:?!\'"()-]', '', text)
        
        return text.strip()
    
    @staticmethod
    def detect_language(text: str) -> str:
        """檢測語言"""
        try:
            return detect(text)
        except:
            return 'unknown'
    
    @staticmethod
    def split_into_chunks(text: str, chunk_size: int = None, overlap: int = None) -> List[dict]:
        """將文本分割成塊"""
        if chunk_size is None:
            chunk_size = config.CHUNK_SIZE
        if overlap is None:
            overlap = config.CHUNK_OVERLAP
        
        if not text:
            return []
        
        # 清理文本
        text = TextProcessor.clean_text(text)
        
        # 按句子分割（支援中英文）
        sentences = re.split(r'([。！？.!?]+)', text)
        sentences = [''.join(i) for i in zip(sentences[0::2], sentences[1::2] + [''])]
        
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            if current_length + sentence_length <= chunk_size:
                current_chunk += sentence
                current_length += sentence_length
            else:
                if current_chunk:
                    chunks.append({
                        'text': current_chunk.strip(),
                        'length': current_length
                    })
                
                # 開始新塊，保留重疊部分
                if overlap > 0 and current_chunk:
                    overlap_text = current_chunk[-overlap:]
                    current_chunk = overlap_text + sentence
                    current_length = len(overlap_text) + sentence_length
                else:
                    current_chunk = sentence
                    current_length = sentence_length
        
        # 添加最後一塊
        if current_chunk:
            chunks.append({
                'text': current_chunk.strip(),
                'length': current_length
            })
        
        return chunks
    
    @staticmethod
    def extract_keywords(text: str, top_n: int = 5) -> List[str]:
        """提取關鍵詞（簡單版本）"""
        # 移除停用詞
        stop_words = set(['的', '了', '在', '是', '我', '有', '和', '就', '不', '人', '都', '一', '一個', '上', '也', '很', '到', '說', '要', '去', '你', '會', '著', '沒有', '看', '好', '自己', '這'])
        
        words = re.findall(r'[\u4e00-\u9fff]+', text)
        word_freq = {}
        
        for word in words:
            if len(word) > 1 and word not in stop_words:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 排序並返回前 N 個
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        return [word for word, freq in sorted_words[:top_n]]
