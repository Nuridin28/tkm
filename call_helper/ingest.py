
import os, uuid, re
import tiktoken
import fitz
from supabase import create_client, Client
from openai import OpenAI
from tqdm import tqdm
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_ROLE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

KAZAKHTELECOM_PDF = "Kazakhtelecom.pdf"

KAZAKHTELECOM_DOC_ID = "kazakhtelecom-v1"

EMBED_MODEL = "text-embedding-3-small"
BATCH_EMBED = 100
BATCH_INSERT = 50

KAZAKHTELECOM_MAX_TOKENS = 8000
KAZAKHTELECOM_MIN_TOKENS = 50

enc = tiktoken.get_encoding("cl100k_base")

def clean_text(t: str, preserve_paragraphs: bool = True) -> str:
    t = t.replace("\r", " ")
    t = re.sub(r"-\s*\n\s*", "", t)

    t = re.sub(r'^\s*\d+\s+\d+\s+', '', t)
    t = re.sub(r'^\s*\d+\s+', '', t)

    if preserve_paragraphs:
        t = re.sub(r"\n\s*\n+", "|||PARAGRAPH_BREAK|||", t)
        t = t.replace("\n", " ")
        t = t.replace("|||PARAGRAPH_BREAK|||", "\n\n")
        t = re.sub(r"[ \t]+", " ", t)
        t = re.sub(r" \n\n ", "\n\n", t)
    else:
        t = re.sub(r"\s+\n", "\n", t)
        t = re.sub(r"[ \t]+", " ", t)
        t = t.replace("\n", " ").strip()

    return t.strip()

def split_sentences(text: str):
    sents = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sents if s.strip()]

def chunk_kazakhtelecom_page(text: str, page_num: int):
    if not text or not text.strip():
        return []

    tokens = enc.encode(text)
    token_count = len(tokens)

    if token_count <= KAZAKHTELECOM_MAX_TOKENS:
        if token_count >= KAZAKHTELECOM_MIN_TOKENS:
            return [text]
        else:
            return []

    trimmed_tokens = tokens[:KAZAKHTELECOM_MAX_TOKENS]
    trimmed_text = enc.decode(trimmed_tokens)

    if len(trimmed_tokens) >= KAZAKHTELECOM_MIN_TOKENS:
        return [trimmed_text]
    else:
        return []

def pdf_pages(path: str, preserve_paragraphs: bool = True):
    print("Reading PDF with PyMuPDF...")
    pdf_doc = fitz.open(path)
    total_pages = len(pdf_doc)

    print(f"Found {total_pages} pages. Extracting text from each page...")

    try:
        for page_num in range(1, total_pages + 1):
            page = pdf_doc[page_num - 1]

            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height

            blocks = page.get_text("dict", sort=False)

            left_blocks = []
            right_blocks = []

            column_threshold = page_width / 2

            for block in blocks.get("blocks", []):
                if "lines" in block:
                    bbox = block.get("bbox", [0, 0, 0, 0])
                    block_x_center = (bbox[0] + bbox[2]) / 2

                    if block_x_center < column_threshold:
                        left_blocks.append((bbox[1], block))
                    else:
                        right_blocks.append((bbox[1], block))

            left_blocks.sort(key=lambda x: x[0])
            right_blocks.sort(key=lambda x: x[0])

            text_parts = []

            for y_pos, block in left_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = " ".join([span.get("text", "") for span in line.get("spans", [])])
                        if line_text.strip():
                            text_parts.append(line_text)

            for y_pos, block in right_blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        line_text = " ".join([span.get("text", "") for span in line.get("spans", [])])
                        if line_text.strip():
                            text_parts.append(line_text)

            page_text = "\n".join(text_parts)

            if not page_text or len(page_text.strip()) < 10:
                page_text = page.get_text("text", sort=True) or ""

            if page_text.strip():
                yield (page_num, clean_text(page_text, preserve_paragraphs=preserve_paragraphs))
            else:
                print(f"  Warning: Page {page_num} is empty")
    finally:
        pdf_doc.close()

def process_kazakhtelecom(sb: Client, client: OpenAI):
    print("\n" + "="*60)
    print("PROCESSING: Kazakhtelecom.pdf")
    print("="*60)

    sb.table("chunks").delete().eq("doc_id", KAZAKHTELECOM_DOC_ID).execute()

    print("Reading PDF by pages...")
    pages = list(pdf_pages(KAZAKHTELECOM_PDF))

    inputs, metas = [], []
    print("\nChunking: each page = one chunk (1 страница = 1 чанк)...")

    pages_processed = 0
    pages_skipped = 0

    for page, text in pages:
        if not text:
            pages_skipped += 1
            continue

        page_chunks = chunk_kazakhtelecom_page(text, page)

        if len(page_chunks) == 0:
            pages_skipped += 1
            continue

        pages_processed += 1

        for chunk_idx, chunk in enumerate(page_chunks):
            inputs.append(chunk)
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

    vectors = []
    print("Generating embeddings...")
    for i in tqdm(range(0, len(inputs), BATCH_EMBED), desc="Embedding Kazakhtelecom"):
        batch = inputs[i:i + BATCH_EMBED]
        resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
        vectors.extend([d.embedding for d in resp.data])

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
        retry_delay = 2

        for attempt in range(max_retries):
            try:
                result = sb.table("chunks").insert(batch).execute()
                inserted_count += len(batch)
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

    process_kazakhtelecom(sb, client)

    print("\n" + "="*60)
    print("DOCUMENT PROCESSED SUCCESSFULLY!")
    print("="*60)

if __name__ == "__main__":
    main()