"""Estado da edição: a imagem aberta e o histórico de versões (desfazer e refazer)."""
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Step:
    label: str
    matrix: np.ndarray


class EditorSession:
    def __init__(self):
        self._steps: list[Step] = []
        self._index = -1
        self.name = ""
        self.version = 0  # muda a cada alteração; o navegador usa para não reaproveitar imagem antiga

    @property
    def has_image(self) -> bool:
        return self._index >= 0

    @property
    def current(self) -> np.ndarray:
        return self._steps[self._index].matrix

    @property
    def original(self) -> np.ndarray:
        return self._steps[0].matrix

    def open(self, matrix: np.ndarray, name: str) -> None:
        self._steps = [Step("Imagem original", matrix)]
        self._index = 0
        self.name = name
        self.version += 1

    def commit(self, label: str, matrix: np.ndarray) -> None:
        del self._steps[self._index + 1:]
        self._steps.append(Step(label, matrix))
        self._index += 1
        self.version += 1

    def jump_to(self, index: int) -> None:
        if not 0 <= index < len(self._steps):
            raise IndexError(index)
        self._index = index
        self.version += 1

    def undo(self) -> None:
        if self._index > 0:
            self.jump_to(self._index - 1)

    def redo(self) -> None:
        if self._index < len(self._steps) - 1:
            self.jump_to(self._index + 1)

    def reset(self) -> None:
        self.jump_to(0)

    def state(self) -> dict:
        if not self.has_image:
            return {"has_image": False, "version": self.version}
        height, width = self.current.shape
        return {
            "has_image": True,
            "version": self.version,
            "name": self.name,
            "width": width,
            "height": height,
            "history": [step.label for step in self._steps],
            "index": self._index,
        }
