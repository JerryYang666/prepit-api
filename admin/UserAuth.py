# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: UserAuth.py.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 5/21/24 17:23
"""
import uuid
from datetime import datetime, timedelta
from migrations.models import User, RefreshToken, UserWorkspace
from migrations.session import get_db
from utils.token_utils import jwt_generator
import logging


class UserAuth:
    def __init__(self):
        self.db = None

    def user_login(self, signin_source: str, user_info: dict, signin_metadata: dict) -> int or bool:
        """
        login the user when sso authentication is successful
        :param signin_source: which way the user sign in, can be 'google' or 'email' or 'cwru'
        :param user_info: user info from sign in source, must contain 'email', 'first_name', 'last_name'
        can contain 'student_id', 'profile_img_url', 'school_id'
        :param signin_metadata: all metadata from sign in source
        :return: user_id if login successful, False otherwise
        """
        if self.db is None:
            self.db = next(get_db())
        try:
            user = self.db.query(User).filter(
                User.email == user_info['email']).first()
            signin_metadata['signin_source'] = signin_source
            if user:
                # if user already exists, update last login time
                user.last_login = datetime.now()
                user.last_auth_metadata = signin_metadata
            else:
                # if user does not exist, create a new user
                user = User(
                    first_name=user_info['first_name'],
                    last_name=user_info['last_name'],
                    email=user_info['email'],
                    system_admin=False,
                    workspace_role={'prepit': 'student'},
                    school_id=0,
                    student_id=user_info.get('student_id', ''),
                    last_auth_metadata=signin_metadata,
                    last_login=datetime.now(),
                    create_at=datetime.now(),
                    profile_img_url=user_info.get('profile_img_url',
                                                  f"https://api.dicebear.com/9.x/notionists-neutral/png?seed={user_info['first_name']}{user_info['last_name']}")
                )
                self.db.add(user)
            self.db.commit()
            user_id = user.user_id
            # TODO: add user to default workspace 'prepit'
            # # add user to default workspace 'prepit'
            # user_workspace = UserWorkspace(
            #     user_id=user_id,
            #     student_id=user_info.get('student_id', ''),
            #     workspace_id="prepit",
            #     role='student',
            # )
            # self.db.add(user_workspace)
            # self.db.commit()
            return user_id
        except Exception as e:
            logging.error(f"Error during user login: {e}")
            self.db.rollback()
            return False

    def gen_refresh_token(self, user_id: int, signin_metadata: dict) -> str or bool:
        """
        Generate refresh token for user.
        :param user_id: user id
        :param signin_metadata: all metadata from sign in source
        :return: refresh token if successful, False otherwise
        """
        if self.db is None:
            self.db = next(get_db())
        try:
            token = uuid.uuid4()
            token_id = uuid.uuid4()
            expire_at = datetime.now() + timedelta(
                days=30)  # refresh token expires in 30 days
            refresh_token = RefreshToken(
                token_id=token_id,
                user_id=user_id,
                token=token,
                created_at=datetime.now(),
                expire_at=expire_at,
                auth_metadata=signin_metadata,
                issued_access_token_count=0
            )
            self.db.add(refresh_token)
            self.db.commit()
            return str(token)
        except Exception as e:
            logging.error(f"Error during refresh token generation: {e}")
            self.db.rollback()
            return False

    def gen_access_token(self, refresh_token) -> str or bool:
        """
        Generate access token from refresh token.
        :param refresh_token: refresh token
        :return: access token if refresh token is valid, False otherwise
        """
        if self.db is None:
            self.db = next(get_db())
        try:
            # Check if the refresh token is valid
            refresh_token_obj = self.db.query(RefreshToken).filter(
                RefreshToken.token == refresh_token).first()
            if refresh_token_obj and refresh_token_obj.expire_at > datetime.now():
                # refresh token is valid, get user info
                user_id = refresh_token_obj.user_id
                user = self.db.query(User).filter(User.user_id == user_id).first()
                first_name = user.first_name
                last_name = user.last_name
                email = user.email
                system_admin = user.system_admin
                workspace_role = user.workspace_role
                student_id = user.student_id
                profile_img_url = user.profile_img_url
                try:
                    token = jwt_generator(user_id, first_name, last_name, email, system_admin, workspace_role,
                                          student_id,
                                          profile_img_url)
                    refresh_token_obj.issued_access_token_count += 1
                    refresh_token_obj.last_access_token_issued_at = datetime.now()
                    self.db.commit()
                    return token
                except Exception as e:
                    logging.error(f"Error during access token generation: {e}")
                    self.db.rollback()
                    return False
            else:
                return False
        except Exception as e:
            logging.error(f"Error during access token generation: {e}")
            self.db.rollback()
            return False

    def user_logout_all_devices(self, user_id) -> bool:
        """
        Logout user from all devices.
        :param user_id: user id
        :return: True if logout successful, False otherwise
        """
        if self.db is None:
            self.db = next(get_db())
        try:
            tokens = self.db.query(RefreshToken).filter(
                RefreshToken.user_id == user_id,
                RefreshToken.expire_at > datetime.now()).all()
            for token in tokens:
                token.expire_at = datetime.now()
            self.db.commit()
            return True
        except Exception as e:
            logging.error(f"Error during user logout: {e}")
            self.db.rollback()
            return False
