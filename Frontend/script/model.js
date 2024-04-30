import * as THREE from 'three';
import { MTLLoader } from 'MTLLoader';
import { OBJLoader } from 'OBJLoader';

class MeshLoader {
    constructor() {
        this.materialLoader = new MTLLoader();
        this.meshLoader = new OBJLoader();
        this.textureLoader = new THREE.TextureLoader();
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
                console.log("Mesh loaded")
                loadedMesh.position.set(-0.5, 0.5, 0);
                
                var texture = this.textureLoader.load(textureURL);
                console.log("Texture loaded")
                var material = new THREE.MeshBasicMaterial({ map: texture });

                loadedMesh.traverse((node) => {
                    if (node instanceof THREE.Mesh) {
                        node.material = material;
                    }
                });
        
                console.log("Setting the mesh");
                MeshGenModel.instance.setMesh(loadedMesh);
                console.log("Mesh set")
            });
        });
    }
}

class MeshGenData {
    constructor() {
        this.image = null;
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
    setImage(image) {
        this.triggerEvent('onImageWillChange');
        this.image = image;
        this.triggerEvent('onImageDidChange');
    }

    setMesh(mesh) {
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
        this.triggerEvent('onMeshDidChange');
    }

    addListener(event, callback) {
        if (this.listeners[event]) {
            this.listeners[event].push(callback);
        } else {
            console.warn(`No event named ${event} found.`);
        }
    }

    triggerEvent(event) {
        console.log("Triggering event: " + event)

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
        this.meshLoader = new MeshLoader();

        console.log("MeshGenModel initialized");
    }

    requestImageGen(promptData) {
        fetch(this.server_url + '/image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(promptData)
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('HTTP error! Status: ${response.status}');
            }
            return response.blob(); // Process the response as Blob
        })
        .then(blob => {
            const imageUrl = URL.createObjectURL(blob);
            this.data.setImage(imageUrl);
        })
        .catch(error => {
            console.error('Error fetching the image:', error);
        });
    }

    requestMeshGen(settings) {

    }
}

export { MeshGenModel };