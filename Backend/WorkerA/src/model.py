# Base
import io
import json
import zipfile
from pathlib import Path

# Third-party
import numpy as np
import open3d as o3d

# Local
from . import depth, utils
from .diffusion import load_2_1
from .storage import S3Helper
from .queue import SQSHelper, QueueMessage, AWSCredentials

class MeshGenServerModel:
    def __init__(
        self,
        credentials: AWSCredentials = None,
        temp_dir: Path = "data/temp"
    ) -> None:
        self.temp_dir = Path(temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
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
        self.sd = load_2_1()
    
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
            wait_time=20
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
            print(f"Error in mesh generation: {e}")
    
    def __run_mesh_generation(self):
        print(f"Looking for mesh generation tasks")
        tasks = self.sqs_perspective_gen.receive_messages(
            max_messages=1,
            wait_time=1
        )
        print(f"Read {len(tasks)} tasks from p-mesh queue")
        
        for task in tasks:
            task_data = task.body_json()
            print(f"Task data: {task_data}")

            try:
                print("Loading image")
                image_bytes = self.s3_storage.download_file(
                    f"{task_data['image_uuid']}.png"
                )
                print(image_bytes)
                
                image_pil = utils.open_image(image_bytes, mode="RGB")
                image_np = np.array(image_pil)
                
                print("Inferencing")
                depth_map = self.mde(image_np)

                print("Reconstructing")
                mesh = self.depth_to_mesh(image_np, depth_map)
                buffer = self.mesh_to_zip(mesh)

                print("Saving mesh")
                self.s3_storage.upload_file(
                    f"{task_data['mesh_uuid']}.zip",
                    buffer
                )
            
            except Exception as e:
                print(f"Failed to process p-mesh task: {e}")
            
            finally:
                print("Deleting message")
                self.sqs_perspective_gen.delete_message(task.receipt_handle)
                
                # Send result message
                message = json.dumps({
                    "uuid": task_data["mesh_uuid"],
                    "status": "OK"
                })
                self.sqs_result.send_message(message)
    
    def depth_to_mesh(
        self,
        image: np.ndarray,
        depth_map: np.ndarray,
    ) -> o3d.geometry.TriangleMesh:
        mask = depth_map > 5
        depth_map /= -200
        v_grid, v_num = depth.create_pixel_vertice_mapping(mask)
        mesh = depth.create_mesh(image, depth_map, v_grid, v_num)
        
        return mesh
    
    def mesh_to_zip(
        self,
        mesh: o3d.geometry.TriangleMesh
    ):
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