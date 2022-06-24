import requests
from requests import RequestException, Response
import urllib.error
import urllib.request
import musicbrainzngs
from musicbrainzngs.musicbrainz import ResponseError
from secrets import *
import json

from typing import Union, Tuple, Dict


DISCOGS_API: str = "https://api.discogs.com"
DC_HEADERS: Dict[str, str] = {
    "User-Agent": USER_AGENT,
    "Authorization": f"Discogs key={DC_API_KEY}, secret={DC_API_SECRET}"
}


def get_artist_from_dcid(dcid: Union[int, str]) -> Union[int, dict]:
    try:
        response: Response = requests.get("https://api.discogs.com/artists/" + str(dcid), headers=DC_HEADERS)
    except RequestException as error:
        return error.response.status_code

    discogs: dict = response.json()
    return discogs


def get_artist_from_mbid(mbid: str) -> Tuple[Union[int, dict], dict]:
    try:
        mb_artist: dict = musicbrainzngs.get_artist_by_id(mbid, includes=["url-rels", "tags"])["artist"]
    except ResponseError as error:
        return error.cause.code

    dc_artist: dict = get_artist_from_mbobj(mb_artist)
    return dc_artist, mb_artist


def get_artist_from_mbobj(mbobj: dict) -> Union[int, dict]:
    if "url-relation-list" not in mbobj:
        return 404
    discogs_rel = [x for x in mbobj["url-relation-list"] if x["type"] == "discogs"]
    if len(discogs_rel) < 1:
        return 404
    discogs_link: str = discogs_rel[0]["target"].replace("www", "api").replace("artist", "artists")
    try:
        req = urllib.request.Request(discogs_link, headers=DC_HEADERS)
        response = urllib.request.urlopen(req)
    except urllib.error.HTTPError as error:
        return error.code

    discogs: dict = json.load(response)
    return discogs
