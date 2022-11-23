import json

import requests


class ResultsReturn:
    def __init__(self, post_signed_url:str = "https://it_randd.cog.sanger.ac.uk/post_signed_url.json"):
        self.post_signed_url = post_signed_url

    def post_results(self, raw_result_filename : str, jsondata : str, verbose:bool=False):
        # Fetch signed post URL from s3 cog
        r = requests.get(url=self.post_signed_url)
        if not r.ok:
            if verbose:
                print(f'Fetch of POST URL for data return failed. Error {r.status_code}')
            return
        myurl_raw = json.loads(r.text)

        # POST results JSON to fetched URL
        files = {'file': (raw_result_filename, jsondata.encode('utf-8'))}
        resp = requests.post(myurl_raw['url'], data=myurl_raw['fields'], files=files)
        if not resp.ok:
            if verbose:
                print(f'Error {resp.status_code} uploading results: {resp.text}')
        else:
            if verbose:
                print('Results returned successfully.')
