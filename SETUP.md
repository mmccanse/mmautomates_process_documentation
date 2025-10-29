# Process Documenter - Setup Guide

## Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Get Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the generated key

### 3. Set Environment Variable

**Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

**Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**Mac/Linux:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 4. Run the App
```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## How to Use

### Basic Workflow
1. **Start Recording** - Click the "Start Recording" button
2. **Open Capture Interface** - Click the button to open screen/audio capture
3. **Allow Permissions** - Grant screen sharing and microphone access
4. **Demonstrate Process** - Perform your workflow while talking through it
5. **Mark Steps** - Click "Mark Step" or press `Ctrl+Shift+S` at key moments
6. **Stop Recording** - Click "Stop Recording" when finished
7. **Generate Documentation** - Click "Generate Documentation" to create AI-powered docs

### Features
- **Screen Capture**: Records your screen while you work
- **Audio Recording**: Captures your narration
- **Step Marking**: Mark important moments with hotkeys
- **AI Processing**: Gemini analyzes screenshots and audio to create documentation
- **Export**: Download as Markdown or view in browser

## Troubleshooting

### Screen Capture Not Working
- Make sure you're using HTTPS (required for screen capture)
- For local development, Streamlit should handle this automatically
- If not, try: `streamlit run app.py --server.enableCORS false --server.enableXsrfProtection false`

### API Key Issues
- Make sure the environment variable is set correctly
- Restart the terminal/command prompt after setting the variable
- Check that the API key is valid in Google AI Studio

### Audio Not Recording
- Check browser permissions for microphone access
- Make sure you're not in a private/incognito window
- Try refreshing the page and allowing permissions again

## Deployment

### Streamlit Cloud (Recommended)
1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repository
4. Deploy!

### Other Platforms
- **Heroku**: Add `Procfile` with `web: streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`
- **Railway**: Similar to Heroku
- **AWS/GCP/Azure**: Use containerized deployment

## Security Notes

This is a prototype for demonstration purposes. For production use, consider:
- Implementing user authentication
- Adding data encryption
- Setting up proper data retention policies
- Implementing audit logging
- Adding privacy controls for sensitive data
