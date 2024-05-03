from PIL import Image

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