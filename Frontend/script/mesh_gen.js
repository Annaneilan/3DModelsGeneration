import * as THREE from 'three';
import { OrbitControls } from 'OrbitControls';

class MeshGenView {
    constructor(
        model,
        delegate
    ) {
        // Ref
        this.model = model;
        this.delegate = delegate;
        
        this.setupUI();
        this.setupScene();

        this.setupControls();
        this.subscribeToModel();

        console.log("MeshGenView initialized");
    }
    
    // Setup
    ////////////////////////////////////////////////////////////////

    setupUI() {
        this.image = document.getElementById('input-image');
        this.generateModelButton = document.getElementById('generate-3d-model-btn');
        this.downloadModelButton = document.getElementById('download-3d-model-btn');
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
        this.generateModelButton.addEventListener(
            'click',
            () => { this.delegate.onGenerateModelClick(); }
        );

        this.downloadModelButton.addEventListener(
            'click',
            () => { this.delegate.onDownloadModelClick(); }
        );
    }

    // Subscribe
    ////////////////////////////////////////////////////////////////

    subscribeToModel() {
        this.model.data.addListener('onImageDidChange', () => { this.updateImage(); });
        this.model.data.addListener('onMeshWillChange', () => { this.removeMeshFromScene(); });
        this.model.data.addListener('onMeshDidChange', () => { this.setMeshToScene(); });
    }

    // UI
    ////////////////////////////////////////////////////////////////

    updateImage() {
        console.log("[ImageGenView:updateImage]");
        this.image.src = this.model.data.image;
    }
    
    activateGenerateButton() {
        this.generateModelButton.disabled = false;
        this.generateModelButton.innerHTML = "Generate Model";
    }

    deactivateGenerateButton() {
        this.generateModelButton.disabled = true;
        this.generateModelButton.innerHTML = `
        <span class="spinner-border spinner-border-sm" aria-hidden="true"></span>
        <span role="status">Loading...</span>
        `;
    }

    removeMeshFromScene() {
        if (this.model.mesh) {
            this.scene.remove(this.model.mesh);
        }
        //renderer.renderLists.dispose();
        console.log("TODO: Dispose of old renders");
    }

    setMeshToScene() {
        console.log("[MeshGenView:setMeshToScene]");
        
        this.activateGenerateButton();
        
        this.scene.add(this.model.data.mesh);
        this.animate();
    }

    // Animate utility
    animate() {
        requestAnimationFrame(() => this.animate() );
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

    onGenerateModelClick() {
        console.log("[MeshGenController:onGenerateModelClick]")
        this.view.deactivateGenerateButton();

        // Request data
        // const promptData = {
        //     prompt: this.view.getImagePromptPositive(),
        //     negative_prompt: this.view.getImagePromptNegative()
        // }
        this.model.requestMeshGen();
    }
    
    onDownloadModelClick() {
        this.model.downloadMesh();
    }
}

export { MeshGenController, MeshGenView };