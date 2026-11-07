import time
from pathlib import Path
import requests

BASE_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json"

class SECClient:
    def __init__(self, user_agent: str, delay_seconds: float = 0.15):
        if not user_agent or "your.email@example.com" in user_agent:
            raise ValueError("Set SEC_USER_AGENT in .env to an application name and your contact email.")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": user_agent,
            "Accept-Encoding": "gzip, deflate",
            "Host": "data.sec.gov",
        })
        self.delay_seconds = max(0.1, delay_seconds)

    def fetch_companyfacts(self, cik: str) -> dict:
        url = BASE_URL.format(cik=cik.zfill(10))
        response = self.session.get(url, timeout=45)
        response.raise_for_status()
        time.sleep(self.delay_seconds)
        return response.json()

    def save_companyfacts(self, cik: str, ticker: str, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        payload = self.fetch_companyfacts(cik)
        path = output_dir / f"{ticker}_companyfacts.json"
        path.write_text(__import__("json").dumps(payload), encoding="utf-8")
        return path
