"""API do CatPixel. Também serve o front-end, então um único comando abre o programa."""
import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import UnidentifiedImageError
from pydantic import BaseModel, Field

from backend.model.image_io import encode_image, load_image
from backend.model.sampling import downscale_for_preview
from backend.operations import run_operation
from backend.session import EditorSession

ROOT = Path(__file__).resolve().parent.parent
PREVIEW_MAX_SIDE = 640
NO_CACHE = {"Cache-Control": "no-store"}
SAVE_FORMATS = {
    "bmp": ("BMP", "image/bmp", ".bmp"),
    "jpg": ("JPEG", "image/jpeg", ".jpg"),
}


class OperationRequest(BaseModel):
    op: str
    params: dict[str, Any] = Field(default_factory=dict)


def create_app(session: EditorSession | None = None) -> FastAPI:
    session = session or EditorSession()
    app = FastAPI(title="CatPixel")

    def require_image() -> None:
        if not session.has_image:
            raise HTTPException(409, "Abra uma imagem primeiro.")

    def run(request: OperationRequest, matrix):
        try:
            return run_operation(request.op, matrix, request.params)
        except KeyError:
            raise HTTPException(404, f"Operação desconhecida: {request.op}")
        except ValueError as error:
            raise HTTPException(422, str(error))

    @app.get("/api/state")
    def get_state():
        return session.state()

    @app.post("/api/open")
    async def open_image(file: UploadFile):
        try:
            matrix = load_image(io.BytesIO(await file.read()))
        except (UnidentifiedImageError, OSError):
            raise HTTPException(400, "O arquivo não é uma imagem válida.")
        session.open(matrix, file.filename or "imagem")
        return session.state()

    @app.get("/api/image")
    def get_image(which: str = "current"):
        require_image()
        matrix = session.original if which == "original" else session.current
        return Response(encode_image(matrix, "PNG"), media_type="image/png", headers=NO_CACHE)

    @app.post("/api/preview")
    def preview(request: OperationRequest):
        require_image()
        small = downscale_for_preview(session.current, PREVIEW_MAX_SIDE)
        _, result = run(request, small)
        return Response(encode_image(result, "PNG"), media_type="image/png", headers=NO_CACHE)

    @app.post("/api/apply")
    def apply(request: OperationRequest):
        require_image()
        label, result = run(request, session.current)
        session.commit(label, result)
        return session.state()

    @app.post("/api/undo")
    def undo():
        require_image()
        session.undo()
        return session.state()

    @app.post("/api/redo")
    def redo():
        require_image()
        session.redo()
        return session.state()

    @app.post("/api/reset")
    def reset():
        require_image()
        session.reset()
        return session.state()

    @app.post("/api/jump/{index}")
    def jump(index: int):
        require_image()
        try:
            session.jump_to(index)
        except IndexError:
            raise HTTPException(404, "Passo inexistente no histórico.")
        return session.state()

    @app.get("/api/save")
    def save(format: str = "bmp"):
        require_image()
        if format not in SAVE_FORMATS:
            raise HTTPException(400, "Formato inválido. Use bmp ou jpg.")
        pillow_format, media_type, extension = SAVE_FORMATS[format]
        filename = f"{Path(session.name).stem}_editada{extension}"
        return Response(
            encode_image(session.current, pillow_format),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{filename}"', **NO_CACHE},
        )

    app.mount("/assets", StaticFiles(directory=ROOT / "assets"), name="assets")
    app.mount("/", StaticFiles(directory=ROOT / "frontend", html=True), name="frontend")
    return app


app = create_app()
