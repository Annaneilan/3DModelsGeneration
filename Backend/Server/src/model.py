# Base
import io
import uuid
import json
import threading

# Local
from . import utils
from .data_key import DataKey
from .storage import S3Helper
from .queue import SQSHelper, QueueMessage, AWSCredentials
from .resource import ResourceStatus, RequestedResource

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
        self.pending_tasks = {
            "image_gen": set(),
            "pmesh_gen": set(),
            "omesh_gen": set()
        }
        
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
    ) -> uuid.UUID:
        new_uuid = uuid.uuid4()
        while self.s3_storage.file_exists(str(new_uuid)):
            new_uuid = uuid.uuid4()
        
        return new_uuid
    
    def observe_results(self):
        print("Observation Thread: Started")
        
        while not self.result_observation_termination_event.is_set():
            print("Observation Thread: Running")
            # Read message
            messages = self.sqs_result.receive_messages(max_messages=10)
            
            # Process messages
            for msg in messages:
                
                try:
                    # Parse
                    body_json = msg.body_json()
                    project_id = uuid.UUID(body_json["project_id"])
                    task_type = str(body_json["task_type"])
                    
                    # Verify task type
                    assert task_type in self.pending_tasks, "Invalid task type"
                    
                    # Remove from pending
                    if project_id in self.pending_tasks[task_type]:
                        self.pending_tasks[task_type].remove(project_id)
                    else:
                        print(f"Task {project_id} not found in pending tasks of type {task_type}")
                
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
        project_id = self.generate_identifier()
        
        # Create task data
        task_data = {
            "project_id": str(project_id),
            "positive_prompt": positive_prompt,
            "negative_prompt": negative_prompt
        }
        
        # Write task data to string
        message = json.dumps(task_data)
        
        # Send message
        self.sqs_image_gen.send_message(message)
        
        # Add to pending tasks
        self.pending_tasks["image_gen"].add(project_id)
        
        return project_id
    
    def upload_image(
        self,
        image_bytes: bytes
    ) -> uuid.UUID:
        # Generate new uuid
        project_id = self.generate_identifier()
        
        # Resize to 512x512
        image = utils.open_image(io.BytesIO(image_bytes), mode="RGB")
        image = utils.resize_with_aspect(image, 512)
        
        # Write to buffer
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        buffer.seek(0)
         
        # Upload iamge
        self.s3_storage.upload_file(
            DataKey.image(str(project_id)),
            buffer
        )
        
        return project_id
    
    def download_image(
        self,
        project_id: uuid.UUID
    ) -> RequestedResource:
        # Task is not completed
        if project_id in self.pending_tasks["image_gen"]:
            print("Task is not completed")
            return RequestedResource(project_id, ResourceStatus.PENDING)
        
        # Try download image
        image_buffer = self.s3_storage.download_file(DataKey.image(str(project_id)))
        
        status = ResourceStatus.NOT_AVAILABLE if image_buffer is None else ResourceStatus.AVAILABLE
        result = RequestedResource(
            project_id,
            status,
            data=image_buffer
        )
        return result
    
    # Public (Mesh)
    ################################################################
    
    def request_mesh_generation(
        self,
        project_id: uuid.UUID,
        perspective: bool,
    ):
        # Validate image is uploaded to S3
        assert self.s3_storage.file_exists(DataKey.image(str(project_id))), "Image not found!"
        
        if self.s3_storage.file_exists(
            DataKey.mesh(str(project_id), perspective=perspective)
        ):
            print("Mesh already exists")
            return
        
        # Create task
        task_data = { "project_id": str(project_id) }
        message = json.dumps(task_data)
        
        # Task type
        if perspective:
            self.pending_tasks["pmesh_gen"].add(project_id)
            self.sqs_perspective_gen.send_message(message)
        else:
            self.pending_tasks["omesh_gen"].add(project_id)
            self.sqs_object_gen.send_message(message)
    
    def download_mesh_zip(
        self,
        project_id: uuid.UUID,
        perspective: bool = True,
        textured: bool = True
    ) -> RequestedResource:
        # Task is not completed
        if perspective and project_id in self.pending_tasks["pmesh_gen"]:
            print("Task is not completed")
            return RequestedResource(project_id, ResourceStatus.PENDING)
        
        elif project_id in self.pending_tasks["omesh_gen"]:
            print("Task is not completed")
            return RequestedResource(project_id, ResourceStatus.PENDING)

        # Try download mesh
        file_key = DataKey.mesh(
            str(project_id),
            perspective=perspective,
            textured=textured
        )
        mesh_buffer = self.s3_storage.download_file(file_key)
        
        status = ResourceStatus.NOT_AVAILABLE if mesh_buffer is None else ResourceStatus.AVAILABLE
        result = RequestedResource(
            project_id,
            status,
            data=mesh_buffer
        )
        
        return result
    