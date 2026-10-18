import io

import numpy as np
from PIL import Image

from backend.model.image_io import encode_image, load_image, save_image

SAMPLE = np.array([[0, 128, 255], [10, 20, 30]], dtype=np.uint8)


def test_images_are_saved_loaded_and_encoded_as_grayscale_matrices(tmp_path):
    path = str(tmp_path / "copia.bmp")
    save_image(SAMPLE, path)
    assert np.array_equal(load_image(path), SAMPLE)  # BMP não perde pixels

    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), (255, 0, 0)).save(buffer, format="PNG")
    buffer.seek(0)
    color = load_image(buffer)  # imagem colorida vira matriz 2D uint8
    assert color.shape == (3, 4) and color.dtype == np.uint8

    assert encode_image(SAMPLE, "PNG").startswith(b"\x89PNG")
    assert encode_image(SAMPLE, "BMP").startswith(b"BM")
    assert encode_image(SAMPLE, "JPEG").startswith(b"\xff\xd8")
