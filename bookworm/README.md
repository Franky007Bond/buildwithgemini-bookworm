# 📚 Bookworm — Intelligent Literary Concierge & Reading Companion

A conversational, agentic book assistant built on Google Cloud's **Agent Platform (Agent Runtime)** and the **Agent Development Kit (ADK)**. Bookworm pairs long-term personalized memory with structured catalog querying, rich A2UI card rendering, on-demand AI cover art design, and short video teasers.

<div align="center">

![Bookworm Demo](demo.gif)

*Demonstration of Bookworm recommending curated books based on long-term genre preferences from Memory Bank, followed by generating custom book cover artwork stored in Cloud Storage and displayed via A2UI cards.*

</div>

---

## 🌟 What Bookworm Does

Bookworm acts as a personal literary concierge and reading list tracker:

- **Cross-Session Memory Bank**: Remembers user preferences, favorite genres (such as Product Management, AI, and Detective Fiction), preferred authors, and reading habits across conversation sessions using Google Cloud Vertex AI Memory Bank.
- **Structured Literary Catalog (Firestore)**: Searches a curated Firestore database of books across diverse genres, complete with synopses, page counts, community ratings, and thematic tags.
- **Reading List Manager (Firestore)**: Tracks the reader's active personal reading list across `want_to_read`, `reading`, and `completed` statuses, supporting custom reviews, ratings, and status updates.
- **External Book Metadata (OpenLibrary API)**: Live metadata lookup tool fetching verified author names, median page counts, and publication years for unfamiliar or external titles.
- **Custom AI Cover Art Generation (Gemini 3.1 Flash Lite Image)**: Synthesizes bespoke cover art based on literary themes and custom art styles, saving the image directly to the session artifact context and publishing to Google Cloud Storage.
- **Cinematic Book Teaser Videos (Gemini Omni Flash Preview)**: Generates short 3-second teaser trailers using Google's Omni model (`gemini-omni-flash-preview`), uploading the video bytes to Cloud Storage and recording session artifacts.
- **Classical Poetry & Literary Excerpts (PoetryDB API)**: Fetches classic poems, verses, and sonnets to match literary themes or inquiries.
- **Agent-First UI (A2UI)**: Returns structured A2UI surfaces containing interactive book cards, typography hints, and embedded visual media rather than plain markdown text.
- **Secure Code Sandbox (Python)**: Executes code calculations for reading pace forecasts and reading challenge timelines inside an isolated Agent Platform sandbox environment.

---

## 🏗️ Architecture & Google Cloud Services

Bookworm is built directly on the Google Cloud Agent Platform stack:

| Component | Technology | Purpose in Bookworm |
|---|---|---|
| **Agent Reasoning Engine** | ADK (Agent Development Kit) & `gemini-2.5-flash` | Core ReAct reasoning loop, tool orchestration, and callback hooks |
| **Long-Term Memory** | Vertex AI Memory Bank | Automatic turn fact extraction via `CallbackContext` and retrieval via `PreloadMemoryTool` |
| **Structured Database** | Google Cloud Firestore | `books` catalog and `reading_list` tracking |
| **Object & Asset Storage** | Google Cloud Storage | Public asset hosting for generated cover art and video teasers |
| **Image Generation** | `gemini-3.1-flash-lite-image` | Generates stylized cover artwork on demand |
| **Video Generation** | `gemini-omni-flash-preview` | Generates short cinematic book teaser clips via the Interactions API |
| **Secure Code Execution** | Agent Engine Sandbox | Python code sandbox for reading pace and goal analytics |
| **Agent-to-User Interface** | A2UI (v0.8 Basic Catalog) | Structured cards, columns, rows, images, and video players |
| **Web Frontend Proxy** | FastAPI & A2A SDK on Cloud Run | Browser client talking to the deployed agent over the Agent-to-Agent (A2A) protocol |

---

## 🛠️ Implemented Function Tools

All tools are declared in [`app/agent.py`](app/agent.py) and registered directly to the agent's reasoning loop:

1. `preload_memory` (`PreloadMemoryTool`): Automatically injects relevant cross-session facts and preferences into the prompt turn.
2. `search_books(genre, keyword)`: Queries the Firestore `books` collection with filtering on genre, title, author, synopsis, and tags.
3. `get_reading_list(status)`: Fetches items from the reader's Firestore `reading_list` collection.
4. `add_to_reading_list(title, author, status, genre, notes, rating)`: Adds or updates an entry in the Firestore `reading_list`.
5. `update_reading_status(title, status, rating, notes)`: Updates reading status or ratings for books already in the list.
6. `fetch_book_details(title_or_query)`: Real-time metadata lookup via the OpenLibrary Search API.
7. `generate_book_cover(title, tool_context, style_description)`: Generates custom cover art via `gemini-3.1-flash-lite-image`, saves the session artifact via `tool_context.save_artifact`, and uploads to Cloud Storage.
8. `generate_book_trailer_video(title, tool_context, visual_description)`: Generates a 3-second teaser trailer via `gemini-omni-flash-preview` in `global`, saves session artifact, and uploads to Cloud Storage.
9. `lookup_classic_poem(author, title)`: Fetches poems, verses, and excerpts via the PoetryDB API.

---

## 📋 Roadmap & Planned Features

The following items are planned for future iterations and not yet implemented:
- [ ] *Planned*: Direct audio reading summaries and voice book teasers via Gemini Native Audio / TTS.
- [ ] *Planned*: Exportable social media quote cards and reading milestone graphics.
- [ ] *Planned*: Direct Google Books OAuth integration for personal library syncing.

---

## 🚀 Running Locally

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- [`agents-cli`](https://google.github.io/agents-cli/) (`uv tool install google-agents-cli`)
- Google Cloud SDK (`gcloud`) authenticated with Application Default Credentials:
  ```bash
  gcloud auth login
  gcloud auth application-default login
  ```

### 1. Install Dependencies & Seed Database

```bash
# Navigate to the project root
cd bookworm

# Install project dependencies
uv sync

# Populate sample books in Firestore
uv run python seed_firestore.py
```

### 2. Test Agent in the Local ADK Playground

```bash
uv run agents-cli playground
```

This launches the local development UI with interactive turn stepping, memory inspection, and artifact preview.

### 3. Run the Web Frontend Locally

The frontend consists of a lightweight FastAPI proxy and an A2UI chat interface:

```bash
cd frontend

# Set the deployed reasoning engine resource name and agent directory
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<REGION>/reasoningEngines/<REASONING_ENGINE_ID>"
export AGENT_DIRECTORY="app"
export PORT=8080

uv run python main.py
```

---

## 📦 Deploying to Google Cloud

### 1. Deploy Agent to Agent Runtime

To deploy or update the agent logic to Google Cloud Agent Runtime:

```bash
agents-cli deploy \
  --project="<YOUR_PROJECT_ID>" \
  --region="<YOUR_REGION>"
```

### 2. Deploy Web Frontend to Cloud Run

To build and deploy the frontend proxy container to Cloud Run:

```bash
cd frontend

gcloud run deploy bookworm-frontend \
  --source . \
  --region "<YOUR_REGION>" \
  --platform managed \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_ID>/locations/<REGION>/reasoningEngines/<REASONING_ENGINE_ID>",AGENT_DIRECTORY="app"
```
