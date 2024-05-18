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

    async loadMeshFromZip(
        zipFile,
        textured = false
    ) {
        // Unzip
        let zip = await JSZip.loadAsync(zipFile);
        let files = await zip.files;

        // Get urls
        let meshObj = URL.createObjectURL(await files['mesh.obj'].async('blob'));

        if (textured) {
            let meshMtl = URL.createObjectURL(await files['mesh.mtl'].async('blob'));
            let meshTex = URL.createObjectURL(await files['mesh_0.png'].async('blob'));
            this.loadTexturedMesh(meshObj, meshMtl, meshTex);
        } else {
            this.loadMesh(meshObj);
        }
    }

    loadMesh(meshURL) {
        this.meshLoader.load(meshURL, (loadedMesh) => {
            console.log("Mesh loaded")
            var mesh = loadedMesh;
            mesh.name = "mesh";
            //mesh.position.set(-0.5, 0.5, 0);
            this.onMeshLoaded(mesh);
        });
    }

    loadTexturedMesh(
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
                mesh.name = "mesh";
                console.log("Mesh loaded")
                
                var texture = this.textureLoader.load(textureURL);
                console.log("Texture loaded")
                var material = new THREE.MeshBasicMaterial({ map: texture });

                mesh.traverse((node) => {
                    if (node instanceof THREE.Mesh) {
                        node.material = material;
                    }
                });
                //mesh.position.set(-0.5, 0.5, 0);
                this.onMeshLoaded(mesh);
            });
        });
    }
}

class MeshGenData {
    constructor() {
        this.projectId = null;

        this.image = null;
        this.meshZipBlob = null;

        this.mesh = null;
        
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
    setProjectId(projectId) {
        console.log("[MeshGenData:setProjectId]");
        this.projectId = projectId;
    }

    setImage(image) {
        console.log("[MeshGenData:setImage]");
        this.triggerEvent('onImageWillChange');
        
        this.image = image;

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

        // Events
        this.listeners = {
            onImageRequestFailed: [],
            onMeshRequestFailed: [],
        };
    }

    addListener(event, callback) {
        console.log("[MeshGenModel:addListener] Adding listener for event: " + event);

        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        } else {
            console.warn(`No event named ${event} found.`);
        }
    }

    triggerEvent(event) {
        console.log("[MeshGenModel:triggerEvent] Event: " + event);

        if (this.listeners[event]) {
            this.listeners[event].forEach(callback => callback());
        }
    }

    async uploadImage() {
        console.log("[MeshGenModel:uploadImage] Uploading image");
        
        if (this.data.image === null) {
            console.log("[MeshGenModel:uploadImage] No image to upload");
            return;
        }
        
        let imageBlob = await fetch(this.data.image).then(r => r.blob());
        const response = await fetch(this.server_url + '/image', {
            method: "PUT",
            headers: {
                'Content-Type': 'application/image'
            },
            body: imageBlob
        });
        console.log("[MeshGenModel:uploadImage] Response:", response);

        if (response.ok) {
            const responseData = await response.json();
            this.data.setProjectId(responseData.project_id);
            return true;
        } else {
            return false;
        }
    }

    async requestImageGen(promptData) {
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
            const projectId = responseData.project_id;

            // Set image id
            this.data.projectId = projectId;

            // Function to repeatedly check the status of the image
            const checkImageStatus = async () => {
                console.log("[MeshGenModel:requestImageGen] Checking image status");

                const imageResponse = await fetch(this.server_url + `/image/${projectId}`);
                
                // Image is ready
                if (imageResponse.status === 200) {
                    console.log("[MeshGenModel:requestImageGen] Image is ready");

                    // Check if requested id matches the response
                    if (projectId === this.data.projectId) {
                        const imageBlob = await imageResponse.blob();
                        const imageUrl = URL.createObjectURL(imageBlob);
                        this.data.setImage(imageUrl);
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
                    this.triggerEvent('onImageRequestFailed');
                }
            };

            // Start checking image status
            checkImageStatus();

        //} catch (error) {
        //    console.error('Error:', error.message);
        //}
    }

    async requestMeshGen(genParams) {
        //try {
        if (this.data.image === null) {
            console.log("[MeshGenModel:requestMeshGen] No image to generate mesh from");
        
        } else if (this.data.projectId === null) {
            console.log("[MeshGenModel:requestMeshGen] No project id, uploading image");

            let uploadingResult = await this.uploadImage();
            if (!uploadingResult) {
                console.error("[MeshGenModel:requestMeshGen] Failed to upload image");
                return;
            }
        }
        
        // Request object
        let meshGenerationParams = {
            project_id: this.data.projectId,
            perspective: genParams.perspective,
            textured: genParams.textured,
        }
        console.log(meshGenerationParams);

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
    
        //} catch (error) {
        //    console.error('Error:', error.message);
        //}
        const projectId = this.data.projectId;

        // Function to repeatedly check the status of the mesh generation task
        const checkMeshStatus = async () => {
            console.log("[MeshGenModel:requestMeshGen] Checking mesh status");
            
            // GET mesh with query params
            const queryParams = new URLSearchParams({
                perspective: genParams.perspective,
                textured: genParams.textured,
            });

            const meshReponse = await fetch(
                this.server_url + `/model/${projectId}?${queryParams}`, {
                method: "GET",
            });
            
            // Image is ready
            if (meshReponse.status === 200) {
                console.log("[MeshGenModel:requestMeshGen] Mesh is ready");

                // Check if requested id matches the response
                if (projectId === this.data.projectId) {
                    let meshZipBlob = await meshReponse.blob();

                    this.data.setMeshZip(meshZipBlob);
                    this.meshLoader.loadMeshFromZip(meshZipBlob, meshGenerationParams.textured);
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
                this.triggerEvent('onMeshRequestFailed');
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