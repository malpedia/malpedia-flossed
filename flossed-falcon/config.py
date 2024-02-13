import os

# config location and project root
THIS_FILE_PATH = str(os.path.abspath(__file__))
PROJECT_ROOT = str(os.path.abspath(os.sep.join([THIS_FILE_PATH, ".."])))
# location for the FLOSS file
FLOSS_FILE = "/data/malpedia_flossed.json"
# location where to write logs
LOG_PATH = "/var/log/flossed-falcon/"
# number of requests that an IP address may use for lookups before RATE_LIMIT kicks in 
BURST_QUOTA = 200
# time in seconds an IP address has to wait with its next lookup once BURST_QUOTA is depleted
RATE_LIMIT = 5
# limit contains queries to at most this number of results
MAX_CONTAINS_RESULTS = 200
# omit logging of individual IP addresses and aggregate data instead
AGGREGATE_ONLY = True
# write logfile to disk every <n> seconds
LOG_RATE = 3600 * 24

# TODO adjust these parts if needed
SERVICE_ADDR = "https://strings.malpedia.io"
API_WELCOME_MESSAGE = f"""Welcome to the API endpoint of {SERVICE_ADDR}!
This service enables lookups against a database of extracted strings from unpacked+dumped malware found in Malpedia.

Apart from this rendered view, you can interact with this service using GET and POST requests.

GET {SERVICE_ADDR}/api/query/<needle>
* Gives you the lookup result for a single target string.
POST {SERVICE_ADDR}/api/query/
* Allows multiple string lookups at once and requires you do submit your data as POST body in one CSV encoded line.

Note that we log your IP address for at most {LOG_RATE} seconds in order to enact rate limiting.
This service is configured to allow a burst of up to {BURST_QUOTA} requests, afterwards you have to wait for {RATE_LIMIT} seconds between requests.

Want to run your instance or get more documentation? 
* https://github.com/malpedia/malpedia-flossed
"""
