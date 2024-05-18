# Base
import io
import json
import zipfile
from uuid import UUID
from pathlib import Path

# InstantMesh
import sys
sys.path.append("InstantMesh")
from InstantMesh import pipeline

# Local
import utils
from data_key import DataKey
from aws.storage import S3Helper
from aws.queue import SQSHelper, QueueMessage
from aws.credentials import AWSCredentials

class ObjectMeshGenModel:
    def __init__(
        self,
        credentials: AWSCredentials = None,
        temp_dir: Path = "data/temp",
        wait_time: int = 2,
    ) -> None:
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.wait_time = wait_time
        
        self.setup_aws(credentials)
    
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
    
    def run(self):
        while True:
            try:
                self._run_mesh_generation()
            except Exception as e:
                print(f"Error in mesh generation: {e}")
    
    def _run_mesh_generation(self):
        print(f"Looking for mesh generation tasks")
        tasks = self.sqs_object_gen.receive_messages(
            max_messages=1,
            wait_time=self.wait_time
        )
        print(f"Read {len(tasks)} tasks from o-mesh queue")
        
        for task in tasks:
            task_data = task.body_json()
            print(f"Task data: {task_data}")

            try:
                print("Loading image")
                image_bytes = self.s3_storage.download_file(
                    DataKey.image(task_data["project_id"])
                )
                
                print("Processing image")
                image = utils.open_image(image_bytes, mode="RGB")
                image = utils.resize_with_aspect(image, 512)
                
                print("Inferencing")
                vertices, uvs, faces, tex_idx, tex_map = pipeline.run(image)
                
                print("Creating texturless mesh")
                self.clear_temp()
                utils.save_obj(vertices, faces, self.temp_dir / "mesh.obj")
                buffer = self.zip_temp()

                print("Saving texturless mesh")
                self.s3_storage.upload_file(
                    DataKey.mesh(task_data["project_id"], perspective=False, textured=False),
                    buffer
                )
                
                print("Creating textured mesh")
                self.clear_temp()
                utils.save_obj_with_mtl(vertices, uvs, faces, tex_idx, tex_map, self.temp_dir / "mesh.obj")
                buffer = self.zip_temp()
                
                print("Saving textured mesh")
                self.s3_storage.upload_file(
                    DataKey.mesh(task_data["project_id"], perspective=False, textured=True),
                    buffer
                )
        
            except Exception as e:
                print(f"Failed to process o-mesh task: {e}")
            
            finally:
                print("Deleting message")
                self.sqs_object_gen.delete_message(task.receipt_handle)
                
                # Send result message
                message = json.dumps({
                    "project_id": task_data["project_id"],
                    "task_type": "omesh_gen"
                })
                self.sqs_result.send_message(message)
    
    def clear_temp(self):
        for file_p in self.temp_dir.glob("*"):
            file_p.unlink()
    
    def zip_temp(self):
        # Write to zip
        files_p = list(self.temp_dir.glob("*"))
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for file_p in files_p:
                zip_file.write(file_p, file_p.name)
                file_p.unlink()
        
        # Return
        buffer.seek(0)
        return buffer