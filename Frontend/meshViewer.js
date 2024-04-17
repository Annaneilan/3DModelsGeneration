const imports = {
    "three": "https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.module.js",
    "MTLLoader": "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/loaders/MTLLoader.js",
    "OBJLoader": "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/loaders/OBJLoader.js",
    "OrbitControls": "https://cdn.jsdelivr.net/npm/three@0.128.0/examples/jsm/controls/OrbitControls.js"
};


import * as THREE from 'three';
import { MTLLoader } from 'MTLLoader';
import { OBJLoader } from 'OBJLoader';
import { OrbitControls } from 'OrbitControls';

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

var mesh; 

var materialLoader = new MTLLoader();
var meshLoader = new OBJLoader();

materialLoader.load('./MeshBachelor/mesh.mtl', function (materials) {
    materials.preload();
    meshLoader.setMaterials(materials);
    meshLoader.load('./MeshBachelor/mesh.obj', function (loadedMesh) {
        mesh = loadedMesh; 
        
        var textureLoader = new THREE.TextureLoader();
        var texture = textureLoader.load('./MeshBachelor/mesh_example2_0.png');
        var material = new THREE.MeshBasicMaterial({ map: texture });
        mesh.traverse(function (node) {
            if (node instanceof THREE.Mesh) {
                node.material = material;
            }
        });
        mesh.position.set(-0.5, 0.5, 0);
        scene.add(mesh);
        animate();
    });
});

function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
}