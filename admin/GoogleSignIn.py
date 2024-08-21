# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: GoogleSignIn.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 6/8/24 20:47
"""
from google.oauth2 import id_token
from google.auth.transport import requests
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv
import os
import redis
from admin.UserAuth import UserAuth
from fastapi.responses import RedirectResponse
import logging

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_SIGNIN_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_SIGNIN_CLIENT_SECRET")
GOOGLE_PROJECT_ID = os.getenv("GOOGLE_SIGNIN_PROJECT_ID")
CURRENT_ENV = os.getenv("REDIS_ADDRESS")
if CURRENT_ENV == "redis-dev-server":
    GOOGLE_REDIRECT_URI = "https://api.prepit-ai.com/v1/dev/admin/google_signin_callback"
else:
    GOOGLE_REDIRECT_URI = "https://api.prepit-ai.com/v1/prod/admin/google_signin_callback"
redis_client = redis.Redis(host=os.getenv("REDIS_ADDRESS"), port=6379, protocol=3, decode_responses=True)


def get_flow():
    """
    get google signin flow
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": GOOGLE_CLIENT_ID,
                "project_id": GOOGLE_PROJECT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "redirect_uris": [GOOGLE_REDIRECT_URI],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        },
        scopes=["https://www.googleapis.com/auth/userinfo.email", "https://www.googleapis.com/auth/userinfo.profile", "openid"],
    )
    flow.redirect_uri = GOOGLE_REDIRECT_URI

    return flow


def get_signin_url(current_url):
    """
    get google signin url
    :param current_url: current url to redirect back to
    """
    flow = get_flow()

    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    # Store the state so the callback can verify the auth server response.
    redis_client.set(state, current_url)

    return authorization_url


def signin_callback(code, state, error):
    """
    google signin callback
    use code to get token
    use token to get user info
    log user in
    """
    # Validate the state to protect against cross-site request forgery.
    redirect_url = redis_client.get(state)
    if redirect_url is None:
        return False
    redis_client.delete(state)
    if error is not None:
        return RedirectResponse(url=f"{redirect_url}?refresh=error&access=error")
    try:
        flow = get_flow()
        token = flow.fetch_token(code=code)
        id_token_info = id_token.verify_oauth2_token(token["id_token"], requests.Request(), GOOGLE_CLIENT_ID)
        user_auth = UserAuth()
        processed_user_info = {
            'email': id_token_info['email'],
            'first_name': id_token_info['given_name'],
            'last_name': id_token_info['family_name'],
            'profile_img_url': id_token_info['picture'] if 'picture' in id_token_info
            else f"https://api.dicebear.com/9.x/notionists-neutral/png?seed={id_token_info['given_name']}{id_token_info['family_name']}"
        }
        user_id = user_auth.user_login('google', processed_user_info, id_token_info)
        if user_id:
            refresh_token = user_auth.gen_refresh_token(user_id, id_token_info)
            access_token = user_auth.gen_access_token(refresh_token)
            return RedirectResponse(
                url=f"{redirect_url}?refresh={refresh_token}&access={access_token}")
        else:
            return RedirectResponse(url=f"{redirect_url}?refresh=error&access=error")
    except Exception as e:
        logging.error(f"Error during google signin callback: {e}")
        return RedirectResponse(url=f"{redirect_url}?refresh=error&access=error")
