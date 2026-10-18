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


def test_history_commit_undo_redo_and_discarding_redo_steps(session):
    assert session.state()["history"] == ["Imagem original"]
    assert session.state()["width"] == 3 and session.state()["height"] == 2

    before = session.version
    session.commit("A", matrix_of(20))
    assert session.current[0, 0] == 20 and session.version > before
    session.undo()
    assert session.current[0, 0] == 10
    session.redo()
    assert session.current[0, 0] == 20

    session.undo()
    session.commit("B", matrix_of(30))  # editar depois de desfazer descarta o passo refazível
    assert session.state()["history"] == ["Imagem original", "B"]


def test_reset_jump_and_state_without_image(session):
    session.commit("A", matrix_of(20))
    session.reset()
    assert np.array_equal(session.current, session.original)
    assert len(session.state()["history"]) == 2  # voltar à original mantém o histórico
    with pytest.raises(IndexError):
        session.jump_to(5)
    assert EditorSession().state()["has_image"] is False
