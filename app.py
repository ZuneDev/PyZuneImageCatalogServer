import json

from typing import Dict, List
from flask import Flask, request, Response, abort, send_file
from io import BytesIO
import requests
from requests import RequestException

import musicbrainzngs
import api.discogs as discogs
from secrets import USER_AGENT

from locale import *


locale = getdefaultlocale()[0]


app = Flask(__name__)
caa_supported_sizes = [250, 500, 1200]
dc_artist_cache: Dict[str, dict] = {}

musicbrainzngs.set_useragent("Zune", "4.8", "https://github.com/yoshiask/PyZuneImageCatalogServer")
DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": USER_AGENT
}


import re
@app.after_request
def allow_zunestk_cors(response):
    r = request.origin
    if r is None:
        return response
    if re.match(r"https?://(127\.0\.0\.(?:\d*)|localhost(?:\:\d+)?|(?:\w*\.)*zunes\.tk)", r):
        response.headers.add('Access-Control-Allow-Origin', r)
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Headers', 'Cache-Control')
        response.headers.add('Access-Control-Allow-Headers', 'X-Requested-With')
        response.headers.add('Access-Control-Allow-Headers', 'Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS, PUT, DELETE')
    return response


@app.route("/")
def default():
    return Response("Welcome to the Social", mimetype="text/plain")


@app.route(f"/v3.2/<string:locale>/image/<string:mbid>")
def get_image(mbid: str, locale: str):
    image_url: str = ""
    if mbid.endswith('0' * 12):
        dcid: int = int(mbid[:8], 16)
        img_idx: int = int(mbid[9:13], 16)

        # Get or update cached artist
        dc_artist: dict = dc_artist_cache.get(dcid)
        if dc_artist is None:
            # Artist not in cache
            dc_artist = discogs.get_artist_from_dcid(dcid)
            dc_artist_cache[dcid] = dc_artist

        # Get URL for requested image
        image_url = dc_artist["images"][img_idx]["uri"]
    else:
        # The Cover Art Archive API supports sizes of 250, 500, and 1200
        requested_width = request.args.get("width", default=500, type=int)
        width = min(caa_supported_sizes, key=lambda x: abs(x - requested_width))
        image_url = f"http://coverartarchive.org/release/{mbid}/front-{width}"

    # Request the image from the API and forward it to the Zune software
    try:
        image = requests.get(image_url, headers=DEFAULT_HEADERS, stream=True)
        return Response(BytesIO(image.content), content_type="image/jpeg")
    except RequestException as error:
        return send_file('noart.png', attachment_filename='noart.png')


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=80)
