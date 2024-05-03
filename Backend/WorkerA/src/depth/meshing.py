import numpy as np
from tqdm import tqdm
from typing import Tuple

import open3d as o3d
o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Error)

def create_pixel_vertice_mapping(
    mask: np.ndarray
) -> Tuple[np.ndarray, int]:
    grid = np.ones(mask.shape[:2], dtype=np.int32) * -1
    i = 0
    for y in range(mask.shape[0]):
        for x in range(mask.shape[1]):
            if mask[y, x]:
                grid[y, x] = i
                i += 1
    return grid, i

def create_mesh(
    img: np.ndarray,
    depth: np.ndarray,
    grid: np.ndarray,
    v_num: int,
    verbose: bool = False
) -> o3d.geometry.TriangleMesh:
    # Params
    scaler = np.max(grid.shape[:2])
    
    # Init vertices, triangles, uvs
    v = np.zeros((v_num, 3), dtype=np.float32)
    t = []
    t_uv = []
    
    for y in tqdm(range(grid.shape[0]), 'Triangulation', disable=not verbose):
        prev_block = False
        for x in range(grid.shape[1]):
            if grid[y, x] == -1:
                prev_block = False
                continue
            
            # Vertice coordinate
            v[grid[y, x]] = [x / scaler, -y / scaler, -depth[y, x]]
            
            if y == grid.shape[0] - 1:
                continue
            
            # Check available pixels
            bl = True
            if x == 0 or grid[y + 1, x - 1] == -1:
                bl = False
            
            b = True
            if grid[y + 1, x] == -1:
                b = False
            
            br = True
            if x == grid.shape[1] - 1 or grid[y + 1, x + 1] == -1:
                br = False
            
            r = True
            if x == grid.shape[1] - 1 or grid[y, x + 1] == -1:
                r = False
            
            # Add triangles
            if bl and b and not prev_block:
                t.append([grid[y, x], grid[y + 1, x - 1], grid[y + 1, x]])
                t_uv.append([x, y])
                t_uv.append([x - 1, y + 1])
                t_uv.append([x, y + 1])
            
            prev_block = False
            if b and br:
                t.append([grid[y, x], grid[y + 1, x], grid[y + 1, x + 1]])
                t_uv.append([x, y])
                t_uv.append([x, y + 1])
                t_uv.append([x + 1, y + 1])
                prev_block = True
                
            if r and br:
                t.append([grid[y, x], grid[y + 1, x + 1], grid[y, x + 1]])
                t_uv.append([x, y])
                t_uv.append([x + 1, y + 1])
                t_uv.append([x + 1, y])
                prev_block = True
                
            if r and b and not prev_block:
                t.append([grid[y, x], grid[y + 1, x], grid[y, x + 1]])
                t_uv.append([x, y])
                t_uv.append([x, y + 1])
                t_uv.append([x + 1, y])
                prev_block = True

    # To numpy
    t = np.array(t, dtype=np.int32)
    t_uv = np.array(t_uv, dtype=np.float32)
    
    # Normalize UV
    t_uv[:, 0] = t_uv[:, 0] / grid.shape[1]
    t_uv[:, 1] = (1 - t_uv[:, 1] / grid.shape[0])
    
    # Create mesh
    mesh = o3d.geometry.TriangleMesh(o3d.utility.Vector3dVector(v),
                                     o3d.utility.Vector3iVector(t))
    mesh.textures = [o3d.geometry.Image(img.copy()).flip_vertical()]
    mesh.triangle_material_ids = o3d.utility.IntVector(np.zeros(t.shape[0], dtype=np.int32))
    mesh.triangle_uvs = o3d.utility.Vector2dVector(t_uv)
    
    return mesh

def create_pc(
    image: np.ndarray,
    depth: np.ndarray,
    grid: np.ndarray,
    v_num: int,
    verbose: bool = False
) -> o3d.geometry.PointCloud:
    # Params
    scaler = np.max(grid.shape[:2])
    
    # Init vertices, triangles, uvs
    vertices = np.zeros((v_num, 3), dtype=np.float32)
    vertices_color = np.zeros((v_num, 3), dtype=np.float32)
    
    for y in tqdm(range(grid.shape[0]), 'PC Building', disable=not verbose):
        for x in range(grid.shape[1]):
            vi = grid[y, x]
            if vi == -1: continue
            vertices[vi] = [x / scaler, -y / scaler, -depth[y, x]]
            vertices_color[vi] = image[y, x] / 255.0
    
    pc = o3d.geometry.PointCloud()
    
    pc.points = o3d.utility.Vector3dVector(vertices)
    pc.colors = o3d.utility.Vector3dVector(vertices_color)
    pc.translate(-pc.get_center())
    
    return pc