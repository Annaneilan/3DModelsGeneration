# Base
import uuid
import json
from typing import Tuple, List, Union
from pathlib import Path

# AWS
import boto3
from botocore.exceptions import ClientError

# Local
from .credentials import AWSCredentials

class QueueMessage:
    def __init__(
        self,
        body: str,
        receipt_handle: str
    ) -> None:
        self.body = body
        self.receipt_handle = receipt_handle

class SQSHelper:
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
            sqs = boto3.client(
                "sqs",
                region_name=self.region
            )
        
        # Use provided credentials
        else:
            sqs = boto3.client(
                "sqs",
                region_name=self.region,
                aws_access_key_id=self.credentials.access_key_id,
                aws_secret_access_key=self.credentials.secret_access_key,
                aws_session_token=self.credentials.session_token
            )
        
        return sqs
    
    # Public methods
    ################################################################
    
    def send_message(
        self,
        message: str
    ):
        sqs = self._init_client()
        response = sqs.send_message(
            QueueUrl=self.name,
            MessageBody=message
        )
        return response

    def receive_messages(
        self,
        max_messages: int = 1
    ) -> List[QueueMessage]:
        # Init client
        sqs = self._init_client()
        
        # Get messages
        response = sqs.receive_message(
            QueueUrl=self.name,
            MaxNumberOfMessages=max_messages,
            MessageAttributeNames=['All'],
            WaitTimeSeconds=20
        )
        
        # Post-process
        messages: List[QueueMessage] = []
        for msg in response.get("Messages", []):
            msg_entity = QueueMessage(
                body=msg["Body"],
                receipt_handle=msg["ReceiptHandle"]
            )
            messages.append(msg_entity)
        
        return messages

    def delete_message(
        self,
        receipt_handle: str
    ):
        sqs = self._init_client()
        response = sqs.delete_message(
            QueueUrl=self.name,
            ReceiptHandle=receipt_handle
        )
        return response