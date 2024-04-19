import * as THREE from 'three';
import * as JSZIP from 'jszip';

import { MTLLoader } from 'MTLLoader';
import { OBJLoader } from 'OBJLoader';
import { OrbitControls } from 'OrbitControls';

// Model
////////////////////////////////////////////////////////////////

class Bus {
    constructor() {
        // Singleton
        if (Bus.instance) {
            return Bus.instance;
        }
        Bus.instance = this;

        this.image = null;
        this.depth = null;
        this.depthImage = null;

        this.mesh = null;
        
        this.listeners = {
            // Image
            onImageWillChange: [],
            onImageDidChange: [],
            
            // Depth
            onDepthDidChange: [],
            
            // Mesh
            onMeshWillChange: [],
            onMeshDidChange: []
        };
    }

    // Setters / Getters
    setImage(imageURL) {
        this.triggerEvent('onImageWillChange');
        this.image = imageURL;
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

// Init bus
var bus = new Bus();


// View
////////////////////////////////////////////////////////////////

// Update image on change
bus.addListener('onImageDidChange', () => {
    document.getElementById('generated-photo').src = Bus.instance.image;
});

// Delete old mesh
bus.addListener('onMeshWillChange', () => {
    // Remove old mesh
    if (Bus.instance.mesh) {
        scene.remove(Bus.instance.mesh);
    }
    //renderer.renderLists.dispose();
});

// Set new mesh
bus.addListener('onMeshDidChange', () => {
    scene.add(Bus.instance.mesh);
    animate();
});

const SERVER_URL = "http://127.0.0.1:8000"

var canvas = document.getElementById("meshCanvas");
var scene = new THREE.Scene();
var camera = new THREE.PerspectiveCamera(55, 800 / 550, 0.1, 1000);
var renderer = new THREE.WebGLRenderer({ canvas: canvas });
renderer.setSize(800, 550);
renderer.setClearColor(0x363a3e); 

camera.position.z = 2.5;

var controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; 
controls.dampingFactor = 0.05;
controls.screenSpacePanning = false;

// Utils
////////////////////////////////////////////////////////////////

// Facade mesh loader
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
                Bus.instance.setMesh(loadedMesh);
                console.log("Mesh set")
            });
        });
    }
}

// Text example
let meshLoaderHelper = new MeshLoader();
meshLoaderHelper.loadMesh(
    './MeshBachelor/mesh.obj',
    './MeshBachelor/mesh.mtl',
    './MeshBachelor/mesh_example2_0.png'
);

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}

document.addEventListener('DOMContentLoaded', function() {
    const inputPhoto = document.getElementById('input-photo');
    const generatedPhoto = document.getElementById('generated-photo');

    inputPhoto.addEventListener('change', function() {
        const file = this.files[0];

        if (file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                generatedPhoto.src = e.target.result;
            };

            reader.readAsDataURL(file);
        } else {
            generatedPhoto.src = 'placeholder.jpg'; 
        }
    });
});

document.addEventListener('DOMContentLoaded', function () {
    const downloadBtn = document.getElementById('download-photo');
    const generatedPhoto = document.getElementById('generated-photo');

    downloadBtn.addEventListener('click', function () {
        const url = generatedPhoto.src;
        const a = document.createElement('a');
        a.href = url;
        a.download = 'image.jpg';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    });
});

// Controller
////////////////////////////////////////////////////////////////

const generateImageButton = document.getElementById('generate-image');
generateImageButton.addEventListener('click', requestImageGen);

function requestImageGen() {
    // Get input elements
    const posPromptInput = document.getElementById('input-description')
    const negPromptInput = document.getElementById('without-description')

    // Request data
    const promptData = {
        prompt: posPromptInput.value,
        negative_prompt: negPromptInput.value
    }

    // Send request
    fetch(SERVER_URL + '/image', {
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
        const imgElement = document.getElementById('generated-photo');
        imgElement.src = imageUrl;
    })
    .catch(error => {
        console.error('Error fetching the image:', error);
    });
}

async function unpackZip(zipFile) {
    let zip = await JSZip.loadAsync(zipFile);
    console.log(zip.files);
    return zip.files;
}

const generateMeshButton = document.getElementById('generate-3d-model-btn');
generateMeshButton.addEventListener('click', requestMeshGen);

async function requestMeshGen() {
    const response = await fetch(SERVER_URL + '/mesh', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    })

    const blob = await response.blob();
    const files = await unpackZip(blob);

    let meshObj = URL.createObjectURL(await files['mesh.obj'].async('blob'));
    let meshMtl = URL.createObjectURL(await files['mesh.mtl'].async('blob'));
    let meshTex = URL.createObjectURL(await files['mesh_0.png'].async('blob'));
    
    let ml = new MeshLoader();
    console.log("Loading mesh");
    ml.loadMesh(meshObj, meshMtl, meshTex);
}