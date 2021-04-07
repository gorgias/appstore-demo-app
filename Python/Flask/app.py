"""Demo app example integrating with Gorgias."""


import os
import urllib.parse as urlparse

import requests
from authlib.integrations.flask_client import FlaskRemoteApp, OAuth, OAuthError
from authlib.integrations.requests_client import OAuth2Session
from flask import Flask, abort, current_app, jsonify, redirect, request, session, url_for


# Client (app) settings: take these details from the Developer Portal after publishing the app.
APP_NAME = "Python Flask - Cosmin Local"
CLIENT_ID = os.getenv("CLIENT_ID", "606d8961c9809e208baf1835")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "python-flask-cosmin-local")

# Other OAuth2 settings.
GORGIAS_DOMAIN = os.getenv("GORGIAS_DOMAIN", "gorgias.com")
GORGIAS_DEV_BASE_URL = os.getenv("GORGIAS_DEV_BASE_URL", f"https://acme-cmin.ngrok.io")
SCOPE = "openid email profile offline write:all"

app = Flask(__name__)
app.secret_key = "flask-app-secret"
oauth = OAuth(app)


get_gorgias_base_url = lambda account: (
    f"https://{account}.{GORGIAS_DOMAIN}" if not current_app.debug else GORGIAS_DEV_BASE_URL
)
get_oauth2_base_url = lambda account: get_gorgias_base_url(account) + "/oauth"
get_api_base_url = lambda account: get_gorgias_base_url(account) + "/api"


def register_client(name: str, *, account: str, client_id: str, client_secret: str) -> FlaskRemoteApp:
    oauth2_base_url = get_oauth2_base_url(account)
    authorize_url = f"{oauth2_base_url}/authorize"
    access_token_url = f"{oauth2_base_url}/token"
    # NOTE: Don't worry, the registration is cached already by `oauth`.
    client = oauth.register(
        name,
        overwrite=True,
        client_id=client_id,
        client_secret=client_secret,
        api_base_url=oauth2_base_url,
        authorize_url=authorize_url,
        access_token_url=access_token_url,
        client_kwargs={
            "scope": SCOPE,
        },
    )
    return client


def get_access_token(refresh_token: str, *, account: str, client_id: str, client_secret: str) -> str:
    """Obtains a new access token based on the `refresh_token`."""
    session = OAuth2Session(client_id=client_id, client_secret=client_secret)
    oauth2_base_url = get_oauth2_base_url(account)
    access_token_url = f"{oauth2_base_url}/token"
    resp = session.refresh_token(access_token_url, refresh_token=refresh_token)
    current_app.logger.info("Access token refreshed for client %r.", client_id)
    return resp["access_token"]


@app.route("/oauth/login")
def oauth_login():
    account = request.args.get("account")
    if not account:
        abort(400, "missing 'account' query parameter (where the installation was triggered)")

    auth_client = register_client(APP_NAME, account=account, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    redirect_uri = urlparse.urljoin(request.base_url, url_for("oauth_callback", account=account))
    return auth_client.authorize_redirect(redirect_uri=redirect_uri, scope=SCOPE)


@app.route("/oauth/callback")
def oauth_callback():
    account = request.args.get("account")
    if not account:
        abort(400, "missing 'account' query parameter (where the installation was triggered)")

    auth_client = register_client(APP_NAME, account=account, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

    # Handles response from the `/oauth/token` endpoint and retrieves the tokens.
    try:
        token = auth_client.authorize_access_token()
    except OAuthError as exc:
        current_app.logger.exception(exc)
        abort(403, exc)

    # This isn't safe, the refresh token should never leave the back-end except when is sent to the Auth server.
    #  (cache it in a database instead)
    session["refresh_token"] = token["refresh_token"]
    # Be careful, the access token is a pretty long JWT which might exceed the cookie capacity.
    session["access_token"] = token["access_token"]
    next_url = url_for("list_tickets", account=account)
    return redirect(next_url)


@app.route("/tickets")
def list_tickets():
    account = request.args.get("account")
    if not account:
        abort(400, "missing 'account' query parameter (where the installation was triggered)")

    api_url = get_api_base_url(account)
    access_token = session["access_token"] = request.args.get("token", session.get("access_token", ""))  # testing purposes
    while True:
        try:
            resp = requests.get(f"{api_url}/tickets", headers={"Authorization": f"Bearer {access_token}"})
            resp.raise_for_status()
        except requests.HTTPError as exc:
            current_app.logger.exception(exc)
            # Usually token expired, let's get a new one using the currently available refresh token. If still doesn't
            #  work, go to `/oauth/login` for restarting the flow. (or simply reinstall the app in Gorgias)
            refresh_token = session.get("refresh_token", "N/A")
            try:
                access_token = session["access_token"] = get_access_token(
                    refresh_token, account=account, client_id=CLIENT_ID, client_secret=CLIENT_SECRET
                )
            except OAuthError:
                abort(401, "can't refresh token, most probably the app isn't installed")
        else:
            return jsonify(resp.json())
