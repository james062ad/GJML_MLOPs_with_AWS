import streamlit as st
import requests
import time
from datetime import datetime

# Custom CSS for improved styling


def apply_custom_css():
    st.markdown("""
    <style>
    /* Main container styling */
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }
    
    /* Header styling */
    .header-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
        background-color: #f0f2f6;
        border-radius: 10px;
    }
    
    /* Chat message styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
    }
    
    /* User message styling */
    .stChatMessage[data-testid="stChatMessage"][data-role="user"] {
        background-color: #e6f3ff;
    }
    
    /* Assistant message styling */
    .stChatMessage[data-testid="stChatMessage"][data-role="assistant"] {
        background-color: #f0f2f6;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f0f2f6;
    }
    
    /* Button styling */
    .stButton button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        font-weight: bold;
    }
    
    /* Input field styling */
    .stTextInput input {
        border-radius: 5px;
        border: 1px solid #ccc;
    }
    
    /* Error message styling */
    .error-message {
        color: #d32f2f;
        font-weight: bold;
        padding: 0.5rem;
        border-radius: 5px;
        background-color: #ffebee;
    }
    </style>
    """, unsafe_allow_html=True)


def query_fastapi(query, top_k=5, max_tokens=200, temperature=0.7):
    """Send a query to the FastAPI backend and return the response."""
    url = "http://localhost:8000/generate"
    params = {
        "query": query,
        "top_k": top_k,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()  # Raise an error for bad responses (4xx, 5xx)
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


def display_header():
    """Display the app header with title and description."""
    st.markdown('<div class="header-container">', unsafe_allow_html=True)
    st.title("🤖 AI Assistant")
    st.markdown(
        "Ask me anything! I'll use the FastAPI backend to generate responses.")
    st.markdown('</div>', unsafe_allow_html=True)


def display_sidebar():
    """Display sidebar with controls and information."""
    with st.sidebar:
        st.header("⚙️ Settings")

        # Model parameters
        st.subheader("Model Parameters")
        top_k = st.slider("Top K", min_value=1, max_value=10, value=5,
                          help="Number of top results to consider")
        st.session_state["top_k"] = top_k

        max_tokens = st.slider("Max Tokens", min_value=50, max_value=500, value=200,
                               help="Maximum number of tokens in the response")
        st.session_state["max_tokens"] = max_tokens

        temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.7,
                                help="Higher values make the output more random, lower values more deterministic")
        st.session_state["temperature"] = temperature

        # Clear chat button
        if st.button("🗑️ Clear Chat History"):
            st.session_state["messages"] = []
            st.rerun()

        # App information
        st.markdown("---")
        st.subheader("ℹ️ About")
        st.markdown("""
        This app uses a FastAPI backend to generate responses to your questions.
        The backend processes your query and returns relevant information.
        """)

        # Footer
        st.markdown("---")
        st.markdown("Made with ❤️ using Streamlit")


def display_chat_message(message, role):
    """Display a chat message with timestamp."""
    with st.chat_message(role):
        st.markdown(message["content"])
        # Add timestamp if available
        if "timestamp" in message:
            st.caption(f"Sent at {message['timestamp']}")


def main():
    # Set page configuration - MUST BE THE FIRST STREAMLIT COMMAND
    st.set_page_config(
        page_title="AI Assistant",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply custom CSS
    apply_custom_css()

    # Display header
    display_header()

    # Display sidebar
    display_sidebar()

    # Initialize chat history if not already set
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Display chat history
    for msg in st.session_state["messages"]:
        display_chat_message(msg, msg["role"])

    # User input field
    query = st.chat_input("Ask something...")
    if query:
        # Get parameters from sidebar
        top_k = st.session_state.get("top_k", 5)
        max_tokens = st.session_state.get("max_tokens", 200)
        temperature = st.session_state.get("temperature", 0.7)

        # Display user message
        timestamp = datetime.now().strftime("%H:%M:%S")
        user_message = {"role": "user",
                        "content": query, "timestamp": timestamp}
        st.session_state["messages"].append(user_message)
        display_chat_message(user_message, "user")

        # Show loading spinner while waiting for response
        with st.spinner("Thinking..."):
            # Get response from FastAPI backend
            response = query_fastapi(query, top_k, max_tokens, temperature)

            if "error" in response:
                answer = f"⚠️ Error: {response['error']}"
            else:
                answer = response.get("response", "No response from server.")

            # Display bot response
            timestamp = datetime.now().strftime("%H:%M:%S")
            assistant_message = {"role": "assistant",
                                 "content": answer, "timestamp": timestamp}
            st.session_state["messages"].append(assistant_message)
            display_chat_message(assistant_message, "assistant")


if __name__ == "__main__":
    main()
