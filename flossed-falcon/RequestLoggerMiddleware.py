import json
import datetime

from math import ceil

class RequestLoggerMiddleware:

    def __init__(self) -> None:
        self._last_logwrite = datetime.datetime.utcnow()
        self._by_ip = {}
        # allow an API request every <n> seconds
        self._rate_limit = 5
        self._burst_quota = 100
    
    def process_request(self, req, resp):
        now = datetime.datetime.utcnow()
        # dump the rate limit and stats to log file, reset tracker daily
        if (now - self._last_logwrite).seconds > 24 * 3600:
            with open(f"/data/logs/{now.strftime('%Y%m%d_%H%M%S')}.log", "w") as fout:
                for ip_addr, data in self._by_ip.items():
                    self._by_ip[ip_addr]["last_request"] = self._by_ip[ip_addr]["last_request"].strftime("%Y-%m-%d %H:%M:%S")
                    self._by_ip[ip_addr]["last_api_request"] = self._by_ip[ip_addr]["last_api_request"].strftime("%Y-%m-%d %H:%M:%S")
                json.dump(self._by_ip, fout, indent=1)
                self._by_ip = {}
            self._last_logwrite = now
        # log the request and monitor rate limit
        is_api_request = req.path.startswith("/api")
        if req.remote_addr not in self._by_ip:
            self._by_ip[req.remote_addr] = {
                "total_requests": 1,
                "total_lookups": 0,
                "burst_quota_remaining": self._burst_quota,
                "last_request": now,
                "last_api_request": datetime.datetime(1970, 1, 1)
            }
        else:
            self._by_ip[req.remote_addr]["last_request"] = now
            if is_api_request:
                self._by_ip[req.remote_addr]["total_lookups"] += 1
                # in case of rate-limiting, possible return here already
                seconds_since_last_api_request = (now - self._by_ip[req.remote_addr]["last_api_request"]).seconds
                wait_timeout = self._rate_limit - seconds_since_last_api_request
                if self._by_ip[req.remote_addr]["burst_quota_remaining"]:
                    self._by_ip[req.remote_addr]["burst_quota_remaining"] = max(0, self._by_ip[req.remote_addr]["burst_quota_remaining"] - 1)
                elif seconds_since_last_api_request < self._rate_limit:
                    resp.status = 429
                    resp.append_header("Retry-After", wait_timeout)
                    resp.data = json.dumps({"status": "failed", "msg": f"You are exceeding the rate limit (burst quota depleted), try again in {wait_timeout} seconds", "data": []}).encode("utf-8")
                    resp.complete = True
                    return
                self._by_ip[req.remote_addr]["last_api_request"] = now
