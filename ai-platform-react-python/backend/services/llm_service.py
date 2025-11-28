import google.generativeai as genai
from typing import List, Dict, Optional, Generator
from config import get_config
from utils.logger import logger

config = get_config()


class LLMService:
    """Gemini LLM 服務（支援 Grounding）"""
    
    def __init__(self):
        """初始化 Gemini API"""
        try:
            if not config.GOOGLE_API_KEY:
                logger.warning("未配置 GOOGLE_API_KEY，將使用模擬回應")
                self._initialized = False
                return
            
            genai.configure(api_key=config.GOOGLE_API_KEY)
            self._model = genai.GenerativeModel(config.GEMINI_MODEL)
            self._initialized = True
            logger.info(f"Gemini LLM 服務初始化成功，模型: {config.GEMINI_MODEL}")
        except Exception as e:
            logger.error(f"Gemini 初始化失敗: {e}")
            self._initialized = False
    
    def generate_response(
        self,
        messages: List[Dict[str, str]],
        temperature: float = None,
        max_tokens: int = None,
        stream: bool = False,
        grounding_sources: Optional[List[Dict]] = None
    ) -> Dict:
        """生成回應（支援 Grounding）"""
        try:
            if not self._initialized:
                logger.warning("Gemini 未配置，使用模擬回應")
                return self._mock_response(messages)
            
            # 使用配置的默認值
            if temperature is None:
                temperature = config.GEMINI_TEMPERATURE
            if max_tokens is None:
                max_tokens = config.GEMINI_MAX_TOKENS
            
            # 轉換訊息格式為 Gemini 格式
            prompt = self._convert_messages_to_prompt(messages)
            
            # 如果有 Grounding Sources，添加到 prompt
            if grounding_sources and config.USE_GROUNDING:
                context = self._format_grounding_sources(grounding_sources)
                prompt = f"{context}\n\n{prompt}"
            
            # 配置生成參數
            generation_config = genai.types.GenerationConfig(
                temperature=temperature,
                max_output_tokens=max_tokens
            )
            
            # 生成回應
            if stream:
                return self._generate_stream(prompt, generation_config)
            else:
                response = self._model.generate_content(
                    prompt,
                    generation_config=generation_config
                )
                
                # 提取 token 使用量
                token_usage = {
                    'prompt_tokens': getattr(response.usage_metadata, 'prompt_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    'completion_tokens': getattr(response.usage_metadata, 'candidates_token_count', 0) if hasattr(response, 'usage_metadata') else 0,
                    'total_tokens': getattr(response.usage_metadata, 'total_token_count', 0) if hasattr(response, 'usage_metadata') else 0
                }
                
                # 構建 Citations（從 grounding_sources）
                citations = []
                if grounding_sources:
                    for i, source in enumerate(grounding_sources):
                        citations.append({
                            'index': i + 1,
                            'text': source.get('text', '')[:200],
                            'source': source.get('source', ''),
                            'score': source.get('score', 0.0)
                        })
                
                return {
                    'content': response.text,
                    'token_usage': token_usage,
                    'model': config.GEMINI_MODEL,
                    'citations': citations,
                    'grounded': bool(grounding_sources)
                }
        except Exception as e:
            logger.error(f"Gemini 生成失敗: {e}")
            return self._mock_response(messages)
    
    def _format_grounding_sources(self, sources: List[Dict]) -> str:
        """格式化 Grounding Sources 為 Context"""
        context_parts = ["以下是相關的知識庫內容，請基於這些內容回答問題：\n"]
        
        for i, source in enumerate(sources, 1):
            context_parts.append(f"[來源 {i}]\n{source.get('text', '')}\n")
        
        return "\n".join(context_parts)
    
    def _generate_stream(self, prompt: str, generation_config) -> Generator:
        """串流生成回應"""
        try:
            response = self._model.generate_content(
                prompt,
                generation_config=generation_config,
                stream=True
            )
            
            for chunk in response:
                if chunk.text:
                    yield chunk.text
        except Exception as e:
            logger.error(f"串流生成失敗: {e}")
            yield "抱歉，生成回應時發生錯誤。"
    
    def _convert_messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """將訊息列表轉換為單一提示詞"""
        prompt_parts = []
        
        for msg in messages:
            role = msg.get('role', 'user')
            content = msg.get('content', '')
            
            if role == 'system':
                prompt_parts.append(f"系統指示：{content}\n")
            elif role == 'user':
                prompt_parts.append(f"用戶：{content}\n")
            elif role == 'assistant':
                prompt_parts.append(f"助手：{content}\n")
        
        return "\n".join(prompt_parts)
    
    def _mock_response(self, messages: List[Dict[str, str]]) -> Dict:
        """模擬回應（用於測試或未配置 API 的情況）"""
        last_message = messages[-1]['content'] if messages else ""
        
        mock_content = f"這是一個模擬回應。您的問題是：「{last_message}」。請配置 Google API Key 以使用真實的 Gemini 服務。"
        
        return {
            'content': mock_content,
            'token_usage': {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            },
            'model': 'mock',
            'citations': [],
            'grounded': False
        }
    
    def build_rag_prompt(
        self,
        query: str,
        context_docs: List[Dict],
        system_prompt: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """構建 RAG 提示詞"""
        if system_prompt is None:
            system_prompt = """你是一個專業的AI助手，基於提供的知識庫內容回答用戶問題。
請遵循以下規則：
1. 僅基於提供的上下文回答問題
2. 如果上下文中沒有相關信息，請誠實地說明
3. 提供清晰、準確、有幫助的回答
4. 使用繁體中文回答
5. 在回答中標註引用來源（使用 [來源 N] 的格式）"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
        
        return messages


# 創建全局 LLM 服務實例
llm_service = LLMService()

