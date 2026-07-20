import os 
from pinecone import Pinecone, ServerlessSpec
from langchain_pinecone import PineconeVectorStore
from langchain_community.embeddings import HuggingFaceInferenceAPIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

PINECONE_INDEX_NAME = os.getenv("PINECONE_INDEX_NAME", "meeting-transcript")

def get_embeddings():
    api_key = os.getenv("HF_API_KEY")
    if not api_key:
        raise ValueError("HF_API_KEY environment variable is not set. Please set it in your .env file or configuration.")
    return HuggingFaceInferenceAPIEmbeddings(
        api_key=api_key,
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )

def get_pinecone_index():
    api_key = os.getenv("PINECONE_API_KEY")
    if not api_key:
        raise ValueError("PINECONE_API_KEY environment variable is not set. Please add it to your .env file or configure it in the application sidebar.")
    
    # Initialize Pinecone Client
    pc = Pinecone(api_key=api_key)
    
    # Check if index exists, and create if it doesn't
    existing_indexes = [index.name for index in pc.list_indexes()]
    if PINECONE_INDEX_NAME not in existing_indexes:
        print(f"Creating Pinecone index: {PINECONE_INDEX_NAME}...")
        pc.create_index(
            name=PINECONE_INDEX_NAME,
            dimension=384, # all-MiniLM-L6-v2 embedding dimension is 384
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
    return PINECONE_INDEX_NAME

def build_vector_store(transcript : str)->PineconeVectorStore:
    print("Building Pinecone vector store...")
    
    index_name = get_pinecone_index()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50
    )
    chunks = splitter.split_text(transcript)

    docs = [
        Document(page_content=chunk, metadata = {'chunk_index' : i})
        for i,chunk in enumerate(chunks)
    ]

    embeddings = get_embeddings()
    
    # Clear previous vectors from the index so transcripts don't bleed into each other
    try:
        pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
        index = pc.Index(index_name)
        index.delete(delete_all=True)
        print("Cleared previous vectors in Pinecone index.")
    except Exception as e:
        print(f"Warning: Could not clear previous vectors: {e}")

    vector_store = PineconeVectorStore.from_documents(
        documents= docs,
        embedding=embeddings,
        index_name=index_name
    )

    return vector_store

def load_vector_store() ->PineconeVectorStore:
    index_name = get_pinecone_index()
    embeddings = get_embeddings()
    vector_store = PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings
    )
    return vector_store

def get_retriever(vector_store : PineconeVectorStore, k :int = 4):
    return vector_store.as_retriever(
        search_type = 'similarity',
        search_kwargs = {"k":k}
    )