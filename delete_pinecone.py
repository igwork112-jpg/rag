"""
Quick script to delete all records from Pinecone.
Run: python delete_pinecone.py
"""
import os
from dotenv import load_dotenv
from pinecone import Pinecone

load_dotenv()

# Initialize Pinecone
pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
index_name = os.getenv("PINECONE_INDEX_NAME", "shopify-products")

print(f"Connecting to Pinecone index: {index_name}")
index = pc.Index(index_name)

# Get stats before deletion
stats = index.describe_index_stats()
print(f"Current vector count: {stats.get('total_vector_count', 0)}")

# Delete all vectors
print("Deleting all records...")
index.delete(delete_all=True, namespace="")

# Delete from other namespaces if any
for namespace in stats.get("namespaces", {}).keys():
    if namespace:
        index.delete(delete_all=True, namespace=namespace)

print("✓ All records deleted successfully!")
