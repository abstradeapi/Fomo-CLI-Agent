import random
import time
from collections import deque
from urllib.parse import quote

import requests

from fomo_bot.config import BASE_URL, MAX_RETRIES, REQUEST_TIMEOUT


class FomoApiError(Exception):
    pass


class FomoAuthError(FomoApiError):
    pass


class FomoClient:
    def __init__(self, api_key=""):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json", "User-Agent": "FomoTerminal/1.0"})
        self.requests = deque()

    def set_api_key(self, api_key):
        self.api_key = api_key.strip()

    def close(self):
        self.session.close()

    def _throttle(self):
        now = time.monotonic()
        while self.requests and now - self.requests[0] >= 1:
            self.requests.popleft()
        if len(self.requests) >= 5:
            time.sleep(max(1 - (now - self.requests[0]), 0))
            now = time.monotonic()
            while self.requests and now - self.requests[0] >= 1:
                self.requests.popleft()
        self.requests.append(time.monotonic())

    def _get(self, path, params=None, protected=True):
        if protected and not self.api_key:
            raise FomoAuthError("A Fomo API key is required")
        headers = {"X-API-Key": self.api_key} if protected else {}
        url = f"{BASE_URL}{path}"
        for attempt in range(MAX_RETRIES + 1):
            self._throttle()
            try:
                response = self.session.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
            except requests.RequestException as error:
                if attempt == MAX_RETRIES:
                    raise FomoApiError(f"Network request failed: {error}") from error
                time.sleep(min(2 ** attempt, 30) + random.uniform(0, 0.5))
                continue
            if response.status_code < 400:
                try:
                    payload = response.json()
                except ValueError as error:
                    raise FomoApiError("The API returned invalid JSON") from error
                if isinstance(payload, dict) and payload.get("success") is False:
                    raise FomoApiError(payload.get("message", "API request failed"))
                return payload
            detail = self._error_detail(response)
            if response.status_code not in {429, 502, 503, 504} or attempt == MAX_RETRIES:
                if response.status_code in {401, 403}:
                    raise FomoAuthError(detail)
                raise FomoApiError(f"HTTP {response.status_code}: {detail}")
            retry_after = response.headers.get("Retry-After")
            try:
                delay = float(retry_after) if retry_after else min(2 ** attempt, 30)
            except ValueError:
                delay = min(2 ** attempt, 30)
            time.sleep(delay + random.uniform(0, 0.5))
        raise FomoApiError("Request failed")

    def _error_detail(self, response):
        try:
            payload = response.json()
            return payload.get("detail") or payload.get("message") or response.reason
        except ValueError:
            return response.text.strip() or response.reason

    def health(self):
        return self._get("/api/health", protected=False)

    def public_leaderboard(self):
        return self._get("/frontpage/leaderboard", protected=False)

    def leaderboard(self, window="24h", limit=10):
        return self._get(f"/api/leaderboard/{quote(window, safe='')}", {"limit": limit})

    def resolve_trader(self, handle):
        return self._get(f"/api/users/{quote(handle.lstrip('@'), safe='')}")

    def balances(self, user_id):
        return self._get(f"/api/users/{quote(user_id, safe='')}/balances")

    def spotlight(self, user_id):
        return self._get(f"/api/users/{quote(user_id, safe='')}/spotlight")

    def swaps(self, user_id, limit=20, cursor=None):
        params = {"limit": limit}
        if cursor:
            params["cursor"] = cursor
        return self._get(f"/api/users/{quote(user_id, safe='')}/swaps", params)

    def trader_ranking(self, user_id):
        return self._get(f"/api/users/{quote(user_id, safe='')}/leaderboard")

    def aggregated_snapshot(self, user_id, snapshot_id):
        return self._get("/api/user-tokens/aggregated-snapshot", {"user_id": user_id, "snapshot_id": snapshot_id})

    def following_ids(self):
        return self._get("/api/users/current/following-ids")

    def response_object(self, payload):
        return payload.get("responseObject", {}) if isinstance(payload, dict) else {}
