import { MeshGenModel } from './model.js';
import { ImageGenController } from './image_gen.js';
import { MeshGenController } from './mesh_gen.js';

// Init
const SERVER_URL = "http://127.0.0.1:8000"
//const SERVER_URL = "http://3.68.143.6:8000"

var model = new MeshGenModel(SERVER_URL);

//model.data.projectId = "0920c0c9-ef6e-4c7d-92aa-44cad14a53f8";

var imageGenController = new ImageGenController(model);
var meshGenController = new MeshGenController(model);