import streamlit as st
import os
from PIL import Image
import io
import base64
import zipfile
from dotenv import load_dotenv
from services.ocr_service import OCRService
from services.vision_service import VisionService
from services.embedding_service import EmbeddingService
from services.search_service import SearchService

# Load environment variables from .env file
load_dotenv()

# Page config
st.set_page_config(
    page_title="SSSearch",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for ivory green theme
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: 700;
        color: #4A5D23;
        text-align: center;
        margin-bottom: 0.5rem;
        letter-spacing: 2px;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #7C9885;
        text-align: center;
        margin-bottom: 2rem;
        font-style: italic;
    }
    .search-container {
        background: linear-gradient(135deg, #F8F6F0 0%, #E8E6E0 100%);
        padding: 2rem;
        border-radius: 15px;
        border: 2px solid #7C9885;
        margin: 1rem 0;
    }
    .result-card {
        background: #FFFFFF;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #7C9885;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(124, 152, 133, 0.1);
    }
    .upload-zone {
        background: #F8F6F0;
        padding: 2rem;
        border-radius: 10px;
        border: 2px dashed #7C9885;
        text-align: center;
        margin: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #7C9885 0%, #A8C69F 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        margin: 0.5rem;
    }
    .stButton>button {
        background: linear-gradient(135deg, #7C9885 0%, #A8C69F 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(124, 152, 133, 0.3);
    }
    
    /* Hide sidebar completely */
    .css-1d391kg {
        display: none;
    }
    
    /* Hide the top bar/header area */
    .stAppHeader {
        display: none;
    }
    
    /* Remove extra padding */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">SSSearch</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Visual Memory Search</div>', unsafe_allow_html=True)
    
    # Initialize services and show loading status
    if not init_services():
        st.stop()  # Stop if initialization fails
    
    # Layout - single column, no sidebar
    render_upload_section()
    st.markdown("---")
    render_search_section()
    st.markdown("---")
    render_stats_section()

def init_services():
    """Initialize all services with proper error handling"""
    try:
        # Show initialization status
        if 'services_initialized' not in st.session_state:
            with st.container():
                status_placeholder = st.empty()
                
                # Initialize OCR service
                status_placeholder.info("🔧 Initializing OCR service...")
                if 'ocr_service' not in st.session_state:
                    st.session_state.ocr_service = OCRService()
                
                # Initialize Vision service
                status_placeholder.info("👁️ Initializing vision service...")
                if 'vision_service' not in st.session_state:
                    try:
                        api_key = os.getenv('ANTHROPIC_API_KEY')
                        if not api_key:
                            st.warning("⚠️ ANTHROPIC_API_KEY not found - visual analysis will be disabled")
                            st.session_state.vision_service = None
                        else:
                            st.session_state.vision_service = VisionService()
                    except ValueError as e:
                        st.warning(f"⚠️ Vision service unavailable: {e}")
                        st.session_state.vision_service = None
                
                # Initialize embedding service (pre-load model)
                status_placeholder.info("🧠 Loading AI model (first time only)...")
                if 'embedding_service' not in st.session_state:
                    st.session_state.embedding_service = EmbeddingService()
                    # Pre-load the model
                    st.session_state.embedding_service._load_model()
                
                # Initialize search service
                status_placeholder.info("🔍 Initializing search service...")
                if 'search_service' not in st.session_state:
                    st.session_state.search_service = SearchService()
                
                status_placeholder.success("✅ All services ready!")
                st.session_state.services_initialized = True
        
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize services: {e}")
        return False

def render_upload_section():
    """Render the upload section with both file and folder options"""
    st.markdown("### 📂 Upload Screenshots")
    
    # File upload
    uploaded_files = st.file_uploader(
        "Choose screenshot files",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        accept_multiple_files=True,
        help="Select multiple image files"
    )
    
    # Zip upload for folder-like functionality
    st.markdown("**Or upload a ZIP folder:**")
    zip_file = st.file_uploader(
        "Upload ZIP containing screenshots",
        type=['zip'],
        help="Upload a ZIP file containing your screenshots"
    )
    
    files_to_process = []
    
    if uploaded_files:
        files_to_process.extend(uploaded_files)
    
    if zip_file:
        extracted_files = extract_zip_files(zip_file)
        files_to_process.extend(extracted_files)
    
    if files_to_process:
        st.success(f"📁 {len(files_to_process)} files ready to process")
        
        if st.button("🚀 Process Screenshots", use_container_width=True):
            process_screenshots(files_to_process)

def extract_zip_files(zip_file):
    """Extract image files from uploaded ZIP"""
    extracted_files = []
    try:
        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    file_data = zip_ref.read(file_info.filename)
                    # Create a file-like object
                    file_obj = io.BytesIO(file_data)
                    file_obj.name = os.path.basename(file_info.filename)
                    extracted_files.append(file_obj)
        
        st.success(f"📦 Extracted {len(extracted_files)} images from ZIP")
    except Exception as e:
        st.error(f"Failed to extract ZIP: {e}")
    
    return extracted_files

def render_stats_section():
    """Render statistics section"""
    st.markdown("### 📊 Database Stats")
    
    total_screenshots = st.session_state.search_service.get_total_screenshots()
    
    st.markdown(f"""
    <div class="metric-card">
        <h3>{total_screenshots}</h3>
        <p>Screenshots Processed</p>
    </div>
    """, unsafe_allow_html=True)

def render_search_section():
    """Render the search interface"""
    st.markdown('<div class="search-container">', unsafe_allow_html=True)
    st.markdown("### 🔎 Search Your Screenshots")
    
    query = st.text_input(
        "Enter your search query:",
        placeholder="e.g., 'error message about auth', 'blue button', 'login form'",
        help="Search using natural language - describe what you're looking for!"
    )
    
    col1, col2 = st.columns([3, 1])
    with col1:
        search_button = st.button("🔍 Search", use_container_width=True)
    with col2:
        top_k = st.selectbox("Results", [3, 5, 10], index=1)
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if query and search_button:
        search_results(query, top_k)

def process_screenshots(uploaded_files):
    """Process uploaded screenshots with better progress tracking"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        filename = getattr(uploaded_file, 'name', f'image_{i}.png')
        status_text.text(f"Processing {filename}...")
        
        try:
            # Load image
            if hasattr(uploaded_file, 'read'):
                image = Image.open(uploaded_file)
            else:
                image = Image.open(io.BytesIO(uploaded_file.getvalue()))
            
            # Extract OCR text
            with st.spinner("Extracting text..."):
                ocr_text = st.session_state.ocr_service.extract_text(image)
            
            # Get visual description
            visual_description = ""
            if st.session_state.vision_service:
                with st.spinner("Analyzing visuals..."):
                    image_base64 = image_to_base64(image)
                    visual_description = st.session_state.vision_service.describe_image(image_base64)
            else:
                visual_description = "Visual analysis unavailable (API key not configured)"
            
            # Combine text for embedding
            combined_text = f"{ocr_text} {visual_description}"
            
            # Store in database
            with st.spinner("Storing data..."):
                st.session_state.search_service.store_screenshot(
                    filename=filename,
                    image_data=image_to_base64(image),
                    ocr_text=ocr_text,
                    visual_description=visual_description,
                    combined_text=combined_text
                )
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        except Exception as e:
            st.error(f"Failed to process {filename}: {e}")
    
    status_text.text("✅ All screenshots processed!")
    st.balloons()

def search_results(query, top_k):
    """Display search results with improved layout"""
    with st.spinner("Searching..."):
        results = st.session_state.search_service.search(query, top_k=top_k)
    
    if not results:
        st.warning("🔍 No results found. Try different keywords or upload more screenshots.")
        return
    
    st.markdown(f"### 🎯 Top {len(results)} Results for '{query}'")
    
    for i, result in enumerate(results):
        with st.container():
            st.markdown(f'<div class="result-card">', unsafe_allow_html=True)
            
            col1, col2 = st.columns([1, 2])
            
            with col1:
                # Display image with click to expand
                image_data = base64.b64decode(result['image_data'])
                image = Image.open(io.BytesIO(image_data))
                
                # Use st.image with expanded viewing
                st.image(
                    image, 
                    caption=f"{result['filename']} (Score: {result['score']:.3f})",
                    use_container_width=True
                )
                
                # Add a button to view full size
                if st.button(f"🔍 View Full Size", key=f"view_{i}"):
                    show_full_image(image, result['filename'])
            
            with col2:
                st.markdown(f"**📄 {result['filename']}**")
                st.markdown(f"**🎯 Confidence:** {result['score']:.1%}")
                
                with st.expander("📝 OCR Text", expanded=True):
                    ocr_text = result['ocr_text'][:500]
                    if len(result['ocr_text']) > 500:
                        ocr_text += "..."
                    st.text(ocr_text if ocr_text else "No text detected")
                
                with st.expander("👁️ Visual Description"):
                    visual_desc = result['visual_description'][:500]
                    if len(result['visual_description']) > 500:
                        visual_desc += "..."
                    st.text(visual_desc if visual_desc else "No visual description available")
            
            st.markdown('</div>', unsafe_allow_html=True)
            st.markdown("---")

def show_full_image(image, filename):
    """Show full size image in modal-like display"""
    st.markdown(f"### 🖼️ {filename}")
    st.image(image, use_container_width=True)

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

if __name__ == "__main__":
    main()