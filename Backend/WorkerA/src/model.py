# Base
import io
import uuid
import json
import threading

# Third Party
from PIL import Image

# Local
from .diffusion import load_2_1
from .storage import S3Helper
from .queue import SQSHelper, QueueMessage, AWSCredentials

class MeshGenServerModel:
    def __init__(
        self,
        credentials: AWSCredentials = None
    ) -> None:
        self.setup_aws(credentials)
        self.setup_dl()
    
    def setup_aws(
        self,
        credentials: AWSCredentials = None
    ):
        # S3
        self.s3_storage = S3Helper(
            name="mg-data-storage",
            region="eu-central-1",
            credentials=credentials
        )
        
        # SQS
        self.sqs_image_gen = SQSHelper(
            "mg-image-queue",
            region="eu-central-1",
            credentials=credentials
        )
        self.sqs_perspective_gen = SQSHelper(
            "mg-perspective-gen",
            region="eu-central-1",
            credentials=credentials
        )
        self.sqs_result = SQSHelper(
            "mg-result-queue",
            region="eu-central-1",
            credentials=credentials
        )
    
    def setup_dl(self):
        self.sd = load_2_1()
    
    # Private (Image)
    ################################################################
    
    def _run_image_generation(self):
        try:
            self.__run_image_generation()
        except Exception as e:
            print(f"Error in image generation: {e}")
    
    def __run_image_generation(self):
        print(f"Looking for image generation tasks")
        tasks = self.sqs_image_gen.receive_messages(
            max_messages=1,
            wait_time=1
        )
        print(f"Read {len(tasks)} tasks from image queue")
        
        for task in tasks:
            task_data = task.body_json()
            print(f"Task data: {task_data}")

            try:
                print("Inferencing")
                out = self.sd(
                    prompt=task_data["positive_prompt"],
                    negative_prompt=task_data["negative_prompt"]
                )
                image_pil = out.images[0]

                print("Writing image to buffer")
                image_bytes = io.BytesIO()
                image_pil.save(image_bytes, format="PNG")
                image_bytes.seek(0)
                
                print("Saving image")
                self.s3_storage.upload_file(
                    f"{task_data['image_uuid']}.png",
                    image_bytes
                )
            
            except Exception as e:
                print(f"Failed to process image task: {e}")
            
            finally:
                print("Deleting message")
                self.sqs_image_gen.delete_message(task.receipt_handle)
                
                # Send result message
                message = json.dumps({
                    "uuid": task_data["image_uuid"],
                    "status": "OK"
                })
                self.sqs_result.send_message(message)
    
    # Private (Mesh)
    ################################################################
    
    def _run_mesh_generation(self):
        try:
            self.__run_mesh_generation()
        except Exception as e:
            print(f"Error in image generation: {e}")
    
    def __run_mesh_generation(self):
        pass
    
    # Public
    ################################################################
    
    def run(self):
        while True:
            self._run_image_generation()
            self._run_mesh_generation()