import streamlit as st
import requests
from datetime import datetime


def apply_custom_css():
    st.markdown("""
    <style>
    .main .block-container { max-width: 1000px; padding-top: 2rem; }
    .header-container { text-align: center; padding: 1rem 0; margin-bottom: 2rem; background-color: #f0f2f6; border-radius: 10px; }
    .stChatMessage { padding: 1rem; border-radius: 10px; margin-bottom: 1rem; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .stChatMessage[data-testid="stChatMessage"][data-role="user"] { background-color: #e6f3ff; }
    .stChatMessage[data-testid="stChatMessage"][data-role="assistant"] { background-color: #f0f2f6; }
    .css-1d391kg { background-color: #f0f2f6; }
    .stButton button { background-color: #4CAF50; color: white; border-radius: 5px; padding: 0.5rem 1rem; font-weight: bold; }
    .stTextInput input { border-radius: 5px; border: 1px solid #ccc; }
    .error-message { color: #d32f2f; font-weight: bold; padding: 0.5rem; border-radius: 5px; background-color: #ffebee; }
    </style>
    """, unsafe_allow_html=True)


def query_fastapi(query, top_k=5, max_tokens=200, temperature=0.7):
    url = "http://localhost:8000/generate"
    params = {
        "query": query,
        "top_k": top_k,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "llm_provider": st.session_state.get("llm_provider"),
        "embedding_provider": st.session_state.get("embedding_provider")
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def display_header():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("🤖 AI Assistant")
    st.markdown(
        "Ask me anything! I'll use the FastAPI backend to generate responses.")
    st.markdown('</div>', unsafe_allow_html=True)


def display_sidebar():
    with st.sidebar:
        st.header("⚙️ Settings")

        model_mode = st.selectbox(
            "Model Configuration",
            options=[
                "OpenAI + SentenceTransformer",
                "OpenAI (Embedding + LLM)",
                "Bedrock",
                "Cohere",
                "Ollama",
                "Google PaLM"
            ],
            index=0
        )

        provider_map = {
            "OpenAI + SentenceTransformer": ("openai", "sentence-transformer"),
            "OpenAI (Embedding + LLM)": ("openai", "openai"),
            "Bedrock": ("bedrock", "bedrock"),
            "Cohere": ("cohere", "cohere"),
            "Ollama": ("ollama", "sentence-transformer"),
            "Google PaLM": ("google", "google")
        }

        llm, emb = provider_map[model_mode]

        if "llm_provider" in st.session_state and st.session_state["llm_provider"] != llm:
            st.session_state["db_is_fresh"] = False
        if "embedding_provider" in st.session_state and st.session_state["embedding_provider"] != emb:
            st.session_state["db_is_fresh"] = False

        st.session_state["llm_provider"] = llm
        st.session_state["embedding_provider"] = emb
        if "db_is_fresh" not in st.session_state:
            st.session_state["db_is_fresh"] = True

        st.markdown(f"🔁 **LLM**: `{llm}` | **Embedding**: `{emb}`")

        with st.expander("🔧 Advanced Parameters", expanded=False):
            st.session_state["top_k"] = st.slider(
                "Top K", 1, 10, 5, help="How many top matching chunks to retrieve")
            st.session_state["max_tokens"] = st.slider(
                "Max Tokens", 50, 2000, 300, help="Maximum number of tokens in the generated answer")
            st.session_state["temperature"] = st.slider(
                "Temperature", 0.0, 1.0, 0.7, help="Controls creativity. Lower = more focused.")
            st.session_state["chunk_size"] = st.slider(
                "Chunk Size", 128, 2048, 512, help="Token count per chunk in document ingestion")
            st.session_state["overlap"] = st.slider(
                "Overlap", 0, 512, 50, help="Overlap between chunks to avoid breaking up ideas")

        if st.button("🗑️ Clear Chat History"):
            st.session_state["messages"] = []
            st.rerun()

        st.subheader("🛠️ Vector Database Control")
        st.caption(
            "Rebuilds the pgvector table and reruns ingestion based on the current embedding model.")
        if st.button("Rebuild Vector DB"):
            with st.spinner("🔄 Rebuilding vector DB..."):
                try:
                    response = requests.post(
                        "http://localhost:8000/rebuild",
                        params={
                            "json_dir": "./papers-downloads",
                            "output_file": "init/processed_papers.json",
                            "chunk_size": st.session_state["chunk_size"],
                            "overlap": st.session_state["overlap"],
                            "embedding_provider": st.session_state["embedding_provider"]
                        }
                    )
                    result = response.json()
                    st.code(result, language="json")
                    message = result.get("message") or result.get(
                        "detail", "No message returned")
                    if result.get("status") == "success":
                        st.success(f"✅ {message}")
                        st.session_state["db_is_fresh"] = True
                    else:
                        st.error("❌ Rebuild incomplete or returned no message.")
                except Exception as e:
                    st.error("❌ Rebuild failed with unexpected error.")
                    st.code(str(e))

        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown(
            "This app uses a FastAPI backend to generate responses to your questions.")
        st.caption(
            "💡 To use Google PaLM, you need a valid API key and enabled Vertex AI access.")
        st.markdown("Made with ❤️ using Streamlit")


def display_chat_message(message, role):
    with st.chat_message(role):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"Sent at {message['timestamp']}")


def main():
    st.set_page_config(page_title="AI Assistant", page_icon="🤖",
                       layout="wide", initial_sidebar_state="expanded")
    apply_custom_css()
    display_header()
    display_sidebar()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        display_chat_message(msg, msg["role"])

    if not st.session_state.get("db_is_fresh", False):
        st.info("ℹ️ Vector DB is not ready. Please rebuild it above.")
        st.chat_input("Ask something...", disabled=True)
    else:
        st.success("✅ Vector database is ready.")
        query = st.chat_input("Ask something...")
        if query:
            top_k = st.session_state.get("top_k", 5)
            max_tokens = st.session_state.get("max_tokens", 200)
            temperature = st.session_state.get("temperature", 0.7)

            timestamp = datetime.now().strftime("%H:%M:%S")
            user_message = {"role": "user",
                            "content": query, "timestamp": timestamp}
            st.session_state["messages"].append(user_message)
            display_chat_message(user_message, "user")

            with st.spinner("Thinking..."):
                response = query_fastapi(query, top_k, max_tokens, temperature)
                answer = response.get(
                    "response", f"⚠️ Error: {response.get('error', 'Unknown error')}")
                assistant_message = {"role": "assistant",
                                     "content": answer, "timestamp": timestamp}
                st.session_state["messages"].append(assistant_message)
                display_chat_message(assistant_message, "assistant")


if __name__ == "__main__":
    main()
