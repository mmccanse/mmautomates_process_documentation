import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import tempfile
import json
from datetime import datetime
from moviepy.editor import VideoFileClip
import time

# Load environment variables
load_dotenv()

# Configure Gemini API
if 'GEMINI_API_KEY' in os.environ:
    genai.configure(api_key=os.environ['GEMINI_API_KEY'])
    model = genai.GenerativeModel('gemini-2.5-pro')
else:
    model = None

# Page config
st.set_page_config(
    page_title="AI Process Documentation Generator",
    page_icon="📹",
    layout="wide"
)

# Custom CSS
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
    .timestamp-item {
        background: #f0f2f6;
        padding: 10px;
        margin: 5px 0;
        border-radius: 5px;
        border-left: 4px solid #667eea;
    }
    .success-box {
        background: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 15px;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables"""
    if 'transcript' not in st.session_state:
        st.session_state.transcript = None
    if 'key_moments' not in st.session_state:
        st.session_state.key_moments = None
    if 'video_path' not in st.session_state:
        st.session_state.video_path = None
    if 'audio_path' not in st.session_state:
        st.session_state.audio_path = None

def extract_audio_from_video(video_path):
    """Extract audio from video file"""
    try:
        with st.spinner("📹 Extracting audio from video..."):
            video = VideoFileClip(video_path)
            
            # Create temporary audio file
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.wav').name
            video.audio.write_audiofile(audio_path, verbose=False, logger=None)
            
            # Get video duration
            duration = video.duration
            
            video.close()
            
            return audio_path, duration
    except Exception as e:
        st.error(f"Error extracting audio: {str(e)}")
        return None, None

def transcribe_audio_with_gemini(audio_path):
    """Transcribe audio using Gemini API"""
    try:
        with st.spinner("🎤 Transcribing audio with AI... This may take a minute..."):
            # Upload audio file to Gemini
            audio_file = genai.upload_file(audio_path)
            
            # Wait for file to be processed
            while audio_file.state.name == "PROCESSING":
                time.sleep(2)
                audio_file = genai.get_file(audio_file.name)
            
            if audio_file.state.name == "FAILED":
                raise ValueError("Audio processing failed")
            
            # Create prompt for transcription
            prompt = """
            Please transcribe this audio recording. 
            
            This is someone explaining an accounting or business process.
            
            Provide the transcript with approximate timestamps in the format [MM:SS] at the beginning of each major sentence or thought.
            
            Be accurate with the transcription, including any technical terms, system names, or navigation paths mentioned.
            """
            
            # Generate transcription
            response = model.generate_content([prompt, audio_file])
            
            # Clean up uploaded file
            genai.delete_file(audio_file.name)
            
            return response.text
            
    except Exception as e:
        st.error(f"Error transcribing audio: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def analyze_transcript_for_key_moments(transcript):
    """Analyze transcript to identify key moments for screenshots"""
    try:
        with st.spinner("🧠 AI is analyzing the process to identify key moments..."):
            prompt = f"""
            You are an expert at analyzing process documentation and identifying key moments that should be captured in screenshots.
            
            Analyze this transcript of someone explaining an accounting or business process. The transcript includes timestamps.
            
            Identify timestamps where screenshots should be captured, specifically when the person describes:
            
            1. **Navigation paths** - When they describe how to get somewhere (e.g., "go to Menu > Options > Add Account", "click on the Transactions tab", "navigate to Reports")
            2. **Clicking buttons or links** - Any action that opens something new
            3. **Entering data** - When they're filling out forms or fields
            4. **Submitting or saving** - Final actions in a step
            5. **Key decision points** - Where choices need to be made
            6. **Opening menus or dropdowns** - Especially navigation menus
            7. **Important screens or pages** - When they arrive at a significant location in the system
            
            **IMPORTANT FOR NAVIGATION**: If someone describes a navigation path like "Menu > Options > Add Account", that should be ONE screenshot showing that final destination, not multiple screenshots.
            
            Return your analysis as a JSON array with this exact structure:
            [
                {{
                    "timestamp": "MM:SS",
                    "type": "navigation|action|data_entry|decision|submission",
                    "description": "Brief description of what's happening",
                    "navigation_path": "Menu > Options > Add Account" (only if type is navigation, otherwise null)
                }}
            ]
            
            Only include the JSON array in your response, no other text.
            
            TRANSCRIPT:
            {transcript}
            """
            
            response = model.generate_content(prompt)
            
            # Extract JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            response_text = response_text.strip()
            
            # Parse JSON
            key_moments = json.loads(response_text)
            
            return key_moments
            
    except json.JSONDecodeError as e:
        st.error(f"Error parsing AI response: {str(e)}")
        st.error(f"AI Response was: {response_text}")
        return None
    except Exception as e:
        st.error(f"Error analyzing transcript: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def format_timestamp(timestamp_str):
    """Convert timestamp string to seconds"""
    try:
        parts = timestamp_str.split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + int(seconds)
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
    except:
        return 0

def main():
    initialize_session_state()
    
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>📹 AI Process Documentation Generator</h1>
        <p>Upload a screen recording → AI generates professional documentation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # API Key Setup
    if not model:
        st.error("""
        **⚠️ Setup Required**: Gemini API key not configured.
        
        1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Create a `.env` file with: `GEMINI_API_KEY=your_key_here`
        3. Restart the app
        """)
        return
    
    # Instructions
    with st.expander("ℹ️ How to Use This Tool", expanded=False):
        st.markdown("""
        ### Quick Start Guide
        
        1. **Record your process** using any screen recording tool:
           - Zoom
           - Loom
           - QuickTime (Mac)
           - OBS
           - Windows Game Bar
        
        2. **Talk through the process** as you demonstrate:
           - Explain navigation paths: "Now I'm going to Menu, then Options, then Add Account"
           - Describe what you're clicking
           - Mention what data you're entering
           - Note any important decisions or confirmations
        
        3. **Upload your video** (MP4, MOV, AVI, WebM)
        
        4. **AI analyzes everything**:
           - Transcribes your narration
           - Identifies key moments for screenshots
           - Captures navigation paths
        
        5. **Review and refine** the identified moments
        
        6. **Generate documentation** (Coming in Phase 2!)
        
        ### Tips for Best Results
        
        - Speak clearly and at a moderate pace
        - Explicitly mention navigation: "Click on Reports", "Go to Settings menu"
        - Describe what you see: "Now I'm on the Transaction Entry screen"
        - Keep recordings under 10 minutes for faster processing
        
        ### What This Tool Captures
        
        ✅ Navigation paths (Menu > Options > Add Account)  
        ✅ Button clicks and actions  
        ✅ Data entry points  
        ✅ Decision points  
        ✅ Screen transitions  
        """)
    
    # Main interface
    st.markdown("### Step 1: Upload Your Screen Recording")
    
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'mov', 'avi', 'webm', 'mkv'],
        help="Upload a screen recording where you talk through a process"
    )
    
    if uploaded_file is not None:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as tmp_file:
            tmp_file.write(uploaded_file.read())
            video_path = tmp_file.name
            st.session_state.video_path = video_path
        
        # Show video preview
        st.video(video_path)
        
        col1, col2 = st.columns([1, 3])
        with col1:
            process_button = st.button("🚀 Process Video", type="primary", use_container_width=True)
        
        if process_button:
            # Extract audio
            audio_path, duration = extract_audio_from_video(video_path)
            
            if audio_path:
                st.session_state.audio_path = audio_path
                st.success(f"✅ Audio extracted successfully! Video duration: {duration:.1f} seconds")
                
                # Transcribe audio
                transcript = transcribe_audio_with_gemini(audio_path)
                
                if transcript:
                    st.session_state.transcript = transcript
                    st.success("✅ Transcription complete!")
                    
                    # Analyze transcript
                    key_moments = analyze_transcript_for_key_moments(transcript)
                    
                    if key_moments:
                        st.session_state.key_moments = key_moments
                        st.success(f"✅ Analysis complete! Found {len(key_moments)} key moments")
    
    # Display results
    if st.session_state.transcript:
        st.markdown("---")
        st.markdown("### Step 2: Review Transcript")
        
        with st.expander("📝 Full Transcript", expanded=False):
            st.text_area(
                "Transcript",
                st.session_state.transcript,
                height=300,
                disabled=True
            )
    
    if st.session_state.key_moments:
        st.markdown("---")
        st.markdown("### Step 3: Key Moments Identified by AI")
        
        st.info(f"🎯 AI identified **{len(st.session_state.key_moments)}** moments where screenshots should be captured")
        
        # Display key moments
        for i, moment in enumerate(st.session_state.key_moments, 1):
            with st.container():
                col1, col2, col3 = st.columns([1, 2, 3])
                
                with col1:
                    st.markdown(f"**⏱️ {moment['timestamp']}**")
                
                with col2:
                    # Color code by type
                    type_colors = {
                        'navigation': '🧭',
                        'action': '👆',
                        'data_entry': '⌨️',
                        'decision': '🤔',
                        'submission': '✅'
                    }
                    icon = type_colors.get(moment['type'], '📍')
                    st.markdown(f"{icon} **{moment['type'].replace('_', ' ').title()}**")
                
                with col3:
                    st.markdown(moment['description'])
                    if moment.get('navigation_path'):
                        st.markdown(f"📍 Path: `{moment['navigation_path']}`")
                
                st.markdown("---")
        
        # Export key moments
        st.markdown("### Export Key Moments")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Download as JSON
            json_data = json.dumps(st.session_state.key_moments, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"key_moments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        with col2:
            # Show next steps
            st.info("**Phase 2 Coming Soon:**\n- Extract video frames at these timestamps\n- Generate documentation with screenshots")
    
    # Sidebar info
    with st.sidebar:
        st.markdown("### 📊 Current Status")
        
        status_items = [
            ("Video Uploaded", st.session_state.video_path is not None),
            ("Audio Extracted", st.session_state.audio_path is not None),
            ("Transcript Generated", st.session_state.transcript is not None),
            ("Key Moments Identified", st.session_state.key_moments is not None)
        ]
        
        for label, completed in status_items:
            icon = "✅" if completed else "⏳"
            st.markdown(f"{icon} {label}")
        
        if st.session_state.key_moments:
            st.markdown("---")
            st.markdown(f"**{len(st.session_state.key_moments)}** screenshots to capture")
        
        st.markdown("---")
        
        if st.button("🔄 Start Over", use_container_width=True):
            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        ### 💡 Pro Tips
        
        - Keep videos under 10 min
        - Speak clearly
        - Mention navigation paths
        - Describe key actions
        """)

if __name__ == "__main__":
    main()