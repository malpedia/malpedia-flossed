import json
import logging

import falcon

import config
from FlossedResource import FlossedResource
from RequestLoggerMiddleware import RequestLoggerMiddleware


# Only do basicConfig if no handlers have been configured
if len(logging._handlerList) == 0:
    logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
logging.basicConfig(level=logging.INFO, format="%(asctime)-15s %(message)s")
LOGGER = logging.getLogger(__name__)


def load_flossed_data():
    print("Loading FLOSSed data...")
    flossed_data = {}
    if not flossed_data:
        with open(config.FLOSS_FILE, "r") as fin:
            raw = fin.read()
            flossed_data = json.loads(raw)
        print(f"Finished loading FLOSSed data with length: {len(raw)}")
    print(f"Finished loading FLOSSed data with fields: {len(flossed_data)}")
    return flossed_data


def get_app():
    flossed_data = load_flossed_data()
    request_logger = RequestLoggerMiddleware()
    flossed_resource = FlossedResource(flossed_data, request_logger)
    print("Building app...")

    _app = falcon.App(middleware=[request_logger])
    _app.req_options.strip_url_path_trailing_slash = True
    _app.add_route("/", flossed_resource)
    _app.add_route("/about", flossed_resource, suffix="about")
    _app.add_route("/api", flossed_resource, suffix="api_welcome")
    _app.add_route("/api/query", flossed_resource, suffix="multiquery")
    _app.add_route("/api/query/{needle}", flossed_resource, suffix="query")

    return _app
