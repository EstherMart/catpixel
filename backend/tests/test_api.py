import base64
import io

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app import create_app
from backend.session import EditorSession


@pytest.fixture
def client():
    return TestClient(create_app(EditorSession()))


def png_bytes(color=(200, 200, 200), size=(8, 6)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color).save(buffer, format="PNG")
    return buffer.getvalue()


def photo_bytes(size=(60, 60)) -> bytes:
    noise = np.random.default_rng(2).integers(0, 256, size=size[::-1], dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(noise).save(buffer, format="PNG")
    return buffer.getvalue()


def open_sample(client):
    return client.post("/api/open", files={"file": ("foto.png", png_bytes(), "image/png")})


def open_photo(client):
    return client.post("/api/open", files={"file": ("foto.png", photo_bytes(), "image/png")})


def apply(client, op, params=None):
    return client.post("/api/apply", json={"op": op, "params": params or {}})


def mask_png(width, height, value=255) -> str:
    """Máscara de espectro (imagem cinza uniforme) em PNG codificado em base64, como o navegador envia."""
    buffer = io.BytesIO()
    Image.fromarray(np.full((height, width), value, dtype=np.uint8)).save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()


def current_pixels(client):
    return np.array(Image.open(io.BytesIO(client.get("/api/image").content)))


def test_actions_without_an_image_are_rejected(client):
    assert client.get("/api/state").json()["has_image"] is False
    for response in (client.get("/api/image"), apply(client, "negative"), client.get("/api/histogram"),
                     client.get("/api/steganography"), client.post("/api/undo")):
        assert response.status_code == 409


def test_open_and_save(client):
    state = open_sample(client).json()
    assert state["has_image"] is True and (state["width"], state["height"]) == (8, 6) and state["name"] == "foto.png"
    assert client.post("/api/open", files={"file": ("a.txt", b"texto", "text/plain")}).status_code == 400

    bmp = client.get("/api/save", params={"format": "bmp"})
    assert bmp.content.startswith(b"BM") and "foto_editada.bmp" in bmp.headers["content-disposition"]
    assert client.get("/api/save", params={"format": "jpg"}).content.startswith(b"\xff\xd8")
    assert client.get("/api/save", params={"format": "gif"}).status_code == 400


def test_apply_preview_history_and_invalid_requests(client):
    open_sample(client)
    state = apply(client, "threshold", {"limit": 250}).json()
    assert state["history"] == ["Imagem original", "Limiarização (250)"] and state["index"] == 1
    assert set(np.unique(current_pixels(client))) == {0}  # 200 < 250: tudo preto
    original = Image.open(io.BytesIO(client.get("/api/image", params={"which": "original"}).content))
    assert set(np.unique(np.array(original))) == {200}  # a original continua guardada

    preview = client.post("/api/preview", json={"op": "threshold", "params": {"limit": 1}})
    assert preview.status_code == 200 and preview.content.startswith(b"\x89PNG")
    assert client.get("/api/state").json()["history"] == ["Imagem original", "Limiarização (250)"]  # prévia não grava

    assert client.post("/api/undo").json()["index"] == 0
    assert client.post("/api/redo").json()["index"] == 1
    assert client.post("/api/reset").json()["index"] == 0

    assert apply(client, "threshold", {"limit": 999}).status_code == 422
    assert apply(client, "threshold", {}).status_code == 422
    assert apply(client, "nao-existe").status_code == 404


def test_point_operations_are_applied_recorded_and_validated(client):
    open_sample(client)
    for op, params, label in (
        ("negative", {}, "Negativo"),
        ("brightness", {"factor": 1.5}, "Brilho (x1.5)"),
        ("gamma", {"gamma": 0.5}, "Gama (0.5)"),
        ("log", {}, "Logaritmo"),
        ("piecewise", {"r1": 50, "s1": 10, "r2": 200, "s2": 240}, "Linear por partes (50,10) (200,240)"),
    ):
        assert apply(client, op, params).json()["history"][-1] == label

    assert apply(client, "brightness", {"factor": 1}).status_code == 200  # o navegador pode mandar 1 no lugar de 1.0
    for op, params in (("brightness", {"factor": "2"}), ("gamma", {"gamma": 0}), ("piecewise", {"r1": 1})):
        assert apply(client, op, params).status_code == 422


def test_histogram_equalization_convolution_spatial_filters_and_geometry(client):
    open_sample(client)  # 8x6, tudo em 200
    counts = client.get("/api/histogram").json()["counts"]
    assert len(counts) == 256 and counts[200] == 48 and sum(counts) == 48
    apply(client, "negative")
    assert client.get("/api/histogram").json()["counts"][55] == 48
    assert client.get("/api/histogram", params={"which": "original"}).json()["counts"][200] == 48

    open_photo(client)
    box = [[1] * 5 for _ in range(5)]
    for op, params, label in (
        ("equalize", {}, "Equalização de histograma"),
        ("convolution", {"kernel": box, "divisor": 25, "normalize": 0}, "Convolução 5x5"),
        ("mean", {"size": 5}, "Média 5x5"),
        ("gaussian", {"size": 3}, "Gaussiana 3x3"),
        ("median", {"size": 7}, "Mediana 7x7"),
        ("laplacian", {"diagonals": 1, "sharpen": 0}, "Laplaciano (só a imagem laplaciana)"),
        ("highboost", {"size": 3, "k": 2.5, "gaussian": 1}, "High-boost (k=2.5)"),
    ):
        state = apply(client, op, params).json()
        assert state["history"][-1] == label
        assert (state["width"], state["height"]) == (60, 60)  # filtros mantêm o tamanho

    identity = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    for op, params in (
        ("mean", {"size": 4}),
        ("median", {}),
        ("highboost", {"size": 3, "k": -1, "gaussian": 0}),
        ("laplacian", {"diagonals": 0}),
        ("convolution", {"kernel": [[1, 1], [1, 1]], "divisor": 1, "normalize": 0}),
        ("convolution", {"kernel": identity, "divisor": 0, "normalize": 0}),
        ("convolution", {"kernel": "x", "divisor": 1, "normalize": 0}),
    ):
        assert apply(client, op, params).status_code == 422

    open_sample(client)  # 8x6
    state = apply(client, "scale", {"scale_x": 2, "scale_y": 3, "method": 0}).json()
    assert state["history"][-1] == "Escala (x2, y3, vizinho mais próximo)"
    assert (state["width"], state["height"]) == (16, 18)  # escala muda o tamanho da imagem
    preview = client.post("/api/preview", json={"op": "scale", "params": {"scale_x": 2, "scale_y": 1, "method": 1}})
    assert preview.headers["x-result-size"] == "32x18"  # tamanho final, mesmo com a prévia reduzida
    state = apply(client, "rotate", {"angle": 90, "expand": 1, "method": 1}).json()
    assert state["history"][-1] == "Rotação (90°, bilinear)" and (state["width"], state["height"]) == (18, 16)
    state = apply(client, "rotate_pivot", {"angle": 30, "pivot_x": 0, "pivot_y": 100, "method": 1}).json()
    assert state["history"][-1] == "Rotação com pivô (30°, pivô 0%, 100%, bilinear)"
    assert (state["width"], state["height"]) == (18, 16)  # com pivô a tela não muda
    for op, params in (
        ("scale", {"scale_x": 0, "scale_y": 1, "method": 1}),
        ("scale", {"scale_x": 1, "scale_y": 1}),
        ("rotate", {"angle": "90", "expand": 1, "method": 1}),
        ("rotate_pivot", {"angle": 10, "pivot_x": 150, "pivot_y": 0, "method": 1}),
    ):
        assert apply(client, op, params).status_code == 422

    # domínio da frequência (a imagem agora tem 18x16)
    before = current_pixels(client)
    fft = client.get("/api/spectrum", params={"algorithm": 0})
    assert fft.content.startswith(b"\x89PNG") and fft.headers["x-spectrum-size"] == "32x16"  # FFT completa até potência de 2
    assert client.get("/api/spectrum", params={"algorithm": 1}).headers["x-spectrum-size"] == "18x16"  # DFT mantém o tamanho
    state = apply(client, "frequency_filter", {"mask": mask_png(32, 16), "algorithm": 0, "normalize": 0}).json()
    assert state["history"][-1] == "Filtro no espectro (FFT)" and (state["width"], state["height"]) == (18, 16)
    assert np.array_equal(current_pixels(client), before)  # máscara toda branca não muda a imagem
    state = apply(client, "frequency_filter", {"mask": mask_png(18, 16, 0), "algorithm": 1, "normalize": 0}).json()
    assert state["history"][-1] == "Filtro no espectro (DFT)" and not current_pixels(client).any()  # máscara preta zera
    for params in ({"mask": "isto não é base64", "algorithm": 0, "normalize": 0}, {"mask": mask_png(4, 4), "algorithm": 5}, {"algorithm": 0, "normalize": 0}):
        assert apply(client, "frequency_filter", params).status_code == 422

    big = io.BytesIO()
    Image.fromarray(np.zeros((1100, 1100), dtype=np.uint8)).save(big, format="PNG")
    client.post("/api/open", files={"file": ("grande.png", big.getvalue(), "image/png")})
    assert client.get("/api/spectrum", params={"algorithm": 1}).status_code == 422  # DFT ingênua não aceita imagem grande


def test_steganography(client):
    open_photo(client)
    assert client.get("/api/steganography").json() == {"found": False, "text": ""}

    state = apply(client, "hide_message", {"text": "Olá!"}).json()
    assert "Olá" not in " ".join(state["history"])  # o segredo não aparece no histórico
    assert client.get("/api/steganography").json() == {"found": True, "text": "Olá!"}

    for fmt, expected in (("bmp", True), ("jpg", False)):  # só o BMP guarda a mensagem
        saved = client.get("/api/save", params={"format": fmt}).content
        client.post("/api/open", files={"file": (f"s.{fmt}", saved, "application/octet-stream")})
        assert client.get("/api/steganography").json()["found"] is expected

    open_sample(client)  # 8x6: não cabe nem o cabeçalho
    for text in ("oi", "", 5):
        assert apply(client, "hide_message", {"text": text}).status_code == 422


def test_frontend_files_are_revalidated_by_the_browser(client):
    response = client.get("/")
    assert response.status_code == 200 and response.headers["cache-control"] == "no-cache"
    assert client.get("/api/state").headers.get("cache-control") != "no-cache"
