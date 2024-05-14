import * as THREE from 'three';
import { MTLLoader } from 'MTLLoader';
import { OBJLoader } from 'OBJLoader';
import * as JSZIP from 'jszip';

class MeshLoader {
    constructor(onMeshLoaded) {
        this.materialLoader = new MTLLoader();
        this.meshLoader = new OBJLoader();
        this.textureLoader = new THREE.TextureLoader();

        this.onMeshLoaded = onMeshLoaded;
        
        console.log(JSZip)
    }

    async loadMeshFromZip(zipFile) {
        
        let zip = await JSZip.loadAsync(zipFile);
        let files = await zip.files;

        // Get urls
        let meshObj = URL.createObjectURL(await files['mesh.obj'].async('blob'));
        let meshMtl = URL.createObjectURL(await files['mesh.mtl'].async('blob'));
        let meshTex = URL.createObjectURL(await files['mesh_0.png'].async('blob'));

        this.loadMesh(meshObj, meshMtl, meshTex);
    }

    loadMesh(
        meshURL,
        materialURL,
        textureURL,
    ) {
        // Load materials
        this.materialLoader.load(materialURL, (materials) => {
            materials.preload();
            console.log("Materials loaded")

            // Load mesh
            this.meshLoader.setMaterials(materials);
            console.log("Materials set")

            this.meshLoader.load(meshURL, (loadedMesh) => {
                var mesh = loadedMesh;
                console.log("Mesh loaded")
                
                var texture = this.textureLoader.load(textureURL);
                console.log("Texture loaded")
                var material = new THREE.MeshBasicMaterial({ map: texture });

                mesh.traverse((node) => {
                    if (node instanceof THREE.Mesh) {
                        node.material = material;
                    }
                });
        
                console.log("Setting the mesh");
                
                mesh.position.set(-0.5, 0.5, 0);

                this.onMeshLoaded(mesh);
                console.log("Mesh set")
            });
        });
    }
}

class MeshGenData {
    constructor() {
        // Image & image uuid
        this.image = null;
        this.imageId = null;
        
        // Mesh & mesh uuid
        this.meshZipBlob = null;
        this.mesh = null;
        this.meshId = null;
        
        this.listeners = {
            // Image
            onImageWillChange: [],
            onImageDidChange: [],
            
            // Mesh
            onMeshWillChange: [],
            onMeshDidChange: []
        };
    }

    // Setters / Getters
    setImage(
        image,
        imageId = null
    ) {
        console.log("[MeshGenData:setImage]");

        this.triggerEvent('onImageWillChange');
        
        this.image = image;
        this.imageId = imageId;

        this.triggerEvent('onImageDidChange');
    }

    resetImage() {
        setImage('placeholder.jpg');
    }

    setMeshZip(meshZip) {
        console.log("[MeshGenData:setMeshZip]");
        this.meshZipBlob = meshZip;
    }

    setMesh(
        mesh,
        meshId = null
    ) {
        console.log("[MeshGenData:setMesh]");

        // Cleanup
        this.triggerEvent('onMeshWillChange');
        console.log("Disposing old mesh");
        console.log(this.mesh);
        // FIXME: Delete old mesh
        // if (this.mesh) {
        //     this.mesh.geometry.dispose();
        //     this.mesh.material.dispose();
        // }

        // Update
        this.mesh = mesh;
        this.meshId = meshId;

        this.triggerEvent('onMeshDidChange');
    }

    addListener(event, callback) {
        console.log("[MeshGenData:addListener] Adding listener for event: " + event);

        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        } else {
            console.warn(`No event named ${event} found.`);
        }
    }

    triggerEvent(event) {
        console.log("[MeshGenData:triggerEvent] Event: " + event);

        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback());
        }
    }
}

class MeshGenModel {
    constructor(
        server_url
    ) {
        // Singleton
        if (MeshGenModel.instance) {
            return MeshGenModel.instance;
        }
        MeshGenModel.instance = this;
        
        // Server URL
        this.server_url = server_url;

        // Data
        this.data = new MeshGenData();

        // Helpers
        this.meshLoader = new MeshLoader(
            (loadedMesh) => {
                console.log(loadedMesh);
                this.data.setMesh(loadedMesh);
            }
        );
        console.log("MeshGenModel initialized");
    }

    async requestImageGen(promptData) {

        // Request image generation
        //try {
            const response = await fetch(this.server_url + '/image', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(promptData)
            });
    
            if (!response.ok) {
                throw new Error('Failed to request image');
            }
    
            const responseData = await response.json();
            const imageId = responseData.uuid;

            // Set image id
            this.data.imageId = imageId;

            // Function to repeatedly check the status of the image
            const checkImageStatus = async () => {
                console.log("[MeshGenModel:requestImageGen] Checking image status");

                const imageResponse = await fetch(this.server_url + `/image/${imageId}`);
                
                // Image is ready
                if (imageResponse.status === 200) {
                    console.log("[MeshGenModel:requestImageGen] Image is ready");

                    // Check if requested id matches the response
                    if (imageId === this.data.imageId) {
                        const imageBlob = await imageResponse.blob();
                        const imageUrl = URL.createObjectURL(imageBlob);
                        this.data.setImage(imageUrl, imageId);
                    }
                }
                
                // Pending
                else if (imageResponse.status === 202) {
                    console.log("[MeshGenModel:requestImageGen] Pending");
                    setTimeout(checkImageStatus, 1000); // Repeat after 1 second
                }
                
                // Error
                else {
                    console.error('Error:', response.message);
                }
            };

            // Start checking image status
            checkImageStatus();

        //} catch (error) {
        //    console.error('Error:', error.message);
        //}
    }

    async requestMeshGen(genParams) {
        if (this.data.imageId === null) {
            // TODO: Upload image & get image id
            console.log("[MeshGenModel:requestMeshGen] No image to generate mesh from");
        }

        // Request object
        let meshGenerationParams = {
            image_uuid: this.data.imageId,
            perspective: genParams.perspective,
            textured: genParams.textured,
            meshing: genParams.meshing
        }

        const response = await fetch(this.server_url + '/model', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(meshGenerationParams)
        });
    
        if (!response.ok) {
            throw new Error('Failed to request mesh generation');
        }
    
        const responseData = await response.json();
        const meshId = responseData.uuid;
        //const meshId = "2dd3b975-86d5-4104-8aa1-a15440d8f182";

        // Set image id
        this.data.meshId = meshId;

        // Function to repeatedly check the status of the mesh generation task
        const checkMeshStatus = async () => {
            console.log("[MeshGenModel:requestMeshGen] Checking mesh status");

            const meshReponse = await fetch(this.server_url + `/model/${meshId}`);
            
            // Image is ready
            if (meshReponse.status === 200) {
                console.log("[MeshGenModel:requestMeshGen] Mesh is ready");

                // Check if requested id matches the response
                if (meshId === this.data.meshId) {
                    let meshZipBlob = await meshReponse.blob();
                    this.data.setMeshZip(meshZipBlob);
                    this.meshLoader.loadMeshFromZip(meshZipBlob);
                }
            }
            
            // Pending - repeat
            else if (meshReponse.status === 202) {
                console.log("[MeshGenModel:requestMeshGen] Pending");
                setTimeout(checkMeshStatus, 1000); // Repeat after 1 second
            }
            
            // Error
            else {
                console.error('Error:', response.message);
            }
        };

        checkMeshStatus();
    }

    async downloadMesh()
    {
        if (this.data.meshZipBlob === null) {
            console.log("[MeshGenModel:downloadMesh] No mesh to download");
            return;
        }

        let a = document.createElement('a');
        a.href = URL.createObjectURL(this.data.meshZipBlob);;
        a.download = 'mesh.zip';

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    }
}

export { MeshGenModel };