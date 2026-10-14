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
