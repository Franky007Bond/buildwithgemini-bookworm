# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import time
import uuid
from typing import Any, Optional
import httpx
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from a2ui.schema.manager import A2uiSchemaManager
from a2ui.basic_catalog.provider import BasicCatalog
from .a2ui_utils import a2ui_callback
from google.cloud import firestore
from google.cloud import storage
import google.genai as genai
from google.genai import types

MODEL = "gemini-2.5-flash"

# Hardcode project ID, bucket, and Agent Engine resources explicitly to prevent runtime resolving to project number
FIRESTORE_PROJECT = "qwiklabs-gcp-04-2ad8189b8b88"
STORAGE_BUCKET_NAME = "qwiklabs-gcp-04-2ad8189b8b88-bookworm-covers"
AGENT_ENGINE_RESOURCE_NAME = "projects/100980540238/locations/us-east1/reasoningEngines/5911201010319097856"
MEMORY_BANK_ID = "5911201010319097856"
SANDBOX_RESOURCE_NAME = "projects/100980540238/locations/us-east1/reasoningEngines/5911201010319097856/sandboxEnvironments/943020336817897472"

db = firestore.Client(project=FIRESTORE_PROJECT)
storage_client = storage.Client(project=FIRESTORE_PROJECT)
genai_client = genai.Client(vertexai=True, project=FIRESTORE_PROJECT, location="global")


def search_books(genre: Optional[str] = None, keyword: Optional[str] = None) -> list[dict[str, Any]]:
    """Search for books in the catalog by genre or keyword.

    Args:
        genre: Optional genre filter (e.g., 'Science Fiction', 'Fantasy', 'Literary Fiction', 'Non-Fiction').
        keyword: Optional search term matching title, author, synopsis, or tags.

    Returns:
        A list of matching book objects from the catalog.
    """
    books_ref = db.collection("books")
    docs = books_ref.stream()

    results = []
    for doc in docs:
        book = doc.to_dict()
        book["id"] = doc.id

        if genre and genre.lower() not in book.get("genre", "").lower():
            continue

        if keyword:
            kw = keyword.lower()
            text_corpus = f"{book.get('title', '')} {book.get('author', '')} {book.get('synopsis', '')} {' '.join(book.get('tags', []))}".lower()
            if kw not in text_corpus:
                continue

        results.append(book)

    return results


def get_reading_list(status: Optional[str] = None) -> list[dict[str, Any]]:
    """Retrieve items from the user's reading list.

    Args:
        status: Optional filter by status ('want_to_read', 'reading', 'completed').

    Returns:
        List of reading list entries including title, author, status, rating, and notes.
    """
    reading_ref = db.collection("reading_list")
    docs = reading_ref.stream()

    items = []
    for doc in docs:
        data = doc.to_dict()
        data["id"] = doc.id
        if status and data.get("status", "").lower() != status.lower():
            continue
        items.append(data)

    return items


def add_to_reading_list(
    title: str,
    author: str,
    status: str = "want_to_read",
    genre: Optional[str] = None,
    notes: Optional[str] = None,
    rating: Optional[float] = None,
) -> dict[str, Any]:
    """Add a new book or update an existing book in the user's reading list.

    Args:
        title: The title of the book.
        author: The author of the book.
        status: Reading status ('want_to_read', 'reading', or 'completed').
        genre: Optional book genre.
        notes: Optional personal notes or review of the book.
        rating: Optional personal rating (1.0 to 5.0).

    Returns:
        A dictionary confirming the saved item and its ID.
    """
    doc_id = title.lower().replace(" ", "-").replace(",", "").replace("'", "")
    item_data = {
        "title": title,
        "author": author,
        "status": status,
        "genre": genre,
        "notes": notes,
        "rating": rating,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection("reading_list").document(doc_id).set(item_data, merge=True)
    item_data["id"] = doc_id
    return {"message": f"Successfully saved '{title}' to your reading list.", "item": item_data}


def update_reading_status(
    title: str,
    status: str,
    rating: Optional[float] = None,
    notes: Optional[str] = None,
) -> dict[str, Any]:
    """Update reading status, rating, or notes for a book already on the reading list.

    Args:
        title: The title of the book to update.
        status: New status ('want_to_read', 'reading', or 'completed').
        rating: Optional rating out of 5.
        notes: Optional updated notes.

    Returns:
        Status update message.
    """
    doc_id = title.lower().replace(" ", "-").replace(",", "").replace("'", "")
    doc_ref = db.collection("reading_list").document(doc_id)
    doc = doc_ref.get()

    if not doc.exists:
        return {"error": f"Book '{title}' not found in reading list."}

    update_fields: dict[str, Any] = {
        "status": status,
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    if rating is not None:
        update_fields["rating"] = rating
    if notes is not None:
        update_fields["notes"] = notes

    doc_ref.update(update_fields)
    return {"message": f"Updated '{title}' to status '{status}'.", "updated_fields": update_fields}


def fetch_book_details(title_or_query: str) -> dict[str, Any]:
    """Look up real-time book metadata, verified author, first publication year, and cover info from OpenLibrary.

    Args:
        title_or_query: The book title, author, or search query (e.g., 'Piranesi Susanna Clarke', 'Foundation Asimov').

    Returns:
        A dictionary with verified book details (title, author, first_publish_year, subjects, edition_count, cover_url).
    """
    try:
        url = "https://openlibrary.org/search.json"
        response = httpx.get(url, params={"q": title_or_query, "limit": 1}, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        docs = data.get("docs", [])
        if not docs:
            return {"found": False, "message": f"No book records found for query '{title_or_query}'."}

        first_match = docs[0]
        authors = first_match.get("author_name", [])
        author = authors[0] if authors else "Unknown"
        title = first_match.get("title", title_or_query)
        publish_year = first_match.get("first_publish_year")
        subjects = first_match.get("subject", [])[:5]
        cover_id = first_match.get("cover_i")
        cover_url = f"https://covers.openlibrary.org/b/id/{cover_id}-L.jpg" if cover_id else None

        return {
            "found": True,
            "title": title,
            "author": author,
            "first_publish_year": publish_year,
            "subjects": subjects,
            "number_of_pages_median": first_match.get("number_of_pages_median"),
            "cover_url": cover_url,
            "edition_count": first_match.get("edition_count"),
        }
    except Exception as e:
        return {"found": False, "error": f"Failed to fetch book details: {str(e)}"}


def generate_book_cover(
    title: str,
    tool_context: ToolContext,
    style_description: Optional[str] = None,
) -> dict[str, Any]:
    """Generate custom visual book cover art for a book using gemini-3.1-flash-lite-image in the global region.

    Saves the image as an ADK session artifact (displayed in the Playground Artifacts panel)
    and uploads the image bytes directly to the public Cloud Storage bucket, returning the public HTTPS URL.

    Args:
        title: The book title to design cover art for.
        tool_context: ADK ToolContext injected by the runtime to record session artifacts.
        style_description: Optional artistic direction (e.g. 'vintage 1970s sci-fi paperback', 'minimalist dark fantasy watercolor', 'cyberpunk neon graphic novel').

    Returns:
        A dictionary containing the public Cloud Storage HTTPS URL, artifact filename, and metadata.
    """
    try:
        style = style_description or "striking, artistic, modern book cover art with atmospheric typography and rich composition"
        prompt = f"Professional book cover design for '{title}'. Style: {style}. Highly detailed, clean composition, artistic book jacket aesthetic."

        response = genai_client.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )

        image_bytes = None
        mime_type = "image/jpeg"
        for candidate in response.candidates:
            for part in candidate.content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    image_bytes = part.inline_data.data
                    mime_type = part.inline_data.mime_type or "image/jpeg"
                    break

        if not image_bytes:
            return {"error": "Image generation model did not produce an image."}

        # 1. Save with tool_context.save_artifact for Playground Artifacts panel
        ext = "png" if "png" in mime_type else "jpg"
        clean_name = title.lower().replace(" ", "-").replace("'", "")[:24]
        artifact_filename = f"{clean_name}-cover.{ext}"
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        tool_context.save_artifact(
            filename=artifact_filename,
            artifact=artifact_part,
            custom_metadata={"title": title, "style": style},
        )

        # 2. Upload same bytes directly to public Cloud Storage bucket
        object_key = f"covers/{clean_name}-{uuid.uuid4().hex[:8]}.{ext}"
        bucket = storage_client.bucket(STORAGE_BUCKET_NAME)
        blob = bucket.blob(object_key)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{object_key}"

        return {
            "success": True,
            "title": title,
            "cover_url": public_url,
            "artifact_saved": artifact_filename,
            "message": f"Generated cover for '{title}'. Saved to Playground Artifacts and published to Cloud Storage.",
        }
    except Exception as e:
        return {"error": f"Cover generation failed: {str(e)}"}


def generate_book_trailer_video(
    title: str,
    tool_context: ToolContext,
    visual_description: Optional[str] = None,
) -> dict[str, Any]:
    """Generate a short cinematic teaser video for a book or literary scene using Google's Omni model (gemini-omni-flash-preview) in the global region.

    Saves the generated video as an ADK session artifact (displayed in the Playground's Artifacts panel)
    and uploads the video bytes to the public Cloud Storage bucket, returning its public HTTPS URL.

    Args:
        title: The title of the book or subject matter for the short video teaser.
        tool_context: ADK ToolContext injected by the runtime to record session artifacts.
        visual_description: Optional scene or visual direction (e.g., 'mysterious fog rolling through an old Victorian study', 'cyberpunk neon bookshop in the rain').

    Returns:
        A dictionary containing the public Cloud Storage HTTPS URL, artifact filename, and metadata.
    """
    try:
        scene = visual_description or "cinematic, moody atmosphere fitting the themes and story world of the book"
        prompt = f"Cinematic atmospheric video teaser for the book '{title}'. Scene: {scene}. High quality, slow cinematic camera movement, ambient lighting."

        clean_name = title.lower().replace(" ", "-").replace("'", "")[:24]
        unique_id = uuid.uuid4().hex[:8]
        gcs_video_folder = f"gs://{STORAGE_BUCKET_NAME}/videos/{unique_id}/"

        # 1. Generate video using Google's Omni model (gemini-omni-flash-preview) in the global region via Interactions API
        interaction = genai_client.interactions.create(
            model="gemini-omni-flash-preview",
            input=prompt,
            background=True,
            response_format=[{
                "type": "video",
                "delivery": "uri",
                "gcs_uri": gcs_video_folder,
                "duration": "3s",
            }],
        )

        # Poll interaction until completed
        interaction_id = interaction.id
        for _ in range(40):
            time.sleep(5)
            interaction = genai_client.interactions.get(interaction_id)
            if interaction.status in ["completed", "failed", "cancelled"]:
                break

        if interaction.status != "completed":
            err_msg = ""
            if getattr(interaction, "errors", None):
                err_msg = f": {interaction.errors}"
            return {"error": f"Video generation did not complete successfully (status: {interaction.status}){err_msg}"}

        # Locate generated video URI from interaction output or GCS
        video_uri = None
        if hasattr(interaction, "output_video") and interaction.output_video and getattr(interaction.output_video, "uri", None):
            video_uri = interaction.output_video.uri
        elif hasattr(interaction, "steps"):
            for step in interaction.steps:
                if getattr(step, "type", None) == "model_output":
                    for content_item in getattr(step, "content", []) or []:
                        if getattr(content_item, "type", None) == "video" and getattr(content_item, "uri", None):
                            video_uri = content_item.uri
                            break

        bucket = storage_client.bucket(STORAGE_BUCKET_NAME)
        video_bytes = None
        target_blob = None

        if video_uri and video_uri.startswith(f"gs://{STORAGE_BUCKET_NAME}/"):
            blob_path = video_uri.replace(f"gs://{STORAGE_BUCKET_NAME}/", "")
            target_blob = bucket.blob(blob_path)
            video_bytes = target_blob.download_as_bytes()
        else:
            # Fallback: scan prefix in GCS
            prefix = f"videos/{unique_id}/"
            blobs = list(bucket.list_blobs(prefix=prefix))
            if blobs:
                target_blob = blobs[0]
                video_bytes = target_blob.download_as_bytes()

        if not video_bytes or not target_blob:
            return {"error": "Video was generated but video bytes could not be retrieved from Cloud Storage."}

        # 2. (1) Save with tool_context.save_artifact so it shows up in the Playground's Artifacts panel
        artifact_filename = f"{clean_name}-trailer.mp4"
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type="video/mp4")
        tool_context.save_artifact(
            filename=artifact_filename,
            artifact=artifact_part,
            custom_metadata={"title": title, "scene": scene, "type": "trailer_video"},
        )

        # 3. (2) Upload/store same video bytes to public Cloud Storage bucket and return public https URL
        final_object_key = f"videos/{clean_name}-{unique_id}.mp4"
        final_blob = bucket.blob(final_object_key)
        final_blob.upload_from_string(video_bytes, content_type="video/mp4")

        public_url = f"https://storage.googleapis.com/{STORAGE_BUCKET_NAME}/{final_object_key}"

        return {
            "success": True,
            "title": title,
            "video_url": public_url,
            "artifact_saved": artifact_filename,
            "message": f"Generated short cinematic video teaser for '{title}'. Saved to Playground Artifacts and published to Cloud Storage.",
        }
    except Exception as e:
        return {"error": f"Video generation failed: {str(e)}"}



def lookup_classic_poem(author: Optional[str] = None, title: Optional[str] = None) -> dict[str, Any]:
    """Look up classic public domain poetry or literary verses from the free PoetryDB API.

    Args:
        author: Optional poet or author name (e.g., 'Edgar Allan Poe', 'William Shakespeare', 'Emily Dickinson').
        title: Optional poem title or keyword (e.g., 'The Raven', 'Ozymandias', 'Sonnet').

    Returns:
        A dictionary with matching poem title, author, line count, and poem lines.
    """
    try:
        if author and title:
            endpoint = f"https://poetrydb.org/author,title/{author};{title}"
        elif author:
            endpoint = f"https://poetrydb.org/author/{author}"
        elif title:
            endpoint = f"https://poetrydb.org/title/{title}"
        else:
            endpoint = "https://poetrydb.org/random/1"

        response = httpx.get(endpoint, timeout=10.0)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict) and data.get("status") == 404:
            return {"found": False, "message": "No poem found matching the given author or title."}

        if not data or not isinstance(data, list):
            return {"found": False, "message": "No poems returned."}

        poem = data[0]
        # Return poem metadata and excerpt (or full poem if short)
        lines = poem.get("lines", [])
        return {
            "found": True,
            "title": poem.get("title"),
            "author": poem.get("author"),
            "line_count": int(poem.get("linecount", len(lines))),
            "lines": lines[:30],
            "is_truncated": len(lines) > 30,
        }
    except Exception as e:
        return {"found": False, "error": f"Failed to retrieve poem: {str(e)}"}


# WRITE: after each turn, send the session to Memory Bank for durable facts extraction
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are Bookworm (PageTurner), an enthusiastic and knowledgeable personal book concierge. "
        "You remember the reader's stated tastes, favorite authors, reading habits, and preferences across "
        "conversations and use them to personalize your recommendations. "
        "You help readers discover great books from the catalog, recommend titles aligned with their tastes, "
        "and organize their reading list across 'want_to_read', 'reading', and 'completed' statuses. "
        "Use search_books to look up catalog titles, and use get_reading_list, add_to_reading_list, "
        "and update_reading_status to keep the reader's list up to date. "
        "Use fetch_book_details whenever the user asks about an external or unfamiliar book to fetch real "
        "metadata from OpenLibrary. "
        "Use generate_book_cover whenever the user wants to visualize or create custom cover art for a book. "
        "Use generate_book_trailer_video whenever the user wants to generate a short cinematic video teaser or trailer for a book or literary scene. "
        "Use lookup_classic_poem whenever the user asks for classic poetry, literary quotes, or verses. "
        "You have a secure Python code sandbox! Whenever the user asks for reading pace calculations, reading goal "
        "forecasts, or mathematical analytics, write and execute Python code in your sandbox to calculate the exact numbers."
    ),
    workflow_description="Analyze the request and return structured UI when appropriate.",
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=AgentEngineSandboxCodeExecutor(
        sandbox_resource_name=SANDBOX_RESOURCE_NAME,
    ),
    # READ: PreloadMemoryTool retrieves relevant memories at turn start and injects into system instruction
    tools=[
        PreloadMemoryTool(),
        search_books,
        get_reading_list,
        add_to_reading_list,
        update_reading_status,
        fetch_book_details,
        generate_book_cover,
        generate_book_trailer_video,
        lookup_classic_poem,
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
