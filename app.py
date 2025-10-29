import streamlit as st
import google.generativeai as genai
import json
import base64
import io
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Gemini API
if 'GEMINI_API_KEY' in os.environ:
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-1.5-pro')
else:
    model = None

# Page config
st.set_page_config(
    page_title="Process Documenter",
    page_icon="📝",
    layout="wide"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 2rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .step-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #f9f9f9;
    }
    .recording-indicator {
        background: #ff4444;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        display: inline-block;
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0% { opacity: 1; }
        50% { opacity: 0.5; }
        100% { opacity: 1; }
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'recording' not in st.session_state:
        st.session_state.recording = False
    if 'steps' not in st.session_state:
        st.session_state.steps = []
    if 'session_id' not in st.session_state:
        st.session_state.session_id = None
    if 'audio_data' not in st.session_state:
        st.session_state.audio_data = None

def start_recording():
    """Start the recording session"""
    st.session_state.recording = True
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.steps = []
    st.session_state.audio_data = None

def stop_recording():
    """Stop the recording session"""
    st.session_state.recording = False

def add_step(step_data):
    """Add a step to the current session"""
    if st.session_state.recording:
        step = {
            'id': len(st.session_state.steps) + 1,
            'timestamp': datetime.now().isoformat(),
            'screenshot': step_data.get('screenshot'),
            'note': step_data.get('note', '')
        }
        st.session_state.steps.append(step)

def show_capture_interface():
    """Show the screen capture interface"""
    st.markdown("""
    <div style="text-align: center; padding: 20px; border: 2px dashed #ccc; border-radius: 10px; margin: 20px 0;">
        <h3>🎥 Screen & Audio Capture</h3>
        <p>For this prototype, we'll simulate the capture process. In a real implementation, this would use browser APIs to capture your screen and audio.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("""
    ### 📋 How to Test the App
    
    **For this demo, we'll simulate the capture process:**
    
    1. **Click "Mark Step (Manual)"** below to simulate capturing screenshots
    2. **Add notes** describing what you would be doing
    3. **Repeat** for 3-5 steps to simulate a complete process
    4. **Stop Recording** when you have enough steps
    5. **Generate Documentation** to see the AI create step-by-step instructions
    
    **Example process to simulate:**
    - Step 1: "Open Google Docs"
    - Step 2: "Create new document" 
    - Step 3: "Add title and content"
    - Step 4: "Format the text"
    - Step 5: "Save the document"
    """)
    
    # Manual step input
    st.subheader("📝 Add Step Manually")
    col1, col2 = st.columns([3, 1])
    
    with col1:
        step_note = st.text_input("Describe what you're doing:", placeholder="e.g., Click 'New Document' button")
    
    with col2:
        if st.button("📸 Add Step", type="primary"):
            if step_note:
                add_step({
                    'screenshot': f"data:image/png;base64,mock_screenshot_{len(st.session_state.steps) + 1}",
                    'note': step_note
                })
                st.success(f"Step {len(st.session_state.steps)} added!")
                st.rerun()
            else:
                st.warning("Please enter a description for the step")

def generate_documentation():
    """Generate documentation using Gemini AI"""
    if not model:
        st.error("⚠️ Gemini API key not configured. Please set GEMINI_API_KEY environment variable.")
        return None
    
    if not st.session_state.steps:
        st.error("No steps recorded yet!")
        return None
    
    try:
        # Prepare content for Gemini
        content_parts = []
        
        # Add instructions
        instructions = """
        You are an expert technical writer creating step-by-step process documentation for accounting and finance teams.
        
        I will provide you with screenshots and audio narration from a user demonstrating a process.
        Please create clear, professional documentation that includes:
        
        1. A descriptive title
        2. Purpose/overview
        3. Prerequisites
        4. Numbered step-by-step instructions
        5. Clear action descriptions for each step
        
        Make the instructions concise but complete. Use imperative language ("Click the...", "Enter...", "Select...").
        Focus on what the user needs to do, not what the system is doing.
        """
        
        content_parts.append(instructions)
        
        # Add each step
        for i, step in enumerate(st.session_state.steps, 1):
            step_text = f"Step {i}:\n"
            if step.get('note'):
                step_text += f"User note: {step['note']}\n"
            step_text += f"Timestamp: {step['timestamp']}\n"
            
            content_parts.append(step_text)
            
            # Add screenshot if available
            if step.get('screenshot'):
                content_parts.append(step['screenshot'])
        
        # Generate documentation
        with st.spinner("🤖 AI is generating your documentation..."):
            response = model.generate_content(content_parts)
            
        return response.text
        
    except Exception as e:
        st.error(f"Error generating documentation: {str(e)}")
        return None

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📝 Process Documenter</h1>
        <p>Record your workflow, capture screenshots, and generate step-by-step documentation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key Setup
    if not model:
        st.warning("""
        **Setup Required**: To use AI features, you need to configure your Gemini API key.
        
        1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Set the environment variable: `GEMINI_API_KEY=your_key_here`
        3. Restart the app
        """)
    
    # Main interface
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎥 Recording Session")
        
        if not st.session_state.recording:
            st.info("Click 'Start Recording' to begin capturing your process")
            if st.button("🎬 Start Recording", type="primary", use_container_width=True):
                start_recording()
                st.rerun()
        else:
            st.markdown('<div class="recording-indicator">🔴 Recording...</div>', unsafe_allow_html=True)
            
            # Show capture interface
            show_capture_interface()
            
            # Stop recording button
            if st.button("⏹️ Stop Recording", type="secondary", use_container_width=True):
                stop_recording()
                st.rerun()
            
            # Current steps
            if st.session_state.steps:
                st.subheader(f"📋 Captured Steps ({len(st.session_state.steps)})")
                for step in st.session_state.steps:
                    with st.expander(f"Step {step['id']}: {step['note']}"):
                        st.write(f"**Timestamp:** {step['timestamp']}")
                        if step.get('screenshot', '').startswith('data:image'):
                            st.image(step['screenshot'], caption=f"Screenshot for Step {step['id']}")
                        else:
                            st.write(f"**Screenshot:** {step.get('screenshot', 'Not available')}")
    
    with col2:
        st.subheader("📄 Documentation")
        
        if st.session_state.steps and not st.session_state.recording:
            if st.button("🤖 Generate Documentation", type="primary", use_container_width=True):
                doc = generate_documentation()
                if doc:
                    st.success("Documentation generated successfully!")
                    st.text_area("Generated Documentation", doc, height=400)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download as Markdown",
                        data=doc,
                        file_name=f"process_documentation_{st.session_state.session_id}.md",
                        mime="text/markdown"
                    )
        else:
            st.info("Record some steps first, then generate documentation")
    
    # Instructions
    with st.expander("ℹ️ How to Use"):
        st.markdown("""
        ### Getting Started
        
        1. **Start Recording**: Click the "Start Recording" button
        2. **Demonstrate Process**: Perform your workflow while talking through it
        3. **Mark Steps**: Press "Mark Step" at key moments (or use Ctrl+Shift+S hotkey)
        4. **Stop Recording**: Click "Stop Recording" when finished
        5. **Generate Docs**: Click "Generate Documentation" to create AI-powered documentation
        
        ### Tips for Better Documentation
        
        - **Speak clearly** while demonstrating
        - **Mark steps** at important decision points
        - **Explain what you're doing** as you do it
        - **Include context** about why each step matters
        
        ### Privacy Note
        
        This prototype sends screenshots and audio to Google's Gemini AI for processing.
        In a production environment, additional privacy controls would be implemented.
        """)

if __name__ == "__main__":
    main()
