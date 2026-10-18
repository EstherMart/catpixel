import io

import numpy as np
from PIL import Image

from backend.model.image_io import encode_image, load_image, save_image
from backend.model.sampling import downscale_for_preview

SAMPLE = np.array([[0, 128, 255], [10, 20, 30]], dtype=np.uint8)


def test_images_are_saved_loaded_encoded_and_downscaled_for_preview(tmp_path):
    path = str(tmp_path / "copia.bmp")
    save_image(SAMPLE, path)
    assert np.array_equal(load_image(path), SAMPLE)  # BMP não perde pixels

    buffer = io.BytesIO()
    Image.new("RGB", (4, 3), (255, 0, 0)).save(buffer, format="PNG")
    buffer.seek(0)
    color = load_image(buffer)  # imagem colorida continua colorida: (altura, largura, R-G-B)
    assert color.shape == (3, 4, 3) and color.dtype == np.uint8 and color[0, 0].tolist() == [255, 0, 0]
    gray_buffer = io.BytesIO()
    Image.new("L", (4, 3), 7).save(gray_buffer, format="BMP")
    gray_buffer.seek(0)
    assert load_image(gray_buffer).shape == (3, 4)  # cinza continua 2D, mesmo salvo em BMP

    assert encode_image(SAMPLE, "PNG").startswith(b"\x89PNG")
    assert encode_image(SAMPLE, "BMP").startswith(b"BM")
    assert encode_image(SAMPLE, "JPEG").startswith(b"\xff\xd8")

    assert downscale_for_preview(np.zeros((10, 20), dtype=np.uint8), 640).shape == (10, 20)  # imagem pequena fica igual
    height, width = downscale_for_preview(np.zeros((1000, 2000), dtype=np.uint8), 640).shape
    assert max(height, width) <= 640
