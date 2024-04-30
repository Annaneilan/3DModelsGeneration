// import * as THREE from 'three';
// import * as JSZIP from 'jszip';

// import { MTLLoader } from 'MTLLoader';
// import { OBJLoader } from 'OBJLoader';
// import { OrbitControls } from 'OrbitControls';

import { MeshGenModel } from './model.js';
import { ImageGenController } from './image_gen.js';
import { MeshGenController } from './mesh_gen.js';

var model = new MeshGenModel("http://127.0.0.1:8000");
var imageGenController = new ImageGenController(model);
var meshGenController = new MeshGenController(model);

// Text example
// let meshLoaderHelper = new MeshLoader();
// meshLoaderHelper.loadMesh(
//     './MeshBachelor/mesh.obj',
//     './MeshBachelor/mesh.mtl',
//     './MeshBachelor/mesh_example2_0.png'
// );

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

async function unpackZip(zipFile) {
    let zip = await JSZip.loadAsync(zipFile);
    console.log(zip.files);
    return zip.files;
}

async function requestMeshGen() {
    const response = await fetch(SERVER_URL + '/mesh', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        }
    });

    const blob = await response.blob();
    const files = await unpackZip(blob);

    let meshObj = URL.createObjectURL(await files['mesh.obj'].async('blob'));
    let meshMtl = URL.createObjectURL(await files['mesh.mtl'].async('blob'));
    let meshTex = URL.createObjectURL(await files['mesh_0.png'].async('blob'));
    
    let ml = new MeshLoader();
    console.log("Loading mesh");
    ml.loadMesh(meshObj, meshMtl, meshTex);
}