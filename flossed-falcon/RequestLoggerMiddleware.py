import os
import json
import logging
import datetime

import config


LOGGER = logging.getLogger(__name__)


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

    def _get_remote_ip(self, req):
        # take outmost IP addr in case we are behind a proxied setup
        remote_ip_addr = req.access_route[0]
        return remote_ip_addr

    def _writeLogFile(self, log_filepath, now):
        with open(log_filepath, "w") as fout:
            log_output = {
                "aggregated": self.getStats(),
                "details": self._by_ip
            }
            # aggregate data to omit PII beyond our rate limiting
            for ip_addr, data in self._by_ip.items():
                # stringify timestamps
                self._by_ip[ip_addr]["last_request"] = self._by_ip[ip_addr]["last_request"].strftime("%Y-%m-%d %H:%M:%S")
                self._by_ip[ip_addr]["last_api_request"] = self._by_ip[ip_addr]["last_api_request"].strftime("%Y-%m-%d %H:%M:%S")
            if config.AGGREGATE_ONLY:
                log_output.pop("details")
            json.dump(log_output, fout, indent=1)
            self._last_logwrite = now

    def _persistLog(self, now):
        self._ensure_path(config.LOG_PATH)
        log_filepath = f"{config.LOG_PATH}" + os.sep + f"{now.strftime('%Y%m%d_%H%M%S')}_log.json"
        try:
            self._writeLogFile(log_filepath, now)
        except:
            LOGGER.error(f"Could not write logfile to {log_filepath}, logging into local directly instead.")
            local_log_filepath = config.PROJECT_ROOT + os.sep + f"{now.strftime('%Y%m%d_%H%M%S')}_log.json"
            self._writeLogFile(local_log_filepath, now)


    def getStats(self):
        aggregated = {
            "total_requests": 0,
            "total_lookups": 0,
            "total_lookup_strings": 0,
            "total_resolved_strings": 0,
            "total_returned_strings": 0,
            "num_ip_addresses": len(self._by_ip),
            "data_since": self._last_logwrite.strftime("%Y-%m-%d %H:%M:%S")
        }
        for ip_addr, data in self._by_ip.items():
            # aggregates
            aggregated["total_requests"] += data["total_requests"]
            aggregated["total_lookups"] += data["total_lookups"]
            aggregated["total_lookup_strings"] += data["total_lookup_strings"]
            aggregated["total_resolved_strings"] += data["total_resolved_strings"]
            aggregated["total_returned_strings"] += data["total_returned_strings"]
        return aggregated
    
    def getQuotaStatus(self, req):
        remote_ip_addr = self._get_remote_ip(req)
        quota_status = {
            "remaining_burst_quota": config.BURST_QUOTA,
            "wait_timeout": 0
        }
        if remote_ip_addr in self._by_ip:
            quota_status["remaining_burst_quota"] = self._by_ip[remote_ip_addr]["burst_quota_remaining"]
            if self._by_ip[remote_ip_addr]["burst_quota_remaining"] == 0:
                now = datetime.datetime.utcnow()
                seconds_since_last_api_request = (now - self._by_ip[remote_ip_addr]["last_api_request"]).seconds
                wait_timeout = config.RATE_LIMIT - seconds_since_last_api_request
                quota_status["wait_timeout"] = max(0, wait_timeout)
        return quota_status

    def process_request(self, req, resp):
        now = datetime.datetime.utcnow()
        remote_ip_addr = self._get_remote_ip(req)
        # dump the rate limit and stats to log file, reset tracker daily
        if (now - self._last_logwrite).total_seconds() > config.LOG_RATE:
            self._persistLog(now)
            self._by_ip = {}
        # log the request and monitor rate limit
        is_api_request = req.path.startswith("/api") or req.path.startswith("/query")
        if remote_ip_addr not in self._by_ip:
            self._by_ip[remote_ip_addr] = {
                "total_requests": 0,
                "total_lookups": 0,
                "total_lookup_strings": 0,
                "total_resolved_strings": 0,
                "total_returned_strings": 0,
                "burst_quota_remaining": config.BURST_QUOTA,
                "last_request": now,
                "last_api_request": datetime.datetime(1970, 1, 1)
            }
        self._by_ip[remote_ip_addr]["total_requests"] += 1
        self._by_ip[remote_ip_addr]["last_request"] = now
        if is_api_request:
            # in case of rate-limiting, possible return here already
            seconds_since_last_api_request = (now - self._by_ip[remote_ip_addr]["last_api_request"]).seconds
            wait_timeout = config.RATE_LIMIT - seconds_since_last_api_request
            if self._by_ip[remote_ip_addr]["burst_quota_remaining"]:
                self._by_ip[remote_ip_addr]["burst_quota_remaining"] = max(0, self._by_ip[remote_ip_addr]["burst_quota_remaining"] - 1)
            elif seconds_since_last_api_request < config.RATE_LIMIT:
                resp.status = 429
                resp.append_header("Retry-After", wait_timeout)
                resp.data = json.dumps({"status": "failed", "msg": f"You are exceeding the rate limit (burst quota depleted), try again in {wait_timeout} seconds", "data": []}).encode("utf-8")
                resp.complete = True
                return
            self._by_ip[remote_ip_addr]["total_lookups"] += 1
            self._by_ip[remote_ip_addr]["last_api_request"] = now

    def logLookup(self, req, num_lookup_strings, num_resolved_strings, num_returned_strings):
        remote_ip_addr = self._get_remote_ip(req)
        self._by_ip[remote_ip_addr]["total_lookup_strings"] += num_lookup_strings
        self._by_ip[remote_ip_addr]["total_resolved_strings"] += num_resolved_strings
        self._by_ip[remote_ip_addr]["total_returned_strings"] += num_returned_strings
