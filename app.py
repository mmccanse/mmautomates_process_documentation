import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import tempfile
import json
from datetime import datetime
from moviepy.editor import VideoFileClip
import time
import cv2
from PIL import Image
import io
import base64
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

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
    .moment-card {
        background: white;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
    if 'extracted_frames' not in st.session_state:
        st.session_state.extracted_frames = None
    if 'final_documentation' not in st.session_state:
        st.session_state.final_documentation = None
    if 'editing_mode' not in st.session_state:
        st.session_state.editing_mode = False

def extract_audio_from_video(video_path):
    """Extract audio from video file"""
    try:
        with st.spinner("📹 Extracting audio from video..."):
            # Verify file exists and has content
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            file_size = os.path.getsize(video_path)
            if file_size == 0:
                raise ValueError("Video file is empty")
            
            st.info(f"Video file size: {file_size / (1024*1024):.2f} MB")
            
            # Try to open video with error handling
            try:
                video = VideoFileClip(video_path)
            except Exception as e:
                st.error("The video file appears to be corrupted or incompatible.")
                st.error("Please try:")
                st.error("1. Re-exporting the video in MP4 format")
                st.error("2. Using a smaller file size")
                st.error("3. Using a different recording tool")
                raise e
            
            # Check if video has audio
            if video.audio is None:
                video.close()
                raise ValueError("Video file has no audio track. Please record with audio enabled.")
            
            # Create temporary audio file
            audio_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
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
            # Read audio file
            with open(audio_path, 'rb') as f:
                audio_bytes = f.read()
            
            # Create prompt
            prompt = """
            Please transcribe this audio recording. 
            
            This is someone explaining an accounting or business process.
            
            Provide the transcript with approximate timestamps in the format [MM:SS] at the beginning of each major sentence or thought.
            
            Be accurate with the transcription, including any technical terms, system names, or navigation paths mentioned.
            """
            
            # Generate transcription using File API
            import mimetypes
            mime_type = mimetypes.guess_type(audio_path)[0] or 'audio/mpeg'
            
            # Create file part
            audio_part = {
                "mime_type": mime_type,
                "data": audio_bytes
            }
            
            # Generate content
            response = model.generate_content([prompt, audio_part])
            
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

def timestamp_to_seconds(timestamp_str):
    """Convert timestamp string (MM:SS or HH:MM:SS) to seconds"""
    try:
        parts = timestamp_str.strip().split(':')
        if len(parts) == 2:
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        elif len(parts) == 3:
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    except:
        return 0

def seconds_to_timestamp(seconds):
    """Convert seconds to timestamp string (MM:SS)"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins}:{secs:02d}"

def extract_frame_at_timestamp(video_path, timestamp_seconds):
    """Extract a single frame from video at given timestamp"""
    try:
        cap = cv2.VideoCapture(video_path)
        
        # Set position to timestamp (in milliseconds)
        cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_seconds * 1000)
        
        # Read frame
        success, frame = cap.read()
        cap.release()
        
        if success:
            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Convert to PIL Image
            img = Image.fromarray(frame_rgb)
            return img
        else:
            return None
            
    except Exception as e:
        st.error(f"Error extracting frame at {timestamp_seconds}s: {str(e)}")
        return None

def extract_all_frames(video_path, key_moments):
    """Extract frames for all key moments"""
    frames = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, moment in enumerate(key_moments):
        timestamp_seconds = timestamp_to_seconds(moment['timestamp'])
        status_text.text(f"Extracting frame {i+1}/{len(key_moments)} at {moment['timestamp']}...")
        
        frame = extract_frame_at_timestamp(video_path, timestamp_seconds)
        
        if frame:
            frames.append({
                'moment': moment,
                'image': frame,
                'timestamp': moment['timestamp']
            })
        
        progress_bar.progress((i + 1) / len(key_moments))
    
    status_text.empty()
    progress_bar.empty()
    
    return frames

def image_to_base64(image):
    """Convert PIL Image to base64 string"""
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"

def generate_documentation(transcript, frames):
    """Generate final documentation with Gemini"""
    try:
        with st.spinner("🤖 Generating professional documentation... This may take 1-2 minutes..."):
            # Prepare content for Gemini
            content_parts = []
            
            # Instructions
            instructions = """
You are an expert technical writer specializing in accounting and finance process documentation.

I will provide you with:
1. A transcript of someone explaining a process
2. Screenshots at key moments in the process

Please create professional, audit-ready Standard Operating Procedure (SOP) documentation that includes:

**Document Structure:**
1. **Process Title** - Clear, descriptive title (just the title, no "Process Title:" label)
2. **Purpose** - Why this process exists and what it accomplishes
3. **Scope** - What this process covers
4. **Prerequisites** - What needs to be in place before starting (access, permissions, data, etc.)
5. **Step-by-Step Instructions** - Numbered steps with:
   - Clear action-oriented language (Click, Enter, Select, Navigate, etc.)
   - Navigation paths when relevant (Menu > Options > Add Account)
   - What data to enter
   - What to verify or check
   - Expected results
   - Mark where screenshots should be referenced with: [Screenshot X]
6. **Control Points** - Key moments where accuracy is critical (for SOX compliance)
7. **Common Issues & Troubleshooting** - Potential problems and solutions
8. **Frequency** - How often this process is performed

**Writing Guidelines:**
- Use imperative mood (command form): "Click the Submit button" not "You click the Submit button"
- Be concise but complete
- Include screenshot references like [Screenshot 1], [Screenshot 2] exactly where they should appear
- Highlight control points with ⚠️ symbol
- Use proper accounting terminology
- Make it audit-ready with clear accountability and verification steps

**CRITICAL: Screenshot References**
For each screenshot provided, you MUST include [Screenshot X] in the appropriate step where that screenshot should be displayed. Match the screenshot number to the step it illustrates.

**Format:**
- Use markdown formatting
- Clear headers (use ## for main sections, ### for subsections)
- Numbered lists for sequential steps
- Bullet points for options or notes

Create documentation that would satisfy internal audit requirements and be immediately usable by a new team member.
"""
            
            content_parts.append(instructions)
            
            # Add transcript
            content_parts.append(f"\n\n**TRANSCRIPT:**\n{transcript}\n\n")
            
            # Add screenshots with context
            content_parts.append("**SCREENSHOTS:**\n\n")
            
            for i, frame_data in enumerate(frames, 1):
                moment = frame_data['moment']
                
                screenshot_context = f"""
Screenshot {i} [{moment['timestamp']}]:
- Type: {moment['type']}
- Description: {moment['description']}
"""
                if moment.get('navigation_path'):
                    screenshot_context += f"- Navigation: {moment['navigation_path']}\n"
                
                content_parts.append(screenshot_context)
                content_parts.append(frame_data['image'])
                content_parts.append("\n---\n")
            
            # Generate documentation
            response = model.generate_content(content_parts)
            
            return response.text
            
    except Exception as e:
        st.error(f"Error generating documentation: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def create_word_document(markdown_text, frames):
    """Create a Word document with embedded screenshots"""
    try:
        doc = Document()
        
        # Set default font
        style = doc.styles['Normal']
        font = style.font
        font.name = 'Calibri'
        font.size = Pt(11)
        
        # Parse markdown and build document
        lines = markdown_text.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines
            if not line:
                i += 1
                continue
            
            # Handle headers
            if line.startswith('# '):
                # Main title (H1)
                title = line[2:].strip()
                p = doc.add_heading(title, level=0)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                
            elif line.startswith('## '):
                # Section header (H2)
                doc.add_heading(line[3:].strip(), level=1)
                
            elif line.startswith('### '):
                # Subsection header (H3)
                doc.add_heading(line[4:].strip(), level=2)
            
            # Handle screenshot references
            elif '[Screenshot' in line:
                # Extract screenshot number
                import re
                matches = re.findall(r'\[Screenshot (\d+)\]', line)
                
                # Add the text before/after screenshot
                text_parts = re.split(r'\[Screenshot \d+\]', line)
                
                for j, text in enumerate(text_parts):
                    if text.strip():
                        doc.add_paragraph(text.strip())
                    
                    # Add screenshot if there's a match
                    if j < len(matches):
                        screenshot_num = int(matches[j])
                        if screenshot_num <= len(frames):
                            frame_data = frames[screenshot_num - 1]
                            
                            # Save image to temporary file
                            img_buffer = io.BytesIO()
                            frame_data['image'].save(img_buffer, format='PNG')
                            img_buffer.seek(0)
                            
                            # Add image to document
                            doc.add_picture(img_buffer, width=Inches(6))
                            
                            # Add caption
                            caption = doc.add_paragraph()
                            caption.add_run(f"Screenshot {screenshot_num}: {frame_data['moment']['description']}").italic = True
                            caption.alignment = WD_ALIGN_PARAGRAPH.CENTER
            
            # Handle numbered lists
            elif re.match(r'^\d+\.', line):
                doc.add_paragraph(line, style='List Number')
            
            # Handle bullet points
            elif line.startswith('- ') or line.startswith('* '):
                doc.add_paragraph(line[2:], style='List Bullet')
            
            # Handle bold text (simplified)
            elif '**' in line:
                p = doc.add_paragraph()
                parts = line.split('**')
                for idx, part in enumerate(parts):
                    if idx % 2 == 0:
                        p.add_run(part)
                    else:
                        p.add_run(part).bold = True
            
            # Regular paragraph
            else:
                doc.add_paragraph(line)
            
            i += 1
        
        # Add footer with generation date
        section = doc.sections[0]
        footer = section.footer
        footer_para = footer.paragraphs[0]
        footer_para.text = f"Generated by AI Process Documentation Generator on {datetime.now().strftime('%B %d, %Y')}"
        footer_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Save to bytes
        doc_buffer = io.BytesIO()
        doc.save(doc_buffer)
        doc_buffer.seek(0)
        
        return doc_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Error creating Word document: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
        return None

def show_moment_editor(key_moments):
    """Show interactive editor for key moments"""
    st.markdown("### 📝 Edit Key Moments")
    st.info("Review and edit the AI-identified moments. You can modify timestamps, descriptions, add new moments, or delete unwanted ones.")
    
    edited_moments = []
    
    # Display each moment with edit controls
    for i, moment in enumerate(key_moments):
        with st.container():
            col1, col2, col3, col4 = st.columns([1, 2, 4, 1])
            
            with col1:
                # Editable timestamp
                new_timestamp = st.text_input(
                    "Time",
                    value=moment['timestamp'],
                    key=f"time_{i}",
                    label_visibility="collapsed"
                )
            
            with col2:
                # Type selector
                type_options = ['navigation', 'action', 'data_entry', 'decision', 'submission']
                current_type = moment.get('type', 'action')
                if current_type not in type_options:
                    current_type = 'action'
                
                new_type = st.selectbox(
                    "Type",
                    options=type_options,
                    index=type_options.index(current_type),
                    key=f"type_{i}",
                    label_visibility="collapsed"
                )
            
            with col3:
                # Editable description
                new_description = st.text_area(
                    "Description",
                    value=moment['description'],
                    height=60,
                    key=f"desc_{i}",
                    label_visibility="collapsed"
                )
                
                # Navigation path (only for navigation type)
                if new_type == 'navigation':
                    new_nav_path = st.text_input(
                        "Navigation Path",
                        value=moment.get('navigation_path', ''),
                        key=f"nav_{i}",
                        placeholder="Menu > Options > Add Account"
                    )
                else:
                    new_nav_path = None
            
            with col4:
                # Delete button
                delete = st.button("❌", key=f"delete_{i}", help="Delete this moment")
            
            # Only add if not deleted
            if not delete:
                edited_moment = {
                    'timestamp': new_timestamp,
                    'type': new_type,
                    'description': new_description,
                    'navigation_path': new_nav_path
                }
                edited_moments.append(edited_moment)
            
            st.markdown("---")
    
    # Add new moment section
    with st.expander("➕ Add New Moment"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_timestamp = st.text_input("Timestamp (MM:SS)", key="new_time", placeholder="2:30")
            new_type = st.selectbox("Type", options=['navigation', 'action', 'data_entry', 'decision', 'submission'], key="new_type")
        
        with col2:
            new_description = st.text_area("Description", key="new_desc", height=100)
            if new_type == 'navigation':
                new_nav_path = st.text_input("Navigation Path", key="new_nav", placeholder="Menu > Options > Add Account")
            else:
                new_nav_path = None
        
        if st.button("➕ Add This Moment"):
            if new_timestamp and new_description:
                edited_moments.append({
                    'timestamp': new_timestamp,
                    'type': new_type,
                    'description': new_description,
                    'navigation_path': new_nav_path
                })
                st.success("Moment added! Click 'Apply Changes' below to update.")
            else:
                st.error("Please enter both timestamp and description")
    
    return edited_moments

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
        
        1. **Record your process** using any screen recording tool (Zoom, Loom, QuickTime, OBS)
        2. **Talk through the process** as you demonstrate - explain navigation, actions, and decisions
        3. **Upload your video** (MP4, MOV, AVI, WebM)
        4. **AI analyzes** and identifies key moments
        5. **Review and edit** the identified moments (add, remove, or modify)
        6. **Extract frames** to see all screenshots
        7. **Generate documentation** - AI creates professional SOP
        8. **Download** your documentation
        
        ### Tips for Best Results
        
        - Speak clearly and describe what you're doing
        - Mention navigation paths explicitly
        - Keep recordings under 10 minutes
        - Explain the "why" not just the "what"
        """)
    
    # Main interface
    st.markdown("### Step 1: Upload Your Screen Recording")
    
    uploaded_file = st.file_uploader(
        "Choose a video file",
        type=['mp4', 'mov', 'avi', 'webm', 'mkv'],
        help="Upload a screen recording where you talk through a process"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.info(f"📁 File: {uploaded_file.name} ({uploaded_file.size / (1024*1024):.2f} MB)")
        
        # Save uploaded file temporarily with proper flushing
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            bytes_data = uploaded_file.getvalue()
            tmp_file.write(bytes_data)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
            video_path = tmp_file.name
            st.session_state.video_path = video_path
        
        # Verify file was saved correctly
        if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
            st.success(f"✅ Video uploaded successfully!")
        else:
            st.error("❌ Video upload failed. Please try again.")
            video_path = None
        
        # Show video preview (only if file exists)
        if video_path:
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
                            st.rerun()
    
    # Display transcript
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
    
    # Edit key moments
    if st.session_state.key_moments and not st.session_state.extracted_frames:
        st.markdown("---")
        st.markdown("### Step 3: Review & Edit Key Moments")
        
        st.info(f"🎯 AI identified **{len(st.session_state.key_moments)}** moments")
        
        # Show editor
        edited_moments = show_moment_editor(st.session_state.key_moments)
        
        # Apply changes button
        col1, col2, col3 = st.columns([2, 2, 2])
        
        with col1:
            if st.button("✅ Apply Changes & Extract Frames", type="primary", use_container_width=True):
                st.session_state.key_moments = edited_moments
                
                # Extract frames
                with st.spinner("📸 Extracting screenshots from video..."):
                    frames = extract_all_frames(st.session_state.video_path, edited_moments)
                    st.session_state.extracted_frames = frames
                
                st.success(f"✅ Extracted {len(frames)} screenshots!")
                st.rerun()
        
        with col2:
            # Download edited moments as JSON
            json_data = json.dumps(edited_moments, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=json_data,
                file_name=f"key_moments_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
    
    # Show extracted frames
    if st.session_state.extracted_frames:
        st.markdown("---")
        st.markdown("### Step 4: Review Extracted Screenshots")
        
        st.success(f"✅ {len(st.session_state.extracted_frames)} screenshots ready")
        
        # Display frames in grid
        cols_per_row = 3
        for i in range(0, len(st.session_state.extracted_frames), cols_per_row):
            cols = st.columns(cols_per_row)
            for j in range(cols_per_row):
                if i + j < len(st.session_state.extracted_frames):
                    frame_data = st.session_state.extracted_frames[i + j]
                    with cols[j]:
                        st.image(frame_data['image'], caption=f"{frame_data['timestamp']} - {frame_data['moment']['type']}", use_container_width=True)
                        st.caption(frame_data['moment']['description'][:100] + "...")
        
        # Generate documentation button
        st.markdown("---")
        
        if not st.session_state.final_documentation:
            if st.button("🤖 Generate Professional Documentation", type="primary", use_container_width=True):
                doc = generate_documentation(
                    st.session_state.transcript,
                    st.session_state.extracted_frames
                )
                
                if doc:
                    st.session_state.final_documentation = doc
                    st.success("✅ Documentation generated!")
                    st.rerun()
        else:
            st.success("✅ Documentation ready!")
    
    # Show final documentation
    if st.session_state.final_documentation:
        st.markdown("---")
        st.markdown("### Step 5: Your Professional Documentation")
        
        # Display documentation
        with st.expander("📄 View Full Documentation", expanded=True):
            st.markdown(st.session_state.final_documentation)
        
        # Generate Word document
        with st.spinner("📝 Creating Word document with embedded screenshots..."):
            word_doc = create_word_document(
                st.session_state.final_documentation,
                st.session_state.extracted_frames
            )
        
        if word_doc:
            # Download options
            col1, col2 = st.columns(2)
            
            with col1:
                st.download_button(
                    label="📥 Download as Word Document (.docx)",
                    data=word_doc,
                    file_name=f"process_documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    type="primary"
                )
            
            with col2:
                st.download_button(
                    label="📥 Download as Markdown",
                    data=st.session_state.final_documentation,
                    file_name=f"process_documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            st.success("✅ Word document ready with all screenshots embedded!")
        else:
            # Fallback to markdown only
            st.download_button(
                label="📥 Download as Markdown",
                data=st.session_state.final_documentation,
                file_name=f"process_documentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                mime="text/markdown",
                use_container_width=True
            )
    
    # Sidebar
    with st.sidebar:
        st.markdown("### 📊 Progress")
        
        status_items = [
            ("Video Uploaded", st.session_state.video_path is not None),
            ("Audio Extracted", st.session_state.audio_path is not None),
            ("Transcript Generated", st.session_state.transcript is not None),
            ("Key Moments Identified", st.session_state.key_moments is not None),
            ("Frames Extracted", st.session_state.extracted_frames is not None),
            ("Documentation Generated", st.session_state.final_documentation is not None)
        ]
        
        for label, completed in status_items:
            icon = "✅" if completed else "⏳"
            st.markdown(f"{icon} {label}")
        
        st.markdown("---")
        
        if st.button("🔄 Start New Process", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
        
        st.markdown("---")
        st.markdown("""
        ### 💡 Tips
        
        - Edit moments before extracting
        - Review screenshots carefully
        - Download immediately
        - Keep videos under 10 min
        """)

if __name__ == "__main__":
    main()