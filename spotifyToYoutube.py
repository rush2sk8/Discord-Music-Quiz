# coding: utf-8
import json
import os
import sys
import time
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyClientCredentials
from youtubesearchpython import VideosSearch

load_dotenv(dotenv_path=Path('.')/'.env')


def getTracks(playlistURL):
    SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
    SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')
    client_credentials_manager = SpotifyClientCredentials(
        SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
    spotify = spotipy.Spotify(
        client_credentials_manager=client_credentials_manager)

    results = spotify.user_playlist_tracks(user="", playlist_id=playlistURL)
    trackList = []
    for i in results["items"]:
        if (i["track"]["artists"].__len__() == 1):
            trackList.append(i["track"]["name"] + ":" +
                             i["track"]["artists"][0]["name"])
        else:
            nameString = ""
            for index, b in enumerate(i["track"]["artists"]):
                nameString += (b["name"])
                if (i["track"]["artists"].__len__() - 1 != index):
                    nameString += ", "
            trackList.append(i["track"]["name"] + ":" + nameString)

    return trackList


if (__name__ == "__main__"):
    if len(sys.argv) != 3:
        print("Usage: python spotifyToYoutube.py <spotify url> [genre]")
        sys.exit(-1)

    tracks = getTracks(sys.argv[1])
    filename = f'{int(time.time())}'

    songs = []

    for idx, i in enumerate(tracks):
        print(f'{idx}/{len(tracks)}')
        s = i.split(":")
        try:
            song_url = VideosSearch(i, limit=2).result()['result'][0]['link']
        except:
            continue
        if song_url is not None:
            js = {
                "title": s[0],
                "artist": s[1],
                "url": song_url
            }
            songs.append(js)

    if len(sys.argv) == 3:
        genre = sys.argv[2]

    with open(f'songs/{int(time.time())}-_-{genre}.json', 'w') as f:
        f.write(json.dumps(songs, indent=2))

    # exit with number of tracks written
    sys.exit(len(tracks))
