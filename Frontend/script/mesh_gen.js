import * as THREE from 'three';
import { OrbitControls } from 'OrbitControls';
import { MeshGenParams } from './entities.js';

class MeshGenParamView {
    constructor(formDivId="mesg-gen-params") {
        this.formDiv = document.getElementById(formDivId);
        this.setupUI();
    }

    setupUI() {
        this.formDiv.querySelectorAll('.btn.option').forEach(button => {
            button.addEventListener('click', function() {
                let siblings = this.parentNode.querySelectorAll('.btn.option');
                siblings.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
            });
        });
    }

    getSelectedOptions() {
        let result = new MeshGenParams(
            this.formDiv.querySelector('#gen-perspective-btn').classList.contains('active'),
            this.formDiv.querySelector('#gen-textured-btn').classList.contains('active'),
        );
        return result;
    }
}

class MeshGenView {
    constructor(
        model,
        delegate
    ) {
        // Ref
        this.model = model;
        this.delegate = delegate;
        
        this.setupUI();

        this.setupControls();
        this.subscribeToModel();

        console.log("MeshGenView initialized");
    }
    
    // Setup
    ////////////////////////////////////////////////////////////////

    setupUI() {
        this.setupUIElements();
        this.setupUIScene();
        this.meshGenParamsView = new MeshGenParamView("gen-params");
    }

    setupUIElements() {
        this.image = document.getElementById('input-image');
        this.generateModelButton = document.getElementById('generate-3d-model-btn');
        this.downloadModelButton = document.getElementById('download-3d-model-btn');

        this.canvas = document.getElementById("meshCanvas");
    }

    setupUIScene() {
        this.scene = new THREE.Scene();
        this.camera = new THREE.PerspectiveCamera(55, 800 / 470, 0.1, 1000);
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas });

        this.renderer.setSize(800, 470);
        this.renderer.setClearColor(0x363a3e); 

        this.camera.position.z = 2.5;

        this.controls = new OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true; 
        this.controls.dampingFactor = 0.05;
        this.controls.screenSpacePanning = false;
        
        // Add lights
        var ambientLight = new THREE.AmbientLight(0xffffff, 0.5);
        this.scene.add(ambientLight);

        //var directionalLight = new THREE.DirectionalLight(0xffffff, 0.5);
        //directionalLight.position.set(1, 1, 1);
        //this.scene.add(directionalLight);
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

        this.model.addListener('onMeshRequestFailed', () => { this.activateGenerateButton(); });
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
        let oldMesh = this.model.data.mesh;
        if (oldMesh) {
            var selectedObject = this.scene.getObjectByName(oldMesh.name);
            this.scene.remove(selectedObject);
        }
        //this.renderer.renderLists.dispose();
        //this.animate();
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

        // Update UI 
        this.view.deactivateGenerateButton();
        
        // Get selected options
        let meshGenParams = this.view.meshGenParamsView.getSelectedOptions();
        
        console.log(meshGenParams);

        // Request generation
        this.model.requestMeshGen(meshGenParams);
    }
    
    onDownloadModelClick() {
        this.model.downloadMesh();
    }
}

export { MeshGenController, MeshGenView };