import json

from flask import Flask, request, Response, abort
import urllib.request
from urllib.error import HTTPError

import musicbrainzngs

from locale import *
locale = getdefaultlocale()[0]


app = Flask(__name__)
caa_supported_sizes = [250, 500, 1200]

musicbrainzngs.set_useragent("Zune", "4.8", "https://github.com/yoshiask/PyZuneImageCatalogServer")


@app.route(f"/v3.2/<string:locale>/image/<string:mbid>")
def get_image(mbid: str, locale: str):
    # The Cover Art Archive API supports sizes of 250, 500, and 1200
    requested_width = request.args.get("width", default=500, type=int)
    width = min(caa_supported_sizes, key=lambda x: abs(x - requested_width))

    # Request the image from the API and forward it to the Zune software
    try:
        image = urllib.request.urlopen(f"http://coverartarchive.org/release/{mbid}/front-{width}")
        return Response(image.read(), mimetype="image/jpeg")
    except urllib.error.HTTPError as error:
        abort(error.code)


@app.route("/v3.2/<string:locale>/music/artist/<string:mbid>/primaryImage")
def get_artist_primary_image(mbid: str, locale: str):
    try:
        artist = musicbrainzngs.get_artist_by_id(mbid, ["url-rels"])["artist"]
    except musicbrainzngs.ResponseError as error:
        abort(error.cause.code)
        return

    # Get the Deezer artist ID
    deezerUrls = [
        rel["target"]
        for rel in artist["url-relation-list"]
        if rel["type"] == "free streaming" and "deezer" in rel["target"]
    ]
    if len(deezerUrls) == 0:
        abort(404)
    deezerUrl: str = deezerUrls[0]

    # Get Deezer's artist info
    dzResponse = urllib.request.urlopen(deezerUrl.replace("www", "api", 1))
    raw_data = dzResponse.read()
    encoding = dzResponse.info().get_content_charset('utf8')  # JSON default
    dzArtist = json.loads(raw_data.decode(encoding))

    # Request the image from the API and forward it to the Zune software
    image = urllib.request.urlopen(dzArtist["picture_xl"])
    return Response(image.read(), mimetype="image/jpeg")


if __name__ == "__main__":
    app.run(port=80)
