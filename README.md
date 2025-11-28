這是一份經過修改的系統設計文件。已將底層技術棧替換為 Google Cloud Platform (GCP) 的 **Vertex AI** 生態系，並具體整合了您指定的組件：**Gemini**、**Vertex AI Embeddings**、**Vertex AI Vector Search** 以及 **Vertex AI RAG Engine**。

-----

# 智能客服管理平台 (Vertex AI Native 版)

提供支援多企業（Multi-Tenant）的智能客服管理平台。
企業管理員可自行上傳知識檔案，透過 **Vertex AI RAG Engine** 實現 RAG，並使用 **Gemini** 系列模型進行問答。
一般使用者可在前台選擇企業並發問，未來可擴充為即時語音互動（語音問答）。

-----

## 目錄

1.  [專案簡介](https://www.google.com/search?q=%231-%E5%B0%88%E6%A1%88%E7%B0%A1%E4%BB%8B)
2.  [角色與使用情境](https://www.google.com/search?q=%232-%E8%A7%92%E8%89%B2%E8%88%87%E4%BD%BF%E7%94%A8%E6%83%85%E5%A2%83)
3.  [系統功能總覽](https://www.google.com/search?q=%233-%E7%B3%BB%E7%B5%B1%E5%8A%9F%E8%83%BD%E7%B8%BD%E8%A6%BD)
4.  [RAG 知識管線（Vertex AI RAG Engine）](https://www.google.com/search?q=%234-rag-%E7%9F%A5%E8%AD%98%E7%AE%A1%E7%B7%9Avertex-ai-rag-engine)
5.  [系統架構總覽](https://www.google.com/search?q=%235-%E7%B3%BB%E7%B5%B1%E6%9E%B6%E6%A7%8B%E7%B8%BD%E8%A6%BD)
6.  [核心服務與職責](https://www.google.com/search?q=%236-%E6%A0%B8%E5%BF%83%E6%9C%8D%E5%8B%99%E8%88%87%E8%81%B7%E8%B2%AC)
7.  [資料與 Multi-Tenant 設計](https://www.google.com/search?q=%237-%E8%B3%87%E6%96%99%E8%88%87-multi-tenant-%E8%A8%AD%E8%A8%88)
8.  [關鍵流程說明](https://www.google.com/search?q=%238-%E9%97%9C%E9%8D%B5%E6%B5%81%E7%A8%8B%E8%AA%AA%E6%98%8E)
9.  [基礎設施與技術選型](https://www.google.com/search?q=%239-%E5%9F%BA%E7%A4%8E%E8%A8%AD%E6%96%BD%E8%88%87%E6%8A%80%E8%A1%93%E9%81%B8%E5%9E%8B)
10. [觀測、營運與功能旗標](https://www.google.com/search?q=%2310-%E8%A7%80%E6%B8%AC%E7%87%9F%E9%81%8B%E8%88%87%E5%8A%9F%E8%83%BD%E6%97%97%E6%A8%99)
11. [安全與合規](https://www.google.com/search?q=%2311-%E5%AE%89%E5%85%A8%E8%88%87%E5%90%88%E8%A6%8F)
12. [後續擴充與 Roadmap](https://www.google.com/search?q=%2312-%E5%BE%8C%E7%BA%8C%E6%93%B4%E5%85%85%E8%88%87-roadmap)

-----

## 1\. 專案簡介

本專案是一套 **多企業共享平台** 的智能客服解決方案，深度整合 Google Cloud Vertex AI：

  - **支援多租戶（Multi-Tenant）**：單一平台服務多家企業，透過 Vertex AI 的 Namespace 或 Metadata Filter 進行嚴格資料隔離。
  - **企業管理員可**：
      - 上傳檔案建立自己的知識庫（利用 **Vertex AI RAG Engine** 自動化管線）。
      - 配置 **Gemini** 模型參數（Gemini 1.5 Pro / Flash 等）。
  - **終端使用者可**：
      - 在前台選擇要詢問的企業。
      - 以文字（未來支援語音）進行問答。
  - **預留即時語音互動架構**：
      - WebRTC + STT（Google Cloud Speech-to-Text / Chirp）
      - TTS（Google Cloud Text-to-Speech）

-----

## 2\. 角色與使用情境

### 2.1 角色定義

| 角色 | 說明 |
| :--- | :--- |
| **Platform Admin** (平台超級管理員) | 管理 GCP 資源配額、Vertex AI 索引節點規模、全平台計費與觀測。 |
| **Tenant Admin** (企業管理員) | 上傳文件至 RAG Engine Corpus；選擇 Gemini 模型版本；監控對話品質與 Token 成本。 |
| **Agent / Operator** (企業客服) | 審閱 Gemini 回覆內容、標註 Grounding 來源準確度、建立 FAQ。 |
| **End User** (終端使用者) | 在前台選擇企業並提問，取得基於企業知識的 Gemini 回覆。 |

### 2.2 典型使用情境 (略，同原版)

-----

## 3\. 系統功能總覽

### 3.1 平台層功能（Platform Admin）

  - 租戶註冊與 GCP Service Account 綁定管理（如需）。
  - **Vertex AI 配額管理**：監控 Embedding API 與 Gemini API 的 QPM (Queries Per Minute)。
  - 全平台觀測：透過 Google Cloud Monitoring 監控 Vector Search 延遲與 RAG Engine 狀態。

### 3.2 企業層功能（Tenant Admin）

  - **知識庫管理 (RAG Engine)**：
      - 檔案上傳：支援 PDF, HTML, Markdown 等，直接透過 API 注入 RAG Corpus。
      - 索引狀態：查看 Vertex AI RAG Corpus 的同步與索引進度。
  - **LLM 模型管理**：
      - 選擇模型：Gemini 1.5 Pro (擅長複雜推理/長文本) 或 Gemini 1.5 Flash (擅長快速回應/低成本)。
      - Prompt Engineering：設定 System Instructions 與 Safety Settings（安全性過濾）。
  - **對話與成本監控**：
      - 基於 Token 用量與 Vector Search 節點小時數計算成本。

### 3.3 \~ 3.4 (略，同原版)

-----

## 4\. RAG 知識管線（Vertex AI RAG Engine）

本系統使用 **Vertex AI RAG Engine** 搭配 **Vertex AI Vector Search** 進行全託管或半託管的知識處理。

### 4.1 支援檔案與擴充

**Vertex AI RAG Engine 支援格式**

  - 直接支援：PDF, HTML, Markdown, TXT。
  - 結構化資料：透過 Connector 連接 BigQuery 或 Cloud Storage。
  - **OCR 與多模態**：利用 Gemini 的多模態能力（Multimodal），可直接解析圖片與圖表內容進行 Embedding。

### 4.2 Chunk 與 Metadata (由 RAG Engine 輔助)

**Chunk 策略**

  - 利用 **Vertex AI RAG API** 的自動 Chunking 功能（Semantic Chunking）。
  - 針對特殊需求，可自行切分後使用 `ImportRagFiles` API 上傳。

**Metadata 與隔離**

  - **Tenant Isolation**：在建立 RAG Corpus 或 Index 時，為每個 Chunk 標記 `tenant_id`。
  - 使用 Vertex AI Vector Search 的 **Filtering (Restricts)** 功能，在檢索時強制帶入 `tenant_id` 條件，確保不會搜到其他企業的資料。

### 4.3 向量與索引 (Vertex AI Vector Search)

**Embedding 服務**

  - **模型**：`gemini-embedding-001` (或更新的 `text-embedding-004`)。
  - **多語言支援**：Google 的 Embedding 模型原生支援多語系，無需切換模型。

**向量庫 (Vertex AI Vector Search)**

  - **架構**：基於 Google 的 ScaNN 演算法，提供高吞吐量、低延遲的向量檢索。
  - **Index Endpoint**：部署 Index 至 Endpoint，支援 Public 或 VPC Peering 私有存取。
  - **Update 策略**：使用 Streaming Update (即時更新) 模式，讓企業上傳文件後能在秒級/分級內被檢索到。

### 4.4 檢索與生成流程 (Grounding with Gemini)

1.  **查詢進入**：Chat Orchestrator 接收使用者問題與 `tenant_id`。
2.  **檢索 (Retrieval)**：
      - 呼叫 **Vertex AI RAG Engine API** (Retrieve)。
      - 參數包含 `filter: "tenant_id = '123'"` 確保資料隔離。
      - 底層自動透過 Vertex AI Vector Search 進行語意搜尋。
3.  **生成 (Generation)**：
      - 使用 **Gemini API** (e.g., `generateContent`)。
      - 啟用 **Grounding** 功能：將檢索到的 Context 直接作為 Grounding Source 傳入 Gemini。
      - Gemini 自動生成回覆並附帶 \*\*Citation (引用來源)\*\*Metadata。
4.  **後處理**：
      - Gemini 內建 Safety Filters (阻擋仇恨言論、騷擾內容)。
      - 回傳最終答案與引用連結給前端。

-----

## 5\. 系統架構總覽

### 5.1 分層架構 (GCP Native)

```text
[Client Layer]
  - Web Portal / Admin Console
        |
        v
[Gateway & Security Layer]
  - Google Cloud Load Balancing (GCLB) / Cloud Armor (WAF)
  - Identity Aware Proxy (IAP) / Firebase Auth
  - Tenant Resolver
        |
        v
[Application Services Layer (Cloud Run / GKE)]
  - Auth & Tenant Service
  - Document Service (RAG Manager)
  - Chat Orchestrator
  - Agent Service
        |
        v
[AI & Data Layer (Vertex AI Managed)]
  - Vertex AI RAG Engine (Orchestration)
  - Vertex AI Embeddings (gemini-embedding-001)
  - Vertex AI Vector Search (Vector DB)
  - Vertex AI Gemini API (LLM)
  - Cloud Storage (GCS) - 原始檔案
  - Firestore / Cloud SQL - Metadata & Conversations
```

-----

## 6\. 核心服務與職責

### 6.1 Auth & Tenant Service

管理租戶與權限。建議整合 **Identity Platform (Firebase Auth)** 處理多租戶登入。

### 6.2 Knowledge Base & Document Service (RAG Manager)

  - 負責呼叫 Vertex AI API 建立 `RagCorpus`。
  - 將企業上傳的檔案 (GCS URI) 匯入至指定的 RAG Corpus。
  - 管理檔案的 `upload_status` 與同步狀態。

### 6.3 Vertex AI RAG Engine (取代原 RAG Orchestrator)

  - 這是 Google 全託管服務，負責從 GCS 拉取檔案、執行 Chunking、呼叫 Embedding API、並寫入 Vector Search Index。
  - 應用層只需呼叫 `ImportRagFiles` 即可。

### 6.4 Vertex AI Embeddings

  - 提供 `gemini-embedding-001` 或 `text-embedding-004` 模型。
  - 負責將文字轉為 768 維 (或更高) 的向量。

### 6.5 Vertex AI Vector Search

  - 高性能向量資料庫。
  - 負責儲存向量索引，並執行帶有 Filter (`tenant_id`) 的 ANN (Approximate Nearest Neighbor) 搜尋。

### 6.6 Chat Orchestrator

  - 核心對話邏輯。
  - 呼叫 Vertex AI Gemini API，設定 `tools: [retrieval_tool]` 來實現 RAG。
  - 處理對話歷史 (Context Window) 的管理。

-----

## 7\. 資料與 Multi-Tenant 設計

### 7.1 資料隔離原則

  - **Vector Search**：利用 **Numeric Restricts** 或 **String Allows** (Filtering) 機制。每個 Point (向量) 寫入時帶有 `restrict: [{"namespace": "tenant_123"}]`。查詢時必須帶上相同 Filter。
  - **RAG Engine**：若規模較大，可為每個大型租戶建立獨立的 `RagCorpus`；中小型租戶共用 Corpus 但透過 Metadata 過濾。

### 7.2 資料儲存 (Google Cloud)

**Metadata (Firestore / Cloud SQL)**

```json
// documents (metadata)
{
  "id": "doc_001",
  "tenantId": "tenant_123",
  "gcsUri": "gs://bucket/tenant_123/doc.pdf",
  "vertexRagFileId": "rag_file_xyz", // 對應 Vertex RAG 內的 ID
  "status": "IMPORTED"
}
```

**Vector Data (Vertex AI Vector Search)**

  - 由 RAG Engine 自動維護，或手動維護 Index 時包含：
      - `id`: `doc_001_chunk_01`
      - `embedding`: `[...]`
      - `restricts`: `[{ "namespace": "tenant_123" }, { "kb_id": "kb_faq" }]`

-----

## 8\. 關鍵流程說明

### 8.1 企業上傳文件 (RAG Ingestion)

1.  Tenant Admin 上傳檔案 -\> 存入 **Cloud Storage (GCS)**。
2.  Document Service 呼叫 **Vertex AI RAG API** (`UploadRagFile` 或 `ImportRagFiles`)。
      - 指定來源為 GCS URI。
      - 指定目標 RAG Corpus。
3.  Vertex AI 背景執行：解析 -\> Chunking -\> **Vertex AI Embeddings** -\> 更新 **Vertex AI Vector Search** 索引。
4.  完成後回調或透過 API 輪詢狀態，更新前端顯示「已就緒」。

### 8.2 終端使用者文字問答 (Retrieval & Generation)

1.  User 提問。
2.  Chat Orchestrator 呼叫 **Gemini API**：
      - Model: `gemini-1.5-pro`
      - Tool: `grounding_service` (指向 Vertex AI Search 或 RAG Corpus)。
      - **重點**：在 Retrieval Config 中設定 `filter` 為 `tenant_id`。
3.  Gemini 內部執行：
      - 將 Query 轉向量 (using **gemini-embedding-001**)。
      - 向 Vector Search 查詢 Top-K 相關片段 (Filtered by tenant)。
      - 將片段作為 Context 輸入模型。
4.  Gemini 回傳生成結果與 `grounding_metadata` (包含引用來源)。

-----

## 9\. 基礎設施與技術選型

### 9.1 Orchestration

  - **Google Kubernetes Engine (GKE)** 或 **Cloud Run** (Serverless)。
  - 全容器化微服務。

### 9.2 AI 核心組件 (Google Cloud)

  - **LLM**: Gemini 1.5 Pro / Flash (透過 Vertex AI API)。
  - **Embeddings**: `gemini-embedding-001` / `text-embedding-004`。
  - **Vector DB**: **Vertex AI Vector Search** (原 Matching Engine)。
  - **RAG Pipeline**: **Vertex AI RAG Engine**。

### 9.3 資料存儲

  - **Object Storage**: Google Cloud Storage (GCS)。
  - **App DB**: Cloud SQL (PostgreSQL) 或 Firestore (NoSQL)。
  - **Cache**: Memorystore for Redis (快取對話與 Session)。

### 9.4 Gateway 與安全

  - **API Gateway**: Apigee 或 Google Cloud API Gateway。
  - **Security**: IAM, Secret Manager (儲存 API Keys)。

-----

## 10\. 觀測、營運與功能旗標

### 10.1 Observability

  - **Metrics**: Google Cloud Monitoring。
      - 監控 Vector Search 的 QPS、Recall 率。
      - 監控 Gemini API 的 Quota usage。
  - **Logging**: Cloud Logging。
  - **Tracing**: Cloud Trace。

### 10.2 Feature Flags

  - 使用 Firebase Remote Config 或自行建置 OpenFeature 服務，控制 Gemini 模型版本的灰度發布。

-----

## 11\. 安全與合規

  - **資料駐留 (Data Residency)**：Vertex AI 支援指定 Region (如 `asia-east1` 台灣)，確保數據不離境。
  - **VPC Service Controls**：建立安全邊界，防止資料被未授權存取。
  - **Customer-Managed Encryption Keys (CMEK)**：使用 Cloud KMS 自管金鑰加密 Vector Search 索引與 GCS 檔案。

-----

## 12\. 後續擴充與 Roadmap

#### 語音模式 (Google Native)

  - **STT**: 使用 **Google Cloud Speech-to-Text v2** (Chirp 模型) 支援多語系高準確度辨識。
  - **TTS**: 使用 **Google Cloud Text-to-Speech** (Journey voices) 生成自然人聲。
  - **Multimodal Live**: 未來可整合 Gemini 1.5 Pro 的原生 Audio 輸入能力，略過 STT 直接進行語音理解。

#### 企業私有化 (Private Cloud)

  - 利用 **Google Distributed Cloud** (GDC) 或 Vertex AI on GDC 方案，支援高敏感產業的地端部署需求。