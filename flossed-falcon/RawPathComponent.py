
class RawPathComponent:

    def process_request(self, req, resp):
        raw_uri = req.env.get('RAW_URI') or req.env.get('REQUEST_URI')

        # NOTE: Reconstruct the percent-encoded path from the raw URI.
        if raw_uri:
            req.path, _, _ = raw_uri.partition('?')