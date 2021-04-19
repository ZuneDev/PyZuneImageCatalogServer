from flask import Flask, request, Response
import urllib.request

from locale import *
locale = getdefaultlocale()[0]


app = Flask(__name__)
caa_supported_sizes = [250, 500, 1200]


@app.route(f"/v3.2/<string:locale>/image/<string:mbid>")
def get_image(mbid: str, locale: str):
    # The Cover Art Archive API supports sizes of 250, 500, and 1200
    requested_width = request.args.get("width", default=500, type=int)
    width = min(caa_supported_sizes, key=lambda x: abs(x - requested_width))

    # Request the image from the API and forward it to the Zune software
    image = urllib.request.urlopen(f"http://coverartarchive.org/release/{mbid}/front-{width}")
    return Response(image.read(), mimetype="image/jpeg")
