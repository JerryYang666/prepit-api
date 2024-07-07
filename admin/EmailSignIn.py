# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: EmailSignIn.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 7/6/24 16:55
"""
import redis
import os
import random
import uuid
import json
import logging
from fastapi import APIRouter, Depends
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Asm, GroupId, ReplyTo
from dotenv import load_dotenv
from pydantic import BaseModel

from migrations.session import get_db
from migrations.models import User
from utils.response import response
from admin.UserAuth import UserAuth

load_dotenv(dotenv_path="/run/secrets/prepit-secret")
redis_client = redis.Redis(host=os.getenv("REDIS_ADDRESS"), port=6379, protocol=3, decode_responses=True)
sg_client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))

router = APIRouter()
logger = logging.getLogger(__name__)


class GetOtpRequest(BaseModel):
    email: str


class EmailSignInRequest(BaseModel):
    email: str
    otp: str
    event_id: str = "no-user-event-id"
    first_name: str = "Default"
    last_name: str = "User"


OTP_EXPIRATION = 900


@router.post("/get_email_otp")
async def get_email_otp(email_signin_request: GetOtpRequest, db=Depends(get_db)):
    """
    get email otp for a given email.
    :param email_signin_request: email sign in request, must contain email
    :param db: database session
    :return: if a new account is being created, return True, otherwise return False. Second return value is the email event id
    """
    email = email_signin_request.email
    # check if the email is already in redis, if so, get the info and do not send email again
    sent_check = redis_client.get(email)
    if sent_check:
        sent_info = json.loads(str(sent_check))
        return response(True, data={"new_account": sent_info["new_account"], "event_id": sent_info["event_id"],
                                    "duplicate_request": True})
    try:
        # check if the email is already in the database
        user = db.query(User).filter(User.email == email).first()
        new_account = True
        user_first_name = "Future Partner at Top Tier Consulting Firm"
        if user:
            new_account = False
            user_first_name = user.first_name
        # generate email otp, 6 digits number, as a string
        email_otp = str(random.randint(100000, 999999))
        # generate a uuid event id
        event_id = str(uuid.uuid4())
        # save the email otp to redis, email as key, email otp and event id as value, valid for 15 minutes
        info = {
            "email_otp": email_otp,
            "event_id": event_id,
            "new_account": new_account
        }
        cache = redis_client.set(email, json.dumps(info), ex=OTP_EXPIRATION)
    except Exception as e:
        print(f"Error during get email otp: {e}")
        return response(False, status_code=500, message="Error during get email otp")
    try:
        # send the email otp to the user
        message = Mail(
            from_email='prepit-service@coursey.ai',
            to_emails=email,
        )
        message.template_id = 'd-aff816bd2bb340b0b142c748730b8ac7'
        message.dynamic_template_data = {
            'name': user_first_name,
            'otp': email_otp,
            'event_id': event_id
        }
        message.asm = Asm(GroupId(28734))
        message.reply_to = ReplyTo('service@coursey.ai', 'Prepit Customer Service')
        # send the email
        email_send_status = sg_client.send(message)
        if email_send_status.status_code != 202:
            return response(False, status_code=500, message="Error during send email otp")
        else:
            return response(True, data={"new_account": new_account, "event_id": event_id, "duplicate_request": False})
    except Exception as e:
        print(f"Error during send email otp: {e}")
        return response(False, status_code=500, message="Error during send email otp")


@router.post("/email_signin")
async def email_signin(email_signin_request: EmailSignInRequest):
    """
    sign in user using email and otp
    :param email_signin_request: email sign in request, must contain email and otp
    :return: user id if successful, False otherwise
    """
    email = email_signin_request.email
    otp = email_signin_request.otp
    user_event_id = email_signin_request.event_id
    first_name = email_signin_request.first_name
    last_name = email_signin_request.last_name
    # check if the email and otp are in redis
    sent_check = redis_client.get(email)
    if not sent_check:
        return response(False, status_code=401, message="Email OTP expired or not found, please try again")
    sent_info = json.loads(str(sent_check))
    if sent_info["email_otp"] != otp:
        return response(False, status_code=401, message="Email OTP does not match")
    ttl = redis_client.ttl(email)
    email_send_time = OTP_EXPIRATION - ttl
    try:
        user_auth = UserAuth()
        user_info_dict = {
            "email": email,
            "first_name": first_name,
            "last_name": last_name
        }
        signin_metadata_dict = {
            "new_account": sent_info["new_account"],
            "redis_event_id": sent_info["event_id"],
            "user_event_id": user_event_id,
            "email_send_time": email_send_time
        }
        login_result = user_auth.user_login("email", user_info_dict, signin_metadata_dict)
        if login_result is False:
            return response(False, status_code=401, message="Error during email sign in")
        else:
            dele = redis_client.delete(email)
            refresh_token = user_auth.gen_refresh_token(login_result, signin_metadata_dict)
            access_token = user_auth.gen_access_token(refresh_token)
            return response(True, data={"refresh_token": refresh_token, "access_token": access_token})
    except Exception as e:
        print(f"Error during email sign in: {e}")
        return response(False, status_code=500, message="Error during email sign in")
