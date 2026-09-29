"""Seed script to populate initial book catalog and reading list items in Firestore.
"""

from google.cloud import firestore

# Explicitly hardcode project ID as string so Agent Platform or ADC doesn't resolve to project number
FIRESTORE_PROJECT = "qwiklabs-gcp-04-2ad8189b8b88"

SAMPLE_BOOKS = [
    {
        "id": "project-hail-mary",
        "title": "Project Hail Mary",
        "author": "Andy Weir",
        "genre": "Science Fiction",
        "rating": 4.9,
        "page_count": 496,
        "synopsis": "A lone astronaut must save the Earth from an extinction-level catastrophe while piecing together his forgotten memories.",
        "tags": ["space", "first contact", "survival", "humorous"],
        "cover_url": "https://images.unsplash.com/photo-1618609377864-68609b857e90?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "tomorrow-and-tomorrow-and-tomorrow",
        "title": "Tomorrow, and Tomorrow, and Tomorrow",
        "author": "Gabrielle Zevin",
        "genre": "Literary Fiction",
        "rating": 4.7,
        "page_count": 416,
        "synopsis": "Two childhood friends become creative partners in video game design, navigating fame, identity, love, and tragedy over three decades.",
        "tags": ["gaming", "friendship", "creativity", "contemporary"],
        "cover_url": "https://images.unsplash.com/photo-1544947950-fa07a98d237f?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "the-name-of-the-wind",
        "title": "The Name of the Wind",
        "author": "Patrick Rothfuss",
        "genre": "Fantasy",
        "rating": 4.8,
        "page_count": 662,
        "synopsis": "The story of Kvothe, an infamous magician, musician, and hero who recounts the truth behind his legendary deeds.",
        "tags": ["magic", "epic fantasy", "coming of age", "worldbuilding"],
        "cover_url": "https://images.unsplash.com/photo-1512820790803-83ca734da794?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "klara-and-the-sun",
        "title": "Klara and the Sun",
        "author": "Kazuo Ishiguro",
        "genre": "Speculative Fiction",
        "rating": 4.5,
        "page_count": 303,
        "synopsis": "Klara, an Artificial Friend with outstanding observational qualities, watches the behavior of those who come in to browse.",
        "tags": ["artificial intelligence", "dystopian", "poignant", "philosophical"],
        "cover_url": "https://images.unsplash.com/photo-1506880018603-83d5b814b5a6?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "atomic-habits",
        "title": "Atomic Habits",
        "author": "James Clear",
        "genre": "Non-Fiction",
        "rating": 4.8,
        "page_count": 320,
        "synopsis": "A proven framework for improving every day through tiny changes that deliver remarkable results.",
        "tags": ["self-improvement", "productivity", "psychology", "habits"],
        "cover_url": "https://images.unsplash.com/photo-1499750310107-5fef28a66643?w=600&auto=format&fit=crop&q=80",
    },
    # --- Product Management ---
    {
        "id": "inspired",
        "title": "Inspired: How to Create Tech Products Customers Love",
        "author": "Marty Cagan",
        "genre": "Product Management",
        "rating": 4.9,
        "page_count": 368,
        "synopsis": "The definitive guide for product managers on discovering and delivering technology products that customers love and that work for business.",
        "tags": ["product management", "leadership", "tech", "strategy", "innovation"],
        "cover_url": "https://images.unsplash.com/photo-1553484771-371a605b060b?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "the-lean-product-playbook",
        "title": "The Lean Product Playbook",
        "author": "Dan Olsen",
        "genre": "Product Management",
        "rating": 4.7,
        "page_count": 336,
        "synopsis": "A practical guide to building products that achieve product-market fit using iterative Lean Startup principles.",
        "tags": ["product management", "lean", "product-market fit", "agile", "frameworks"],
        "cover_url": "https://images.unsplash.com/photo-1460925895917-afdab827c52f?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "continuous-discovery-habits",
        "title": "Continuous Discovery Habits",
        "author": "Teresa Torres",
        "genre": "Product Management",
        "rating": 4.8,
        "page_count": 240,
        "synopsis": "How product teams can infuse continuous customer discovery and structured opportunity solution trees into daily workflows.",
        "tags": ["product management", "customer discovery", "user research", "decision making"],
        "cover_url": "https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?w=600&auto=format&fit=crop&q=80",
    },
    # --- Artificial Intelligence (AI) ---
    {
        "id": "superintelligence",
        "title": "Superintelligence: Paths, Dangers, Strategies",
        "author": "Nick Bostrom",
        "genre": "AI",
        "rating": 4.6,
        "page_count": 352,
        "synopsis": "A groundbreaking exploration of what happens when machine intelligence surpasses human intellect and how we can steer the outcome.",
        "tags": ["ai", "artificial intelligence", "future", "philosophy", "technology"],
        "cover_url": "https://images.unsplash.com/photo-1620712943543-bcc4688e7485?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "life-3-0",
        "title": "Life 3.0: Being Human in the Age of Artificial Intelligence",
        "author": "Max Tegmark",
        "genre": "AI",
        "rating": 4.7,
        "page_count": 384,
        "synopsis": "MIT professor Max Tegmark explores how automation, neural networks, and superhuman AI will transform society, crime, war, and justice.",
        "tags": ["ai", "artificial intelligence", "science", "cosmology", "ethics"],
        "cover_url": "https://images.unsplash.com/photo-1531746790731-6c087fecd65a?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "the-coming-wave",
        "title": "The Coming Wave: Technology, Power, and the Twenty-first Century's Greatest Dilemma",
        "author": "Mustafa Suleyman",
        "genre": "AI",
        "rating": 4.7,
        "page_count": 352,
        "synopsis": "DeepMind co-founder Mustafa Suleyman reveals how frontier AI and synthetic biology will define our future and the urgent need for containment.",
        "tags": ["ai", "deepmind", "frontier models", "geopolitics", "technology"],
        "cover_url": "https://images.unsplash.com/photo-1677442136019-21780efad99a?w=600&auto=format&fit=crop&q=80",
    },
    # --- Detective Fiction ---
    {
        "id": "the-hound-of-the-baskervilles",
        "title": "The Hound of the Baskervilles",
        "author": "Arthur Conan Doyle",
        "genre": "Detective Fiction",
        "rating": 4.8,
        "page_count": 256,
        "synopsis": "Sherlock Holmes and Dr. Watson investigate the legendary curse of a demonic hound haunting the eerie moors of Devonshire.",
        "tags": ["detective", "mystery", "sherlock holmes", "classic", "investigation"],
        "cover_url": "https://images.unsplash.com/photo-1589829085413-56de8ae18c73?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "and-then-there-were-none",
        "title": "And Then There Were None",
        "author": "Agatha Christie",
        "genre": "Detective Fiction",
        "rating": 4.9,
        "page_count": 272,
        "synopsis": "Ten strangers are lured to an isolated mansion on an island off Devon, where one by one they are accused of crimes and murdered according to a nursery rhyme.",
        "tags": ["detective", "murder mystery", "agatha christie", "whodunit", "thriller"],
        "cover_url": "https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=600&auto=format&fit=crop&q=80",
    },
    {
        "id": "the-cuckoos-calling",
        "title": "The Cuckoo's Calling",
        "author": "Robert Galbraith",
        "genre": "Detective Fiction",
        "rating": 4.6,
        "page_count": 464,
        "synopsis": "War veteran turned private investigator Cormoran Strike delves into the suspicious death of a troubled supermodel in London.",
        "tags": ["detective", "private investigator", "crime", "modern mystery", "london"],
        "cover_url": "https://images.unsplash.com/photo-1476275466078-4007374efbbe?w=600&auto=format&fit=crop&q=80",
    },
]

SAMPLE_READING_LIST = [
    {
        "id": "item-1",
        "title": "Project Hail Mary",
        "author": "Andy Weir",
        "status": "completed",
        "rating": 5,
        "notes": "Absolutely loved Rocky! Outstanding hard science fiction.",
        "genre": "Science Fiction",
    },
    {
        "id": "item-2",
        "title": "Tomorrow, and Tomorrow, and Tomorrow",
        "author": "Gabrielle Zevin",
        "status": "reading",
        "rating": None,
        "notes": "On chapter 8, great character depth.",
        "genre": "Literary Fiction",
    },
    {
        "id": "item-3",
        "title": "The Name of the Wind",
        "author": "Patrick Rothfuss",
        "status": "want_to_read",
        "rating": None,
        "notes": "Recommended by a friend.",
        "genre": "Fantasy",
    },
]


def seed_database():
    db = firestore.Client(project=FIRESTORE_PROJECT)
    print(f"Connected to Firestore project: {db.project}")

    # Seed Books catalog collection
    books_ref = db.collection("books")
    for book in SAMPLE_BOOKS:
        doc_id = book["id"]
        data = {k: v for k, v in book.items() if k != "id"}
        books_ref.document(doc_id).set(data, merge=True)
        print(f"  ✓ Seeded catalog book: {book['title']}")

    # Seed Reading List collection
    reading_ref = db.collection("reading_list")
    for item in SAMPLE_READING_LIST:
        doc_id = item["id"]
        data = {k: v for k, v in item.items() if k != "id"}
        reading_ref.document(doc_id).set(data, merge=True)
        print(f"  ✓ Seeded reading list item: {item['title']} [{item['status']}]")

    print("\n✅ Seeding complete!")


if __name__ == "__main__":
    seed_database()
