import streamlit as st
import google.generativeai as genai
import json
import base64
import io
from datetime import datetime
import os
from dotenv import load_dotenv
from streamlit.components.v1 import html
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
    if 'component_key' not in st.session_state:
        st.session_state.component_key = 0

def start_recording():
    """Start the recording session"""
    st.session_state.recording = True
    st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    st.session_state.steps = []
    st.session_state.audio_data = None
    st.session_state.component_key += 1

def stop_recording():
    """Stop the recording session"""
    st.session_state.recording = False

def add_step(step_data):
    """Add a step to the current session"""
    step = {
        'id': len(st.session_state.steps) + 1,
        'timestamp': step_data.get('timestamp', datetime.now().isoformat()),
        'screenshot': step_data.get('screenshot'),
        'note': step_data.get('note', f"Step {len(st.session_state.steps) + 1}")
    }
    st.session_state.steps.append(step)

def create_capture_component():
    """Create a proper Streamlit component for screen capture"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Screen Capture Component</title>
        <style>
            .capture-container {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }
            .controls {
                text-align: center;
                margin: 20px 0;
            }
            button {
                padding: 12px 24px;
                margin: 8px;
                font-size: 16px;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            .start-btn { 
                background: #4CAF50; 
                color: white; 
            }
            .start-btn:hover { background: #45a049; }
            .stop-btn { 
                background: #f44336; 
                color: white; 
            }
            .stop-btn:hover { background: #da190b; }
            .capture-btn { 
                background: #2196F3; 
                color: white; 
            }
            .capture-btn:hover { background: #1976D2; }
            .status {
                text-align: center;
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
                font-weight: bold;
                transition: all 0.3s ease;
            }
            .ready { background: #e8f5e8; color: #2e7d32; }
            .recording { background: #ffebee; color: #c62828; }
            .error { background: #ffcdd2; color: #d32f2f; }
            .success { background: #c8e6c9; color: #388e3c; }
            .screenshots {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 15px;
                margin: 20px 0;
            }
            .screenshot {
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                padding: 10px;
                background: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .screenshot img {
                width: 100%;
                height: auto;
                border-radius: 4px;
            }
            .screenshot-info {
                font-size: 12px;
                color: #666;
                margin-top: 8px;
                text-align: center;
            }
            .hidden { display: none; }
        </style>
    </head>
    <body>
        <div class="capture-container">
            <h2>🎥 Screen & Audio Capture</h2>
            
            <div class="controls">
                <button id="startBtn" class="start-btn">Start Recording</button>
                <button id="stopBtn" class="stop-btn" disabled>Stop Recording</button>
                <button id="captureBtn" class="capture-btn" disabled>Mark Step (Ctrl+Shift+S)</button>
            </div>
            
            <div id="status" class="status ready">Ready to start recording</div>
            
            <div id="screenshots" class="screenshots"></div>
        </div>

        <script>
        class ScreenCapture {
            constructor() {
                this.mediaRecorder = null;
                this.screenStream = null;
                this.audioStream = null;
                this.stepCounter = 0;
                this.isRecording = false;
                this.capturedSteps = [];
                
                this.initializeElements();
                this.bindEvents();
                this.loadFromStorage();
            }
            
            initializeElements() {
                this.startBtn = document.getElementById('startBtn');
                this.stopBtn = document.getElementById('stopBtn');
                this.captureBtn = document.getElementById('captureBtn');
                this.status = document.getElementById('status');
                this.screenshots = document.getElementById('screenshots');
            }
            
            bindEvents() {
                this.startBtn.addEventListener('click', () => this.startRecording());
                this.stopBtn.addEventListener('click', () => this.stopRecording());
                this.captureBtn.addEventListener('click', () => this.captureStep());
                
                // Keyboard shortcut
                document.addEventListener('keydown', (event) => {
                    if (event.ctrlKey && event.shiftKey && event.key === 'S') {
                        event.preventDefault();
                        if (this.isRecording) {
                            this.captureStep();
                        }
                    }
                });
            }
            
            loadFromStorage() {
                // Load any existing captured steps
                const stored = localStorage.getItem('processSteps');
                if (stored) {
                    try {
                        this.capturedSteps = JSON.parse(stored);
                        this.stepCounter = this.capturedSteps.length;
                        
                        // Display stored screenshots
                        this.capturedSteps.forEach(step => {
                            this.displayScreenshot(step);
                        });
                        
                        if (this.capturedSteps.length > 0) {
                            this.updateStatus(`Loaded ${this.capturedSteps.length} steps from previous session`, 'success');
                        }
                    } catch (e) {
                        console.error('Error loading stored steps:', e);
                    }
                }
            }
            
            async startRecording() {
                try {
                    this.updateStatus('Requesting permissions...', 'ready');
                    
                    // Clear old data
                    localStorage.removeItem('processSteps');
                    this.capturedSteps = [];
                    this.stepCounter = 0;
                    this.screenshots.innerHTML = '';
                    
                    // Request screen capture
                    this.screenStream = await navigator.mediaDevices.getDisplayMedia({
                        video: { 
                            mediaSource: 'screen',
                            width: { ideal: 1920 },
                            height: { ideal: 1080 }
                        },
                        audio: false
                    });
                    
                    // Request audio capture
                    this.audioStream = await navigator.mediaDevices.getUserMedia({
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 44100
                        }
                    });
                    
                    this.isRecording = true;
                    
                    this.updateUI();
                    this.updateStatus('🔴 Recording... Click "Mark Step" to capture screenshots', 'recording');
                    
                    // Handle screen share end
                    this.screenStream.getVideoTracks()[0].onended = () => {
                        this.stopRecording();
                    };
                    
                } catch (error) {
                    console.error('Error starting recording:', error);
                    this.handleError(error);
                }
            }
            
            stopRecording() {
                if (this.screenStream) {
                    this.screenStream.getTracks().forEach(track => track.stop());
                }
                if (this.audioStream) {
                    this.audioStream.getTracks().forEach(track => track.stop());
                }
                
                this.isRecording = false;
                this.updateUI();
                
                // Save to localStorage
                this.saveToStorage();
                
                this.updateStatus(`✅ Recording stopped. ${this.stepCounter} steps captured. Click "Load Captured Steps" in Streamlit to import them.`, 'success');
            }
            
            async captureStep() {
                if (!this.screenStream || !this.isRecording) {
                    this.updateStatus('Please start recording first', 'error');
                    return;
                }
                
                try {
                    this.stepCounter++;
                    
                    // Create canvas to capture current screen
                    const canvas = document.createElement('canvas');
                    const ctx = canvas.getContext('2d');
                    const video = document.createElement('video');
                    
                    video.srcObject = this.screenStream;
                    video.play();
                    
                    await new Promise((resolve) => {
                        video.onloadedmetadata = () => {
                            canvas.width = video.videoWidth;
                            canvas.height = video.videoHeight;
                            ctx.drawImage(video, 0, 0);
                            
                            // Convert to base64
                            const dataURL = canvas.toDataURL('image/png');
                            
                            // Store step data
                            const stepData = {
                                step: this.stepCounter,
                                timestamp: new Date().toISOString(),
                                screenshot: dataURL,
                                note: `Step ${this.stepCounter}`
                            };
                            
                            this.capturedSteps.push(stepData);
                            this.displayScreenshot(stepData);
                            this.saveToStorage();
                            
                            this.updateStatus(`✅ Step ${this.stepCounter} captured!`, 'success');
                            
                            // Reset status after 2 seconds
                            setTimeout(() => {
                                if (this.isRecording) {
                                    this.updateStatus('🔴 Recording... Click "Mark Step" to capture screenshots', 'recording');
                                }
                            }, 2000);
                            
                            resolve();
                        };
                    });
                    
                } catch (error) {
                    console.error('Error capturing step:', error);
                    this.updateStatus('Error capturing step', 'error');
                }
            }
            
            displayScreenshot(stepData) {
                const screenshotDiv = document.createElement('div');
                screenshotDiv.className = 'screenshot';
                screenshotDiv.innerHTML = `
                    <img src="${stepData.screenshot}" alt="Step ${stepData.step}">
                    <div class="screenshot-info">
                        Step ${stepData.step}<br>
                        ${new Date(stepData.timestamp).toLocaleTimeString()}
                    </div>
                `;
                
                this.screenshots.appendChild(screenshotDiv);
            }
            
            saveToStorage() {
                try {
                    localStorage.setItem('processSteps', JSON.stringify(this.capturedSteps));
                    console.log(`Saved ${this.capturedSteps.length} steps to localStorage`);
                } catch (e) {
                    console.error('Error saving to localStorage:', e);
                    this.updateStatus('Warning: Could not save data (storage full?)', 'error');
                }
            }
            
            updateUI() {
                this.startBtn.disabled = this.isRecording;
                this.stopBtn.disabled = !this.isRecording;
                this.captureBtn.disabled = !this.isRecording;
            }
            
            updateStatus(message, type) {
                this.status.textContent = message;
                this.status.className = `status ${type}`;
            }
            
            handleError(error) {
                let message = 'Unknown error occurred';
                
                if (error.name === 'NotAllowedError') {
                    message = 'Permission denied. Please allow screen sharing and microphone access.';
                } else if (error.name === 'NotFoundError') {
                    message = 'No screen capture source found.';
                } else if (error.name === 'NotSupportedError') {
                    message = 'Screen capture not supported in this browser.';
                } else if (error.message) {
                    message = error.message;
                }
                
                this.updateStatus(message, 'error');
            }
        }
        
        // Initialize when DOM is loaded
        document.addEventListener('DOMContentLoaded', () => {
            new ScreenCapture();
        });
        </script>
    </body>
    </html>
    """
    return html_content

def load_steps_from_component():
    """Load captured steps from localStorage via a helper component"""
    reader_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
    </head>
    <body>
        <script>
            // Read from localStorage and send to parent
            const steps = localStorage.getItem('processSteps');
            if (steps) {
                // Send to Streamlit via query parameter hack
                const data = JSON.parse(steps);
                document.body.innerHTML = '<pre style="display:none;" id="data">' + JSON.stringify(data) + '</pre>';
                
                // Also try to communicate via title
                document.title = 'DATA:' + steps;
            } else {
                document.body.innerHTML = '<pre style="display:none;" id="data">[]</pre>';
                document.title = 'DATA:[]';
            }
        </script>
    </body>
    </html>
    """
    
    # This won't actually work to return data, but we'll use a different approach
    html(reader_html, height=0)

def show_capture_interface():
    """Show the screen capture interface using proper Streamlit components"""
    st.markdown("""
    <div style="text-align: center; padding: 20px; border: 2px dashed #ccc; border-radius: 10px; margin: 20px 0;">
        <h3>🎥 Screen & Audio Capture</h3>
        <p>Professional screen and audio capture with real browser APIs</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Instructions
    st.markdown("""
    ### 📋 How to Use the Capture Interface
    
    1. **Click "Start Recording"** below to begin screen and audio capture
    2. **Allow screen sharing** when prompted (select the window/tab you want to record)
    3. **Allow microphone access** when prompted
    4. **Mark Steps** by clicking the "Mark Step" button or pressing `Ctrl+Shift+S`
    5. **Stop Recording** when finished
    6. **Click "Load Captured Steps"** button to import your screenshots
    7. **Generate Documentation** to create AI-powered instructions
    
    **Supported Browsers:** Chrome, Edge, Firefox (latest versions)
    """)
    
    # Use Streamlit's HTML component
    capture_html = create_capture_component()
    html(capture_html, height=600, scrolling=True)
    
    # Add a manual load button
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Load Captured Steps", type="primary", use_container_width=True):
            # JavaScript to read localStorage
            js_code = """
            <script>
                const steps = localStorage.getItem('processSteps');
                if (steps) {
                    const data = JSON.parse(steps);
                    // Store in a way Streamlit can access
                    const event = new CustomEvent('streamlit:setValue', { detail: data });
                    window.dispatchEvent(event);
                    alert('Found ' + data.length + ' steps. Copy this and paste in the text area below:\\n\\n' + steps);
                } else {
                    alert('No captured steps found. Make sure you captured some steps first!');
                }
            </script>
            """
            st.components.v1.html(js_code, height=0)
            
    with col2:
        if st.button("🗑️ Clear Browser Storage", use_container_width=True):
            clear_js = """
            <script>
                localStorage.removeItem('processSteps');
                alert('Browser storage cleared!');
            </script>
            """
            st.components.v1.html(clear_js, height=0)
    
    # Manual data import area
    st.markdown("### Manual Import (Temporary Workaround)")
    st.info("👆 Click 'Load Captured Steps', then copy the data from the alert and paste it below:")
    
    data_input = st.text_area(
        "Paste captured steps JSON here:",
        height=150,
        placeholder='[{"step": 1, "timestamp": "...", "screenshot": "data:image/png;base64,...", "note": "Step 1"}]'
    )
    
    if st.button("Import Pasted Data", use_container_width=True):
        if data_input.strip():
            try:
                steps_data = json.loads(data_input)
                st.session_state.steps = []
                for step_data in steps_data:
                    add_step(step_data)
                st.success(f"✅ Successfully imported {len(steps_data)} steps!")
                st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"Invalid JSON data: {str(e)}")
        else:
            st.warning("Please paste the JSON data first")

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

I will provide you with screenshots from a user demonstrating a process.
Please create clear, professional documentation that includes:

1. A descriptive title
2. Purpose/overview
3. Prerequisites (if applicable)
4. Numbered step-by-step instructions
5. Clear action descriptions for each step

Make the instructions concise but complete. Use imperative language ("Click the...", "Enter...", "Select...").
Focus on what the user needs to do, not what the system is doing.
Format the output in clean markdown.
"""
        
        content_parts.append(instructions)
        
        # Add each step with screenshot
        for i, step in enumerate(st.session_state.steps, 1):
            step_text = f"\n\n--- Step {i} ---\n"
            if step.get('note'):
                step_text += f"Note: {step['note']}\n"
            step_text += f"Timestamp: {step['timestamp']}\n"
            
            content_parts.append(step_text)
            
            # Add screenshot if available
            if step.get('screenshot'):
                # For Gemini, we need to convert the data URL to proper format
                screenshot_data = step['screenshot']
                if screenshot_data.startswith('data:image'):
                    # Extract base64 data
                    base64_data = screenshot_data.split(',')[1]
                    image_bytes = base64.b64decode(base64_data)
                    
                    # Create PIL Image for Gemini
                    from PIL import Image
                    image = Image.open(io.BytesIO(image_bytes))
                    content_parts.append(image)
        
        # Generate documentation
        with st.spinner("🤖 AI is analyzing your screenshots and generating documentation..."):
            response = model.generate_content(content_parts)
            
        return response.text
        
    except Exception as e:
        st.error(f"Error generating documentation: {str(e)}")
        import traceback
        st.error(f"Details: {traceback.format_exc()}")
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
        2. Create a `.env` file in your project directory with: `GEMINI_API_KEY=your_key_here`
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
            st.markdown('<div class="recording-indicator">🔴 Recording in Progress</div>', unsafe_allow_html=True)
            st.info("💡 Use Ctrl+Shift+S to quickly mark steps, or click the button in the capture interface below")
            
            # Show capture interface
            show_capture_interface()
            
            # Stop recording button
            if st.button("⏹️ Stop Recording", type="secondary", use_container_width=True):
                stop_recording()
                st.rerun()
        
        # Current steps
        if st.session_state.steps:
            st.markdown("---")
            st.subheader(f"📋 Loaded Steps ({len(st.session_state.steps)})")
            for step in st.session_state.steps:
                with st.expander(f"Step {step['id']}: {step['note']}", expanded=False):
                    st.write(f"**Timestamp:** {step['timestamp']}")
                    if step.get('screenshot', '').startswith('data:image'):
                        st.image(step['screenshot'], caption=f"Screenshot for Step {step['id']}", use_container_width=True)
    
    with col2:
        st.subheader("📄 Documentation")
        
        if st.session_state.steps and not st.session_state.recording:
            st.success(f"✅ {len(st.session_state.steps)} steps ready for documentation")
            
            if st.button("🤖 Generate Documentation", type="primary", use_container_width=True):
                doc = generate_documentation()
                if doc:
                    st.success("Documentation generated successfully!")
                    
                    # Display in expandable section
                    with st.expander("📄 View Generated Documentation", expanded=True):
                        st.markdown(doc)
                    
                    # Download button
                    st.download_button(
                        label="📥 Download as Markdown",
                        data=doc,
                        file_name=f"process_documentation_{st.session_state.session_id}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
        elif st.session_state.recording:
            st.info("⏸️ Stop recording first, then load your captured steps")
        else:
            st.info("📸 Record and load some steps first, then generate documentation")
        
        # Session info
        if st.session_state.session_id:
            st.markdown("---")
            st.caption(f"Session ID: {st.session_state.session_id}")
            if st.button("🔄 Start New Session", use_container_width=True):
                st.session_state.steps = []
                st.session_state.session_id = None
                st.session_state.recording = False
                st.rerun()
    
    # Instructions
    with st.expander("ℹ️ How to Use This Tool"):
        st.markdown("""
        ### Getting Started
        
        1. **Start Recording**: Click the "Start Recording" button
        2. **Grant Permissions**: Allow screen sharing and microphone access when prompted
        3. **Demonstrate Process**: Perform your workflow on the screen you're sharing
        4. **Mark Steps**: Press `Ctrl+Shift+S` or click "Mark Step" at important moments
        5. **Stop Recording**: Click "Stop Recording" when finished
        6. **Load Steps**: Click "Load Captured Steps" and follow the import instructions
        7. **Generate Docs**: Click "Generate Documentation" to create AI-powered instructions
        
        ### Current Limitation
        
        Due to browser security restrictions, there's an extra step to import your captured screenshots:
        - After stopping recording, click "Load Captured Steps"
        - Copy the JSON data from the alert popup
        - Paste it into the text area
        - Click "Import Pasted Data"
        
        This is a temporary workaround - in a production app, this would be automated with a proper backend.
        
        ### Tips for Better Documentation
        
        - **Mark key decision points** - Don't capture every click, just important steps
        - **Show clear screens** - Make sure relevant information is visible
        - **Capture in sequence** - Follow your normal workflow from start to finish
        - **Include context** - Capture screens that show where you are in the process
        
        ### Privacy Note
        
        - Screenshots are stored in your browser's localStorage
        - Only marked screenshots are sent to Google's Gemini AI for documentation generation
        - No continuous video recording is uploaded
        - Clear browser storage when done to remove all data
        """)

if __name__ == "__main__":
    main()