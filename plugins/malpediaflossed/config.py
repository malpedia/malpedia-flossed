import os

### Define location for the FLOSSed file
THIS_FILE_PATH = str(os.path.abspath(__file__))
PROJECT_ROOT = str(os.path.abspath(os.sep.join([THIS_FILE_PATH, "..", "..", "..", "..", ".."])))
# If you don't install it as a plugin (IDA, Ghidra), this relative path below points to the data folder of the repo
# otherwise specify the file yourself or use the lookup service as defined below
FLOSSED_FILEPATH = os.sep.join([PROJECT_ROOT, "data", "malpedia_flossed.json"])
### If you set FLOSSED_SERVICE, this will be take precedence over the local file
# You can e.g. use our hosted
# FLOSSED_SERVICE = "https://strings.malpedia.io/api/query"
# ... or if you have your own local setup
# FLOSSED_SERVICE = "http://127.0.0.1:8000/api/query"
# leaving this empty means local mode, i.e. loading the JSON specified above instead
FLOSSED_SERVICE = "https://strings.malpedia.io/api/query"
### Run analysis immediately when plugin is started.
# Has to be False in BinaryNinja as during start-up the respective View has not been initialized yet
AUTO_ANALYZE = False

