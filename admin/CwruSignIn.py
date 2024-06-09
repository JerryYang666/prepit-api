# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: CwruSignIn.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 5/6/24 10:23
"""
import requests
import xml.etree.ElementTree as ET
from fastapi.responses import RedirectResponse
from admin.UserAuth import UserAuth


class AuthSSO:
    def __init__(self, ticket, came_from):
        self.student_id = None
        self.ticket = ticket
        self.came_from = came_from

    def get_user_info(self):
        """
        get user info from ticket and return user login token
        :return: user login token
        """
        url = "https://login.case.edu/cas/serviceValidate"
        params = {
            "ticket": self.ticket,
            "service": f"https://api.prepit-ai.com/v1/dev/admin/cwru_sso_callback?came_from={self.came_from}",  # TODO: change to prod
        }
        response = requests.get(url, params=params)
        root = ET.fromstring(response.text)
        # get child node
        child = root[0]
        if "authenticationSuccess" in child.tag:
            # redirect to the come from url
            user_info = self.get_user_info_from_xml(child)
            if self.student_id:
                user_auth = UserAuth()
                processed_user_info = {
                    'email': user_info['mail'],
                    'first_name': user_info['givenName'],
                    'last_name': user_info['sn'],
                    'student_id': self.student_id
                }
                user_id = user_auth.user_login('cwru', processed_user_info, user_info)
                if user_id:
                    refresh_token = user_auth.gen_refresh_token(user_id, user_info)
                    access_token = user_auth.gen_access_token(refresh_token)
                    return RedirectResponse(
                        url=f"{self.came_from}?refresh={refresh_token}&access={access_token}")
                else:
                    return RedirectResponse(url=f"{self.came_from}?refresh=error&access=error")
            else:
                return RedirectResponse(url=f"{self.came_from}?refresh=error&access=error")

    def get_user_info_from_xml(self, child):
        """
        get user info from xml
        :param child: child node
        :return: user info
        """
        user_info = {}
        self.student_id = child[0].text
        for i in child[1]:
            # get rid of everything in {}
            key = i.tag.split("}")[1]
            user_info[key] = i.text
        return user_info
