# Base
import json
from uuid import UUID
from io import BytesIO
from pathlib import Path
from typing import Union, Dict, Callable

# AWS
import boto3
from botocore.exceptions import ClientError

# Local
from .credentials import AWSCredentials

class S3Helper:
    def __init__(
        self,
        name: str,
        region: str,
        credentials: AWSCredentials = None
    ) -> None:
        # Init
        self.name = name
        self.region = region
        self.credentials: AWSCredentials = credentials
    
    def _init_client(self):
        # Use instance credentials
        if self.credentials is None:
            s3 = boto3.client(
                "s3",
                region_name=self.region
            )
        
        # Use provided credentials
        else:
            s3 = boto3.client(
                "s3",
                region_name=self.region,
                aws_access_key_id=self.credentials.access_key_id,
                aws_secret_access_key=self.credentials.secret_access_key,
                aws_session_token=self.credentials.session_token
            )
        
        return s3
    
    def _head_file(self, s3, filename:str) -> bool:
        file_exists = True
        try:
            s3.head_object(
                Bucket=self.name,
                Key=filename
            )
        
        except ClientError as e:
            if int(e.response["Error"]["Code"]) == 404:
                file_exists = False
            else:
                logger.error(
                    "Unexpected error occurred, when looking for " + \
                    f"{filename} in {self.name}! Details: {e}"
                )

        except Exception as e:
            logger.error(
                "Unexpected error occurred, when looking for " + \
                f"{filename} in {self.name}! Details: {e}"
            )
        
        return file_exists
    
    # Public methods
    ################################################################
    
    def file_exists(
        self,
        filename: str
    ) -> bool:
        s3 = self._init_client()
        exists = self._head_file(s3, filename)
        return exists
    
    def download_file(
        self,
        filename: str,
    ) -> BytesIO | None:
        s3 = self._init_client()
        
        try:
            file_bytes = BytesIO()
            s3.download_fileobj(self.name, filename, file_bytes)
            
            file_bytes.seek(0)
            return file_bytes
        
        except ClientError as e:
            logger.error(f"Failed to download {filename}! Details: {e}")
        
        except Exception as e:
            logger.error(f"Failed to download {filename}! Details: {e}")
        
        return None
    
    def upload_file(
        self,
        filename: str,
        file_bytes: BytesIO,
    ) -> bool:
        s3 = self._init_client()
        
        try:
            s3.upload_fileobj(file_bytes, self.name, filename)
            return True
        
        except ClientError as e:
            logger.error(f"Failed to upload {filename}! Details: {e}")
            
        except Exception as e:
            logger.error(f"Failed to upload {filename}! Details: {e}")
        
        return False
