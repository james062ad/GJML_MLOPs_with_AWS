import streamlit as st
import requests
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# 💄 Custom CSS for Styling
# ─────────────────────────────────────────────────────────────


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

# ─────────────────────────────────────────────────────────────
# 🔗 Backend Query Function
# ─────────────────────────────────────────────────────────────


def query_fastapi(query, top_k=5, max_tokens=200, temperature=0.7, provider="openai"):
    """Send a query to the FastAPI backend and return the response."""
    url = "http://localhost:8000/generate"
    params = {
        "query": query,
        "top_k": top_k,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "provider": provider  # Send selected LLM provider to backend
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# ─────────────────────────────────────────────────────────────
# 🧱 App UI Sections
# ─────────────────────────────────────────────────────────────


def display_header():
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("🤖 AI Assistant")
    st.markdown(
        "Ask me anything! The assistant uses a FastAPI backend to generate intelligent responses.")
    st.markdown('</div>', unsafe_allow_html=True)


def display_sidebar():
    """Display sidebar with control panel."""
    with st.sidebar:
        st.header("⚙️ Settings")

        # 🔄 MODEL SELECTION UI (IMPORTANT!)
        st.subheader("🔁 Select LLM Provider")
        llm_provider = st.selectbox(
            "Choose a model provider",
            options=["openai", "bedrock", "ollama"],  # extend here
            index=0,
            help="Select which LLM backend to use"
        )
        st.session_state["llm_provider"] = llm_provider

        # Model parameters
        st.subheader("Model Parameters")
        top_k = st.slider("Top K", 1, 10, 5)
        st.session_state["top_k"] = top_k

        max_tokens = st.slider("Max Tokens", 50, 500, 200)
        st.session_state["max_tokens"] = max_tokens

        temperature = st.slider("Temperature", 0.0, 1.0, 0.7)
        st.session_state["temperature"] = temperature

        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state["messages"] = []
            st.rerun()

        # About
        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown(
            "This assistant is backed by FastAPI and integrates with various LLM providers.")
        st.markdown("Supports OpenAI, AWS Bedrock, Ollama, and more.")
        st.markdown("---")
        st.markdown("Made with ❤️ using Streamlit")


def display_chat_message(message, role):
    with st.chat_message(role):
        st.markdown(message["content"])
        if "timestamp" in message:
            st.caption(f"Sent at {message['timestamp']}")

# ─────────────────────────────────────────────────────────────
# 🚀 Main App Logic
# ─────────────────────────────────────────────────────────────


def main():
    # Must come first
    st.set_page_config(
        page_title="AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    apply_custom_css()
    display_header()
    display_sidebar()

    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Render past messages
    for msg in st.session_state["messages"]:
        display_chat_message(msg, msg["role"])

    # Input field
    query = st.chat_input("Ask something...")
    if query:
        top_k = st.session_state.get("top_k", 5)
        max_tokens = st.session_state.get("max_tokens", 200)
        temperature = st.session_state.get("temperature", 0.7)
        provider = st.session_state.get("llm_provider", "openai")

        timestamp = datetime.now().strftime("%H:%M:%S")
        user_message = {"role": "user",
                        "content": query, "timestamp": timestamp}
        st.session_state["messages"].append(user_message)
        display_chat_message(user_message, "user")

        with st.spinner(f"Thinking with {provider}..."):
            response = query_fastapi(
                query, top_k, max_tokens, temperature, provider)

            if "error" in response:
                answer = f"⚠️ Error: {response['error']}"
            else:
                answer = response.get("response", "No response from server.")

            timestamp = datetime.now().strftime("%H:%M:%S")
            assistant_message = {"role": "assistant",
                                 "content": answer, "timestamp": timestamp}
            st.session_state["messages"].append(assistant_message)
            display_chat_message(assistant_message, "assistant")


if __name__ == "__main__":
    main()
