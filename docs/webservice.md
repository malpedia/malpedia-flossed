# Web Service

In order to accelerate lookups, we created a simple dockerized web service.  
It uses `falcon` as API backend, WSGI'd through `waitress`, proxied for deployments through `nginx`.  
The layout is based on [awesome-compose](https://github.com/docker/awesome-compose/tree/master) but updated and adapted for usage with falcon and waitress.

The service supports single lookups as GET requests and multi-lookups as POST requests:
```
$ curl https://strings.malpedia.io/api/query/FIXME  
{"status": "successful", "data": [{"encodings": ["ASCII"], "families": ["win.kins", "win.vmzeus", "win.zeus_sphinx", "win.citadel", "win.ice_ix", "win.murofet", "win.zeus"], "family_count": 7, "methods": ["static"], "string": "FIXME", "tags": [], "matched": true}, {"matched": false, "string": "NOT_FLOSSED"}]}

$ curl -X POST https://strings.malpedia.io/api/query/ --data '"FIXME","NOT_IN_THE_DATABASE"'
{"status": "successful", "data": [{"encodings": ["ASCII"], "families": ["win.kins", "win.vmzeus", "win.zeus_sphinx", "win.citadel", "win.ice_ix", "win.murofet", "win.zeus"], "family_count": 7, "methods": ["static"], "string": "FIXME", "tags": [], "matched": true}, {"matched": false, "string": "NOT_IN_THE_DATABASE"}]}
```
Check out the [demo Python script](https://github.com/malpedia/malpedia-flossed/blob/main/demo_webservice.py) for how to interact with the service.

Additionally, there is also an endpoint for stats:
```
$ curl https://strings.malpedia.io/stats                                                                    
{"status": "successful", "data": {"message": {"total_requests": 1325, "total_lookups": 23, "total_lookup_strings": 4865, "total_resolved_strings": 4361, "num_ip_addresses": 12, "data_since": "2024-01-31 13:57:18"}}}
```

We host a public instance of this service at [strings.malpedia.io](https://strings.malpedia.io).