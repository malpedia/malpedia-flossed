import os
import json
import datetime

import parameters

class RequestLoggerMiddleware:
    # maybe use RWlock if needed https://gist.github.com/tylerneylon/a7ff6017b7a1f9a506cf75aa23eacfd6

    def __init__(self) -> None:
        self._last_logwrite = datetime.datetime.utcnow()
        self._by_ip = {}

    def _ensure_path(self, path):
        try:
            os.makedirs(path)
        except:
            pass

    def process_request(self, req, resp):
        now = datetime.datetime.utcnow()
        # dump the rate limit and stats to log file, reset tracker daily
        if (now - self._last_logwrite).seconds > parameters.LOG_RATE:
            self._ensure_path(parameters.LOG_PATH)
            with open(f"{parameters.LOG_PATH}" + os.sep + f"{now.strftime('%Y%m%d_%H%M%S')}.log", "w") as fout:
                log_output = self._by_ip
                # aggregate data to omit PII beyond our rate limiting
                aggregated_data = {
                    "total_requests": 0,
                    "total_lookups": 0,
                    "total_lookup_strings": 0,
                    "total_resolved_strings": 0,
                    "num_ip_addresses": len(self._by_ip)
                }
                for ip_addr, data in self._by_ip.items():
                    # stringify timestamps
                    self._by_ip[ip_addr]["last_request"] = self._by_ip[ip_addr]["last_request"].strftime("%Y-%m-%d %H:%M:%S")
                    self._by_ip[ip_addr]["last_api_request"] = self._by_ip[ip_addr]["last_api_request"].strftime("%Y-%m-%d %H:%M:%S")
                    # aggregates
                    aggregated_data["total_requests"] += data["total_requests"]
                    aggregated_data["total_lookups"] += data["total_lookups"]
                    aggregated_data["total_lookup_strings"] += data["total_lookup_strings"]
                    aggregated_data["total_resolved_strings"] += data["total_resolved_strings"]
                if parameters.AGGREGATE_LOG:
                    log_output = aggregated_data
                json.dump(log_output, fout, indent=1)
                self._by_ip = {}
            self._last_logwrite = now
        # log the request and monitor rate limit
        is_api_request = req.path.startswith("/api")
        if req.remote_addr not in self._by_ip:
            self._by_ip[req.remote_addr] = {
                "total_requests": 1,
                "total_lookups": 0,
                "total_lookup_strings": 0,
                "total_resolved_strings": 0,
                "burst_quota_remaining": parameters.BURST_QUOTA,
                "last_request": now,
                "last_api_request": datetime.datetime(1970, 1, 1)
            }
        else:
            self._by_ip[req.remote_addr]["total_requests"] += 1
            self._by_ip[req.remote_addr]["last_request"] = now
            if is_api_request:
                self._by_ip[req.remote_addr]["total_lookups"] += 1
                # in case of rate-limiting, possible return here already
                seconds_since_last_api_request = (now - self._by_ip[req.remote_addr]["last_api_request"]).seconds
                wait_timeout = parameters.RATE_LIMIT - seconds_since_last_api_request
                if self._by_ip[req.remote_addr]["burst_quota_remaining"]:
                    self._by_ip[req.remote_addr]["burst_quota_remaining"] = max(0, self._by_ip[req.remote_addr]["burst_quota_remaining"] - 1)
                elif seconds_since_last_api_request < parameters.RATE_LIMIT:
                    resp.status = 429
                    resp.append_header("Retry-After", wait_timeout)
                    resp.data = json.dumps({"status": "failed", "msg": f"You are exceeding the rate limit (burst quota depleted), try again in {wait_timeout} seconds", "data": []}).encode("utf-8")
                    resp.complete = True
                    return
                self._by_ip[req.remote_addr]["last_api_request"] = now

    def logLookup(self, req, num_lookup_strings, num_resolved_strings):
        self._by_ip[req.remote_addr]["total_lookup_strings"] += num_lookup_strings
        self._by_ip[req.remote_addr]["total_resolved_strings"] += num_resolved_strings
