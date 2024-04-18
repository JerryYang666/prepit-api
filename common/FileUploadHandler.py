# Copyright (c) 2024.
# -*-coding:utf-8 -*-
"""
@file: FileUploadHandler.py.py
@author: Jerry(Ruihuang)Yang
@email: rxy216@case.edu
@time: 4/17/24 21:51
"""
import boto3
from botocore.exceptions import ClientError
import uuid
import mimetypes


def get_extension_from_mime(content_type: str) -> str:
    """
    Determine the file extension based on the MIME type.
    :param content_type: The MIME type of the file.
    :return: The file extension (including the dot, e.g., '.jpg') or an empty string if not found.
    """
    extension = mimetypes.guess_extension(content_type)
    if extension is None:
        return ''  # Default to empty string if no extension could be determined
    return extension


class FileUploadHandler:
    BUCKET_NAME = 'bucket-57h03x'  # Specify your S3 bucket name here
    S3_FOLDER = 'prepit_data/uploads/'  # Folder in S3 to store uploaded files

    def __init__(self):
        self.s3_client = boto3.client('s3')

    def upload_file(self, file, content_type: str, public: bool = False) -> str:
        """
        Upload a file to a specified path in S3 with a unique UUID as the filename.
        Optionally make it publicly accessible based on the 'public' flag.
        Set the content type, and return the public URL to the file in S3.
        :param file: A file-like object to upload (e.g., from `open()` or `io.BytesIO`).
        :param content_type: The MIME type of the file, which is used to determine the file extension.
        :param public: A boolean indicating whether the file should be publicly accessible.
        :return: The public URL to the file in S3.
        """
        file_extension = get_extension_from_mime(content_type)
        unique_filename = str(uuid.uuid4()) + file_extension
        object_name = self.S3_FOLDER + unique_filename
        try:
            # Upload the file with content type specified
            self.s3_client.upload_fileobj(file, self.BUCKET_NAME, object_name, ExtraArgs={'ContentType': content_type})

            if public:
                # Set the file's ACL to public-read if required
                self.s3_client.put_object_acl(ACL='public-read', Bucket=self.BUCKET_NAME, Key=object_name)

            # Generate and return the file URL
            url = f"https://{self.BUCKET_NAME}.s3.us-east-2.amazonaws.com/{object_name}"
            return url
        except ClientError as e:
            print(f"An error occurred: {e}")
            return ""

# Usage example:
# with open('path_to_your_file', 'rb') as f:
#     handler = FileUploadHandler()
#     public_url = handler.upload_public_file(f, 'image/jpeg')  # Specify the content type
#     print(public_url)
