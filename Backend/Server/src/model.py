# Base
import io
import uuid
import json
import threading

# Local
from . import utils
from .storage import S3Helper
from .queue import SQSHelper, QueueMessage, AWSCredentials

class MeshGenServerModel:
    def __init__(
        self,
        credentials: AWSCredentials = None
    ) -> None:
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
        self.sqs_object_gen = SQSHelper(
            "mg-object-gen",
            region="eu-central-1",
            credentials=credentials
        )
        self.sqs_result = SQSHelper(
            "mg-result-queue",
            region="eu-central-1",
            credentials=credentials
        )
        
        # Identifier tracking
        self.locked_identifiers = set() # Which uuids are assigned, but not yet completed
        
        # Result observation thread
        self.result_observation_interval_s = 1
        self.result_observation_thread = threading.Thread(target=self.observe_results)
        self.result_observation_termination_event = threading.Event()
        
        # Start observation thread
        self.result_observation_thread.start()
    
    # Private
    ################################################################
    
    def generate_identifier(
        self,
        for_extension: str = "png"
    ) -> uuid.UUID:
        # Generate random image uuid
        new_uuid = uuid.uuid4()
        while new_uuid in self.locked_identifiers or \
            self.s3_storage.file_exists(f"{str(new_uuid)}.{for_extension}"):
            new_uuid = uuid.uuid4()
        
        # Lock identifier locally
        self.locked_identifiers.add(new_uuid)
        
        return new_uuid
    
    def observe_results(self):
        print("Observation Thread: Started")
        
        while not self.result_observation_termination_event.is_set():
            #self.result_observation_termination_event.wait(self.result_observation_interval_s)
            print("Observation Thread: Running")
            # Read message
            messages = self.sqs_result.receive_messages(max_messages=10)
            
            # Process messages
            for msg in messages:
                
                try:
                    body_json = msg.body_json()
                    task_uuid = uuid.UUID(body_json["uuid"])
                    
                    if task_uuid in self.locked_identifiers:
                        self.locked_identifiers.remove(task_uuid)
                    else:
                        print("Received result for unknown task!")
                
                except Exception as e:
                    print(f"Failed to process result message: {e}")

                # Delete processed message
                self.sqs_result.delete_message(msg.receipt_handle)
            
            print(f"Observation Thread: Processed {len(messages)} messages")
        
        print(f"Observation Thread: Finished")
    
    # Public (General)
    ################################################################
    
    def destroy(self):
        self.result_observation_termination_event.set()
    
    # Public (Image)
    ################################################################
    
    def request_image_generation(
        self,
        positive_prompt: str,
        negative_prompt: str = None
    ) -> uuid.UUID:
        # Generate image uuid
        image_uuid = self.generate_identifier(for_extension="png")
        
        # Create task data
        task_data = {
            "image_uuid": str(image_uuid),
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt
        }
        
        # Write task data to string
        message = json.dumps(task_data)
        
        # Send message
        self.sqs_image_gen.send_message(message)
        
        return image_uuid
    
    def upload_image(
        self,
        image_bytes: bytes
    ) -> uuid.UUID:
        # Generate new uuid
        image_uuid = self.generate_identifier(for_extension="png")
        
        # Resize to 512x512
        image = utils.open_image(image_bytes, mode="RGB")
        image = utils.resize_with_aspect(image, 512)
        
        # Write to buffer
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
         
        # Upload iamge
        self.s3_storage.upload_file(
            f"{str(image_uuid)}.png",
            buffer
        )
        
        return image_uuid
    
    def download_image(
        self,
        image_uuid: uuid.UUID
    ) -> io.BytesIO:
        # Task is not completed
        if image_uuid in self.locked_identifiers:
            return None
        
        image_buffer = self.s3_storage.download_file(f"{str(image_uuid)}.png")
        return image_buffer
    
    # Public (Mesh)
    ################################################################
    
    def request_mesh_generation(
        self,
        image_uuid: uuid.UUID,
        perspective: bool = False
    ) -> uuid.UUID:
        # Validate image is uploaded to S3
        assert self.s3_storage.file_exists(f"{str(image_uuid)}.png"), "Image not found!"
        
        # Generate mesh uuid
        mesh_uuid = self.generate_identifier(for_extension="zip")
        
        # Create task
        task_data = {
            "image_uuid": str(image_uuid),
            "mesh_uuid": mesh_uuid,
        }
        message = json.dumps(task_data)
        
        # Send message
        queue = self.sqs_perspective_gen if perspective else self.sqs_object_gen
        queue.send_message(message)
        
        return mesh_uuid
    
    def download_mesh_zip(
        self,
        mesh_uuid: uuid.UUID
    ) -> io.BytesIO:
        # Task is not completed
        if mesh_uuid in self.locked_identifiers:
            return None
        
        mesh_buffer = self.s3_storage.download_file(f"{str(mesh_uuid)}.zip")
        return mesh_buffer
    