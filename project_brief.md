# My agent: Book Concierge (PageTurner)
One-liner: A conversational agent that helps avid readers discover new books, manage their personalized reading lists, and visualize custom cover art with a curated literary catalog.

Tool coverage:
- Memory: Remembers favorite genres, authors, reading pace, themes, and past books read and/or rated
- Tools: Search book recommendations, add/update/remove books in reading list, generate cover art prompts
- Catalog/UI: Firestore collection of book titles with metadata (author, genre, rating, tags) rendered as rich A2UI book cards
- Image gen: Generates imaginative, stylized book cover art or aesthetic reading-vibe images
- Sandbox: Computes reading speed, estimated reading time, and reading challenge progress metrics

Recommended for every project: memory, storage, tools, image generation, A2UI
Agent-specific / stretch:
- Code sandbox for reading goal stats, pace calculations, and yearly challenge analytics
- Google Books API / OpenLibrary integration for live metadata lookups
- Video gen: Generates cinematic 3-second book teasers and literary scene trailers using Google's Omni model (gemini-omni-flash-preview)
- Audio reading summaries and book teasers using Gemini audio/voice capabilities
- Social sharing card export for favorite quotes and completed book reviews

