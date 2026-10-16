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


def open_sample(client):
    return client.post("/api/open", files={"file": ("foto.png", png_bytes(), "image/png")})


def test_actions_without_image_are_rejected(client):
    assert client.get("/api/image").status_code == 409
    assert client.post("/api/apply", json={"op": "threshold", "params": {"limit": 1}}).status_code == 409


def test_open_returns_the_state(client):
    state = open_sample(client).json()
    assert state["has_image"] is True
    assert (state["width"], state["height"]) == (8, 6)
    assert state["name"] == "foto.png"


def test_open_rejects_a_file_that_is_not_an_image(client):
    response = client.post("/api/open", files={"file": ("a.txt", b"texto", "text/plain")})
    assert response.status_code == 400


def test_apply_threshold_adds_a_history_step(client):
    open_sample(client)
    state = client.post("/api/apply", json={"op": "threshold", "params": {"limit": 128}}).json()
    assert state["history"] == ["Imagem original", "Limiarização (128)"]
    assert state["index"] == 1


def test_apply_threshold_makes_the_image_black_and_white(client):
    open_sample(client)
    client.post("/api/apply", json={"op": "threshold", "params": {"limit": 250}})
    image = Image.open(io.BytesIO(client.get("/api/image").content))
    assert set(np.unique(np.array(image))) == {0}


def test_invalid_parameters_and_operations_are_rejected(client):
    open_sample(client)
    assert client.post("/api/apply", json={"op": "threshold", "params": {"limit": 999}}).status_code == 422
    assert client.post("/api/apply", json={"op": "threshold", "params": {}}).status_code == 422
    assert client.post("/api/apply", json={"op": "nao-existe"}).status_code == 404


def test_preview_does_not_change_the_history(client):
    open_sample(client)
    response = client.post("/api/preview", json={"op": "threshold", "params": {"limit": 128}})
    assert response.status_code == 200
    assert response.content.startswith(b"\x89PNG")
    assert client.get("/api/state").json()["history"] == ["Imagem original"]


def test_undo_redo_and_reset(client):
    open_sample(client)
    client.post("/api/apply", json={"op": "threshold", "params": {"limit": 128}})
    assert client.post("/api/undo").json()["index"] == 0
    assert client.post("/api/redo").json()["index"] == 1
    assert client.post("/api/reset").json()["index"] == 0


def test_original_image_is_kept_after_editing(client):
    open_sample(client)
    client.post("/api/apply", json={"op": "threshold", "params": {"limit": 250}})
    original = Image.open(io.BytesIO(client.get("/api/image", params={"which": "original"}).content))
    assert set(np.unique(np.array(original))) != {0}


def test_save_downloads_bmp_and_jpg(client):
    open_sample(client)
    bmp = client.get("/api/save", params={"format": "bmp"})
    assert bmp.content.startswith(b"BM")
    assert "foto_editada.bmp" in bmp.headers["content-disposition"]

    jpg = client.get("/api/save", params={"format": "jpg"})
    assert jpg.content.startswith(b"\xff\xd8")

    assert client.get("/api/save", params={"format": "gif"}).status_code == 400


def photo_bytes(size=(60, 60)) -> bytes:
    noise = np.random.default_rng(2).integers(0, 256, size=size[::-1], dtype=np.uint8)
    buffer = io.BytesIO()
    Image.fromarray(noise).save(buffer, format="PNG")
    return buffer.getvalue()


@pytest.mark.parametrize("op, params, label", [
    ("negative", {}, "Negativo"),
    ("brightness", {"factor": 1.5}, "Brilho (x1.5)"),
    ("gamma", {"gamma": 0.5}, "Gama (0.5)"),
    ("log", {}, "Logaritmo"),
    ("piecewise", {"r1": 50, "s1": 10, "r2": 200, "s2": 240}, "Linear por partes (50,10) (200,240)"),
])
def test_point_operations_are_applied_and_recorded(client, op, params, label):
    open_sample(client)
    state = client.post("/api/apply", json={"op": op, "params": params}).json()
    assert state["history"][-1] == label


def test_decimal_parameters_accept_integers_and_reject_text(client):
    open_sample(client)
    assert client.post("/api/apply", json={"op": "brightness", "params": {"factor": 1}}).status_code == 200
    assert client.post("/api/apply", json={"op": "brightness", "params": {"factor": "2"}}).status_code == 422
    assert client.post("/api/apply", json={"op": "gamma", "params": {"gamma": 0}}).status_code == 422
    assert client.post("/api/apply", json={"op": "piecewise", "params": {"r1": 1}}).status_code == 422


def test_steganography_hide_and_reveal_through_the_api(client):
    client.post("/api/open", files={"file": ("foto.png", photo_bytes(), "image/png")})
    assert client.get("/api/steganography").json() == {"found": False, "text": ""}

    state = client.post("/api/apply", json={"op": "hide_message", "params": {"text": "Olá!"}}).json()
    assert "Olá" not in " ".join(state["history"])  # o segredo não aparece no histórico
    assert client.get("/api/steganography").json() == {"found": True, "text": "Olá!"}


def test_steganography_survives_saving_as_bmp_but_not_as_jpg(client):
    client.post("/api/open", files={"file": ("foto.png", photo_bytes(), "image/png")})
    client.post("/api/apply", json={"op": "hide_message", "params": {"text": "segredo"}})

    for fmt, expected in (("bmp", True), ("jpg", False)):
        saved = client.get("/api/save", params={"format": fmt}).content
        client.post("/api/open", files={"file": (f"s.{fmt}", saved, "application/octet-stream")})
        assert client.get("/api/steganography").json()["found"] is expected
        client.post("/api/open", files={"file": ("foto.png", photo_bytes(), "image/png")})
        client.post("/api/apply", json={"op": "hide_message", "params": {"text": "segredo"}})


def test_steganography_rejects_empty_text_and_messages_that_do_not_fit(client):
    open_sample(client)  # 8x6: não cabe nem o cabeçalho
    assert client.post("/api/apply", json={"op": "hide_message", "params": {"text": "oi"}}).status_code == 422
    assert client.post("/api/apply", json={"op": "hide_message", "params": {"text": ""}}).status_code == 422
    assert client.post("/api/apply", json={"op": "hide_message", "params": {"text": 5}}).status_code == 422


def test_steganography_without_image_is_rejected(client):
    assert client.get("/api/steganography").status_code == 409


def test_histogram_endpoint_counts_every_pixel(client):
    open_sample(client)  # 8x6, todo em 200
    counts = client.get("/api/histogram").json()["counts"]
    assert len(counts) == 256 and counts[200] == 48 and sum(counts) == 48
    assert client.get("/api/histogram", params={"which": "original"}).status_code == 200


def test_histogram_follows_the_current_image(client):
    open_sample(client)
    client.post("/api/apply", json={"op": "negative", "params": {}})
    assert client.get("/api/histogram").json()["counts"][55] == 48
    assert client.get("/api/histogram", params={"which": "original"}).json()["counts"][200] == 48


def test_histogram_without_image_is_rejected(client):
    assert client.get("/api/histogram").status_code == 409


def test_equalize_is_applied_and_recorded(client):
    client.post("/api/open", files={"file": ("foto.png", photo_bytes(), "image/png")})
    state = client.post("/api/apply", json={"op": "equalize", "params": {}}).json()
    assert state["history"][-1] == "Equalização de histograma"


def test_convolution_is_applied_and_keeps_the_size(client):
    open_sample(client)
    kernel = [[1] * 5 for _ in range(5)]
    state = client.post(
        "/api/apply", json={"op": "convolution", "params": {"kernel": kernel, "divisor": 25, "normalize": 0}}
    ).json()
    assert state["history"][-1] == "Convolução 5x5"
    assert (state["width"], state["height"]) == (8, 6)


def test_convolution_rejects_bad_parameters(client):
    open_sample(client)
    ok = [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
    for params in (
        {"kernel": [[1, 1], [1, 1]], "divisor": 1, "normalize": 0},
        {"kernel": "x", "divisor": 1, "normalize": 0},
        {"kernel": ok, "divisor": 0, "normalize": 0},
        {"kernel": ok, "normalize": 0},
        {"divisor": 1, "normalize": 0},
    ):
        assert client.post("/api/apply", json={"op": "convolution", "params": params}).status_code == 422
