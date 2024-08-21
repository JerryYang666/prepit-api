# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: WorkspaceHelper.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 6/16/24 00:16
"""


def check_workspace_agent_use_access(user_jwt: dict, workspace_id: str):
    """
    if the user is a "student" or "teacher" in the workspace, return True, else return False
    """
    user_workspace_role = user_jwt['workspace_role']
    if user_workspace_role.get(workspace_id, None) == 'student' or user_workspace_role.get(workspace_id, None) == 'teacher' or user_jwt.get('system_admin', False):
        return True
    return False


def check_workspace_agent_manage_access(user_jwt: dict, workspace_id: str):
    """
    if the user is a "teacher" in the workspace, return True, else return False
    """
    user_workspace_role = user_jwt['workspace_role']
    if user_workspace_role.get(workspace_id, None) == 'teacher' or user_jwt.get('system_admin', False):
        return True
    return False
