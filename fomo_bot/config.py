import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()

BASE_URL = os.getenv("FOMO_BASE_URL", "https://getfomoapi.fun").rstrip("/")
API_KEY = os.getenv("FOMO_API_KEY", "").strip()
REQUEST_TIMEOUT = float(os.getenv("FOMO_REQUEST_TIMEOUT", "30"))
MAX_RETRIES = int(os.getenv("FOMO_MAX_RETRIES", "5"))
DATABASE_PATH = Path(os.getenv("FOMO_DATABASE_PATH", "data/fomo_bot.db"))
EXPORT_PATH = Path(os.getenv("FOMO_EXPORT_PATH", "exports"))
