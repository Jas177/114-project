# Vertex AI 設置指南

本文檔說明如何設置和配置 Vertex AI 相關服務，讓後端系統能夠使用完整的 Vertex AI Native 功能。

---

## 前提條件

1. **Google Cloud 專案**
   - 已創建 GCP 專案
   - 已啟用計費

2. **必要的 API**
   ```bash
   gcloud services enable aiplatform.googleapis.com
   gcloud services enable storage.googleapis.com
   gcloud services enable generativelanguage.googleapis.com
   ```

3. **身份認證**
   - Vertex AI API Key（已配置）
   - 或服務帳號 JSON 文件

---

## 設置步驟

### 1. Cloud Storage (GCS) 設置

#### 創建 Bucket
```bash
# 設置變數
export PROJECT_ID="your-project-id"
export BUCKET_NAME="your-bucket-name"
export LOCATION="asia-east1"  # 台灣區域

# 創建 Bucket
gsutil mb -p $PROJECT_ID -l $LOCATION gs://$BUCKET_NAME
```

#### 設置 CORS（如需前端直接上傳）
```bash
cat > cors.json << EOF
[
  {
    "origin": ["*"],
    "method": ["GET", "POST", "PUT"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://$BUCKET_NAME
```

#### 更新環境變數
在 `.env` 文件中設置：
```env
GCS_BUCKET_NAME=your-bucket-name
```

---

### 2. Vertex AI RAG Engine 設置

#### 啟用 RAG Engine（自動完成）

RAG Engine 會在首次使用時自動初始化。系統會自動為每個租戶創建獨立的 Corpus。

#### 啟用 RAG Engine 功能
在 `.env` 文件中設置：
```env
USE_RAG_ENGINE=true
RAG_CORPUS_PREFIX=tenant
```

#### 測試 RAG Engine
```python
# Python Shell 測試
from services.rag_engine_service import rag_engine_service

# 創建 Corpus
corpus_name = rag_engine_service.create_or_get_corpus("tenant_123")
print(f"Corpus 名稱: {corpus_name}")
```

---

### 3. Vertex AI Vector Search 設置（可選）

如果要使用實際的 Vertex AI Vector Search 而非內存存儲：

#### 創建 Index
```python
from google.cloud import aiplatform

aiplatform.init(project=PROJECT_ID, location=LOCATION)

# 創建 Index
index = aiplatform.MatchingEngineIndex.create_tree_ah_index(
    display_name="knowledge-base-index",
    dimensions=768,  # Gemini Embedding 維度
    approximate_neighbors_count=10,
    distance_measure_type="COSINE_DISTANCE",
    leaf_node_embedding_count=500,
    leaf_nodes_to_search_percent=7
)

print(f"Index 資源名稱: {index.resource_name}")
```

#### 創建 Index Endpoint`
```python
endpoint = aiplatform.MatchingEngineIndexEndpoint.create(
    display_name="knowledge-base-endpoint",
    public_endpoint_enabled=True
)

print(f"Endpoint 資源名稱: {endpoint.resource_name}")
```

#### 部署 Index
```python
deployed_index = endpoint.deploy_index(
    index=index,
    deployed_index_id="deployed_kb_index",
    machine_type="e2-standard-2",
    min_replica_count=1,
    max_replica_count=2
)

print(f"部署完成: {deployed_index.deployed_index_id}")
```

#### 更新環境變數
```env
VERTEX_AI_INDEX_ID=projects/PROJECT_ID/locations/LOCATION/indexes/INDEX_ID
VERTEX_AI_INDEX_ENDPOINT=projects/PROJECT_ID/locations/LOCATION/indexEndpoints/ENDPOINT_ID
VERTEX_AI_DEPLOYED_INDEX_ID=deployed_kb_index
```

---

### 4. 身份認證設置

#### 方式一：使用 API Key（當前）
```env
GOOGLE_API_KEY=AIzaSyBL7NHjZTfmkJ7HbPg7_V06v_uUkF_RRVg
VERTEX_AI_API_KEY=AQ.Ab8RN6Krm9GqDZaNm_hdfIBerVg2_XDKOMulkEeCzBdnUQL_jw
```

#### 方式二：使用服務帳號（推薦生產環境）

1. 創建服務帳號
```bash
gcloud iam service-accounts create ai-platform-backend \
    --display-name="AI Platform Backend"
```

2. 授予權限
```bash
# Vertex AI 使用者
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:ai-platform-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

# Storage 物件管理員
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:ai-platform-backend@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.objectAdmin"
```

3. 下載金鑰
```bash
gcloud iam service-accounts keys create service-account-key.json \
    --iam-account=ai-platform-backend@$PROJECT_ID.iam.gserviceaccount.com
```

4. 設置環境變數
```env
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

---

## 系統配置

### 環境變數完整清單

```env
# Google Cloud 基礎配置
GOOGLE_API_KEY=AIzaSyBL7NHjZTfmkJ7HbPg7_V06v_uUkF_RRVg
GOOGLE_PROJECT_ID=your-project-id
GOOGLE_LOCATION=asia-east1

# Vertex AI
VERTEX_AI_API_KEY=AQ.Ab8RN6Krm9GqDZaNm_hdfIBerVg2_XDKOMulkEeCzBdnUQL_jw

# Vertex AI Vector Search（可選）
VERTEX_AI_INDEX_ID=
VERTEX_AI_INDEX_ENDPOINT=
VERTEX_AI_DEPLOYED_INDEX_ID=

# Vertex AI RAG Engine
USE_RAG_ENGINE=true
RAG_CORPUS_PREFIX=tenant

# Cloud Storage
GCS_BUCKET_NAME=your-bucket-name
GCS_DOCUMENTS_PREFIX=tenants

# Grounding
USE_GROUNDING=true
GROUNDING_SOURCE_TYPE=rag_engine

# Gemini
GEMINI_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.7
GEMINI_MAX_TOKENS=2048

# Embedding
EMBEDDING_MODEL=models/embedding-001
EMBEDDING_DIMENSION=768
```

---

## 測試與驗證

### 1. 測試 GCS 上傳

```bash
# 測試文件上傳
curl -X POST http://localhost:5000/v1/tenants/tenant_123/documents/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@test.pdf"

# 檢查 GCS
gsutil ls gs://your-bucket-name/tenants/tenant_123/documents/
```

### 2. 測試 RAG Engine

```python
from services.rag_engine_service import rag_engine_service
from services.cloud_storage_service import cloud_storage_service

# 1. 上傳文件到 GCS
gcs_uri = cloud_storage_service.upload_from_filename(
    source_file_path="test.pdf",
    tenant_id="tenant_123",
    destination_filename="test.pdf"
)

# 2. 匯入到 RAG Engine
rag_files = rag_engine_service.import_files(
    tenant_id="tenant_123",
    gcs_uris=[gcs_uri]
)

# 3. 檢索測試
results = rag_engine_service.retrieval_query(
    tenant_id="tenant_123",
    query="文件中提到了什麼？"
)

print(f"檢索到 {len(results)} 個結果")
```

### 3. 測試 Grounding 對話

```bash
curl -X POST http://localhost:5000/v1/tenants/tenant_123/chat \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "請告訴我文件的主要內容"
  }'
```

**預期結果**：
- `grounded: true`
- `citations` 陣列包含引用來源
- 回應內容標註 `[來源 N]`

---

## 故障排除

### 問題：RAG Engine 初始化失敗

**錯誤訊息**：`RAG Engine 初始化失敗`

**解決方案**：
1. 確認 `aiplatform.googleapis.com` API 已啟用
2. 確認 `GOOGLE_PROJECT_ID` 配置正確
3. 檢查權限：服務帳號需要 `aiplatform.user` 角色
4. 暫時禁用 RAG Engine：`USE_RAG_ENGINE=false`

### 問題：GCS 上傳失敗

**錯誤訊息**：`GCS 初始化失敗` 或 `Bucket 不存在`

**解決方案**：
1. 確認 Bucket 已創建：`gsutil ls`
2. 確認 Bucket 名稱正確
3. 確認服務帳號有 `storage.objectAdmin` 權限
4. 檢查 CORS 設置（如需前端直接上傳）

### 問題：Embedding API 配額超限

**錯誤訊息**：`429 Resource has been exhausted`

**解決方案**：
1. 在 GCP Console 提高配額
2. 實施批次處理和重試機制
3. 添加延遲和限流

---

## 成本優化建議

### 1. Gemini API
- 使用 `gemini-1.5-flash` 而非 `gemini-1.5-pro`
- 設置適當的 `max_tokens` 限制
- 啟用快取（對於重複的上下文）

### 2. Embedding API
- 批次處理文本（每次最多 100 個）
- 快取已嵌入的文本
- 使用適當的 chunk_size（建議 512）

### 3. Vector Search
- Streaming Update 而非完全重建
- 使用較小的 `machine_type` 開始
- 設置自動擴展策略

### 4. Cloud Storage
- 使用 Nearline 或 Coldline 存儲歷史文件
- 設置生命週期管理
- 啟用壓縮

---

## 監控與警報

### Cloud Monitoring

創建警報策略：
```bash
# API 配額使用率
gcloud alpha monitoring policies create \
    --notification-channels=CHANNEL_ID \
    --display-name="Gemini API Quota Alert" \
    --condition-display-name="Quota > 80%" \
    --condition-threshold-value=0.8 \
    --condition-threshold-duration=300s
```

### 日誌查詢

```bash
# 查看 RAG Engine 日誌
gcloud logging read "resource.type=aiplatform.googleapis.com/RagCorpus" \
    --limit=50 \
    --format=json

# 查看 Embedding API 錯誤
gcloud logging read "severity>=ERROR AND resource.type=generativelanguage.googleapis.com" \
    --limit=50
```

---

## 下一步

1. ✅ 配置生產環境的服務帳號
2. ✅ 設置 Cloud Monitoring 警報
3. ✅ 實施成本追蹤
4. ✅ 整合前端應用
5. ✅ 負載測試

---

## 參考資源

- [Vertex AI RAG Engine 文檔](https://cloud.google.com/vertex-ai/docs/generative-ai/rag-overview)
- [Vertex AI Vector Search 文檔](https://cloud.google.com/vertex-ai/docs/matching-engine/overview)
- [Gemini API 文檔](https://ai.google.dev/docs)
- [Cloud Storage 文檔](https://cloud.google.com/storage/docs)
