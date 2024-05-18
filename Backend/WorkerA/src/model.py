# Base
import io
import json
import zipfile
from pathlib import Path

# Third-party
import cv2
import numpy as np
import open3d as o3d

# Local
from . import depth, diffusion, utils
from .data_key import DataKey
from .aws.storage import S3Helper
from .aws.queue import SQSHelper, QueueMessage
from .aws.credentials import AWSCredentials

class MeshGenServerModel:
    def __init__(
        self,
        credentials: AWSCredentials = None,
        temp_dir: Path = "data/temp",
        wait_time: int = 2
    ) -> None:
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        self.wait_time = wait_time
        
        self.setup_aws(credentials)
        self.setup_sd()
        self.setup_mde()
    
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
    
    def setup_sd(self):
        self.sd = diffusion.load_2_1()
    
    def setup_mde(self):
        self.mde = depth.DepthAnythingFacade(
            encoder="vitl",
            device="cuda"
        )
    
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
            wait_time=self.wait_time
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
                    DataKey.image(task_data["project_id"]),
                    image_bytes
                )
            
            except Exception as e:
                print(f"Failed to process image task: {e}")
            
            finally:
                print("Deleting message")
                self.sqs_image_gen.delete_message(task.receipt_handle)
                
                # Send result message
                message = json.dumps({
                    "project_id": task_data["project_id"],
                    "task_type": "image_gen"
                })
                self.sqs_result.send_message(message)
    
    # Private (Mesh)
    ################################################################
    
    def _run_mesh_generation(self):
        try:
            self.__run_mesh_generation()
        except Exception as e:
            print(f"Error in mesh generation: {e}")
    
    def __run_mesh_generation(self):
        print(f"Looking for mesh generation tasks")
        tasks = self.sqs_perspective_gen.receive_messages(
            max_messages=1,
            wait_time=self.wait_time
        )
        print(f"Read {len(tasks)} tasks from p-mesh queue")
        
        for task in tasks:
            task_data = task.body_json()
            print(f"Task data: {task_data}")

            try:
                print("Loading image")
                image_bytes = self.s3_storage.download_file(
                    DataKey.image(task_data["project_id"])
                )
                
                image_pil = utils.open_image(image_bytes, mode="RGB")
                image_np = np.array(image_pil)
                
                print("Inferencing")
                depth_map = self.mde(image_np)

                print("Reconstructing")
                textured_mesh = self.generate_textured_mesh(image_np, depth_map, resolution=256)
                texturless_mesh = self.create_texturless_mesh(textured_mesh)
                
                print("Saving textured mesh")
                buffer = self.mesh_to_zip(textured_mesh)
                self.s3_storage.upload_file(
                    DataKey.mesh(task_data["project_id"], perspective=True, textured=True),
                    buffer
                )
                
                print("Saving mesh")
                buffer = self.mesh_to_zip(texturless_mesh)
                self.s3_storage.upload_file(
                    DataKey.mesh(task_data["project_id"], perspective=True, textured=False),
                    buffer
                )
            
            except Exception as e:
                print(f"Failed to process p-mesh task: {e}")
            
            finally:
                print("Deleting message")
                self.sqs_perspective_gen.delete_message(task.receipt_handle)
                
                # Send result message
                message = json.dumps({
                    "project_id": task_data["project_id"],
                    "task_type": "pmesh_gen"
                })
                self.sqs_result.send_message(message)
    
    def generate_textured_mesh(
        self,
        image: np.ndarray,
        depth_map: np.ndarray,
        resolution: int = 512
    ) -> o3d.geometry.TriangleMesh:
        depth_map = cv2.resize(
            depth_map.astype(np.float32),
            (resolution, resolution)
        )
        mask = depth_map > 5
        depth_map /= -200
        
        v_grid, v_num = depth.create_pixel_vertice_mapping(mask)
        mesh = depth.create_mesh(image, depth_map, v_grid, v_num)
        
        # Center mesh
        mesh.translate(-mesh.get_center())
        
        return mesh
    
    def create_texturless_mesh(
        textured_mesh: o3d.geometry.TriangleMesh
    ) -> o3d.geometry.TriangleMesh:
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = textured_mesh.vertices
        mesh.triangles = textured_mesh.triangles
        return mesh
    
    def mesh_to_zip(
        self,
        mesh: o3d.geometry.TriangleMesh
    ):
        # Clean temp dir
        for file_p in self.temp_dir.glob("*"):
            file_p.unlink()
        
        # Save to temp dir
        mesh_p = self.temp_dir / "mesh.obj"
        o3d.io.write_triangle_mesh(str(mesh_p), mesh)
        
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
    
    # Public
    ################################################################
    
    def run(self):
        while True:
            self._run_image_generation()
            self._run_mesh_generation()