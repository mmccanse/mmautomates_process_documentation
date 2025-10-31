# AI Process Documentation Generator

## Overview

**Purpose:**  
The AI Process Documentation Generator converts screen recordings into professional Standard Operating Procedure (SOP) documentation. Users upload a video recording in which they narrate a business process, and the app automatically generates audit-ready documentation with embedded screenshots.

It helps accounting and finance teams quickly document complex procedures such as:
- Preparing journal entries  
- Performing tasks in an ERP like preparing payment batches, pulling reports, submitting JEs, etc  
- Running monthly close reports  
- General system navigation and workflows

The goal is to save hours of manual documentation time, ensure repeatability, and improve auditability across finance operations.

---

## How It Works

### User Workflow

1. **Record Your Process**
   - Use any screen recording tool (Zoom, Loom, QuickTime, OBS, etc.)
   - Narrate the process as you demonstrate it
   - Explain navigation paths, actions, and decisions clearly
   - Save the recording as MP4, MOV, AVI, WebM, or MKV format

2. **Upload Video**
   - Upload your video file to the app
   - The app extracts the audio track for transcription

3. **AI Transcription**
   - Google's Gemini 2.5 Pro AI transcribes the audio
   - Transcript includes timestamps for key moments

4. **AI Analysis**
   - Gemini analyzes the transcript to identify key moments where screenshots should be captured
   - Identifies navigation paths, actions, data entry points, and decision points
   - Returns a list of moments with timestamps and descriptions

5. **Review & Edit Moments**
   - Review the AI-identified key moments
   - Add, remove, or modify moments as needed
   - Edit timestamps, descriptions, and navigation paths

6. **Extract Screenshots**
   - The app extracts video frames at each identified moment
   - Screenshots are displayed for review in chronological order

7. **Generate Documentation**
   - Gemini creates professional SOP documentation using:
     - The transcript (for step descriptions)
     - Screenshots (for visual context)
   - Generates a structured Word document with:
       - Process title and purpose  
     - Scope and prerequisites
     - Numbered step-by-step instructions
     - Control points (for SOX compliance)
     - Common issues & troubleshooting
     - Frequency information

8. **Download or Upload**
   - Download as Word document (.docx)
   - Optionally upload directly to Google Drive

---

## Core Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend UI** | Streamlit (Python) | Web-based interface for video upload and documentation generation |
| **Video Processing** | MoviePy | Extract audio from video files |
| **Image Processing** | OpenCV (cv2), Pillow | Extract frames at specific timestamps from video |
| **AI Transcription** | Google Gemini 2.5 Pro API | Transcribe audio recordings with timestamps |
| **AI Analysis** | Google Gemini 2.5 Pro API | Identify key moments for screenshots from transcript |
| **AI Documentation** | Google Gemini 2.5 Pro API | Generate professional SOP documentation |
| **Document Generation** | python-docx | Create Word documents with embedded screenshots |
| **Google Drive Integration** | Google Drive API | Upload generated documents to user's Drive |
| **Authentication** | Google OAuth 2.0 | Secure Google Drive access with limited scope (`drive.file`) |

---

## Key Features

- **Video-Based Processing**: Upload pre-recorded screen recordings (no live capture required)
- **AI-Powered Transcription**: Automatic transcription with timestamps
- **Smart Moment Detection**: AI identifies optimal screenshot capture points
- **Interactive Editing**: Review and edit AI-identified moments before extraction
- **Professional Documentation**: Generates audit-ready SOP documents with proper structure
- **Multiple Export Options**: Download Word document or upload to Google Drive
- **Google Drive Integration**: Optional seamless upload to user's Google Drive
- **No Installation Required**: Runs entirely in a web browser

---

## Installation & Setup

### Prerequisites

- Python 3.11+
- Google Gemini API key
- (Optional) Google OAuth credentials for Drive integration

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mmautomates_process_documentation
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Key**
   - Get your Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a `.env` file in the root directory:
     ```
     GEMINI_API_KEY=your_api_key_here
     ```

4. **(Optional) Configure Google Drive Integration**
   - Create a Google Cloud Project
   - Enable Google Drive API
   - Create OAuth 2.0 credentials
   - Add credentials to Streamlit Secrets (`.streamlit/secrets.toml`):
     ```toml
     [google_oauth]
     client_id = "your_client_id"
     client_secret = "your_client_secret"
     redirect_uri = "https://your-streamlit-app-url"
     ```

5. **Run the app**
   ```bash
   streamlit run app.py
   ```

---

## Usage Tips

### For Best Results

1. **Video Recording**
   - Speak clearly and describe what you're doing
   - Explicitly mention navigation paths (e.g., "go to Menu > Options > Add Account")
   - Keep recordings under 10 minutes for best performance
   - Explain the "why" not just the "what"

2. **Process Explanation**
   - Describe navigation steps clearly
   - Mention when you're clicking buttons or opening menus
   - Explain data entry and form completion
   - Note any decision points or important choices

3. **After Upload**
   - Review the transcript for accuracy
   - Edit key moments before extracting frames
   - Remove moments that aren't needed
   - Add moments AI may have missed

---

## Privacy & Security

### Data Processing

- **Video Storage**: Videos are stored as temporary files during processing and automatically deleted after screenshot extraction
- **Audio Processing**: Audio tracks are sent to Google's Gemini API for transcription
- **Image Processing**: Screenshots are extracted from videos and sent to Gemini API for documentation generation
- **Temporary Files**: All temporary processing files are deleted immediately after use

### Google Drive Integration

- Uses limited `drive.file` scope - only accesses files created by this app
- Cannot access, read, modify, or delete existing Drive files
- User explicitly authorizes access via Google OAuth consent screen
- All data transmission encrypted via HTTPS

### Important Security Notice

⚠️ **DO NOT upload videos containing:**
- Passwords, credentials, or authentication codes
- Social Security Numbers or personal identification numbers
- Financial account numbers or routing information
- Proprietary trade secrets or confidential business information
- Any other highly sensitive data

**Data Processing**: Audio, transcripts, and screenshots are processed by Google's Gemini API (third-party service). Processing is subject to [Google's Gemini API terms for paid services](https://ai.google.dev/gemini-api/terms#paid-services).

**Deployment**: This prototype is hosted on Streamlit Community Cloud. For enterprise use, this can be deployed on internal company servers for enhanced security. Enterprise deployments can also be configured to use a company's firewalled enterprise Gemini instance.

---

## Output Format

The app generates professional Word documents (.docx) with the following structure:

1. **Title**: Clear, descriptive process title
2. **Purpose**: Why this process exists and what it accomplishes
3. **Scope**: What this process covers
4. **Prerequisites**: What needs to be in place before starting
5. **Step-by-Step Instructions**: Numbered steps with embedded screenshots
6. **Control Points**: Key moments where accuracy is critical (for SOX compliance)
7. **Common Issues & Troubleshooting**: Potential problems and solutions
8. **Frequency**: How often this process is performed

Screenshots are embedded inline with each relevant step, providing visual context for the instructions.

---

## Technical Architecture

### Processing Flow

1. **Video Upload** → Video file saved to temporary storage
2. **Audio Extraction** → Audio track extracted using MoviePy
3. **Transcription** → Audio sent to Gemini API for transcription with timestamps
4. **Moment Analysis** → Transcript analyzed by Gemini to identify key screenshot moments
5. **User Review** → User can edit, add, or remove identified moments
6. **Frame Extraction** → OpenCV extracts video frames at specified timestamps
7. **Documentation Generation** → Transcript + screenshots sent to Gemini for SOP generation
8. **Word Document Creation** → python-docx creates formatted Word document with embedded images
9. **Export** → Download locally or upload to Google Drive
10. **Cleanup** → All temporary files deleted

### Key Functions

- `extract_audio_from_video()`: Extracts audio track from video file
- `transcribe_audio_with_gemini()`: Transcribes audio using Gemini API
- `analyze_transcript_for_key_moments()`: Analyzes transcript to identify screenshot moments
- `extract_all_frames()`: Extracts video frames at specified timestamps
- `generate_documentation()`: Creates SOP documentation from transcript and screenshots
- `create_word_document()`: Builds Word document with proper formatting
- `upload_word_doc_to_drive()`: Uploads document to Google Drive
- `authenticate_google()`: Handles Google OAuth flow

---

## Requirements

See `requirements.txt` for full list. Key dependencies include:

- `streamlit` - Web framework
- `google-generativeai` - Gemini API client
- `moviepy` - Video processing
- `opencv-python` - Image/video frame extraction
- `Pillow` - Image processing
- `python-docx` - Word document generation
- `google-auth-oauthlib` - Google OAuth authentication
- `google-api-python-client` - Google Drive API client
- `python-dotenv` - Environment variable management

---

## Future Enhancements

Planned improvements include:
- Smart annotations to highlight UI elements referenced in audio
- Preview multiple frames around timestamps for optimal screenshot selection
- Multi-language support
- Long-form video segmentation
- Batch processing of multiple videos
- Integration with document management systems

---

## License

[Add your license information here]

---

## Support

For issues, questions, or contributions, please [open an issue](link-to-issues) or [contact the maintainers](contact-info).
