# Malpedia FLOSSed

This repository contains the result of the [FLARE FLOSS tool](https://github.com/mandiant/flare-floss) applied to all unpacked and dumped samples in [Malpedia](https://malpedia.caad.fkie.fraunhofer.de/), pre-processed for further use.

We intend to update this collection periodically.

In the last run in November 2023, 8.010 files associated with 1.751 malware families were processed.  
FLOSSing resulted in 35.645.324 raw strings, which were cleaned and deduplicated down to 2.137.276 unique strings.  
Once decompressed, the collection currently sits at about 400 MB.

## Data Format

The string collection is provided as a JSON dictionary (see folder `data`) and has three sections:

* `about`: like a file header, this contains some metadata about this collection.
* `family_to_id`: a mapping of family_ids to the family names, as found in [Malpedia](https://malpedia.caad.fkie.fraunhofer.de/).
* `strings`: the actual data, a dictionary with string as key and value being a dictionary with some additional information.

In short, the data looks like this:
```
{
 "about": {
  "author": "Daniel Plohmann // daniel.plohmann<at>fkie.fraunhofer.de>",
  "date_flossed": "2023-11-28",
  "date_published": "2024-01-11",
  "floss_version": "floss v2.3.0-0-g037fc4b",
  "info": "This collection contains the output of applying the FLARE team's FLOSS tool to all unpacked and dumped malware samples in Malpedia, with additional information in which families the respective string was found, along with its extraction method and encoding. Minor processing has been applied to reduce the number of mistakenly extracted strings from garbled data with no real value to further analysis.",
  "license": "Creative Commons BY-SA 4.0",
  "num_malware_families": 1751,
  "num_processed_strings": 2137276,
  "num_files_flossed": 8010,
  "num_total_strings": 35645324,
  "reference": "https://malpedia.caad.fkie.fraunhofer.de/",
  "source": "https://github.com/malpedia/malpedia-flossed"
 },
 "family_to_id": {
  "elf.anchor_dns": 1121,
  "elf.angryrebel": 1393,
  "elf.babuk": 899,
  ...
  "win.zupdax": 1328,
  "win.zxxz": 1732,
  "win.zyklon": 689
 },
 "strings": {
  ...
  "Mozilla/4.0 (compatible; MSIE 6.0; Win32)": {
   "encodings": [
    "ASCII"
   ],
   "families": [
    76,
    255,
    640,
    863,
    867,
    1488
   ],
   "family_count": 6,
   "methods": [
    "static"
   ],
   "string": "Mozilla/4.0 (compatible; MSIE 6.0; Win32)"
  },
  ...
```

Possible encodings are `ASCII` and `UTF-16LE`, while methods refers to the FLOSS extraction methods `decoded`, `stack`, `static`, and `tight`.

## Web Service / Docker

Instead of parsing the huge JSON file every time, we provide a dockerized web service that enables lookups.  
It uses `falcon` as API backend, WSGI'd through `waitress`, proxied for deployments through `nginx`.  
The layout is based on [awesome-compose](https://github.com/docker/awesome-compose/tree/master) but adapted for usage with falcon and waitress.

Check out the [demo Python script](https://github.com/malpedia/malpedia-flossed/blob/main/demo_webservice.py) for how to interact with the service.

## Plugins

A good use case for these strings is probably in binary analysis tools, so there is an IDA Pro plugin that demonstrates this.

## License

The data is released as under the [CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/), allowing commercial usage.