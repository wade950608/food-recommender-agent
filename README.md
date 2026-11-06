# 🍜 吃什麼決策小幫手（Food Decision Agent）

輸入心情、預算或隨性想法，LLM 以**結構化輸出**產生 3 個候選餐點與一句話最終決策，並可用**串流**即時顯示推薦詞。採三層式架構，附可即時互動的網頁。

🔗 作品頁：`https://wade950608.github.io/food-recommender-agent/`

## 功能

- **結構化輸出**：Pydantic 定義 `FoodOption` / `DecisionReport`，`price_range` 用 `Literal` 限制選項。
- **串流**：`/api/persuade` 以 SSE 逐字輸出；網頁顯示首字延遲（TTFT）。
- **同一份程式切換本地與雲端**：`LLM_PROFILE=gemini|openai|local`。
- **三層式**：web（Nginx）→ api（FastAPI）→ db（PostgreSQL，internal 網路）。
- **CI/CD**：push 到 `main` → Actions 檢查 → 部署 `docs/` 到 GitHub Pages。
- **安全**：金鑰只在 `.env`，已被 `.gitignore` 排除。

## 架構

```
瀏覽器 ──:8080──▶ web (Nginx，提供 docs/ 並轉發 /api/*)   frontend 網路
                    ▼
                  api (FastAPI)       frontend + backend + ai
                  │         │
                  ▼         ▼
        db (PostgreSQL)   LLM：雲端 API，或選用的 ollama 容器
        backend（internal）
```

## 專案結構

```
├── agent/        llm.py（profile 切換）、schemas.py、api.py、cli.py
├── db/init.sql   decisions 表
├── docs/index.html   即時互動頁 + 作品頁（Nginx 與 GitHub Pages 共用）
├── nginx.conf、Dockerfile、compose.yaml
├── .github/workflows/deploy.yml
├── .env.example、.gitignore、pyproject.toml
```

## 執行（PowerShell）

```powershell
Copy-Item .env.example .env      # 填入 GEMINI_API_KEY 與 POSTGRES_PASSWORD
docker compose up -d --build
start http://localhost:8080
```

Gemini 金鑰可至 [Google AI Studio](https://aistudio.google.com/apikey) 申請。命令列版：

```powershell
uv sync
uv run python -m agent.cli "下雨天想吃辣，預算 300"
```

### 切換模型

| Profile | 設定 |
|---|---|
| Gemini（預設） | `LLM_PROFILE=gemini`、`GEMINI_API_KEY=...` |
| OpenAI | `LLM_PROFILE=openai`、`OPENAI_API_KEY=...` |
| 本地 Ollama | `LLM_PROFILE=local`、`LLM_BASE_URL=http://ollama:11434/v1`，然後 `docker compose --profile local up -d --build` 並 `docker compose exec ollama ollama pull qwen3:1.7b` |

## 部署 GitHub Pages

1. Repo → **Settings → Pages → Source** 選 **GitHub Actions**
2. push 到 `main`，到 **Actions** 分頁確認綠燈

Pages 是純靜態，後端不會跑在上面：頁面偵測不到本機後端時進入「離線示範」，有啟動 compose 時自動連到 `localhost:8080`。

## 排錯

| 症狀 | 處理 |
|---|---|
| 401 | 金鑰錯誤或沒寫進 `.env` |
| 429 | 免費額度限流，稍等或改用 `local` |
| model not found | 檢查 `MODEL_NAME`，本地用 `ollama list` |
| 頁面顯示離線示範 | `docker compose ps` 確認 api 為 running，再重新整理 |

## AI 使用說明

- **使用的工具**：Claude 3.7 Sonnet、ChatGPT、GitHub Copilot
- **用在哪裡**：
  - 協助設計 Pydantic 資料架構（`schemas.py`）與 FastAPI SSE 串流端點（`api.py`）。
  - 產出 GitHub Actions 部署工作流（`deploy.yml`）與 Docker 多容器網路配置。
- **自己修改或驗證了什麼**：
  - 排查並解決 Windows 系統下 `ascii codec` 編碼錯誤（在 `llm.py` 加入金鑰的 ASCII 與空白校驗邏輯）。
  - 測試並修正 Gemini / OpenAI / 本地 Ollama 三種環境變數切換邏輯，驗證 `beta.chat.completions.parse` 格式解析是否正確。
  - 手動測試 Docker 容器內資料庫網路連線（`psycopg` 連線超時與降級處理機制）。

## 安全提醒

請勿 commit `.env`。若金鑰不慎外洩（含 commit 歷史），立即到服務商後台撤銷並重新產生。
