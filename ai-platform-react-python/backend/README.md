# 114 多企業智能客服平台後端

這是一個完整的多租戶（Multi-Tenant）智能客服管理平台後端系統。

## 功能特色

- **多租戶架構**：支援多個企業獨立使用，數據完全隔離
- **RAG 知識管理**：文件上傳、自動向量化、混合檢索
- **LLM 集成**：支援 OpenAI、Azure OpenAI、Anthropic 等多個提供者
- **對話管理**：完整的會話追蹤和歷史記錄
- **權限控制**：基於 RBAC 的多層級權限系統
- **向量搜尋**：使用 Milvus 進行高效的語義搜尋

## 技術棧

- **框架**：Flask 3.0
- **資料庫**：MongoDB、Milvus（向量）、Redis（快取）
- **AI/ML**：LangChain、Sentence Transformers、OpenAI API
- **認證**：JWT Token
- **文件處理**：PyPDF2、python-docx

## 快速開始

### 1. 環境準備

```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境（Windows）
.\venv\Scripts\activate

# 安裝依賴
pip install -r requirements.txt
```

### 2. 配置環境變數

```bash
# 複製環境變數範例
copy .env.example .env

# 編輯 .env 文件，填入必要配置
```

### 3. 啟動服務

**前置需求**：
- MongoDB 運行在 `localhost:27017`
- Milvus 運行在 `localhost:19530`（可選，未配置時會提示警告但仍可運行）
- Redis 運行在 `localhost:6379`（可選）

```bash
# 啟動應用
python app.py
```

服務將在 `http://localhost:5000` 啟動。

## API 文檔

### 認證端點

#### 註冊用戶
```http
POST /v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "User Name",
  "tenant_id": "租戶ID",
  "role": "end_user"
}
```

#### 用戶登入
```http
POST /v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

#### 獲取當前用戶
```http
GET /v1/auth/me
Authorization: Bearer <access_token>
```

### 租戶管理

#### 獲取租戶列表（平台管理員）
```http
GET /v1/tenants
Authorization: Bearer <access_token>
```

#### 創建租戶
```http
POST /v1/tenants
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "name": "企業名稱",
  "description": "企業描述",
  "plan": "專業版"
}
```

### 文件管理

#### 上傳文件
```http
POST /v1/tenants/{tenant_id}/documents/upload
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

file: <文件>
```

#### 獲取文件列表
```http
GET /v1/tenants/{tenant_id}/documents
Authorization: Bearer <access_token>
```

### 對話

#### 發送消息
```http
POST /v1/tenants/{tenant_id}/chat
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "你好",
  "conversation_id": "對話ID（可選）"
}
```

#### 串流對話
```http
POST /v1/tenants/{tenant_id}/chat/stream
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "message": "你好",
  "stream": true
}
```

#### 獲取對話列表
```http
GET /v1/tenants/{tenant_id}/chat/conversations
Authorization: Bearer <access_token>
```

## 專案結構

```
backend/
├── app.py                  # 應用入口
├── config.py              # 配置管理
├── requirements.txt       # 依賴套件
├── .env.example          # 環境變數範例
├── models/               # 資料模型
├── services/             # 業務服務層
├── routes/               # API 路由
├── utils/                # 工具函數
└── uploads/              # 上傳文件目錄
```

## 開發指南

### 添加新的 API 端點

1. 在 `routes/` 目錄創建新的路由文件
2. 定義藍圖和路由處理函數
3. 在 `app.py` 中註冊藍圖

### 添加新的服務

1. 在 `services/` 目錄創建服務文件
2. 實現業務邏輯
3. 在路由中調用服務

## 部署

### Docker 部署（建議）

```bash
# 構建鏡像
docker build -t ai-platform-backend .

# 運行容器
docker run -d -p 5000:5000 \
  -e MONGODB_URI=mongodb://host.docker.internal:27017/ \
  -e MILVUS_HOST=host.docker.internal \
  ai-platform-backend
```

### 生產環境配置

1. 修改 `.env` 中的 `FLASK_ENV=production`
2. 使用 Gunicorn 或 uWSGI 運行
3. 配置 Nginx 作為反向代理
4. 啟用 HTTPS

## 故障排除

### MongoDB 連接失敗
- 確認 MongoDB 服務正在運行
- 檢查 `.env` 中的 `MONGODB_URI` 配置

### Milvus 連接失敗
- 確認 Milvus 服務正在運行
- 系統會在無法連接時發出警告，但仍可繼續運行（搜尋功能將不可用）

### OpenAI API 錯誤
- 檢查 `.env` 中的 `OPENAI_API_KEY`
- 未配置 API Key 時會使用模擬回應

## 授權

MIT License

## 聯絡

如有問題，請聯繫開發團隊。
