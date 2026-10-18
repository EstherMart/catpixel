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


def test_session_history(session):
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

    session.commit("C", matrix_of(40))
    session.reset()
    assert np.array_equal(session.current, session.original)
    assert len(session.state()["history"]) == 3  # voltar à original mantém o histórico
    with pytest.raises(IndexError):
        session.jump_to(5)
    assert EditorSession().state()["has_image"] is False
