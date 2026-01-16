import marqo
import json
import os

# Configuration
MARQO_URL = "http://localhost:8882"
INDEX_NAME = "oan_index"
SETTINGS_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../assets/marqo_settings.json"))

# Dummy Data
documents = [
    {
        "doc_id": "1",
        "type": "scheme",
        "source": "government",
        "name": "Pradhan Mantri Fasal Bima Yojana (PMFBY)",
        "text": "The Pradhan Mantri Fasal Bima Yojana (PMFBY) aims to provide insurance coverage and financial support to the farmers in the event of failure of any of the notified crops as a result of natural calamities, pests & diseases. It stabilizes the income of farmers to ensure their continuance in farming."
    },
    {
        "doc_id": "2",
        "type": "guide",
        "source": "agriculture_dept",
        "name": "Organic Farming Basics",
        "text": "Organic farming is an agricultural system that uses fertilizers of organic origin such as compost manure, green manure, and bone meal and places emphasis on techniques such as crop rotation and companion planting. It forbids the use of synthetic fertilizers and pesticides."
    },
    {
        "doc_id": "3",
        "type": "scheme",
        "source": "government",
        "name": "Kisan Credit Card (KCC)",
        "text": "The Kisan Credit Card scheme provides adequate and timely credit support from the banking system under a single window with typical needs of the farmers for their cultivation and other needs such as post-harvest expenses, produce marketing loan, consumption requirements of farmer household, etc."
    },
    {
        "doc_id": "4",
        "type": "article",
        "source": "agri_news",
        "name": "Modern Irrigation Techniques",
        "text": "Drip irrigation and sprinkler irrigation are modern techniques that save water and increase yield. Drip irrigation delivers water directly to the plant's roots, minimizing evaporation."
    },
    {
        "doc_id": "5",
        "type": "scheme",
        "source": "government",
        "name": "Soil Health Card Scheme",
        "text": "The Soil Health Card Scheme is a scheme launched by the Government of India in 2015. The scheme aims at issuing soil health cards to farmers every two years so as to provide a basis to address nutrient deficiencies in fertilization practices."
    }
]

def main():
    # Initialize Marqo Client
    print(f"Connecting to Marqo at {MARQO_URL}...")
    try:
        mq = marqo.Client(url=MARQO_URL)
    except Exception as e:
        print(f"Error connecting to Marqo: {e}")
        return

    # Load Settings
    print(f"Loading settings from {SETTINGS_PATH}...")
    try:
        with open(SETTINGS_PATH, "r") as f:
            settings = json.load(f)
    except FileNotFoundError:
        print(f"Settings file not found at {SETTINGS_PATH}. Please check the path.")
        return
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from {SETTINGS_PATH}: {e}")
        return

    # Create Index
    print(f"Creating index '{INDEX_NAME}'...")
    try:
        # Check if index exists, delete if it does to start fresh
        try:
             mq.index(INDEX_NAME).delete()
             print(f"Deleted existing index '{INDEX_NAME}'.")
        except Exception:
             # Index likely doesn't exist
             pass
        
        mq.create_index(index_name=INDEX_NAME, settings_dict=settings)
        print(f"Index '{INDEX_NAME}' created successfully.")
    except Exception as e:
        print(f"Error creating index: {e}")
        return

    # Ingest Documents
    print("Ingesting documents...")
    try:
        # Note: tensor_fields is optional if defined in settings, but explicitly passing it is often safer if unsure of version match
        # However, relying on the settings 'tensorFields' is the clean way.
        res = mq.index(INDEX_NAME).add_documents(documents=documents, tensor_fields=["text"])
        print(f"Ingestion response: {res}")
    except Exception as e:
        print(f"Error ingesting documents: {e}")
        return

    # Check Index Stats
    print("Checking index stats...")
    try:
        stats = mq.index(INDEX_NAME).get_stats()
        print(f"Index Stats: {stats}")
    except Exception as e:
        print(f"Error getting stats: {e}")

    # Search Documents
    query = "farming subsidy and insurance"
    print(f"\nSearching for '{query}'...")
    try:
        search_results = mq.index(INDEX_NAME).search(q=query, limit=5)
        print("Search Results:")
        for res in search_results['hits']:
            # Handle potential missing keys if structure varies
            name = res.get('name', 'Unknown')
            text = res.get('text', '')
            score = res.get('_score', 0)
            print(f"- {name} (Score: {score}): {text[:100]}...")
    except Exception as e:
        print(f"Error searching: {e}")

if __name__ == "__main__":
    main()
