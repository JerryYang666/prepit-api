# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: FeedbackStorageHandler.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 6/30/24 01:16
"""
import boto3
import logging
import os
from boto3.dynamodb.conditions import Key
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)


class Feedback(BaseModel):
    thread_id: str
    step_id: int
    agent_id: str
    feedback: str


class FeedbackStorageHandler:
    DYNAMODB_TABLE_NAME = "prepit_ai_feedback"

    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb', region_name='us-east-2',
                                       aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID_DYNAMODB"),
                                       aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY_DYNAMODB"))
        self.table = self.dynamodb.Table(self.DYNAMODB_TABLE_NAME)

    def put_feedback(self, thread_id: str, agent_id: str, step_id: int, feedback: str) -> bool:
        """
        Put the feedback into the database.
        :param thread_id: The ID of the thread.
        :param agent_id: The ID of the agent.
        :param step_id: The ID of the step.
        :param feedback: The feedback.
        :return: True if successful, False otherwise.
        """
        try:
            self.table.put_item(
                Item={
                    'thread_id': thread_id,
                    'step_id': step_id,
                    'agent_id': agent_id,
                    'feedback': feedback
                }
            )
            return True
        except Exception as e:
            logging.error(f"Error putting the feedback into the database: {e}")
            return False

    def get_feedback_for_thread(self, thread_id: str) -> list:
        """
        Get the feedback for a thread.
        :param thread_id: The ID of the thread.
        :return: A list of feedbacks.
        """
        try:
            response = self.table.query(
                KeyConditionExpression=Key('thread_id').eq(thread_id)
            )
            items = response['Items']
            return [Feedback(**item) for item in items]
        except Exception as e:
            logging.error(f"Error getting the feedback for the thread: {e}")
            return []
