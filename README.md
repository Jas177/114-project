# 多企業智能客服管理平台系統架構提案（v0.1）

> 目標：提供支援多企業（Multi‑Tenant）的智能客服管理平台。企業管理員可自行上傳知識檔案以實現 RAG，並可自選/切換 LLM。一般使用者可在前台選擇企業並發問。後續擴充即時語音互動。

---

## 1) 角色與使用情境

* **平台超級管理員（Platform Admin）**：平台級用戶管理、計費、觀測與合規。
* **企業管理員（Tenant Admin）**：設定企業資訊、權限、上傳文件、建立知識庫、選擇/配置 LLM、監控對話與成本。
* **企業客服（Agent/Operator）**：審閱/標註對話、建立 FAQ、修補知識缺口、建立工作流程。
* **終端使用者（End User）**：前台選擇企業 → 提問（文字/語音）。

---

## 2) 高階架構總覽

```
[Client Apps]
  ├─ 前台使用者 Portal (Web/Mobile, 未來 Voice/WebRTC)
  └─ 後台管理 Console (Admin SPA)
        │
        ▼
[Edge]
  ├─ CDN / WAF / DDoS 防護
  └─ API Gateway / Ingress (OIDC, Rate Limit, AuthZ)
        │
        ▼
[Core Backend]
  ├─ 身份與租戶服務 (AuthN/AuthZ, RBAC, SSO, 多租戶隔離)
  ├─ 對話協調器 (Conversation Orchestrator)
  │    ├─ 提示模板/安全防護 (Prompt Guard, Output Filter)
  │    ├─ 檢索器 (Retriever) + 重排序 (Re-Ranker)
  │    └─ LLM 路由器 (Model Router)
  ├─ 知識庫與索引服務 (Ingestion → Chunk → Embedding → Vector Index)
  ├─ 模型管理/註冊 (Model Registry & Provider Connectors)
  ├─ 工作流引擎 (可選，任務/流程自動化)
  ├─ 觀測與治理 (Logs/Traces/Metrics, Token/成本監控)
  ├─ 訂閱與計費 (Plans/Quotas/Billing)
  └─ 通知服務 (Email/Webhook/Slack/LINE)
        │
        ▼
[Data Layer]
  ├─ 物件儲存 (MongoDB； 相容，用於原始檔案/轉換產物)
  ├─ 向量資料庫 (Per-Tenant Namespace/Index)
  ├─ 交易型資料庫 (PostgreSQL，多租戶 schema)
  └─ 快取/佇列 (Redis / MQ)
```

---

## 3) 多用戶（Multi‑Tenant）設計與隔離

* **身份邊界**：所有請求皆須帶上 `tenant_id`（Header/Token 內），Gateway 與後端服務強制驗證。
* **資料隔離**：

  * 向量庫以 `per-tenant index/namespace` 分隔。
  * 交易庫採 **Schema-per-tenant**（中小規模）或 **Row-level security**（大型且數量多）。
  * 物件儲存以前綴 `tenants/{tenant_id}/...` 管理。
* **金鑰隔離**：KMS 產生租戶級別加密金鑰；機密（API Keys、Provider Tokens）以 **Secrets Manager** 持有。
* **配額與節流**：依租戶計算 Token / QPS / 并發度；超限回退、排程、或降級策略。
* **審計**：租戶級審計日誌（設定變更、匯入、對話導出、資料存取）。

---

## 4) RAG 知識管線（Ingestion → Indexing → Retrieval）

### 4.1 支援檔案與擴充

* **格式**：PDF、DOCX、PPTX、XLSX/CSV、Markdown、HTML、TXT、FAQ JSON、知識庫 ZIP。
* **抽取**：

  * 文字抽取（含版面保持/簡化兩模式）。
  * OCR（掃描 PDF/影像）。
  * 表格與清單正規化；圖片（可選：圖說生成）。
* **資料清理**：語言偵測、去噪、標點修復、斷詞/分句、代碼區塊處理、URL 展開。
* **安全/隱私**：PII/敏感資訊偵測與遮蔽策略（可配置規則與允許名單）。

### 4.2 Chunk 與 Metadata

* **Chunk 策略**：語意段落 + 視窗重疊（例如 500–1,000 tokens，overlap 50–150）。
* **Metadata**：`tenant_id, doc_id, section, page, heading, tags, updated_at, language` 等。
* **版本化**：`doc_version` 與 `index_version`；支援回滾與藍綠索引切換（零停機重建）。

### 4.3 向量與索引

* **Embedding 服務**：提供多模型（如通用 vs. 多語、長文本專用）；快取重複段。
* **向量庫**：支援（擇一或混合）
* **混合檢索**：向量相似度 + BM25 + 重排序（Cross-Encoder/Reranker）。

### 4.4 檢索與生成流程（RAG）

1. 對話協調器收到查詢（具 `tenant_id`）。
2. 使用檢索器在該租戶索引中搜尋 k 個候選（Hybrid）。
3. 重排序器精排，保留前 n 個片段。
4. 套用租戶專屬提示模板（含引用格式/語氣/語言政策）。
5. 交由 LLM 生成，並插入引用來源（可選：行內或尾註）。
6. 後處理（檢查 PII、敏感詞、迷惑輸出、長度裁切）。

---

## 5) 模型管理與路由（Model Registry & Router）

* **模型註冊**：每租戶可掛載多個 Provider（OpenAI/Azure/Anthropic/Google、本地 vLLM 等），定義：`model_id, provider, api_key_ref, context_length, cost_profile, latency_slo`。
* **策略路由**：依請求型別（聊天/嵌入/重排序）、長度、成本上限、SLA 需求動態選模；失敗自動 Failover。
* **安全防護**：Prompt Injection 防護、系統提示固定區塊、工具調用白名單、輸出過濾（正則/關鍵詞/分類器）。
* **可觀測**：每模型的延遲、成功率、token 使用量、成本占比；看板與警示。

---

## 6) 對話引擎與會話管理

* **狀態**：Conversation / Turn / Message / ToolCall 表設計（見 §11）。
* **Streaming**：支援 SSE/WebSocket 回傳增量字串。
* **記憶（可選）**：短期（對話上下文裁切）與長期（摘要到向量庫，以租戶隔離）。
* **工具調用**：Connector 風格（FAQ 查詢、企業 API、工單系統、資料庫查詢、日曆/CRM）。
* **內容政策**：支援每租戶自定回應語氣、品牌詞彙、禁回主題清單。

---

## 7) 語音功能規劃（未來擴充）

* **即時語音 QA**：

  * 前端：WebRTC + 麥克風串流；語音活動偵測（VAD）。
  * **ASR**：串流語音轉文字（Whisper/Deepgram/Azure Speech 等插槽化）。
  * **TTS**：文字轉語音（多語音色/語速）；回傳音訊分段播放。
  * **延遲優化**：分段轉寫 + 並行檢索；先粗後細（先回短答，後補充）。
* **語音留言模式**：離線上傳 → 異步轉寫 → 回信/通知結果。

---

## 8) 前後台功能列表

### 後台（企業管理 Console）

* 客戶設定：品牌、域名、SSO；金鑰與 Provider 管理。
* 知識庫：檔案上傳、處理進度、索引版本、資料清理規則、權限（部門/標籤）。
* 模型設定：預設聊天模型/嵌入模型/重排序模型；成本上限；SLA。
* 對話監控：對話記錄、評分、重訓建議、常見落答。
* 成本&配額：Token/請求數/儲存用量看板與警示。

### 前台（終端使用者 Portal）

* 企業選擇器（必填）：`?tenant=xxx` 或 UI 選單。
* 聊天 UI：支援引用展開、檔案上傳（若客戶開啟）、語音模式（未來）。
* 追問/重試、語言切換（自動偵測 zh‑TW 為預設）。

---

## 10) 介面設計（API, 以 REST 為例）

* `POST /v1/auth/login`、`GET /v1/me`
* `GET /v1/tenants/:id`、`PATCH /v1/tenants/:id`
* `POST /v1/tenants/:id/documents/upload`（多段傳輸、進度查詢 `GET /.../tasks/:taskId`）
* `POST /v1/tenants/:id/documents/reindex`（藍綠切換）
* `POST /v1/tenants/:id/chat`（文字）
* `POST /v1/tenants/:id/chat/stream`（SSE/WebSocket）
* `POST /v1/tenants/:id/chat/voice`（語音串流，WebRTC/GRPC）
* `POST /v1/tenants/:id/models`（註冊/更新模型）
* `GET /v1/tenants/:id/analytics`（成本/延遲/成功率）

---

## 11) 流程設計（序列與控制）

### 11.1 使用者提問（文字）

1. 前端攜帶 `tenant_id` → Gateway 驗證身份與配額。
2. 對話協調器建立 `conversation`（或續用）與 `message`。
3. 檢索器在租戶向量庫檢索（Hybrid），重排序器精排。
4. 應用租戶提示模板 → LLM 路由器選模 → 生成（串流）。
5. 後處理與安全審核 → 回傳（附引用）。
6. 記錄遙測、成本、檢索與引用。

### 11.2 管理員上傳文件 → 建索引

1. 上傳至 DB
2. 觸發 Ingestion 任務（佇列）→ 文字抽取/OCR → 清理/切塊 → 嵌入。
3. 寫入向量庫（臨時 index），完成後藍綠切換成「現行」。
4. 產生可視化報表（覆蓋率、檔案健康度、斷詞統計）。

---

## 12) 非功能性需求（NFRs）

* **SLA/SLO**：P50 1.5s / P95 6s（文字查詢，非語音）；可配置降級：關閉重排序、縮小上下文。
* **可用性**：多 AZ；定期備援（DB/Index/S3），RPO ≤ 1h，RTO ≤ 4h。
* **安全**：全站 TLS、靜態加密、最小權限 IAM、CSP、WAF、檔案掃毒。
* **合規**：GDPR/ISO 27001 導向的資料最小化與審計；數據駐留策略。

---

## 13) 可觀測性與治理

* **Metrics**：QPS、延遲、失敗率、Token/成本、檢索命中率、回答採納率。
* **Tracing**：一條查詢橫跨 Gateway → Orchestrator → Retriever → LLM → 後處理。
* **Logging**：結構化，租戶隔離；敏感資訊遮蔽後再存。
* **A/B 與評估**：離線（對齊指標：Faithfulness/Context Recall）+ 線上（CTR/CSAT）。

---

## 14) 基礎設施與技術選型

* **Kubernetes**（EKS/GKE/AKS）+ HPA/Autoscaling；
* **DB**：MongoDB；
* **Cache/Queue**：Redis（快取/節流/工作佇列）或 Kafka（高吞吐流水線）；
* **Object Storage**：S3 相容；
* **Vector DB**：milvus；
* **Gateway**：Nginx Ingress/Envoy + OIDC；
* **觀測**：Prometheus/Grafana + OpenTelemetry + Loki/ELK；
* **功能旗標**：OpenFeature/Unleash；
* **前端**：Next.js/React + Tailwind；
* **語音**：WebRTC +（Whisper/Deepgram/Azure Speech）+ （TTS: Azure/ElevenLabs/Google）。

