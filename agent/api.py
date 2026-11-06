"""應用層：FastAPI。/api/decide（結構化輸出）、/api/persuade（串流）、/api/history（資料層）。"""
import json
import logging
import os
import time

import psycopg
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from .llm import MODEL, PROFILE, client
from .schemas import SYSTEM, DecisionReport

log = logging.getLogger("food")
app = FastAPI(title="Food Decision Agent")
# 讓 GitHub Pages 上的作品頁也能呼叫本機後端（沒有 cookie，僅開放此 API）
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Ask(BaseModel):
    prompt: str = Field(min_length=1, max_length=200)


class Persuade(Ask):
    dish: str = Field(min_length=1, max_length=60)


def _db():
    return psycopg.connect(os.environ["DATABASE_URL"], connect_timeout=3)


@app.get("/api/health")
def health():
    try:
        with _db() as c:
            c.execute("SELECT 1")
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "profile": PROFILE, "model": MODEL, "db": db_ok}


@app.post("/api/decide")
def decide(a: Ask):
    t0 = time.perf_counter()
    try:
        r = client.beta.chat.completions.parse(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM},
                      {"role": "user", "content": a.prompt}],
            response_format=DecisionReport,
        )
    except Exception as e:  # 金鑰錯誤、429、連線失敗…
        raise HTTPException(502, f"LLM 呼叫失敗：{e}") from e
    report = r.choices[0].message.parsed
    if report is None:
        raise HTTPException(502, "模型沒有回傳符合格式的結果，請再試一次")
    ms = int((time.perf_counter() - t0) * 1000)
    tokens = r.usage.total_tokens if r.usage else None
    try:
        with _db() as c:
            c.execute(
                "INSERT INTO decisions(prompt, result, model, latency_ms) VALUES (%s,%s,%s,%s)",
                (a.prompt, report.model_dump_json(), MODEL, ms),
            )
    except Exception as e:  # 資料層壞掉不應讓主功能失敗
        log.warning("寫入資料庫失敗：%s", e)
    return {"report": report.model_dump(), "model": MODEL, "latency_ms": ms, "tokens": tokens}


@app.post("/api/persuade")
def persuade(p: Persuade):
    """串流：邊生成邊送出（Server-Sent Events 格式）。"""
    def sse(obj: dict) -> str:
        return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n"

    def gen():
        t0, ttft = time.perf_counter(), None
        try:
            stream = client.chat.completions.create(
                model=MODEL, stream=True,
                messages=[
                    {"role": "system", "content": "你是熱情的美食朋友，用繁體中文、80 字內說服使用者吃這道菜。"},
                    {"role": "user", "content": f"我的狀況：{p.prompt}。請說服我吃「{p.dish}」。"},
                ],
            )
            for ch in stream:
                if not ch.choices or not ch.choices[0].delta.content:
                    continue
                if ttft is None:
                    ttft = int((time.perf_counter() - t0) * 1000)
                yield sse({"t": ch.choices[0].delta.content})
            yield sse({"done": True, "ttft_ms": ttft})
        except Exception as e:
            yield sse({"error": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/history")
def history():
    try:
        with _db() as c:
            rows = c.execute(
                "SELECT prompt, result->>'final_verdict', model, latency_ms, created_at "
                "FROM decisions ORDER BY id DESC LIMIT 8"
            ).fetchall()
    except Exception as e:
        raise HTTPException(503, f"資料庫無法使用：{e}") from e
    return [{"prompt": r[0], "verdict": r[1], "model": r[2], "latency_ms": r[3],
             "at": r[4].isoformat()} for r in rows]
