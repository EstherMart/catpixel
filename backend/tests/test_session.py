import numpy as np
import pytest

from backend.session import EditorSession


def matrix_of(value):
    return np.full((2, 3), value, dtype=np.uint8)


@pytest.fixture
def session():
    session = EditorSession()
    session.open(matrix_of(10), "foto.jpg")
    return session


def test_open_creates_the_original_step(session):
    assert session.state()["history"] == ["Imagem original"]
    assert session.state()["width"] == 3 and session.state()["height"] == 2


def test_commit_undo_and_redo(session):
    session.commit("A", matrix_of(20))
    assert session.current[0, 0] == 20

    session.undo()
    assert session.current[0, 0] == 10

    session.redo()
    assert session.current[0, 0] == 20


def test_commit_after_undo_discards_the_redo_steps(session):
    session.commit("A", matrix_of(20))
    session.undo()
    session.commit("B", matrix_of(30))
    assert session.state()["history"] == ["Imagem original", "B"]


def test_reset_goes_back_to_the_original_but_keeps_history(session):
    session.commit("A", matrix_of(20))
    session.reset()
    assert np.array_equal(session.current, session.original)
    assert len(session.state()["history"]) == 2


def test_jump_to_invalid_step_fails(session):
    with pytest.raises(IndexError):
        session.jump_to(5)


def test_version_changes_on_every_modification(session):
    before = session.version
    session.commit("A", matrix_of(20))
    assert session.version > before


def test_state_without_image():
    assert EditorSession().state()["has_image"] is False
