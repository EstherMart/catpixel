"""API do CatPixel. Também serve o front-end, então um único comando abre o programa."""
import io
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, Response, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import UnidentifiedImageError
from pydantic import BaseModel, Field

from backend.model.color import channel_histograms, intensity
from backend.model.frequency import DFT, FFT, spectrum_image, timed_spectrum
from backend.model.image_io import encode_image, load_image
from backend.model.sampling import downscale_for_preview
from backend.model.steganography import reveal_message
from backend.operations import result_shape, run_operation
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

    @app.middleware("http")
    async def revalidate_frontend_files(request, call_next):
        """Os arquivos da interface mudam durante o desenvolvimento: o navegador deve conferir a cada carga."""
        response = await call_next(request)
        if not request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-cache"
        return response

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
        # a prévia é reduzida; este cabeçalho diz o tamanho que o resultado final terá, para a tela
        # exibir a prévia no quadro certo quando a operação muda o tamanho (escala, rotação)
        try:
            height, width = result_shape(request.op, session.current.shape[:2], request.params)
        except ValueError as error:  # a prévia coube, mas a imagem inteira ficaria grande demais
            raise HTTPException(422, str(error))
        headers = {**NO_CACHE, "X-Result-Size": f"{width}x{height}"}
        return Response(encode_image(result, "PNG"), media_type="image/png", headers=headers)

    @app.post("/api/apply")
    def apply(request: OperationRequest):
        require_image()
        label, result = run(request, session.current)
        session.commit(label, result)
        return session.state()

    @app.get("/api/histogram")
    def histogram(which: str = "current"):
        require_image()
        matrix = session.original if which == "original" else session.current
        counts = channel_histograms(matrix)
        # "counts" é sempre a intensidade (o próprio cinza, numa imagem em cinza); "channels" só existe em imagem colorida
        return {"counts": counts["i"], "channels": {name: counts[name] for name in "rgb"} if matrix.ndim == 3 else None}

    @app.get("/api/spectrum")
    def spectrum(algorithm: int = 0):
        """Imagem do espectro (deslocado, em escala logarítmica) da imagem atual, para a pessoa editar."""
        require_image()
        try:
            values, seconds = timed_spectrum(intensity(session.current), DFT if algorithm else FFT)  # em cor, a intensidade
        except ValueError as error:
            raise HTTPException(422, str(error))
        image = spectrum_image(values)
        headers = {**NO_CACHE, "X-Spectrum-Size": f"{image.shape[1]}x{image.shape[0]}", "X-Seconds": f"{seconds:.2f}"}
        return Response(encode_image(image, "PNG"), media_type="image/png", headers=headers)

    @app.get("/api/steganography")
    def reveal():
        """Lê a mensagem escondida na imagem inteira (nunca na prévia reduzida)."""
        require_image()
        text = reveal_message(session.current)
        return {"found": text is not None, "text": text or ""}

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
