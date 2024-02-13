import re
import csv
import json
import logging
import urllib.parse
from copy import deepcopy
import os
from io import StringIO

import falcon
from jinja2 import Environment, FileSystemLoader
from rapidfuzz.distance import Levenshtein

import config
from RequestLoggerMiddleware import RequestLoggerMiddleware


LOGGER = logging.getLogger(__name__)


def jsonify(content, debug_print=False):
    if debug_print:
        print(content)
        print(json.dumps(content).encode("utf-8"))
    return json.dumps(content).encode("utf-8")


def find_invalid_char(self, content):
    for index, char in enumerate(content):
        if not re.match("^[ -~\t\r\n]$", char):
            print(f"INVALID CHAR '{char}' (0x{ord(char):x}) @ {index}.")


def load_template(name):
    path = os.path.join(config.PROJECT_ROOT, "templates", name)
    with open(os.path.abspath(path), 'r') as fp:
        return  Environment(loader=FileSystemLoader("templates/"), autoescape=True).from_string(fp.read())

class FlossedResource:
    def __init__(self, flossed_data: dict, request_logger: RequestLoggerMiddleware):
        self._flossed_data = flossed_data
        self.request_logger = request_logger
        self._family_id_to_family = {value: key for key, value in self._flossed_data["family_to_id"].items()}
        self._index_template = load_template("index.j2")
        self._query_template = load_template("query.j2")
        self._error_template = load_template("error.j2")

    def _getValidatedNeedle(self, needle):
        validated_needle = None
        decoded_needle = urllib.parse.unquote(needle)
        if re.match("^[ -~\t\r\n]+$", decoded_needle):
            validated_needle = decoded_needle
        return validated_needle
    
    def _getValidatedNeedleFromParams(self, req):
        validated_needle = None
        if "needle" in req.params:
            decoded_needle = urllib.parse.unquote(req.params["needle"])
            if re.match("^[ -~\t\r\n]+$", decoded_needle):
                validated_needle = decoded_needle
        return validated_needle

    def _isContainsQuery(self, req):
        is_contains_query = False
        if "contains" in req.params:
            is_contains_query = req.params["contains"].lower().strip() in ["1", "true"]
        return is_contains_query

    def _getQueryResults(self, needle, is_contains_query=False):
        all_results = []
        num_results = 0
        # always start with exact result
        lookup_result = self._flossed_data["strings"].get(needle, {})
        if lookup_result:
            response = deepcopy(lookup_result)
            response["matched"] = True
            response["distance"] = 0
            response["families"] = sorted([self._family_id_to_family[family_id] for family_id in lookup_result["families"]])
            all_results.append(response)
            num_results += 1
        # optionally fill up with results containing the string
        if is_contains_query:
            for key in self._flossed_data["strings"]:
                if num_results >= config.MAX_CONTAINS_RESULTS:
                    break
                if needle in key and needle != key:
                    lookup_result = self._flossed_data["strings"][key]
                    response = deepcopy(lookup_result)
                    response["matched"] = True
                    response["distance"] = Levenshtein.distance(needle, key, score_cutoff=19)
                    response["families"] = sorted([self._family_id_to_family[family_id] for family_id in lookup_result["families"]])
                    all_results.append(response)
                    num_results += 1
        # for consistency, add empty / negative result if we didn't match anything
        elif len(all_results) == 0:
            all_results.append({"matched": False, "distance": 0, "string": needle})
        return sorted(all_results, key=lambda x: (x["distance"], len(x["string"])))

    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        resp.text = self._index_template.render(quota=self.request_logger.getQuotaStatus(req))
        LOGGER.info(f"FlossedResource.on_get - success.")

    def on_get_health(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": {}})
        LOGGER.info(f"FlossedResource.on_get_health - success.")

    def on_get_about(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": self._flossed_data["about"]})
        LOGGER.info(f"FlossedResource.on_get_about - success.")

    def on_get_stats(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": {"message": self.request_logger.getStats()}})
        LOGGER.info(f"FlossedResource.status - success.")

    def on_get_query(self, req, resp):
        response = {}
        is_contains_query = self._isContainsQuery(req)
        validated_needle = self._getValidatedNeedleFromParams(req)
        if validated_needle is None:
            resp.status = falcon.HTTP_400
            resp.content_type = 'text/html'
            resp.text = self._error_template.render(error_message="invalid characters included")
            LOGGER.info(f"StatusResource.on_get_api_query - failed - invalid characters included.")
            return
        if is_contains_query and  not config.MAX_CONTAINS_RESULTS:
            resp.status = falcon.HTTP_400
            resp.content_type = 'text/html'
            resp.text = self._error_template.render(error_message="tried to do contains, but not allowed by config")
            LOGGER.info(f"StatusResource.on_get_api_query - failed - tried to do contains, but not allowed by config.")
            return
        query_results = self._getQueryResults(validated_needle, is_contains_query=is_contains_query)
        resp.status = falcon.HTTP_200
        response = {"status": "successful", "data": query_results}
        if is_contains_query:
            response["info"] = f"Results are limited to the first {config.MAX_CONTAINS_RESULTS} hits."
        # render
        resp.status = falcon.HTTP_200
        resp.content_type = 'text/html'
        self.request_logger.logLookup(req, 1, 1 if query_results else 0, len(query_results) if query_results else 0)
        resp.text = self._query_template.render(response=response, needle=validated_needle, quota=self.request_logger.getQuotaStatus(req))
        LOGGER.info(f"FlossedResource.on_get_query - success.")

    def on_get_api_welcome(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": {"message": config.API_WELCOME_MESSAGE}})
        LOGGER.info(f"FlossedResource.on_get_api_welcome - success.")

    def on_get_api_query(self, req, resp, needle=None):
        response = {}
        is_contains_query = self._isContainsQuery(req)
        validated_needle = self._getValidatedNeedle(needle)
        if validated_needle is None:
            resp.status = falcon.HTTP_400
            resp.data = jsonify({"status": "failed", "data": [], "message": "invalid characters included."})
            LOGGER.info(f"StatusResource.on_get_api_query - failed - invalid characters included.")
            return
        if is_contains_query and  not config.MAX_CONTAINS_RESULTS:
            resp.data = jsonify({"status": "failed","data": {"message": "This instance does not allow contains queries."}})
            resp.status = falcon.HTTP_400
            LOGGER.info(f"StatusResource.on_get_api_query - failed - tried to do contains, but not allowed by config.")
            return
        query_results = self._getQueryResults(validated_needle, is_contains_query=is_contains_query)
        resp.status = falcon.HTTP_200
        response = {"status": "successful", "data": query_results}
        if is_contains_query:
            response["info"] = f"Results are limited to the first {config.MAX_CONTAINS_RESULTS} hits."
        resp.data = jsonify(response)
        self.request_logger.logLookup(req, 1, 1 if query_results else 0, len(query_results) if query_results else 0)
        LOGGER.info(f"FlossedResource.on_get_api_query - contains query - success.")

    def on_post_api_multiquery(self, req, resp):
        if not req.content_length:
            resp.data = jsonify({"status": "failed","data": {"message": "POST request without body can't be processed."}})
            resp.status = falcon.HTTP_400
            LOGGER.info(f"StatusResource.on_post_api_multiquery - failed - no POST body.")
            return
        # CSV can only handle string, not bytes
        content = req.stream.read()
        content = content.decode().strip()
        if not re.match("^[ -~\t\r\n]+$", content):
            resp.status = falcon.HTTP_400
            resp.data = jsonify({"status": "failed", "data": []})
            LOGGER.info(f"StatusResource.on_post_api_multiquery - failed - invalid characters posted.")
            return
        LOGGER.info(f"StatusResource.on_post_api_multiquery - processing {len(content)} bytes of content.")
        reader = csv.reader(StringIO(content), delimiter=',', quotechar='"')
        for row in reader:
            # we expect only a single line with many fields, so we can break immediately
            fields = row
            break
        # look up everything and return the result
        if fields:
            all_responses = []
            num_successful_lookups = 0
            for needle in fields:
                result = self._flossed_data["strings"].get(needle, {})
                response = {"matched": False, "string": needle}
                if result:
                    num_successful_lookups += 1
                    response = deepcopy(result)
                    response["matched"] = True
                    response["families"] = [self._family_id_to_family[family_id] for family_id in result["families"]]
                else:
                    # TODO here we could at least apply the tagging that we built for malpedia_flosser
                    pass
                all_responses.append(response)
            self.request_logger.logLookup(req, len(fields), num_successful_lookups, num_successful_lookups)
            LOGGER.info(f"StatusResource.on_post_api_multiquery - success (query strings: {len(fields)}, found: {num_successful_lookups}).")
            resp.status = falcon.HTTP_200
            resp.data = jsonify({"status": "successful", "data": all_responses})
        else:
            resp.status = falcon.HTTP_400
            resp.data = jsonify({"status": "failed", "data": []})
            LOGGER.info(f"StatusResource.on_post_api_multiquery - no fields decoded.")
