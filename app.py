import streamlit as st
import google.generativeai as genai
import json
import base64
import io
from datetime import datetime
import os
from dotenv import load_dotenv
from streamlit.components.v1 import html

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

def get_capture_html():
    """Get the HTML content for the capture interface"""
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Screen & Audio Capture</title>
    <style>
        body {
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
            padding: 10px 20px;
            margin: 5px;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
        }
        .start-btn { background: #4CAF50; color: white; }
        .stop-btn { background: #f44336; color: white; }
        .capture-btn { background: #2196F3; color: white; }
        .status {
            text-align: center;
            padding: 10px;
            margin: 10px 0;
            border-radius: 5px;
        }
        .recording { background: #ffebee; color: #c62828; }
        .ready { background: #e8f5e8; color: #2e7d32; }
        .screenshots {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
            gap: 10px;
            margin: 20px 0;
        }
        .screenshot {
            border: 1px solid #ddd;
            border-radius: 5px;
            padding: 5px;
        }
        .screenshot img {
            width: 100%;
            height: auto;
            border-radius: 3px;
        }
        .screenshot-info {
            font-size: 12px;
            color: #666;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <h1>Process Documenter - Screen & Audio Capture</h1>
    
    <div class="controls">
        <button id="startBtn" class="start-btn">Start Recording</button>
        <button id="stopBtn" class="stop-btn" disabled>Stop Recording</button>
        <button id="captureBtn" class="capture-btn" disabled>Mark Step</button>
    </div>
    
    <div id="status" class="status ready">Ready to start recording</div>
    
    <div id="screenshots" class="screenshots"></div>
    
    <script>
        let mediaRecorder;
        let screenStream;
        let audioStream;
        let combinedStream;
        let recordedChunks = [];
        let stepCounter = 0;
        
        const startBtn = document.getElementById('startBtn');
        const stopBtn = document.getElementById('stopBtn');
        const captureBtn = document.getElementById('captureBtn');
        const status = document.getElementById('status');
        const screenshots = document.getElementById('screenshots');
        
        startBtn.addEventListener('click', startRecording);
        stopBtn.addEventListener('click', stopRecording);
        captureBtn.addEventListener('click', captureStep);
        
        async function startRecording() {
            try {
                // Request screen capture
                screenStream = await navigator.mediaDevices.getDisplayMedia({
                    video: { mediaSource: 'screen' },
                    audio: false
                });
                
                // Request audio capture
                audioStream = await navigator.mediaDevices.getUserMedia({
                    audio: true
                });
                
                // Combine streams
                combinedStream = new MediaStream([
                    ...screenStream.getVideoTracks(),
                    ...audioStream.getAudioTracks()
                ]);
                
                // Set up media recorder
                mediaRecorder = new MediaRecorder(combinedStream, {
                    mimeType: 'video/webm;codecs=vp9,opus'
                });
                
                recordedChunks = [];
                mediaRecorder.ondataavailable = (event) => {
                    if (event.data.size > 0) {
                        recordedChunks.push(event.data);
                    }
                };
                
                mediaRecorder.start(1000); // Collect data every second
                
                // Update UI
                startBtn.disabled = true;
                stopBtn.disabled = false;
                captureBtn.disabled = false;
                status.textContent = 'Recording... Click "Mark Step" to capture screenshots';
                status.className = 'status recording';
                
                // Handle screen share end
                screenStream.getVideoTracks()[0].onended = () => {
                    stopRecording();
                };
                
            } catch (error) {
                console.error('Error starting recording:', error);
                status.textContent = 'Error: ' + error.message;
                status.className = 'status';
            }
        }
        
        function stopRecording() {
            if (mediaRecorder && mediaRecorder.state === 'recording') {
                mediaRecorder.stop();
            }
            
            // Stop all tracks
            if (screenStream) {
                screenStream.getTracks().forEach(track => track.stop());
            }
            if (audioStream) {
                audioStream.getTracks().forEach(track => track.stop());
            }
            
            // Update UI
            startBtn.disabled = false;
            stopBtn.disabled = true;
            captureBtn.disabled = true;
            status.textContent = 'Recording stopped. You can start a new session.';
            status.className = 'status ready';
            
            // Generate final video
            if (recordedChunks.length > 0) {
                generateVideo();
            }
        }
        
        function captureStep() {
            if (!screenStream) return;
            
            stepCounter++;
            
            // Create canvas to capture current screen
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const video = document.createElement('video');
            
            video.srcObject = screenStream;
            video.play();
            
            video.onloadedmetadata = () => {
                canvas.width = video.videoWidth;
                canvas.height = video.videoHeight;
                
                // Draw current frame
                ctx.drawImage(video, 0, 0);
                
                // Convert to blob
                canvas.toBlob((blob) => {
                    const url = URL.createObjectURL(blob);
                    
                    // Create screenshot element
                    const screenshotDiv = document.createElement('div');
                    screenshotDiv.className = 'screenshot';
                    screenshotDiv.innerHTML = `
                        <img src="${url}" alt="Step ${stepCounter}">
                        <div class="screenshot-info">
                            Step ${stepCounter}<br>
                            ${new Date().toLocaleTimeString()}
                        </div>
                    `;
                    
                    screenshots.appendChild(screenshotDiv);
                    
                    // Store data for later processing
                    storeStepData(blob, stepCounter);
                }, 'image/png');
            };
        }
        
        function storeStepData(blob, stepNumber) {
            // Convert blob to base64 for storage
            const reader = new FileReader();
            reader.onload = () => {
                const stepData = {
                    step: stepNumber,
                    timestamp: new Date().toISOString(),
                    screenshot: reader.result,
                    audio: null // Will be filled when recording stops
                };
                
                // Store in localStorage
                const existingSteps = JSON.parse(localStorage.getItem('processSteps') || '[]');
                existingSteps.push(stepData);
                localStorage.setItem('processSteps', JSON.stringify(existingSteps));
            };
            reader.readAsDataURL(blob);
        }
        
        function generateVideo() {
            const blob = new Blob(recordedChunks, { type: 'video/webm' });
            const url = URL.createObjectURL(blob);
            
            // Store video data
            const reader = new FileReader();
            reader.onload = () => {
                const videoData = {
                    timestamp: new Date().toISOString(),
                    video: reader.result,
                    duration: recordedChunks.length
                };
                localStorage.setItem('processVideo', JSON.stringify(videoData));
            };
            reader.readAsDataURL(blob);
            
            // Show download link
            const downloadLink = document.createElement('a');
            downloadLink.href = url;
            downloadLink.download = `process_recording_${Date.now()}.webm`;
            downloadLink.textContent = 'Download Recording';
            downloadLink.style.display = 'block';
            downloadLink.style.textAlign = 'center';
            downloadLink.style.margin = '20px 0';
            downloadLink.style.padding = '10px';
            downloadLink.style.backgroundColor = '#4CAF50';
            downloadLink.style.color = 'white';
            downloadLink.style.textDecoration = 'none';
            downloadLink.style.borderRadius = '5px';
            
            document.body.appendChild(downloadLink);
        }
        
        // Keyboard shortcut for marking steps
        document.addEventListener('keydown', (event) => {
            if (event.ctrlKey && event.shiftKey && event.key === 'S') {
                event.preventDefault();
                if (!captureBtn.disabled) {
                    captureStep();
                }
            }
        });
    </script>
</body>
</html>
"""

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
                <button id="captureBtn" class="capture-btn" disabled>Mark Step</button>
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
                        this.captureStep();
                    }
                });
            }
            
            async startRecording() {
                try {
                    this.updateStatus('Requesting permissions...', 'ready');
                    
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
                    this.updateStatus('Recording... Click "Mark Step" to capture screenshots', 'recording');
                    
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
                this.updateStatus(`Recording stopped. Captured ${this.stepCounter} steps.`, 'ready');
                
                // Send data to parent window
                this.sendDataToParent();
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
                        this.updateStatus(`Step ${this.stepCounter} captured!`, 'success');
                        
                        // Reset status after 2 seconds
                        setTimeout(() => {
                            if (this.isRecording) {
                                this.updateStatus('Recording... Click "Mark Step" to capture screenshots', 'recording');
                            }
                        }, 2000);
                    };
                    
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
            
            sendDataToParent() {
                // Send data to parent window (Streamlit)
                if (window.parent && window.parent !== window) {
                    window.parent.postMessage({
                        type: 'capture_data',
                        data: this.capturedSteps
                    }, '*');
                }
                
                // Also store in localStorage for persistence
                localStorage.setItem('processSteps', JSON.stringify(this.capturedSteps));
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
    6. **Generate Documentation** to create AI-powered instructions
    
    **Supported Browsers:** Chrome, Edge, Firefox (latest versions)
    """)
    
    # Use Streamlit's HTML component properly
    capture_html = create_capture_component()
    
    # Display the component
    html(capture_html, height=600, scrolling=True)
    
    # Load captured data button
    if st.button("📥 Load Captured Data", type="primary"):
        # In a real implementation, this would communicate with the component
        st.info("In a real implementation, this would load the captured screenshots and audio from the component.")
        st.success("✅ Mock data loaded! This simulates loading captured steps.")
        
        # Add some mock steps for demonstration
        for i in range(3):
            add_step({
                'screenshot': f"data:image/png;base64,mock_screenshot_{i+1}",
                'note': f"Step {i+1}: Mock captured step"
            })
        st.rerun()

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
            
            # Recording controls
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📸 Mark Step (Manual)", use_container_width=True):
                    # Manual step marking for testing
                    add_step({
                        'screenshot': f"mock_screenshot_{len(st.session_state.steps) + 1}",
                        'note': f"Manual Step {len(st.session_state.steps) + 1}"
                    })
                    st.success(f"Step {len(st.session_state.steps)} captured!")
                    st.rerun()
            
            with col_b:
                if st.button("⏹️ Stop Recording", use_container_width=True):
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
