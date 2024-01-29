import re
import csv
import json
import falcon
import logging
from copy import deepcopy
from io import StringIO


LOGGER = logging.getLogger(__name__)


def jsonify(content, debug_print=False):
    if debug_print:
        print(content)
        print(json.dumps(content).encode("utf-8"))
    return json.dumps(content).encode("utf-8")


class FlossedResource:
    def __init__(self, flossed_data: dict):
        self._flossed_data = flossed_data
        self._family_id_to_family = {value: key for key, value in self._flossed_data["family_to_id"].items()}
        # rate_limiting
        # maybe use RWlock if needed https://gist.github.com/tylerneylon/a7ff6017b7a1f9a506cf75aa23eacfd6


    def on_get(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": {"message": "Welcome to strings.malpedia.io"}})
        LOGGER.info(f"FlossedResource.on_get - success.")


    def on_get_about(self, req, resp):
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": self._flossed_data["about"]})
        LOGGER.info(f"FlossedResource.on_get_info - success.")


    def on_get_api_welcome(self, req, resp):
        resp.status = falcon.HTTP_200
        message =  "Welcome to the API endpoint of strings.malpedia.io!\n"
        message += "You can interact with this service by using GET and POST queries.\n\n"
        message += "GET /api/query/<needle>.\n"
        message += "Gives you the lookup result for a single target string.\n\n"
        message += "POST /api/query/.\n"
        message += "Allows multiple lookups at once and requires you do submit your data as POST body in one CSV encoded line.\n\n"
        resp.data = jsonify({"status": "successful", "data": {"message": message}})
        LOGGER.info(f"FlossedResource.on_get - success.")


    def on_get_query(self, req, resp, needle=None):
        result = {}
        if not re.match("^[ -~\t\n\r]+$", needle):
            resp.status = falcon.HTTP_400
            resp.data = jsonify({"status": "failed", "data": []})
            LOGGER.info(f"StatusResource.on_post_multiquery - failed - invalid characters posted.")
            return
        result = self._flossed_data["strings"].get(needle, {})
        response = {"matched": False, "string": needle}
        if result:
            response = deepcopy(result)
            response["matched"] = True
            response["families"] = [self._family_id_to_family[family_id] for family_id in result["families"]]
        resp.status = falcon.HTTP_200
        resp.data = jsonify({"status": "successful", "data": [response]})
        LOGGER.info(f"FlossedResource.on_get_export_selection - success.")


    def on_post_multiquery(self, req, resp):
        if not req.content_length:
            resp.data = jsonify({"status": "failed","data": {"message": "POST request without body can't be processed."}})
            resp.status = falcon.HTTP_400
            LOGGER.info(f"StatusResource.on_post_multiquery - failed - no POST body.")
            return
        # CSV can only handle string, not bytes
        content = req.stream.read()
        content = content.decode().strip()
        if not re.match("^[ -~\t\n\r]+$", content):
            resp.status = falcon.HTTP_400
            resp.data = jsonify({"status": "failed", "data": []})
            LOGGER.info(f"StatusResource.on_post_multiquery - failed - invalid characters posted.")
            return
        LOGGER.info(f"StatusResource.on_post_multiquery - processing {len(content)} bytes of content.")
        reader = csv.reader(StringIO(content), delimiter=',', quotechar='"')
        for row in reader:
            # we expect only a single line with many fields
            fields = row
            break
        # look up everything and return the result
        if fields:
            LOGGER.info(f"StatusResource.on_post_multiquery - split into {len(fields)} query strings.")
            all_responses = []
            for needle in fields:
                result = self._flossed_data["strings"].get(needle, {})
                response = {"matched": False, "string": needle}
                if result:
                    response = deepcopy(result)
                    response["matched"] = True
                    response["families"] = [self._family_id_to_family[family_id] for family_id in result["families"]]
                all_responses.append(response)
            LOGGER.info(f"StatusResource.on_post_multiquery - success.")
            resp.status = falcon.HTTP_200
            resp.data = jsonify({"status": "successful", "data": all_responses})
        else:
            resp.status = falcon.HTTP_400
            resp.data = jsonify({"status": "failed", "data": []})
            LOGGER.info(f"StatusResource.on_post_multiquery - no fields decoded.")
