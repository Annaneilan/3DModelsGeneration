# Python
import io
import uuid

# FastAPI
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Local
from src import serializable
from src.credentials import AWSCredentials
from src.model import MeshGenServerModel

# Init model
################################################################

credentials = AWSCredentials.from_json_file("../credentials.json")
app_logic = MeshGenServerModel(credentials)

# Init FastAPI
################################################################

@asynccontextmanager
async def lifespan(app: FastAPI):
    # On startup
    yield
    # On shutdown
    app_logic.destroy()

app = FastAPI(lifespan=lifespan)

# Disable CORS for development
app.add_middleware( 
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    #print("POST /image")
    image_uuid = app_logic.request_image_generation(
        request.prompt,
        request.negative_prompt
    )
    return { "uuid": str(image_uuid) }

@app.get("/image/{image_uuid}")
async def get_image(image_uuid: uuid.UUID):
    image_bytes: io.BytesIO = app_logic.download_image(image_uuid)
    
    if image_bytes is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return Response(
        content=image_bytes.getvalue(),
        media_type="image/png"
    )

@app.put("/image")
async def put_image(request: Request):
    image_bytes = await request.body()
    image_uuid = app_logic.upload_image(image_bytes)
    return { "uuid": str(image_uuid) }

# Mesh
################################################################

@app.post("/model/perspective")
async def post_depth(request: serializable.MeshGenerationRequest):
    mesh_uuid = app_logic.request_mesh_generation(
        request.image_uuid,
        perspective=True
    )
    return { "uuid": str(mesh_uuid) }

@app.post("/model/object")
async def post_mesh(request: serializable.MeshGenerationRequest):
    mesh_uuid = app_logic.request_mesh_generation(
        request.image_uuid,
        perspective=False
    )
    return { "uuid": str(mesh_uuid) }

@app.get("/model/{mesh_uuid}")
async def get_mesh(mesh_uuid: uuid.UUID):
    mesh_bytes: io.BytesIO = app_logic.download_mesh_zip(mesh_uuid)
    
    if mesh_bytes is None:
        raise HTTPException(status_code=404, detail="Mesh not found")
    
    return Response(
        content=mesh_bytes.getvalue(),
        media_type="application/zip"
    )