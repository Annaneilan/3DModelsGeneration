# Python
import io
import zipfile
from pathlib import Path

# Third-party
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Local
import serializable
from diffusion import load_2_1

# Init
app = FastAPI()
sd = load_2_1()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows only specific origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
def root():
    """
    Root endpoint to check if the server is running.
    """
    return {
        "name": "MeshGenAPI",
        "status": "OK"
    }

@app.post("/image")
async def post_image(request: serializable.ImageRequestBody):
    """
    POST Image endpoint to get image by prompt.
    """
    
    # Get prompt from query
    #body = await request.json()
    
    # Inference model
    try:
        print("request.prompt", request.prompt)
        print("request.negative_prompt", request.negative_prompt)
        out = sd(
            prompt=request.prompt,
            negative_prompt=request.negative_prompt
        )
        image_pil = out.images[0]
    except Exception as e:
        return HTTPException(status_code=500, detail=f"Failed to generate image. Error: {e}")
    
    # Write to bytes
    image_bytes = io.BytesIO()
    image_pil.save(image_bytes, format="PNG")
    image_bytes.seek(0)
    
    # Return image
    return Response(
        content=image_bytes.read(),
        media_type="image/png"
    )

@app.post("/mesh")
async def post_mesh(): # request: Request
    """
    GET Mesh endpoint to get mesh by image & depth?.
    """
    
    # TODO: parse request, inference model, create mesh
    
    # Find files
    files_dir = Path("data/2/")
    files_p = list(files_dir.glob("*"))
    if len(files_p) == 0:
        return HTTPException(status_code=500, detail="No files found in data directory.")
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_p in files_p:
            zip_file.write(file_p, file_p.name)
    
    buffer.seek(0)
    
    return Response(
        content=buffer.read(),
        media_type="application/zip",
        headers={
            "Content-Disposition": "attachment; filename=mesh.zip"
        }
    )