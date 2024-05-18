import io
import os
import cv2
import numpy as np
from PIL import Image, ImageOps

def open_image(
    image_bytes: io.BytesIO,
    mode: str = "RGB"
) -> Image.Image:
    image = Image.open(image_bytes)
    image = ImageOps.exif_transpose(image)
    image = image.convert(mode)
    return image

def resize_with_aspect(
    image: Image.Image,
    size: int
) -> Image.Image:

    w, h = image.size
    aspect_ratio = w / h
    
    if w > h:
        new_size = (size, int(size / aspect_ratio))
    else:
        new_size = (int(size * aspect_ratio), size)
    
    image = image.resize(new_size, Image.LANCZOS)
    return image

def save_obj(pointnp_px3, facenp_fx3, fname):
    fol, na = os.path.split(fname)
    na, _ = os.path.splitext(na)

    with open(fname, 'w') as fid:
        for pidx, p in enumerate(pointnp_px3):
            pp = p
            fid.write('v %f %f %f\n' % (pp[0], pp[1], pp[2]))

        for i, f in enumerate(facenp_fx3):
            f1 = f + 1
            fid.write('f %d %d %d\n' % (f1[0], f1[1], f1[2]))

def save_obj_with_mtl(pointnp_px3, tcoords_px2, facenp_fx3, facetex_fx3, texmap_hxwx3, fname):
    fol, na = os.path.split(fname)
    na, _ = os.path.splitext(na)

    matname = '%s/%s.mtl' % (fol, na)
    fid = open(matname, 'w')
    fid.write('newmtl material_0\n')
    fid.write('Kd 1 1 1\n')
    fid.write('Ka 0 0 0\n')
    fid.write('Ks 0.4 0.4 0.4\n')
    fid.write('Ns 10\n')
    fid.write('illum 2\n')
    fid.write(f"map_Kd {na}_0.png\n")
    fid.close()
    ####

    fid = open(fname, 'w')
    fid.write('mtllib %s.mtl\n' % na)

    for pidx, p in enumerate(pointnp_px3):
        pp = p
        fid.write('v %f %f %f\n' % (pp[0], pp[1], pp[2]))

    for pidx, p in enumerate(tcoords_px2):
        pp = p
        fid.write('vt %f %f\n' % (pp[0], pp[1]))

    fid.write('usemtl material_0\n')
    for i, f in enumerate(facenp_fx3):
        f1 = f + 1
        f2 = facetex_fx3[i] + 1
        fid.write('f %d/%d %d/%d %d/%d\n' % (f1[0], f2[0], f1[1], f2[1], f1[2], f2[2]))
    fid.close()

    # save texture map
    lo, hi = 0, 1
    img = np.asarray(texmap_hxwx3, dtype=np.float32)
    img = (img - lo) * (255 / (hi - lo))
    img = img.clip(0, 255)
    mask = np.sum(img.astype(np.float32), axis=-1, keepdims=True)
    mask = (mask <= 3.0).astype(np.float32)
    kernel = np.ones((3, 3), 'uint8')
    dilate_img = cv2.dilate(img, kernel, iterations=1)
    img = img * (1 - mask) + dilate_img * mask
    img = img.clip(0, 255).astype(np.uint8)
    Image.fromarray(np.ascontiguousarray(img[::-1, :, :]), 'RGB').save(f'{fol}/{na}_0.png')