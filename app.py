import streamlit as st
import os
from PIL import Image
import io
import base64
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
    initial_sidebar_state="expanded"
)

# Minimalistic CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    .main-header {
        font-family: 'Inter', sans-serif;
        font-size: 2.5rem;
        font-weight: 700;
        color: #2F4F4F;
        text-align: center;
        margin-bottom: 0.3rem;
        letter-spacing: 1px;
    }
    .subtitle {
        font-family: 'Inter', sans-serif;
        font-size: 0.9rem;
        color: #708090;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 300;
    }
    .stButton>button {
        background: #2F4F4F;
        color: white;
        border: none;
        border-radius: 4px;
        padding: 0.4rem 1.5rem;
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.9rem;
        transition: all 0.2s ease;
    }
    .stButton>button:hover {
        background: #1C3A3A;
        transform: translateY(-1px);
    }
    .stTextInput>div>div>input {
        font-family: 'Inter', sans-serif;
        border-radius: 4px;
        border: 1px solid #E5E5E5;
    }
    .stMarkdown h3 {
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        color: #2F4F4F;
        font-size: 1.1rem;
    }
    /* Remove all padding and spacing fluff */
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
    .stApp > div:first-child {
        background: #FAFAFA;
    }
    /* Clean file uploader */
    .stFileUploader > div {
        border: 1px dashed #D3D3D3;
        border-radius: 4px;
        padding: 1rem;
        background: white;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<div class="main-header">SSSearch</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Visual Memory Search</div>', unsafe_allow_html=True)
    
    # Initialize services
    if not init_services():
        st.stop()
    
    # Sidebar for upload
    with st.sidebar:
        render_upload_section()
        st.markdown("---")
        render_stats_section()
    
    # Main area for search
    render_search_section()

def init_services():
    """Initialize all services"""
    try:
        if 'services_initialized' not in st.session_state:
            status_placeholder = st.empty()
            
            status_placeholder.info("Initializing services...")
            
            if 'ocr_service' not in st.session_state:
                st.session_state.ocr_service = OCRService()
            
            if 'vision_service' not in st.session_state:
                try:
                    api_key = os.getenv('ANTHROPIC_API_KEY')
                    if not api_key:
                        st.warning("ANTHROPIC_API_KEY not found - visual analysis disabled")
                        st.session_state.vision_service = None
                    else:
                        st.session_state.vision_service = VisionService()
                except ValueError as e:
                    st.warning(f"Vision service unavailable: {e}")
                    st.session_state.vision_service = None
            
            if 'embedding_service' not in st.session_state:
                st.session_state.embedding_service = EmbeddingService()
                st.session_state.embedding_service._load_model()
            
            if 'search_service' not in st.session_state:
                st.session_state.search_service = SearchService()
            
            status_placeholder.success("Ready")
            st.session_state.services_initialized = True
        
        return True
        
    except Exception as e:
        st.error(f"Failed to initialize: {e}")
        return False

def render_upload_section():
    """Clean upload section"""
    st.markdown("### Upload Screenshots")
    
    # Folder upload using HTML5 directory API
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <input type="file" id="folder-upload" webkitdirectory multiple style="display: none;" />
        <button onclick="document.getElementById('folder-upload').click()" 
                style="background: #2F4F4F; color: white; border: none; padding: 8px 16px; 
                       border-radius: 4px; cursor: pointer; font-family: Inter;">
            Select Folder
        </button>
        <div id="folder-status" style="margin-top: 8px; font-size: 0.9rem; color: #666;"></div>
    </div>
    
    <script>
    document.getElementById('folder-upload').addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        const imageFiles = files.filter(f => f.type.startsWith('image/'));
        document.getElementById('folder-status').textContent = 
            `Selected ${imageFiles.length} images from folder`;
    });
    </script>
    """, unsafe_allow_html=True)
    
    # Regular file upload
    st.markdown("**Or select individual files:**")
    uploaded_files = st.file_uploader(
        "Choose images",
        type=['png', 'jpg', 'jpeg', 'gif', 'webp'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )
    
    if uploaded_files:
        st.success(f"{len(uploaded_files)} files ready")
        
        if st.button("Process Screenshots", use_container_width=True):
            process_screenshots(uploaded_files)

def render_stats_section():
    """Simple stats"""
    st.markdown("### Database")
    total = st.session_state.search_service.get_total_screenshots()
    st.markdown(f"**{total}** screenshots stored")

def render_search_section():
    """Clean search interface"""
    st.markdown("### Search Screenshots")
    
    col1, col2 = st.columns([4, 1])
    with col1:
        query = st.text_input(
            "Search query",
            placeholder="error message, blue button, login form...",
            label_visibility="collapsed"
        )
    with col2:
        top_k = st.selectbox("Results", [3, 5, 10], index=1, label_visibility="collapsed")
    
    if st.button("Search", use_container_width=True):
        if query:
            search_results(query, top_k)
        else:
            st.warning("Enter a search query")

def process_screenshots(uploaded_files):
    """Process uploaded screenshots"""
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, uploaded_file in enumerate(uploaded_files):
        status_text.text(f"Processing {uploaded_file.name}...")
        
        try:
            image = Image.open(uploaded_file)
            
            # OCR
            ocr_text = st.session_state.ocr_service.extract_text(image)
            
            # Vision analysis
            visual_description = ""
            if st.session_state.vision_service:
                image_base64 = image_to_base64(image)
                visual_description = st.session_state.vision_service.describe_image(image_base64)
            
            # Store
            combined_text = f"{ocr_text} {visual_description}"
            st.session_state.search_service.store_screenshot(
                filename=uploaded_file.name,
                image_data=image_to_base64(image),
                ocr_text=ocr_text,
                visual_description=visual_description,
                combined_text=combined_text
            )
            
            progress_bar.progress((i + 1) / len(uploaded_files))
            
        except Exception as e:
            st.error(f"Failed to process {uploaded_file.name}: {e}")
    
    status_text.text("Complete")

def search_results(query, top_k):
    """Display search results"""
    with st.spinner("Searching..."):
        results = st.session_state.search_service.search(query, top_k=top_k)
    
    if not results:
        st.warning("No results found")
        return
    
    st.markdown(f"**{len(results)} results for '{query}'**")
    
    for i, result in enumerate(results):
        with st.container():
            col1, col2 = st.columns([1, 3])
            
            with col1:
                image_data = base64.b64decode(result['image_data'])
                image = Image.open(io.BytesIO(image_data))
                st.image(image, use_container_width=True)
                
                if st.button("View Full", key=f"view_{i}"):
                    st.image(image, caption=result['filename'])
            
            with col2:
                st.markdown(f"**{result['filename']}**")
                st.markdown(f"Confidence: {result['score']:.1%}")
                
                with st.expander("OCR Text"):
                    st.text(result['ocr_text'][:300] + "..." if len(result['ocr_text']) > 300 else result['ocr_text'])
                
                with st.expander("Visual Description"):
                    st.text(result['visual_description'][:300] + "..." if len(result['visual_description']) > 300 else result['visual_description'])
            
            st.divider()

def image_to_base64(image):
    """Convert PIL image to base64 string"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()
    return img_str

if __name__ == "__main__":
    main()