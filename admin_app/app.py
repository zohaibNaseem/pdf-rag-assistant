import streamlit as st
import os
from chatpdf import process_and_save_pdfs
import hashlib

# Set page config
st.set_page_config(
    page_title="Admin Panel", 
    page_icon="🛡️", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for attractive interface
st.markdown("""
<style>
    .main {
        padding-top: 2rem;
    }
    
    .stFileUploader > div > div > div {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 20px;
        border: none;
    }
    
    .upload-section {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 30px;
        border-radius: 20px;
        margin: 20px 0;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    
    .file-list {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    
    .header-text {
        background: linear-gradient(90deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 30px;
    }
    
    .success-box {
        background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
        padding: 20px;
        border-radius: 15px;
        margin: 20px 0;
        border-left: 5px solid #28a745;
    }
    
    .file-item {
        background: white;
        padding: 15px;
        margin: 10px 0;
        border-radius: 10px;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .sidebar .element-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
        padding: 10px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

# Password protection
def check_password():
    """Returns True if the user has entered the correct password."""
    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if st.session_state["password"] == "admin123":  # Change this password as needed
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store password
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        # First run, show input for password
        st.markdown('<h1 class="header-text">🛡️ Admin Access Required</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                        padding: 30px; border-radius: 20px; text-align: center; color: white;">
                <h3>🔐 Enter Admin Password</h3>
                <p>Access restricted to authorized personnel only</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.text_input(
                "Password", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="Enter admin password..."
            )
        return False
    elif not st.session_state["password_correct"]:
        # Password not correct, show input + error
        st.markdown('<h1 class="header-text">🛡️ Admin Access Required</h1>', unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%); 
                        padding: 30px; border-radius: 20px; text-align: center; color: white;">
                <h3>❌ Access Denied</h3>
                <p>Incorrect password. Please try again.</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.text_input(
                "Password", 
                type="password", 
                on_change=password_entered, 
                key="password",
                placeholder="Enter admin password..."
            )
        return False
    else:
        # Password correct
        return True

if check_password():
    # Create data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)
    
    # Header
    st.markdown('<h1 class="header-text">🛡️ Admin Panel – Document Management System</h1>', unsafe_allow_html=True)
    
    # Sidebar for admin info
    with st.sidebar:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 20px; border-radius: 15px; color: white; text-align: center;">
            <h3>👨‍💼 Admin Dashboard</h3>
            <p>Manage your document library</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### 📊 System Status")
        
        # Count existing files
        data_files = [f for f in os.listdir("data") if f.endswith('.pdf')]
        st.metric("📄 Total Documents", len(data_files))
        
        # Check if embeddings exist
        embeddings_exist = os.path.exists("embeddings/docs_index.faiss")
        st.metric("🧠 Embeddings Status", "✅ Ready" if embeddings_exist else "❌ Not Ready")
        
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        # File upload section
        st.markdown("""
        <div class="upload-section">
            <h3 style="color: white; text-align: center; margin-bottom: 20px;">📤 Upload New Documents</h3>
        </div>
        """, unsafe_allow_html=True)
        
        uploaded_pdfs = st.file_uploader(
            "Choose PDF files", 
            type="pdf", 
            accept_multiple_files=True,
            help="Select one or more PDF files to upload"
        )
        
        if st.button("🚀 Process Documents", use_container_width=True, type="primary") and uploaded_pdfs:
            pdf_paths = []
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Save uploaded files
            for i, pdf in enumerate(uploaded_pdfs):
                status_text.text(f"Saving {pdf.name}...")
                progress_bar.progress((i + 1) / (len(uploaded_pdfs) + 1))
                
                path = os.path.join("data", pdf.name)
                with open(path, "wb") as f:
                    f.write(pdf.read())
                pdf_paths.append(path)
            
            # Process documents
            status_text.text("Processing and creating embeddings...")
            progress_bar.progress(1.0)
            
            try:
                process_and_save_pdfs(pdf_paths)
                st.markdown("""
                <div class="success-box">
                    <h4>✅ Success!</h4>
                    <p>PDFs processed and embeddings saved successfully!</p>
                </div>
                """, unsafe_allow_html=True)
                st.balloons()
            except Exception as e:
                st.error(f"❌ Error processing documents: {str(e)}")
            
            progress_bar.empty()
            status_text.empty()
    
    with col2:
        # Existing files section
        st.markdown("""
        <div class="file-list">
            <h3 style="color: white; text-align: center; margin-bottom: 20px;">📁 Existing Documents</h3>
        </div>
        """, unsafe_allow_html=True)
        
        data_files = [f for f in os.listdir("data") if f.endswith('.pdf')]
        
        if data_files:
            for file in data_files:
                file_path = os.path.join("data", file)
                file_size = os.path.getsize(file_path) / 1024  # Size in KB
                
                col_file, col_size, col_delete = st.columns([3, 1, 1])
                
                with col_file:
                    st.markdown(f"📄 **{file}**")
                
                with col_size:
                    st.markdown(f"*{file_size:.1f} KB*")
                
                with col_delete:
                    if st.button("🗑️", key=f"delete_{file}", help=f"Delete {file}"):
                        try:
                            os.remove(file_path)
                            st.success(f"✅ {file} deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Error deleting {file}: {str(e)}")
                
                st.divider()
        else:
            st.info("📁 No documents uploaded yet. Upload some PDFs to get started!")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 20px;">
        <p>🛡️ Admin Panel - IntelliDocAI System</p>
        <p>Manage your document library with ease</p>
    </div>
    """, unsafe_allow_html=True)