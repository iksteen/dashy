import json
import os
import time
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID", "")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
    redirect_uri = os.environ.get("SPOTIFY_REDIRECT_URI", "")

    if not client_id:
        client_id = input("Spotify application client ID: ")
    if not client_secret:
        client_secret = input("Spotify application client secret: ")
    if not redirect_uri:
        redirect_uri = input("Spotify application redirect URI: ")

    scope = "user-read-currently-playing"

    query_args = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
    }
    auth_url = "https://accounts.spotify.com/authorize?" + urlencode(query_args)
    print(f"Please visit: {auth_url}")  # noqa: T201

    response = input("Please enter the URL you were redirected to: ")
    parsed_response = urlparse(response)
    response_args = parse_qs(parsed_response.query)
    code = response_args["code"][0]

    form_data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
    }

    r = requests.post(
        "https://accounts.spotify.com/api/token",
        auth=requests.auth.HTTPBasicAuth(client_id, client_secret),
        data=form_data,
        timeout=10,
    )
    credentials = r.json()
    credentials["expires"] = int(time.time()) + credentials.pop("expires_in")
    credentials["client_id"] = client_id
    credentials["client_secret"] = client_secret
    with Path("spotify-credentials.json").open("w") as f:
        json.dump(credentials, f)
