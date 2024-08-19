# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: models.py.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 3/16/24 23:48
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, String, Integer, func, MetaData, Boolean, UUID, JSON, UniqueConstraint, \
    ForeignKey

Base = declarative_base(metadata=MetaData(schema="public"))
metadata = Base.metadata


class Agent(Base):
    __tablename__ = "ai_agents"

    agent_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    agent_name = Column(String(255), nullable=False)
    agent_description = Column(String, default='', nullable=False)
    agent_cover = Column(String, default='', nullable=False)
    creator = Column(String(16))
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), nullable=False)
    cat_id = Column(String(31))
    status = Column(Integer, default=1, nullable=False)
    voice = Column(Boolean, default=True, nullable=False)
    allow_model_choice = Column(Boolean, default=True, nullable=False)
    model = Column(String(16))
    agent_total_steps = Column(Integer, default=0, nullable=False)
    files = Column(JSON, default={}, nullable=False)
    workspace_id = Column(String, nullable=False)

    def __repr__(self):
        return f"Agent id: {self.agent_id}, name: {self.agent_name}, description: {self.agent_description}, cover: {self.agent_cover}, creator: {self.creator}, status: {self.status}, model: {self.model}"


class User(Base):
    __tablename__ = "ai_users"

    user_id = Column(Integer, primary_key=True, unique=True)
    first_name = Column(String(60), nullable=False)
    last_name = Column(String(60), nullable=False)
    email = Column(String(150), nullable=False, unique=True)
    system_admin = Column(Boolean, default=False, nullable=False)
    workspace_role = Column(JSON, nullable=False)
    school_id = Column(Integer, nullable=False)
    student_id = Column(String(20))
    last_auth_metadata = Column(JSON)
    last_login = Column(DateTime)
    create_at = Column(DateTime)
    profile_img_url = Column(String(2048), nullable=False)

    __table_args__ = (
        UniqueConstraint('user_id', 'email', name='ai_users_pk'),
    )

    def __repr__(self):
        return f"AIUser id: {self.user_id}, email: {self.email}"


class RefreshToken(Base):
    __tablename__ = "ai_refresh_tokens"

    token_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(Integer, ForeignKey('ai_users.user_id'), nullable=False)
    token = Column(UUID(as_uuid=True), nullable=False, unique=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    expire_at = Column(DateTime, nullable=False)
    auth_metadata = Column(JSON)
    issued_access_token_count = Column(Integer, default=0, nullable=False)
    last_access_token_issued_at = Column(DateTime)

    __table_args__ = (
        UniqueConstraint('token', name='ai_refresh_tokens_token_key'),
    )

    def __repr__(self):
        return f"RefreshToken id: {self.token_id}, user_id: {self.user_id}, token: {self.token}"


class Thread(Base):
    __tablename__ = "ai_threads"

    thread_id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    agent_id = Column(UUID(as_uuid=True), ForeignKey('ai_agents.agent_id'), nullable=False)
    edge_ap = Column(String(20))
    last_trial_timestamp = Column(DateTime)
    last_trial_id = Column(Integer, default=0, nullable=False)
    finished = Column(Boolean, default=False, nullable=False)
    agent_name = Column(String(255))
    workspace_id = Column(String(64))
    student_id = Column(String(20))
    user_name = Column(String(256), nullable=False)

    def __repr__(self):
        return f"Thread id: {self.thread_id}, user_id: {self.user_id}, agent_id: {self.agent_id}, trial_id: {self.last_trial_id}, finished: {self.finished}"
