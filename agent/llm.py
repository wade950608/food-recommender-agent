"""同一份程式，切換本地與雲端：只靠環境變數。"""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# profile -> (base_url, 金鑰變數名, 預設模型)
PROFILES = {
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/",
               "GEMINI_API_KEY", "gemini-3.5-flash"),
    "openai": ("https://api.openai.com/v1", "OPENAI_API_KEY", "gpt-4o-mini"),
    "local": ("http://localhost:11434/v1", "", "qwen2.5:1.5b"),
}

PROFILE = os.getenv("LLM_PROFILE", "gemini")
if PROFILE not in PROFILES:
    raise SystemExit(f"LLM_PROFILE 必須是 {list(PROFILES)} 其中之一")

_base, _key_env, _model = PROFILES[PROFILE]
BASE_URL = os.getenv("LLM_BASE_URL") or _base
MODEL = os.getenv("MODEL_NAME") or _model
API_KEY = (os.getenv(_key_env) if _key_env else "ollama") or "missing-key"

if PROFILE != "local":
    if not API_KEY.isascii():
        raise SystemExit(f"{_key_env} 必須是純 ASCII API 金鑰，不可包含中文或其他 Unicode 字元")
    if API_KEY != API_KEY.strip() or any(char.isspace() for char in API_KEY):
        raise SystemExit(f"{_key_env} 不可包含空白或換行")
    if API_KEY == "missing-key" or "your key here" in API_KEY.lower():
        raise SystemExit(f"請在 .env 設定有效的 {_key_env}")

client = OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=60)
