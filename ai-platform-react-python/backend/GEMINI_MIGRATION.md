# 🚀 Google Gemini & Vertex AI 遷移指南

## 概述

後端系統已成功從 OpenAI/Milvus 遷移到 **Google Gemini 和 Vertex AI** 服務。

---

## 主要變更

### 1. LLM 服務：OpenAI → Gemini

**之前**: OpenAI GPT-3.5/GPT-4  
**現在**: Google Gemini 1.5 Flash

**配置**:
```env
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048
```

### 2. Embedding 服務：Sentence Transformers → Gemini Embedding

**之前**: sentence-transformers/paraphrase-multilingual-mpnet-base-v2  
**現在**: Gemini embedding-001

**特色**:
- 支援 `retrieval_document` 和 `retrieval_query` 任務類型
- 針對文檔存儲和查詢檢索優化
- 更好的多語言支援

**配置**:
```env
EMBEDDING_MODEL=models/embedding-001
EMBEDDING_DIMENSION=768
```

### 3. 向量資料庫：Milvus → Vertex AI Vector Search

**之前**: 自建 Milvus 實例  
**現在**: Vertex AI Vector Search（目前使用內存存儲）

**注意**: 當前實作使用簡化的內存向量存儲。生產環境應配置 Vertex AI Matching Engine。

---

## 快速開始

### 1. 獲取 Google API Key

您的 API Key（已配置）:
```
AIzaSyBL7NHjZTfmkJ7HbPg7_V06v_uUkF_RRVg
```

### 2. 配置環境變數

編輯 `.env` 文件：
```env
# Google Cloud Configuration
GOOGLE_API_KEY=AIzaSyBL7NHjZTfmkJ7HbPg7_V06v_uUkF_RRVg
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_LOCATION=us-central1

# Gemini LLM
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# Gemini Embedding
EMBEDDING_MODEL=models/embedding-001
EMBEDDING_DIMENSION=768
```

### 3. 安裝依賴

```bash
pip install -r requirements.txt
```

新增的套件:
- `google-generativeai==0.3.2`
- `google-cloud-aiplatform==1.38.1`
- `numpy==1.24.3`

移除的套件:
- `pymilvus`
- `openai`
- `sentence-transformers`
- `langchain`

### 4. 啟動服務

```bash
python app.py
```

---

## API 使用沒有變化

所有 API 端點保持不變！遷移對前端完全透明：

```bash
# 文件上傳
POST /v1/tenants/{id}/documents/upload

# 對話
POST /v1/tenants/{id}/chat
{
  "message": "你好，請問..."
}
```

後端會自動使用 Gemini 進行回應生成。

---

## 技術細節

### Embedding 服務更新

**文檔嵌入** (用於存儲):
```python
result = genai.embed_content(
    model="models/embedding-001",
    content=text,
    task_type="retrieval_document"
)
```

**查詢嵌入** (用於搜尋):
```python
result = genai.embed_content(
    model="models/embedding-001",
    content=query,
    task_type="retrieval_query"
)
```

### LLM 服務更新

**生成回應**:
```python
model = genai.GenerativeModel('gemini-1.5-flash')
response = model.generate_content(
    prompt,
    generation_config=genai.types.GenerationConfig(
        temperature=0.7,
        max_output_tokens=2048
    )
)
```

**串流回應**:
```python
response = model.generate_content(prompt, stream=True)
for chunk in response:
    yield chunk.text
```

### 向量存儲簡化

當前使用內存字典存儲向量：
```python
self._vector_store = {
    'tenant_1': [
        {
            'id': 'doc1_chunk0',
            'embedding': [0.1, 0.2, ...],
            'text': '...',
            'document_id': 'doc1',
            'chunk_index': 0
        }
    ]
}
```

**相似度計算**:
使用餘弦相似度（Cosine Similarity）進行向量比對。

---

## 生產環境建議

### 1. 啟用 Vertex AI Matching Engine

創建和部署索引：
```bash
# 創建索引
gcloud ai indexes create \
  --display-name=knowledge-base-index \
  --metadata-file=index-metadata.json

# 部署索引
gcloud ai index-endpoints deploy-index \
  --index=INDEX_ID \
  --deployed-index-id=DEPLOYED_INDEX_ID
```

配置環境變數：
```env
VERTEX_AI_INDEX_ENDPOINT=projects/{project}/locations/{location}/indexEndpoints/{id}
VERTEX_AI_DEPLOYED_INDEX_ID=your_deployed_index_id
```

### 2. 設置服務帳號

```bash
# 創建服務帳號
gcloud iam service-accounts create ai-platform-backend

# 授予權限
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:ai-platform-backend@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/aiplatform.user"

# 下載金鑰
gcloud iam service-accounts keys create key.json \
  --iam-account=ai-platform-backend@PROJECT_ID.iam.gserviceaccount.com
```

設置環境變數：
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/key.json
```

### 3. 啟用 Vertex AI RAG Engine（未來功能）

Vertex AI RAG Engine 可以自動處理檢索和生成：
```python
from vertexai.preview import rag

# 創建 RAG Corpus
corpus = rag.create_corpus(display_name="knowledge-base")

# 導入文件
rag.import_files(
    corpus_name=corpus.name,
    paths=["gs://bucket/docs/*.pdf"]
)

# RAG 查詢
response = rag.retrieval_query(
    corpus_name=corpus.name,
    text="用戶問題"
)
```

---

## 成本估算

### Gemini API 定價

**Gemini 1.5 Flash**:
- 輸入: $0.075 / 1M tokens
- 輸出: $0.30 / 1M tokens

**Gemini Embedding**:
- $0.025 / 1M tokens

### 範例場景
假設每天 1,000 次對話：
- 平均輸入: 500 tokens
- 平均輸出: 300 tokens
- 檢索文檔: 3 個，每個 200 tokens

**每月成本**:
- LLM: ~$12
- Embedding: ~$1.5
- **總計**: ~$13.5/月

---

## 測試驗證

### 1. 測試 Embedding
```python
from services.embedding_service import embedding_service

# 測試文檔嵌入
embedding = embedding_service.embed_text("這是測試文本")
print(f"Embedding 維度: {len(embedding)}")

# 測試查詢嵌入
query_emb = embedding_service.embed_query("測試查詢")
print(f"Query Embedding 維度: {len(query_emb)}")
```

### 2. 測試 LLM
```python
from services.llm_service import llm_service

messages = [
    {"role": "user", "content": "你好，請介紹一下 Gemini"}
]

response = llm_service.generate_response(messages)
print(response['content'])
```

### 3. 測試完整 RAG 流程
```bash
# 上傳文件
curl -X POST http://localhost:5000/v1/tenants/TENANT_ID/documents/upload \
  -H "Authorization: Bearer TOKEN" \
  -F "file=@test.pdf"

# 發起對話
curl -X POST http://localhost:5000/v1/tenants/TENANT_ID/chat \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "文件中提到了什麼？"}'
```

---

## 常見問題

### Q: 為什麼選擇 Gemini？
**A**: 
- 更好的多語言支援（尤其是中文）
- 更大的上下文窗口
- 更具成本效益
- 與 Google Cloud 生態系統無縫集成

### Q: Milvus 數據如何遷移？
**A**: 
1. 導出 Milvus 中的文本數據
2. 使用新的 Gemini Embedding 重新嵌入
3. 存入新的向量存儲

### Q: 支援離線部署嗎？
**A**: Gemini 是雲端 API，不支援完全離線。如需離線，可考慮：
- 使用 Vertex AI 私有端點
- 或保留 Sentence Transformers 本地模型

### Q: Token 限制是多少？
**A**: 
- Gemini 1.5 Flash: 1M tokens 上下文
- Gemini 1.5 Pro: 2M tokens 上下文

---

## 下一步

- [ ] 配置 Vertex AI Matching Engine 生產索引
- [ ] 整合 Vertex AI RAG Engine
- [ ] 設置 Cloud Monitoring 監控
- [ ] 實施成本追蹤和警報
- [ ] 優化批次嵌入效能

---

## 支援

如遇問題，請查看：
- [Gemini API 文檔](https://ai.google.dev/docs)
- [Vertex AI 文檔](https://cloud.google.com/vertex-ai/docs)
- [Google AI Studio](https://aistudio.google.com/)

**遷移完成！** 🎉
