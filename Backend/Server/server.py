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
from src.resource import ResourceStatus

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
    """
    Generate image
    """
    print("POST /image")

    image_uuid = app_logic.request_image_generation(
        request.prompt,
        request.negative_prompt
    )
    return { "project_id": str(image_uuid) }

@app.put("/image")
async def put_image(request: Request):
    """
    Upload image
    """
    print("PUT /image")
    image_bytes = await request.body()
    image_uuid = app_logic.upload_image(image_bytes)
    return { "project_id": str(image_uuid) }

@app.get("/image/{project_id}")
async def get_image(project_id: uuid.UUID):
    result = app_logic.download_image(project_id)
    
    # Error
    if result.status == ResourceStatus.NOT_AVAILABLE:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Not ready, return 202
    elif result.status == ResourceStatus.PENDING:
        return Response(status_code=202)
    
    # Image is ready
    return Response(
        content=result.data.getvalue(),
        media_type="image/png"
    )

# Mesh
################################################################

@app.post("/model")
async def post_depth(request: serializable.MeshGenerationRequest):
    mesh_uuid = app_logic.request_mesh_generation(
        request.image_uuid,
        perspective=request.perspective,
    )
    return { "uuid": str(mesh_uuid) }

@app.get("/model/{project_id}")
async def get_mesh(project_id: uuid.UUID, perspective: bool = True, textured: bool = True):
    result = app_logic.download_mesh_zip(project_id, perspective, textured)
    
    # Error
    if result.status == ResourceStatus.NOT_AVAILABLE:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Not ready, return 202
    elif result.status == ResourceStatus.PENDING:
        return Response(status_code=202)
    
    # Mesh is ready
    return Response(
        content=result.data.getvalue(),
        media_type="application/zip"
    )