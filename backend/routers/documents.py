import os
import logging
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException
from models.schemas import DocumentResponse, DocumentChunksResponse
from utils.pdf_parser import extract_text_from_pdf, chunk_text, get_document_stats
from utils.embeddings import get_embeddings_batch, get_embedding
from utils.chroma_store import add_chunks, search, get_store_stats, delete_file_chunks, collection

logger = logging.getLogger("documents")

router = APIRouter(prefix="/documents", tags=["documents"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

MAX_FILE_SIZE_MB = 50


@router.post("/upload", response_model=DocumentChunksResponse)
async def upload_document(file: UploadFile = File(...)):
    logger.info(f"Upload request: {file.filename} ({file.content_type})")

    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")

    # Check file size before reading fully
    contents = await file.read()
    size_mb = len(contents) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        raise HTTPException(status_code=413, detail=f"File too large. Maximum size is {MAX_FILE_SIZE_MB}MB.")

    file_path = os.path.join(UPLOAD_DIR, file.filename)
    try:
        with open(file_path, "wb") as f:
            f.write(contents)
        logger.info(f"Saved {file.filename} ({size_mb:.1f}MB) to disk")
    except Exception as e:
        logger.error(f"Failed to save {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to save file. Please try again.")

    try:
        text = extract_text_from_pdf(file_path)
        if not text.strip():
            raise ValueError("PDF appears to be empty or image-only (no extractable text).")
        logger.info(f"Extracted {len(text)} characters from {file.filename}")
    except ValueError as e:
        os.remove(file_path)
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        os.remove(file_path)
        logger.error(f"PDF extraction failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Could not read PDF content. The file may be corrupted.")

    chunks = chunk_text(text, chunk_size=500, overlap=100)
    stats = get_document_stats(text, chunks)
    logger.info(f"Created {len(chunks)} chunks from {file.filename}")

    try:
        chunk_texts = [c["text"] for c in chunks]
        embeddings = get_embeddings_batch(chunk_texts)
        logger.info(f"Generated {len(embeddings)} embeddings for {file.filename}")
    except Exception as e:
        os.remove(file_path)
        logger.error(f"Embedding failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embeddings. Check your OpenAI API key.")

    try:
        add_chunks(chunks, embeddings, file.filename)
        logger.info(f"Indexed {file.filename} into ChromaDB successfully")
    except Exception as e:
        os.remove(file_path)
        logger.error(f"ChromaDB indexing failed for {file.filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to index document. Please try again.")

    return DocumentChunksResponse(
        success=True,
        filename=file.filename,
        message=f"Successfully processed and indexed {file.filename}",
        total_chunks=stats["total_chunks"],
        total_words=stats["total_words"],
        chunks=chunks
    )


@router.get("/list")
def list_documents():
    try:
        files = [f for f in os.listdir(UPLOAD_DIR) if f.lower().endswith(".pdf")]
        stats = get_store_stats()
        indexed = stats.get("files_indexed", [])

        result = []
        for f in files:
            chunks_in_db = 0
            if f in indexed:
                try:
                    res = collection.get(where={"filename": f}, include=["metadatas"])
                    chunks_in_db = len(res["ids"])
                except Exception:
                    pass
            result.append({
                "filename": f,
                "total_chunks": chunks_in_db,
                "indexed": f in indexed,
            })

        logger.info(f"Listed {len(result)} documents")
        return {"documents": result, "count": len(result)}
    except Exception as e:
        logger.error(f"Failed to list documents: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve document list.")


@router.delete("/{filename}")
def delete_document(filename: str):
    logger.info(f"Delete request: {filename}")
    file_path = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found.")

    try:
        os.remove(file_path)
        delete_file_chunks(filename)
        logger.info(f"Deleted {filename} from disk and ChromaDB")
        return {"success": True, "deleted_filename": filename}
    except Exception as e:
        logger.error(f"Failed to delete {filename}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete document.")


@router.get("/store/stats")
def store_stats():
    try:
        return get_store_stats()
    except Exception as e:
        logger.error(f"Failed to get store stats: {e}")
        raise HTTPException(status_code=500, detail="Could not retrieve store statistics.")