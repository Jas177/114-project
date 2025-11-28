# lucid-dream-visualizer-closed

面向生產環境的夢境可視化管線：輸入夢境描述，輸出結構化解析、DALL·E 3 圖像、回寫 caption 以及 CLIPScore 等評估指標，並提供 Typer CLI 與批次實驗能力。

---

## 核心能力
- **夢境解析**：使用 GPT-4o-mini 產生結構化 JSON（標題、場景、角色、情緒、視覺風格、負面關鍵字、隨機種子）。
- **影像生成**：將解析結果轉換成 ≤800 字元的圖像提示，呼叫 DALL·E 3 建圖，可一次產生 N 張變體。
- **回合驗證**：以 GPT-4o-mini 對生成影像做 1–2 句 caption，確保語意回對。
- **量化指標**：透過 open-clip (ViT-B/32) 計算 Dream↔Image、Caption↔Image 的 CLIPScore（0–1），並蒐集延遲、估算成本。
- **批次分析**：支援單一夢境或 JSONL 批次，結果寫入 `data/outputs/results_closed.csv`，自動輸出對應圖像與簡易長條圖。

---

## 快速開始

```powershell
cd 114-project
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
```

編輯 `.env` 並填入 `OPENAI_API_KEY`。可視需要調整 `TEXT_MODEL`、`IMAGE_MODEL`、`OUTPUT_DIR`、`DEVICE`（`auto` 會優先使用 CUDA）。

---

## CLI 使用

單次夢境：

```powershell
python -m src.main run --dream "我在海邊追一輪會說話的月亮，很害怕但又興奮" --n 2
```

批次 JSONL（範例檔位於 `data/dreams.sample.jsonl`）：

```powershell
python -m src.main run-file --path data/dreams.sample.jsonl --n 2
```

輸出結構：
- `data/outputs/{dream_id}/closed/img_{k}.png`
- `data/outputs/{dream_id}/closed/prompt_{k}.txt`
- `data/outputs/{dream_id}/closed/caption_{k}.txt`
- `data/outputs/results_closed.csv`
- `data/outputs/charts/{metric}.png`

CSV 內容包含：夢境 ID、原始夢境、解析摘要、圖像檔案路徑、caption、語意分數、caption 分數、延遲、成本等欄位，可直接以 Pandas 或試算表進一步分析。

---

## 成本與延遲估算
- GPT-4o-mini：USD 0.00015 / 1K tokens（輸入、輸出統一計價）。
- DALL·E 3：USD 0.04 / 每張 1024×1024 圖像。
- GPT-4o-mini caption：同上。

程式會以常數估算每次呼叫成本，並記錄實際延遲。可在 `src/config.py` 中調整估算係數。

---

## 圖表輸出
- `semantic_consistency`: Dream↔Image CLIPScore 平均值。
- `caption_consistency`: Caption↔Image CLIPScore 平均值。
- `latency_seconds`: 單張圖像生成全流程延遲平均值。
- `cost_usd`: 單張圖像成本平均值。

每次批次執行後於 `data/outputs/charts/` 更新。圖表採 matplotlib，無需額外主題。

---

## 測試

```powershell
pytest
```

`tests/test_pipeline_smoke.py` 會檢查主要元件能夠在無 API Key 時建立並跳過外部呼叫。若未設定 `OPENAI_API_KEY` 會自動 `pytest.skip`，以利 CI 無密鑰情境。

---

## 開發說明
- 程式碼集中於 `src/`，使用 Typer 建立 CLI。
- 解析與 caption 服務位於 `src/services/` 與 `src/evaluators/`。
- CLIPScore 計算/圖表在 `src/evaluators/metrics.py`。
- 公共工具（檔案 I/O、計時器）在 `src/utils/`。
- 所有設定以 `pydantic` `BaseSettings` 裝載，自動讀取 `.env`。

---

## 注意事項
- 請勿將 `.env` 提交至版本控制。
- 驗證 reproducibility：若解析回傳 `seed`，影像服務會嘗試帶入（DALL·E 3 目前不保證 determinism，但可紀錄）。
- 若需 GPU 推論，請確認 Torch 與 open-clip 支援對應 CUDA 版本。

歡迎提交 Issue/PR 改進解析 schema 或評估指標。

