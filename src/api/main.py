"""FastAPI — point d'entrée de l'API CR de Chantier."""

import io
import json
import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

# Permet l'import de src.pipeline depuis la racine du projet
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.pipeline import (  # noqa: E402
    MOCK_CR,
    MOCK_TRANSCRIPTION,
    export_pdf,
    export_word,
    normalize_cr,
    structure_cr,
    transcribe_audio,
)

app = FastAPI(title="CR Chantier API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class StructureRequest(BaseModel):
    transcription: str
    projet: str = "Projet"


class ExportRequest(BaseModel):
    cr: dict
    projet: str = "Projet"


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Upload audio → transcription texte via faster-whisper (local)."""
    suffix = Path(audio.filename or "audio.mp3").suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await audio.read())
        tmp_path = tmp.name

    try:
        transcription = transcribe_audio(tmp_path)
    except Exception as e:
        raise HTTPException(500, f"Erreur transcription : {e}") from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    return {"transcription": transcription, "mock": False}


@app.post("/api/structure")
async def structure(req: StructureRequest):
    """Transcription + nom projet → CR structuré JSON."""
    mistral_key = os.environ.get("MISTRAL_API_KEY")
    use_mock = not mistral_key or not req.transcription.strip()
    try:
        cr = structure_cr(req.transcription, req.projet, use_mock=use_mock)
    except Exception as e:
        raise HTTPException(500, f"Erreur structuration : {e}") from e
    return cr


@app.post("/api/export")
async def export(req: ExportRequest):
    """CR JSON + nom projet → fichier Word (.docx)."""
    with tempfile.NamedTemporaryFile(suffix=".docx", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        export_word(req.cr, req.projet, tmp_path)
        docx_bytes = Path(tmp_path).read_bytes()
    except Exception as e:
        raise HTTPException(500, f"Erreur export Word : {e}") from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    safe_name = req.projet.replace(" ", "_").replace("/", "-")
    filename = f"CR_Chantier_{safe_name}.docx"
    return StreamingResponse(
        io.BytesIO(docx_bytes),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.post("/api/export/pdf")
async def export_to_pdf(req: ExportRequest):
    """CR JSON + nom projet → fichier PDF."""
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        export_pdf(req.cr, req.projet, tmp_path)
        pdf_bytes = Path(tmp_path).read_bytes()
    except Exception as e:
        raise HTTPException(500, f"Erreur export PDF : {e}") from e
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    safe_name = req.projet.replace(" ", "_").replace("/", "-")
    filename = f"CR_Chantier_{safe_name}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
