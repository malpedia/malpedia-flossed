import io
import csv
import json
import requests


def csv_encode(list_of_strings):
    """ when querying in bulk, this is the expected encoding (CSV) """
    output = io.StringIO()
    writer = csv.writer(output, quotechar='"', delimiter=",", quoting=csv.QUOTE_NONNUMERIC)
    writer.writerow(list_of_strings)
    return output.getvalue()

# demo for single string lookup
response = requests.get("http://127.0.0.1:8000/api/query/SAFECOOKIE")
print(json.dumps(response.json(), indent=1))

# demo for bulk string lookup
response = requests.post("http://127.0.0.1:8000/api/query", data=csv_encode(["SANDBOX", "STRING_NOT_IN_FLOSSED_DATA"]))
print(json.dumps(response.json(), indent=1))
