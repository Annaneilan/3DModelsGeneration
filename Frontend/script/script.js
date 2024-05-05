import { MeshGenModel } from './model.js';
import { ImageGenController } from './image_gen.js';
import { MeshGenController } from './mesh_gen.js';

// Init
var model = new MeshGenModel("http://127.0.0.1:8000");
var imageGenController = new ImageGenController(model);
var meshGenController = new MeshGenController(model);

// async function unpackZip(zipFile) {
//     let zip = await JSZip.loadAsync(zipFile);
//     console.log(zip.files);
//     return zip.files;
// }

// async function requestMeshGen() {
//     const response = await fetch(SERVER_URL + '/mesh', {
//         method: 'POST',
//         headers: {
//             'Content-Type': 'application/json'
//         }
//     });

//     const blob = await response.blob();
//     const files = await unpackZip(blob);

//     let meshObj = URL.createObjectURL(await files['mesh.obj'].async('blob'));
//     let meshMtl = URL.createObjectURL(await files['mesh.mtl'].async('blob'));
//     let meshTex = URL.createObjectURL(await files['mesh_0.png'].async('blob'));
    
//     let ml = new MeshLoader();
//     console.log("Loading mesh");
//     ml.loadMesh(meshObj, meshMtl, meshTex);
// }