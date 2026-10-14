import io

import numpy as np
from PIL import Image

from backend.model.image_io import encode_image, load_image, save_image

SAMPLE = np.array([[0, 128, 255], [10, 20, 30]], dtype=np.uint8)


def test_save_and_load_bmp_keep_the_pixels(tmp_path):
    path = str(tmp_path / "copia.bmp")
    save_image(SAMPLE, path)
    assert np.array_equal(load_image(path), SAMPLE)


def test_load_converts_color_image_to_grayscale_matrix():
    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), (255, 0, 0)).save(buffer, format="PNG")
    buffer.seek(0)

    matrix = load_image(buffer)

    assert matrix.shape == (3, 4)
    assert matrix.dtype == np.uint8


def test_encode_image_produces_the_requested_format():
    assert encode_image(SAMPLE, "PNG").startswith(b"\x89PNG")
    assert encode_image(SAMPLE, "BMP").startswith(b"BM")
    assert encode_image(SAMPLE, "JPEG").startswith(b"\xff\xd8")
