# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: models.py.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 3/16/24 23:48
"""
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, DateTime, String, Integer, func, MetaData, Boolean, UUID, JSON

Base = declarative_base(metadata=MetaData(schema="public"))
metadata = Base.metadata


class Student(Base):
    __tablename__ = "ai_users"

    user_id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    first_name = Column(String(60), nullable=False)
    last_name = Column(String(60), nullable=False)
    email = Column(String(150), unique=True, primary_key=True, nullable=False)
    student_id = Column(String(20), unique=True, nullable=False)
    role = Column(String(20), nullable=False)
    school_id = Column(Integer, nullable=False)
    last_login = Column(DateTime)
    create_at = Column(DateTime, default=func.now())

    def __repr__(self):
        return f"id: {self.user_id}, name: {self.first_name} {self.last_name}, email: {self.email}, student_id: {self.student_id}, role: {self.role}, school_id: {self.school_id}, last_login: {self.last_login}, create_at: {self.create_at}"


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
    files = Column(JSON)

    def __repr__(self):
        return f"Agent id: {self.agent_id}, name: {self.agent_name}, description: {self.agent_description}, cover: {self.agent_cover}, creator: {self.creator}, status: {self.status}, model: {self.model}"
