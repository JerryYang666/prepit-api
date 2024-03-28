# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: FileStorageHandler.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 3/22/24 21:05
"""
import json
import os
from typing import Any, Optional
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv


class FileStorageHandler:
    LOCAL_FOLDER = "./volume_cache/"
    BUCKET_NAME = "bucket-57h03x"
    S3_FOLDER = "prepit_data/"

    def __init__(self):
        load_dotenv()
        self.s3_client = boto3.client('s3')

    @staticmethod
    def _ensure_directory_exists(path: str) -> None:
        """Ensure the directory of the given path exists."""
        directory = os.path.dirname(path)
        if not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _get_s3_object_name(self, filename: str) -> str:
        """Construct the S3 object name based on the local filename."""
        return os.path.join(self.S3_FOLDER, filename)

    def get_file(self, filename: str, parse_json: bool = False) -> Any:
        """
        Get the content of a file from the local cache or S3 bucket.
        :param filename: The name of the file. Can be a relative path to docker volume.
        :param parse_json: Whether to parse the content as JSON.
        :return: The content of the file.
        """
        local_path = os.path.join(self.LOCAL_FOLDER, filename)
        self._ensure_directory_exists(local_path)
        if not os.path.exists(local_path):
            s3_object_name = self._get_s3_object_name(filename)
            self.__download_file(self.BUCKET_NAME, s3_object_name, local_path)
        try:
            with open(local_path, 'r', encoding='utf-8') as file:
                content = file.read()
                if parse_json:
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError:
                        return content
                return content
        except FileNotFoundError:
            return None

    def set_file(self, filename: str, content: Any) -> bool:
        """
        Set the content of a file in the local cache and upload it to the S3 bucket.
        :param filename: The name of the file. Can be a relative path to docker volume.
        :param content: The content to write to the file. If it is a dictionary, it will be converted to JSON.
        :return: Whether the file was successfully uploaded to the S3 bucket.
        """
        if isinstance(content, dict):
            content = json.dumps(content)
        local_path = os.path.join(self.LOCAL_FOLDER, filename)
        self._ensure_directory_exists(local_path)
        with open(local_path, 'w', encoding='utf-8') as file:
            file.write(content)
        s3_object_name = self._get_s3_object_name(filename)
        upload_status = self.__upload_file(self.BUCKET_NAME, local_path, s3_object_name)
        return upload_status

    def __upload_file(self, bucket: str, local_path: str, object_name: Optional[str] = None) -> bool:
        try:
            self.s3_client.upload_file(local_path, bucket, object_name)
        except ClientError as e:
            print(e)
            return False
        return True

    def __download_file(self, bucket_name: str, object_name: str, local_path: str) -> bool:
        self._ensure_directory_exists(local_path)
        try:
            self.s3_client.download_file(bucket_name, object_name, local_path)
        except ClientError as e:
            print(e)
            return False
        return True
