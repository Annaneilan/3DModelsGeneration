import * as THREE from 'three';
import { OrbitControls } from 'OrbitControls';

class MeshGenView {
    constructor(
        model,
        controller
    ) {
        // Ref
        this.model = model;
        this.controller = controller;
        
        this.setupUI();
        this.setupScene();

        this.setupControls();
        this.subscribeToModel();

        console.log("MeshGenView initialized");
    }
    
    setupUI() {
        this.generateMeshButton = document.getElementById('generate-3d-model-btn');
    }

    setupScene() {
        this.canvas = document.getElementById("meshCanvas");
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(55, 800 / 550, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas });

        this.renderer.setSize(800, 550);
        this.renderer.setClearColor(0x363a3e); 

        this.camera.position.z = 2.5;

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true; 
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
    }

    setupControls() {
        //this.generateMeshButton.addEventListener('click', requestMeshGen);
    }

    subscribeToModel() {
        this.model.data.addListener('onMeshWillChange', () => { this.removeMeshFromScene });
        this.model.data.addListener('onMeshDidChange', () => { this.setMeshToScene });
    }

    removeMeshFromScene() {
        if (this.model.mesh) {
            this.scene.remove(this.model.mesh);
        }
        //renderer.renderLists.dispose();
        console.log("TODO: Dispose of old renders");
    }

    setMeshToScene() {
        this.scene.add(this.model.mesh);
        this.animate();
    }

    // Update UI
    animate() {
        requestAnimationFrame(this.animate);
        this.controls.update();
        this.renderer.render(this.scene, this.camera);
    }
}

class MeshGenController {
    constructor(model) {
        // Init
        this.model = model;
        this.view = new MeshGenView(model, this);

        console.log("MeshGenController initialized");
    }
    
    requestMeshGen() {
        // settings = this.view.get_settings();
        // this.model.requestMeshGen(settings);
    }
}

export { MeshGenController, MeshGenView };