# Python
import io
import uuid

# FastAPI
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Local
from src import serializable
from src.model import MeshGenServerModel

app = FastAPI()
app_logic = MeshGenServerModel()

# Disable CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows only specific origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Root
################################################################

@app.get("/")
def root():
    """
    Root endpoint to check if the server is running.
    """
    return {
        "name": "MeshGenAPI",
        "status": "OK"
    }

# Image
################################################################

@app.post("/image")
async def post_image(request: serializable.ImageGenerationRequest):
    image_uuid = app_logic.request_image_generation(request)
    return { "uuid": image_uuid }

@app.get("/image/{image_uuid}")
async def get_image(image_uuid: uuid.UUID):
    image_bytes: io.BytesIO = app_logic.download_image(image_uuid)
    return Response(
        content=image_bytes.getvalue(),
        media_type="image/png"
    )

@app.put("/image")
async def put_image(request: Request):
    image_uuid = app_logic.upload_image(request)
    return { "uuid": image_uuid }

# Mesh
################################################################

@app.post("/model/perspective")
async def post_depth(request: serializable.MeshGenerationRequest):
    mesh_uuid = app_logic.request_mesh_generation(request, perspective=True)
    return { "uuid": mesh_uuid }

@app.post("/model/object")
async def post_mesh(request: serializable.MeshGenerationRequest):
    mesh_uuid = app_logic.request_mesh_generation(request, perspective=False)
    return { "uuid": mesh_uuid }

@app.get("/model/{mesh_uuid}")
async def get_mesh(mesh_uuid: uuid.UUID):
    mesh_bytes: io.BytesIO = app_logic.download_mesh_zip(mesh_uuid)
    return Response(
        content=mesh_bytes.getvalue(),
        media_type="application/zip"
    )