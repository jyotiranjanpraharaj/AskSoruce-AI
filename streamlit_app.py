import streamlit as st
import os
import tempfile
import shutil
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import core modules
from utils.audio_processor import process_input
from core.transcriber import transcribe_all
from core.summarizer import summarize, generate_title
from core.extractor import extract_action_items, extract_key_decisions, extract_questions
from core.rag_engine import build_rag_chain, ask_question, load_rag_chain

# Streamlit Page Config
st.set_page_config(
    page_title="AskSource-AI | Video & Audio Assistant",
    page_icon="🎥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling for premium look (white and light-green accents)
st.markdown("""
<style>
    :root {
        --primary-color: #84cc16;
    }
    .main-title {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.1rem;
        color: #6b7280;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #84cc16;
        color: white;
        border-radius: 8px;
        border: none;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #65a30d;
        color: white;
        border: none;
    }
    .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Helper to check API keys
def check_api_keys():
    groq_ok = bool(os.getenv("GROQ_API_KEY"))
    mistral_ok = bool(os.getenv("MISTRAL_API_KEY"))
    return groq_ok, mistral_ok

# Sidebar Config
with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=80)
    st.title("Settings")
    st.markdown("---")
    
    groq_ok, mistral_ok = check_api_keys()
    
    # GROQ API Key
    if not groq_ok:
        groq_key = st.text_input("Enter Groq API Key:", type="password")
        if groq_key:
            os.environ["GROQ_API_KEY"] = groq_key
            st.success("Groq API Key set for this session!")
    else:
        st.success("✅ Groq API Key Loaded")
        
    # Mistral API Key
    if not mistral_ok:
        mistral_key = st.text_input("Enter Mistral API Key:", type="password")
        if mistral_key:
            os.environ["MISTRAL_API_KEY"] = mistral_key
            st.success("Mistral API Key set for this session!")
    else:
        st.success("✅ Mistral API Key Loaded")
        
    st.markdown("---")
    st.markdown("### About AskSource-AI")
    st.info(
        "AskSource-AI is a meeting and audio assistant that uses **Groq Whisper** for fast transcription "
        "and **Mistral AI** for summarizing, extracting action items, and context-aware Q&A."
    )

# Main App Container
st.markdown("<div class='main-title'>🎥 AskSource-AI Video & Meeting Assistant</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>Ingest YouTube videos or local audio files to transcribe, extract deliverables, and chat with the transcript.</div>", unsafe_allow_html=True)

# Session State Initialization
if "pipeline_result" not in st.session_state:
    st.session_state.pipeline_result = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = None

# Input Sources Setup
col1, col2 = st.columns([2, 1])

with col1:
    source_type = st.radio("Select Audio Source Type:", ["YouTube URL", "Local Audio File"], horizontal=True)

    if source_type == "YouTube URL":
        source_input = st.text_input("Paste YouTube Video URL:", placeholder="https://www.youtube.com/watch?v=...")
    else:
        uploaded_file = st.file_uploader("Upload an Audio File:", type=["wav", "mp3", "m4a", "ogg", "aac"])
        source_input = None
        if uploaded_file:
            # Create downloades directory if not exists
            os.makedirs("downloades", exist_ok=True)
            temp_file_path = os.path.join("downloades", uploaded_file.name)
            with open(temp_file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            source_input = temp_file_path

with col2:
    language = st.selectbox("Transcription Language:", ["english", "hinglish"], index=0)

# Process Button
if st.button("Start AI Assistant Pipeline"):
    # Validate keys
    groq_ok, mistral_ok = check_api_keys()
    if not groq_ok or not mistral_ok:
        st.error("Please ensure both Groq and Mistral API keys are configured (either in `.env` or the sidebar) before starting.")
    elif not source_input:
        st.error("Please enter a YouTube URL or upload an audio file.")
    else:
        try:
            status_container = st.container()
            with status_container:
                # 1. Download/Ingest
                with st.spinner("Step 1/5: Downloading and preparing audio (converting to 16kHz mono WAV)..."):
                    chunks = process_input(source_input)
                st.success("✅ Step 1/5: Audio converted and chunked!")

                # 2. Transcription
                with st.spinner(f"Step 2/5: Transcribing {len(chunks)} chunk(s) via Groq Whisper..."):
                    transcript = transcribe_all(chunks, language)
                st.success("✅ Step 2/5: Transcription complete!")

                # 3. Title Generation
                with st.spinner("Step 3/5: Generating title and summarizing..."):
                    title = generate_title(transcript)
                    summary = summarize(transcript)
                st.success("✅ Step 3/5: Summary generated!")

                # 4. Deliverables Extraction
                with st.spinner("Step 4/5: Extracting action items, key decisions, and questions..."):
                    action_items = extract_action_items(transcript)
                    decisions = extract_key_decisions(transcript)
                    questions = extract_questions(transcript)
                st.success("✅ Step 4/5: Meeting deliverables extracted!")

                # 5. Indexing for RAG
                with st.spinner("Step 5/5: Indexing transcript to vector database for RAG chat..."):
                    rag_chain = build_rag_chain(transcript)
                st.success("✅ Step 5/5: Indexed in Chroma DB! Pipeline finished.")

            # Store result in state
            st.session_state.pipeline_result = {
                "title": title,
                "transcript": transcript,
                "summary": summary,
                "action_items": action_items,
                "key_decisions": decisions,
                "open_questions": questions,
            }
            st.session_state.rag_chain = rag_chain
            st.session_state.chat_history = []  # reset chat for new source
            
            # Clean up temp upload file if local
            if source_type == "Local Audio File" and os.path.exists(source_input):
                try:
                    os.remove(source_input)
                except Exception:
                    pass
            
            st.rerun()

        except Exception as e:
            st.error(f"Pipeline error: {str(e)}")
            # Cleanup local temp file if error occurs
            if source_type == "Local Audio File" and source_input and os.path.exists(source_input):
                try:
                    os.remove(source_input)
                except Exception:
                    pass

st.markdown("---")

# Display Results if Available
if st.session_state.pipeline_result:
    res = st.session_state.pipeline_result
    st.markdown(f"### 📌 Analysis: {res['title']}")
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "📋 Summary & Highlights", 
        "✅ Meeting Deliverables", 
        "📜 Transcript", 
        "💬 Chat Assistant"
    ])
    
    with tab1:
        st.subheader("Executive Summary")
        st.markdown(res["summary"])
        
    with tab2:
        col_act, col_dec, col_que = st.columns(3)
        with col_act:
            st.markdown("#### ✅ Action Items")
            st.markdown(res["action_items"])
        with col_dec:
            st.markdown("#### 🔑 Key Decisions")
            st.markdown(res["key_decisions"])
        with col_que:
            st.markdown("#### ❓ Open Questions")
            st.markdown(res["open_questions"])
            
    with tab3:
        st.subheader("Raw Transcript")
        st.text_area("Full transcript content:", res["transcript"], height=400)
        st.download_button(
            label="Download Transcript (TXT)",
            data=res["transcript"],
            file_name=f"{res['title'].replace(' ', '_')}_transcript.txt",
            mime="text/plain"
        )
        
    with tab4:
        st.subheader("Chat with your Meeting")
        st.write("Ask questions about the meeting content, participants, decisions, or timeline.")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.write(msg["content"])
                
        # Chat input
        question = st.chat_input("Ask a question about the transcript...")
        if question:
            # Display user message
            with st.chat_message("user"):
                st.write(question)
            st.session_state.chat_history.append({"role": "user", "content": question})
            
            # Answer generation
            with st.chat_message("assistant"):
                with st.spinner("Searching transcript..."):
                    try:
                        # Rebuild RAG chain if not available (e.g. after rerun/app state cleanup)
                        if st.session_state.rag_chain is None:
                            st.session_state.rag_chain = load_rag_chain()
                        
                        answer = ask_question(st.session_state.rag_chain, question)
                        st.write(answer)
                        st.session_state.chat_history.append({"role": "assistant", "content": answer})
                    except Exception as e:
                        st.error(f"Error answering question: {str(e)}")
else:
    st.info("No audio analysis is active. Ingest a YouTube URL or upload an audio file to see results.")
