import streamlit as st
from chatpdf import load_vectordb, get_qa_chain
import os

# Set page config
st.set_page_config(
    page_title="IntelliDocAI", 
    page_icon="🤖", 
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Minimal CSS inspired by ChatGPT
st.markdown("""
<style>
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container */
    .main {
        padding: 1rem 0;
        max-width: 48rem;
        margin: 0 auto;
    }
    
    /* Header */
    .app-header {
        text-align: center;
        padding: 2rem 0 1rem 0;
        border-bottom: 1px solid #e5e5e5;
        margin-bottom: 2rem;
    }
    
    .app-title {
        font-size: 1.5rem;
        font-weight: 600;
        color: #374151;
        margin: 0;
    }
    
    .app-subtitle {
        font-size: 0.875rem;
        color: #6b7280;
        margin: 0.25rem 0 0 0;
    }
    
    /* Chat messages */
    .chat-message {
        display: flex;
        margin-bottom: 1.5rem;
        padding: 0;
    }
    
    .message-content {
        max-width: 100%;
        padding: 1rem 1.25rem;
        border-radius: 0.75rem;
        font-size: 0.95rem;
        line-height: 1.6;
    }
    
    .user-message {
        justify-content: flex-end;
    }
    
    .user-message .message-content {
        background-color: #f3f4f6;
        color: #374151;
        margin-left: 3rem;
    }
    
    .assistant-message {
        justify-content: flex-start;
    }
    
    .assistant-message .message-content {
        background-color: #ffffff;
        color: #374151;
        border: 1px solid #e5e7eb;
        margin-right: 3rem;
    }
    
    /* Chat input styling */
    .stChatInput {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        border-top: 1px solid #e5e7eb;
        padding: 1rem;
        z-index: 1000;
    }
    
    .stChatInput > div {
        max-width: 48rem;
        margin: 0 auto;
    }
    
    .stChatInput input {
        border: 1px solid #d1d5db;
        border-radius: 0.75rem;
        padding: 0.875rem 1rem;
        font-size: 0.95rem;
        transition: border-color 0.15s ease;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    .stChatInput input:focus {
        outline: none;
        border-color: #3b82f6;
        box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
    }
    
    /* Welcome message */
    .welcome-message {
        text-align: center;
        padding: 3rem 2rem;
        color: #6b7280;
    }
    
    .welcome-title {
        font-size: 1.25rem;
        font-weight: 600;
        color: #374151;
        margin-bottom: 0.5rem;
    }
    
    .welcome-text {
        font-size: 0.95rem;
        line-height: 1.6;
        max-width: 32rem;
        margin: 0 auto;
    }
    
    /* Error message */
    .error-message {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #dc2626;
        padding: 1rem 1.25rem;
        border-radius: 0.5rem;
        margin: 2rem 0;
        text-align: center;
    }
    
    /* Spacing for fixed input */
    .main-content {
        padding-bottom: 6rem;
    }
    
    /* Spinner styling */
    .stSpinner > div {
        border-color: #3b82f6 transparent transparent transparent !important;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="app-header">
    <h1 class="app-title">IntelliDocAI</h1>
    <p class="app-subtitle">Ask questions about your documents</p>
</div>
""", unsafe_allow_html=True)

# Main content
st.markdown('<div class="main-content">', unsafe_allow_html=True)

try:
    # Load vector DB and QA chain
    vectordb = load_vectordb()
    qa_chain = get_qa_chain(vectordb)
    
    # Initialize chat history
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    # Welcome message if no chat history
    if not st.session_state.chat_history:
        st.markdown("""
        <div class="welcome-message">
            <div class="welcome-title">How can I help you today?</div>
            <div class="welcome-text">
                I can help you find information, answer questions related to Zohaib's care.
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # Display chat history
    for role, message in st.session_state.chat_history:
        if role == "user":
            st.markdown(f"""
            <div class="chat-message user-message">
                <div class="message-content">{message}</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div class="chat-message assistant-message">
                <div class="message-content">{message}</div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Chat input
    if prompt := st.chat_input("Send a message..."):
        # Add user message to history
        st.session_state.chat_history.append(("user", prompt))
        
        # Show thinking spinner
        with st.spinner(""):
            # Get AI response
            result = qa_chain({"question": prompt})
            response = result["answer"]
            
            # Clean up the response
            clean_response = response.replace("According to the Clinic Policies Manual, ", "")
            clean_response = clean_response.replace("The manual states that ", "")
            clean_response = clean_response.replace("Based on the document, ", "")
            clean_response = clean_response.replace("According to the document, ", "")
            
        # Add AI response to history
        st.session_state.chat_history.append(("assistant", clean_response))
        
        # Rerun to show the new messages
        st.rerun()

except FileNotFoundError:
    st.markdown("""
    <div class="error-message">
        <strong>No documents found</strong><br>
        Please upload some PDF documents first to get started.
    </div>
    """, unsafe_allow_html=True)

except Exception as e:
    st.markdown(f"""
    <div class="error-message">
        <strong>Something went wrong</strong><br>
        {str(e)}
    </div>
    """, unsafe_allow_html=True)