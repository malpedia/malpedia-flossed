
# location for the FLOSS file
FLOSS_FILE = "/data/malpedia_flossed.json"
# location where to write logs
LOG_PATH = "/data/logs/"
# number of requests that an IP address may use for lookups before RATE_LIMIT kicks in 
BURST_QUOTA = 100
# time in seconds an IP address has to wait with its next lookup once BURST_QUOTA is depleted
RATE_LIMIT = 5
# omit logging of individual IP addresses and aggregate data instead
AGGREGATE_LOG = True
# write logfile to disk every <n> seconds
LOG_RATE = 3600 * 24

# TODO adjust these parts if needed
SERVICE_ADDR = "strings.malpedia.io"
API_WELCOME_MESSAGE = f"""
Welcome to the API endpoint of {SERVICE_ADDR}!
It enables lookups against a database of extracted strings from malware.

You can interact with this service using GET and POST requests.

GET {SERVICE_ADDR}/api/query/<needle>
* Gives you the lookup result for a single target string.
POST {SERVICE_ADDR}/api/query/
* Allows multiple string lookups at once and requires you do submit your data as POST body in one CSV encoded line.

Want to run your instance or more documentation? 
* https://github.com/malpedia/malpedia-flossed
"""