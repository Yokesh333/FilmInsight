"""
##############################################################################
# DEPRECATED — DO NOT USE
# ──────────────────────────────────────────────────────────────────────────
# This script pushed PDFs to the Flowise Cloud Upsert API which is NO LONGER
# part of the FilmInsight pipeline.
#
# The active ingestion pipeline is:
#   backend/app/services/ingestion_service.py
#
# Flow:
#   PDF uploaded via /api/upload
#       → Supabase Storage
#       → PyMuPDF (text extraction)
#       → RecursiveCharacterTextSplitter
#       → HuggingFace sentence-transformers/all-MiniLM-L6-v2 (embeddings)
#       → Persistent Chroma (local chroma_db/)
#       → PostgreSQL status update
#
# Flowise is NOT involved in any part of document storage or vector indexing.
# This file is kept for historical reference only.
##############################################################################

"""
supabase_to_flowise.py — FilmInsight Cloud Ingestion Pipeline (DEPRECATED)
===========================================================================

Pipeline flow:
  Supabase Storage (movie_scripts bucket)
      -> Download PDF bytes
      -> POST to Flowise Cloud Upsert API
      -> Flowise internally: splits -> embeds (HuggingFace) -> stores in Chroma
      -> Chatflow can now query ALL movies via vector search

Why this approach?
  The existing Python pipeline stores embeddings in a LOCAL chroma_db folder
  which Flowise Cloud (running on remote servers) cannot access.
  The Flowise Upsert API solves this by pushing documents directly into
  Flowise Cloud's own internal vector store — the same one the chatflow queries.

Usage
-----
  # From project root:
  python -m ingestion.supabase_to_flowise

  # Or with options:
  python -m ingestion.supabase_to_flowise --dry-run
  python -m ingestion.supabase_to_flowise --movie "Inception"
  python -m ingestion.supabase_to_flowise --force-all

Environment variables required (in backend/.env or project root .env):
  SUPABASE_URL              -- e.g. https://vbymfkwiotcrncqccbyl.supabase.co
  SUPABASE_SERVICE_ROLE_KEY -- service role key (not anon key)
  FLOWISE_URL               -- e.g. https://cloud.flowiseai.com
  FLOWISE_CHATFLOW_ID       -- e.g. 5a64fe29-4d42-420d-8d6a-6e3d636d968d
  FLOWISE_API_KEY           -- optional, your Flowise Cloud API key
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv

# Resolve paths
_INGESTION_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT  = _INGESTION_DIR.parent

# Load .env from backend/ first (has all keys), fall back to project root
for env_file in [_PROJECT_ROOT / "backend" / ".env", _PROJECT_ROOT / ".env"]:
    if env_file.exists():
        load_dotenv(env_file, override=False)

import os

# Config
SUPABASE_URL              = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
SUPABASE_BUCKET           = "movie_scripts"

FLOWISE_URL         = os.getenv("FLOWISE_URL", "https://cloud.flowiseai.com").rstrip("/")
FLOWISE_CHATFLOW_ID = os.getenv("FLOWISE_CHATFLOW_ID", "")
FLOWISE_API_KEY     = os.getenv("FLOWISE_API_KEY", "")

# Path to track which movies have already been upserted to Flowise Cloud
CLOUD_REGISTRY_FILE = _INGESTION_DIR / "cloud_ingested_movies.json"

# Logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("filminsight.cloud_ingest")


# Registry helpers

def load_registry() -> dict:
    if CLOUD_REGISTRY_FILE.exists():
        with open(CLOUD_REGISTRY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_registry(registry: dict) -> None:
    with open(CLOUD_REGISTRY_FILE, "w", encoding="utf-8") as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)


# Supabase helpers

def _supabase_headers() -> dict:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }


def list_pdfs_in_bucket() -> list:
    url = f"{SUPABASE_URL}/storage/v1/object/list/{SUPABASE_BUCKET}"
    resp = requests.post(
        url,
        headers={**_supabase_headers(), "Content-Type": "application/json"},
        json={"prefix": "", "limit": 500, "sortBy": {"column": "name", "order": "asc"}},
        timeout=30,
    )
    resp.raise_for_status()
    files = resp.json()
    return [f for f in files if f.get("name", "").lower().endswith(".pdf")]


def download_pdf_from_supabase(filename: str) -> bytes:
    url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET}/{filename}"
    resp = requests.get(url, headers=_supabase_headers(), timeout=120)
    resp.raise_for_status()
    return resp.content


# Flowise helpers

def _flowise_headers() -> dict:
    h = {}
    if FLOWISE_API_KEY:
        h["Authorization"] = f"Bearer {FLOWISE_API_KEY}"
    return h


def upsert_pdf_to_flowise(filename: str, pdf_bytes: bytes) -> dict:
    upsert_url = f"{FLOWISE_URL}/api/v1/vector/upsert/{FLOWISE_CHATFLOW_ID}"
    files = {
        "files": (filename, pdf_bytes, "application/pdf"),
    }
    logger.info(f"  -> Upserting to Flowise: {filename} ({len(pdf_bytes) / 1024:.1f} KB)")
    resp = requests.post(
        upsert_url,
        files=files,
        headers=_flowise_headers(),
        timeout=300,
    )
    if resp.status_code == 200:
        return resp.json()
    else:
        raise RuntimeError(
            f"Flowise upsert failed [{resp.status_code}]: {resp.text[:500]}"
        )


# Title helper

def _filename_to_title(filename: str) -> str:
    stem = Path(filename).stem
    stem = stem.lstrip("_")
    stem = stem.replace("_", " ").replace("-", " ")
    return stem.title()


# Validation

def validate_config() -> None:
    errors = []
    if not SUPABASE_URL:
        errors.append("SUPABASE_URL is not set")
    if not SUPABASE_SERVICE_ROLE_KEY:
        errors.append("SUPABASE_SERVICE_ROLE_KEY is not set")
    if not FLOWISE_URL:
        errors.append("FLOWISE_URL is not set")
    if not FLOWISE_CHATFLOW_ID:
        errors.append("FLOWISE_CHATFLOW_ID is not set")
    if errors:
        logger.error("Configuration errors:")
        for e in errors:
            logger.error(f"  X {e}")
        sys.exit(1)
    logger.info(f"  Supabase URL    : {SUPABASE_URL}")
    logger.info(f"  Flowise URL     : {FLOWISE_URL}")
    logger.info(f"  Chatflow ID     : {FLOWISE_CHATFLOW_ID}")
    logger.info(f"  API Key set     : {'yes' if FLOWISE_API_KEY else 'no (unauthenticated)'}")


# Main pipeline

def run_pipeline(
    dry_run: bool = False,
    only_movie: str | None = None,
    force_all: bool = False,
) -> None:
    print()
    print("=" * 60)
    print("  FilmInsight -- Cloud Ingestion Pipeline")
    print("  Supabase Storage -> Flowise Cloud Vector Store")
    print("=" * 60)

    validate_config()

    registry = load_registry()
    logger.info(f"  Already ingested: {len(registry)} movie(s)")

    logger.info(f"\n  Listing PDFs in Supabase bucket '{SUPABASE_BUCKET}'...")
    try:
        pdf_files = list_pdfs_in_bucket()
    except Exception as exc:
        logger.error(f"  Failed to list Supabase bucket: {exc}")
        sys.exit(1)

    logger.info(f"  Found {len(pdf_files)} PDF(s) in bucket.")

    if dry_run:
        print("\n  [DRY RUN] The following PDFs would be upserted:")
        for f in pdf_files:
            title = _filename_to_title(f["name"])
            status = "already ingested" if title in registry and not force_all else "would upsert"
            print(f"    [{status}] {f['name']}  ({title})")
        return

    to_process = []
    for pdf_file in pdf_files:
        title = _filename_to_title(pdf_file["name"])
        if only_movie and only_movie.lower() not in title.lower():
            continue
        if title in registry and not force_all:
            logger.info(f"  Skipping '{title}' -- already in cloud registry.")
            continue
        to_process.append((pdf_file["name"], title))

    if not to_process:
        print("\n  All movies already ingested. Nothing to do.")
        print("  Use --force-all to re-upsert everything.\n")
        return

    logger.info(f"\n  {len(to_process)} movie(s) to process.\n")

    success = 0
    failed  = 0

    for idx, (filename, title) in enumerate(to_process, 1):
        print(f"\n  [{idx}/{len(to_process)}] {title}")
        print(f"  File: {filename}")

        try:
            logger.info(f"  Downloading from Supabase...")
            t0 = time.time()
            pdf_bytes = download_pdf_from_supabase(filename)
            logger.info(f"  Downloaded {len(pdf_bytes) / 1024:.1f} KB in {time.time()-t0:.1f}s")

            logger.info(f"  Upserting to Flowise Cloud...")
            t1 = time.time()
            result = upsert_pdf_to_flowise(filename, pdf_bytes)
            elapsed = time.time() - t1

            num_docs = result.get("numAdded", result.get("added", "unknown"))
            logger.info(f"  OK  Upserted! {num_docs} chunks added. ({elapsed:.1f}s)")

            registry[title] = {
                "filename": filename,
                "ingested_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "flowise_chatflow_id": FLOWISE_CHATFLOW_ID,
                "chunks_added": num_docs,
            }
            save_registry(registry)
            success += 1

        except KeyboardInterrupt:
            logger.warning("\n  Interrupted by user. Progress saved.")
            sys.exit(0)

        except Exception as exc:
            logger.error(f"  FAILED: {exc}")
            failed += 1
            continue

    print()
    print("=" * 60)
    print(f"  Done. {success} succeeded, {failed} failed.")
    print(f"  Registry saved to: {CLOUD_REGISTRY_FILE.name}")
    print("=" * 60)
    print()

    if success > 0:
        print("  Your Flowise Cloud chatflow now has all movies!")
        print("  Questions about any ingested movie will now be answered")
        print("  directly from the screenplay context.\n")


# CLI entry-point

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="supabase_to_flowise",
        description="FilmInsight -- Push Supabase PDFs into Flowise Cloud vector store",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="List files that would be uploaded without actually uploading",
    )
    parser.add_argument(
        "--movie", type=str, default=None, metavar="TITLE",
        help="Only ingest a specific movie (partial match). e.g. --movie 'Prestige'",
    )
    parser.add_argument(
        "--force-all", action="store_true",
        help="Re-upsert all movies, even those already in the cloud registry",
    )
    args = parser.parse_args()
    run_pipeline(dry_run=args.dry_run, only_movie=args.movie, force_all=args.force_all)


if __name__ == "__main__":
    main()
