import fitz  # this is PyMuPDF — the import name is "fitz", not "pymupdf"
import os
from typing import List, Dict

def extract_text_from_pdf(file_path: str) -> str:
    """
    Opens a PDF file and extracts all text from every page.
    Returns one big string with all the text.
    """
    doc = fitz.open(file_path)  # open the PDF
    
    full_text = ""
    
    for page_num in range(len(doc)):  # loop through every page
        page = doc[page_num]          # get this page
        text = page.get_text()        # extract text from this page
        full_text += text             # add it to our growing string
    
    doc.close()
    return full_text


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    """
    Splits a long string into overlapping chunks.
    
    chunk_size: how many characters per chunk
    overlap: how many characters to repeat from the previous chunk
    
    Returns a list of dicts, each containing:
    - chunk_index: which chunk this is (0, 1, 2...)
    - text: the actual text content
    - char_start: where in the original text this chunk starts
    - char_end: where it ends
    """
    chunks = []
    start = 0
    chunk_index = 0
    
    while start < len(text):
        # Calculate where this chunk ends
        end = start + chunk_size
        
        # Extract the chunk
        chunk_text_content = text[start:end]
        
        # Skip empty or whitespace-only chunks
        if chunk_text_content.strip():
            chunks.append({
                "chunk_index": chunk_index,
                "text": chunk_text_content.strip(),
                "char_start": start,
                "char_end": min(end, len(text))
            })
            chunk_index += 1
        
        # Move forward by (chunk_size - overlap)
        # This is what creates the overlap — we go back by `overlap` characters
        start += chunk_size - overlap
    
    return chunks


def get_document_stats(text: str, chunks: List[Dict]) -> Dict:
    """
    Returns basic statistics about a document and its chunks.
    Useful for debugging and displaying info to the user.
    """
    return {
        "total_characters": len(text),
        "total_words": len(text.split()),
        "total_chunks": len(chunks),
        "avg_chunk_size": sum(len(c["text"]) for c in chunks) // len(chunks) if chunks else 0
    }