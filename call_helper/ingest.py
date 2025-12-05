# ingest.py
# Установка зависимостей:
# pip install pymupdf tiktoken supabase openai tqdm python-dotenv
#
# Используется PyMuPDF для точного извлечения текста по страницам
# Kazakhtelecom.pdf: chunking по страницам (1 страница = 1 чанк)
# 
# Примечание: PyMuPDF используется для извлечения текста из PDF

import os, uuid, re
import tiktoken
import fitz  # PyMuPDF
from supabase import create_client, Client
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv

# ---- Load environment
load_dotenv(find_dotenv(usecwd=True))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

# ---- Config
KAZAKHTELECOM_PDF = "Kazakhtelecom.pdf"

KAZAKHTELECOM_DOC_ID = "kazakhtelecom-v1"     # keep this STABLE to avoid duplicates

EMBED_MODEL = "text-embedding-3-small"  # 1536 dims -> matches your table
BATCH_EMBED = 100
BATCH_INSERT = 50  # Reduced to avoid timeout issues

# Chunking params for Kazakhtelecom PDF (1 page = 1 chunk)
KAZAKHTELECOM_MAX_TOKENS = 8000      # max tokens per chunk (fit full pages)
KAZAKHTELECOM_MIN_TOKENS = 50

enc = tiktoken.get_encoding("cl100k_base")  # matches OpenAI embeddings tokenizer

def clean_text(t: str, preserve_paragraphs: bool = True) -> str:
    # normalize whitespace and fix hyphenation across line breaks
    # For structural chunking, preserve paragraph breaks (double newlines)
    t = t.replace("\r", " ")
    t = re.sub(r"-\s*\n\s*", "", t)     # join "nutri-\n tion" => "nutrition"
    
    # Remove page numbers from the beginning (format: "54 55" or "54" at start)
    # This is common in PDFs where page numbers appear at the start
    t = re.sub(r'^\s*\d+\s+\d+\s+', '', t)  # Remove "54 55 " at start
    t = re.sub(r'^\s*\d+\s+', '', t)  # Remove single "54 " at start
    
    if preserve_paragraphs:
        # Preserve paragraph breaks (double newlines) for structural chunking
        # First, mark paragraph breaks with a placeholder
        t = re.sub(r"\n\s*\n+", "|||PARAGRAPH_BREAK|||", t)
        # Replace remaining single newlines with spaces
        t = t.replace("\n", " ")
        # Restore paragraph breaks
        t = t.replace("|||PARAGRAPH_BREAK|||", "\n\n")
        # Normalize spaces (but preserve double newlines)
        t = re.sub(r"[ \t]+", " ", t)  # normalize spaces
        t = re.sub(r" \n\n ", "\n\n", t)  # clean up around paragraph breaks
    else:
        # Old behavior: replace all newlines with spaces
        t = re.sub(r"\s+\n", "\n", t)
        t = re.sub(r"[ \t]+", " ", t)
        t = t.replace("\n", " ").strip()
    
    return t.strip()

def split_sentences(text: str):
    # simple sentence splitter (good for prose)
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if s.strip()]

def chunk_kazakhtelecom_page(text: str, page_num: int):
    """
    Chunking for Kazakhtelecom PDF:
    Each page = one chunk (1 страница = 1 чанк).
    If page is too large, it will be trimmed to fit.
    """
    if not text or not text.strip():
        return []
    
    # Check if page fits in one chunk
    tokens = enc.encode(text)
    token_count = len(tokens)
    
    if token_count <= KAZAKHTELECOM_MAX_TOKENS:
        # Page fits in one chunk - return as single chunk
        if token_count >= KAZAKHTELECOM_MIN_TOKENS:
            return [text]
        else:
            return []  # too small
    
    # Page is too long - trim to fit
    trimmed_tokens = tokens[:KAZAKHTELECOM_MAX_TOKENS]
    trimmed_text = enc.decode(trimmed_tokens)
    
    if len(trimmed_tokens) >= KAZAKHTELECOM_MIN_TOKENS:
        return [trimmed_text]
    else:
        return []

def pdf_pages(path: str, preserve_paragraphs: bool = True):
    """
    Yield (page_number_1based, cleaned_text) using PyMuPDF.
    Each page is extracted separately for accurate page numbers.
    For two-column pages: reads left column first, then right column.
    """
    print("Reading PDF with PyMuPDF...")
    pdf_doc = fitz.open(path)
    total_pages = len(pdf_doc)
    
    print(f"Found {total_pages} pages. Extracting text from each page...")
    
    try:
        for page_num in range(1, total_pages + 1):
            page = pdf_doc[page_num - 1]  # PyMuPDF uses 0-based indexing
            
            # Get page dimensions
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height
            
            # Extract text blocks with coordinates
            blocks = page.get_text("dict", sort=False)  # Don't sort yet, we'll do it manually
            
            # Separate blocks into left and right columns
            left_blocks = []
            right_blocks = []
            
            # Threshold for column separation (usually middle of page, but can adjust)
            column_threshold = page_width / 2
            
            for block in blocks.get("blocks", []):
                if "lines" in block:
                    # Get bounding box of the block
                    bbox = block.get("bbox", [0, 0, 0, 0])  # [x0, y0, x1, y1]
                    block_x_center = (bbox[0] + bbox[2]) / 2
                    
                    # Determine which column this block belongs to
                    if block_x_center < column_threshold:
                        left_blocks.append((bbox[1], block))  # Store with Y coordinate for sorting
                    else:
                        right_blocks.append((bbox[1], block))  # Store with Y coordinate for sorting
            
            # Sort blocks within each column by Y coordinate (top to bottom)
            left_blocks.sort(key=lambda x: x[0])
            right_blocks.sort(key=lambda x: x[0])
            
            # Extract text from blocks in correct order: left column first, then right column
            text_parts = []
            
            # Process left column
            for y_pos, block in left_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = " ".join([span.get("text", "") for span in line.get("spans", [])])
                        if line_text.strip():
                            text_parts.append(line_text)
            
            # Process right column
            for y_pos, block in right_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = " ".join([span.get("text", "") for span in line.get("spans", [])])
                        if line_text.strip():
                            text_parts.append(line_text)
            
            # Combine all text
            page_text = "\n".join(text_parts)
            
            # Fallback: if no text extracted with blocks method, use simple get_text
            if not page_text or len(page_text.strip()) < 10:
                page_text = page.get_text("text", sort=True) or ""
            
            if page_text.strip():
                yield (page_num, clean_text(page_text, preserve_paragraphs=preserve_paragraphs))
            else:
                print(f"  Warning: Page {page_num} is empty")
    finally:
        pdf_doc.close()

def process_kazakhtelecom(sb: Client, client: OpenAI):
    """Process Kazakhtelecom PDF with chunking: 1 page = 1 chunk"""
    print("\n" + "="*60)
    print("PROCESSING: Kazakhtelecom.pdf")
    print("="*60)
    
    # Delete existing chunks
    sb.table("chunks").delete().eq("doc_id", KAZAKHTELECOM_DOC_ID).execute()
    
    print("Reading PDF by pages...")
    pages = list(pdf_pages(KAZAKHTELECOM_PDF))
    
    # Build chunks with page metadata
    # Each page = one chunk (1 страница = 1 чанк)
    inputs, metas = [], []
    print("\nChunking: each page = one chunk (1 страница = 1 чанк)...")
    
    pages_processed = 0
    pages_skipped = 0
    
    for page, text in pages:
        if not text:
            pages_skipped += 1
            continue
        
        # Get chunks for this page (should be exactly 1 chunk per page)
        page_chunks = chunk_kazakhtelecom_page(text, page)
        
        if len(page_chunks) == 0:
            pages_skipped += 1
            continue
        
        pages_processed += 1
        
        for chunk_idx, chunk in enumerate(page_chunks):
            inputs.append(chunk)
            # Metadata includes page number
            meta = {
                "page": page,
                "chunk_in_page": chunk_idx,
                "total_chunks_in_page": len(page_chunks),
                "source": KAZAKHTELECOM_PDF,
                "source_type": "kazakhtelecom"
            }
            metas.append(meta)
    
    print(f"\nChunking summary:")
    print(f"  Pages processed: {pages_processed}")
    print(f"  Pages skipped (empty/too small): {pages_skipped}")
    print(f"  Total chunks created: {len(inputs)}")
    
    if not inputs:
        print("No chunks created!")
        return
    
    # Generate embeddings
    vectors = []
    print("Generating embeddings...")
    for i in tqdm(range(0, len(inputs), BATCH_EMBED), desc="Embedding Kazakhtelecom"):
        batch = inputs[i:i + BATCH_EMBED]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vectors.extend([d.embedding for d in resp.data])
    
    # Prepare rows
    rows = []
    for idx, (content, emb, meta) in enumerate(zip(inputs, vectors, metas)):
        rows.append({
            "doc_id": KAZAKHTELECOM_DOC_ID,
            "chunk_index": idx,
            "content": content,
            "metadata": meta,
            "embedding": emb
        })
    
    print("Uploading to Supabase...")
    import time
    inserted_count = 0
    for j in tqdm(range(0, len(rows), BATCH_INSERT), desc="Uploading Kazakhtelecom"):
        batch = rows[j:j+BATCH_INSERT]
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                result = sb.table("chunks").insert(batch).execute()
                inserted_count += len(batch)
                # Small delay between batches to avoid overwhelming the server
                if j + BATCH_INSERT < len(rows):
                    time.sleep(0.5)
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"\n  Retry {attempt + 1}/{max_retries} after error: {str(e)[:100]}")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    print(f"\n  Failed to insert batch starting at index {j} after {max_retries} attempts")
                    print(f"  Error: {str(e)}")
                    raise
    
    print(f"Done! Inserted {inserted_count} chunks (doc_id={KAZAKHTELECOM_DOC_ID})")


def main():
    sb: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Process Kazakhtelecom PDF
    process_kazakhtelecom(sb, client)
    
    print("\n" + "="*60)
    print("DOCUMENT PROCESSED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    main()