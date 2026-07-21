import os 
import ssl
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_mistralai import MistralAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "meeting-transcript")

def get_embeddings():
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        raise ValueError("MISTRAL_API_KEY environment variable is not set. Please set it in your .env file or configuration.")
    return MistralAIEmbeddings(
        mistral_api_key=api_key,
        model="mistral-embed"
    )

def get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is not set. Please add it to your .env file or configure it in the application sidebar.")
    
    # Initialize Pinecone Client
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists, and recreate if dimension is mismatched
    existing_indexes = [index.name for index in pc.list_indexes()]
    if PINECONE_INDEX_NAME in existing_indexes:
        try:
            desc = pc.describe_index(PINECONE_INDEX_NAME)
            if desc.dimension != 1024:
                print(f"Mismatched index dimension ({desc.dimension} vs 1024). Re-creating index...")
                pc.delete_index(PINECONE_INDEX_NAME)
                existing_indexes.remove(PINECONE_INDEX_NAME)
        except Exception as e:
            print(f"Warning: Could not check index dimension: {e}")
            
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=1024, # mistral-embed embedding dimension is 1024
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    return PINECONE_INDEX_NAME

def build_vector_store(transcript: str) -> PineconeVectorStore:
    print("Building Pinecone vector store...")
    
    index_name = get_pinecone_index()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata={'chunk_index': i})
        for i, chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    
    # Clear previous vectors from the index so transcripts don't bleed into each other
    try:
        api_key = os.getenv("PINECONE_API_KEY").strip()
        pc = Pinecone(api_key=api_key)
        index = pc.Index(index_name)
        index.delete(delete_all=True)
        print("Cleared previous vectors in Pinecone index.")
    except Exception as e:
        print(f"Warning: Could not clear previous vectors: {e}")

    vector_store = PineconeVectorStore.from_documents(
        documents=docs,
        embedding=embeddings,
        index_name=index_name
    )

    return vector_store

def load_vector_store() -> PineconeVectorStore:
    index_name = get_pinecone_index()
    embeddings = get_embeddings()
    vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )
    return vector_store

def get_retriever(vector_store: PineconeVectorStore, k: int = 4):
    return vector_store.as_retriever(
        search_type='similarity',
        search_kwargs={"k": k}
    )