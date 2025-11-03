# Deployment Plan: Self-Host Streamlit App on mmautomates.com

## Overview
Self-host your SOP Streamlit app on your verified domain (mmautomates.com) using Google Cloud Run, migrate OAuth from personal Google account to mmautomates.com Google Cloud Console, host privacy policy/terms on Squarespace, improve accessibility, and leverage MCP servers.

## Platform: Google Cloud Run (Selected)

**Why Cloud Run:**
- **Cost-efficient**: Pay-per-use (typically $5-10/month for low traffic), free tier includes 2M requests/month
- **Google Integration**: Same Google Cloud Console for OAuth setup (easier management)
- **Serverless**: Auto-scales, no server management
- **Custom Domain**: Integrated with Google Cloud (after domain verification)
- **Production-ready**: Enterprise-grade reliability

**Setup Complexity**: Moderate (requires Dockerfile, but step-by-step instructions provided)
**Setup Time**: 60-90 minutes

**Note**: This is the recommended approach since you'll be using Google Cloud Console for OAuth anyway - keeps everything in one place.

---

## Phase 1: Self-Hosting Setup on Google Cloud Run - 60-90 minutes

### Overview
Cloud Run is serverless, pay-per-use, and integrates seamlessly with Google Cloud Console (same account for OAuth setup). This keeps everything in one Google Cloud ecosystem.

### Prerequisites
- Google Cloud account (can use same account as OAuth setup - meredith@mmautomates.com)
- [gcloud CLI](https://cloud.google.com/sdk/docs/install) installed, OR use Cloud Shell in browser (no installation needed)

**Recommended**: Use Cloud Shell in browser (easiest for beginners) - no local installation required.

### 1.1 Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Sign in with meredith@mmautomates.com (or your mmautomates.com Google account)
3. Click "Select a project" → "New Project"
4. Project name: `sop-ai-mmautomates`
5. Click "Create"
6. Wait for project creation (30 seconds)

### 1.2 Enable Required APIs
1. Go to [API Library](https://console.cloud.google.com/apis/library)
2. Enable these APIs (search and enable each):
   - **Cloud Run API** - For deploying containers
   - **Artifact Registry API** (or Container Registry API) - For storing container images
   - **Cloud Build API** - For building containers

### 1.3 Create Dockerfile
Create `Dockerfile` in project root:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for video processing
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run sets PORT env var)
EXPOSE 8080

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8080/_stcore/health || exit 1

# Run Streamlit
CMD streamlit run app.py --server.port=$PORT --server.address=0.0.0.0 --server.headless=true
```

### 1.4 Create .dockerignore (Optional but Recommended)
Create `.dockerignore` to exclude unnecessary files:
```
__pycache__
*.pyc
*.pyo
*.pyd
.Python
env/
venv/
.venv
.env
.git
.gitignore
README.md
*.md
.cursor/
.vscode/
token.pickle
*.pickle
```

### 1.5 Build and Deploy Container

**Option A: Using Cloud Shell (Recommended for Beginners)**
1. Go to [Cloud Shell](https://shell.cloud.google.com) (click terminal icon in top right of Cloud Console)
2. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/mmautomates_process_documentation.git
   cd mmautomates_process_documentation
   ```
   Or if you've already cloned it, just navigate to the directory.
3. Set your project:
   ```bash
   gcloud config set project sop-ai-mmautomates
   ```
4. Build container:
   ```bash
   gcloud builds submit --tag gcr.io/sop-ai-mmautomates/sop-ai
   ```
   This will take 5-10 minutes for first build.
5. Deploy to Cloud Run:
   ```bash
   gcloud run deploy sop-ai \
     --image gcr.io/sop-ai-mmautomates/sop-ai \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --memory 2Gi \
     --timeout 300 \
     --max-instances 10 \
     --set-env-vars "GEMINI_API_KEY=your-actual-key-here"
   ```
   Replace `your-actual-key-here` with your actual Gemini API key.

**Option B: Using gcloud CLI (Local)**
- Same commands as Option A, but run from your local terminal after installing gcloud CLI

### 1.6 Configure Environment Variables
1. Go to Cloud Run → [Your Service](https://console.cloud.google.com/run)
2. Click on `sop-ai` service
3. Click "Edit & Deploy New Revision"
4. Go to "Variables & Secrets" tab
5. Add environment variables:
   - `GEMINI_API_KEY`: Your existing Gemini API key
   - `GOOGLE_OAUTH_CLIENT_ID`: (Leave empty, will add in Phase 4)
   - `GOOGLE_OAUTH_CLIENT_SECRET`: (Leave empty, will add in Phase 4)
   - `GOOGLE_OAUTH_REDIRECT_URI`: (Will set to your domain in Phase 2)
6. Click "Deploy" (wait 2-3 minutes for deployment)

### 1.7 Get Cloud Run URL and Test
1. After deployment, Cloud Run provides URL: `https://sop-ai-xxxxx-uc.a.run.app`
2. Click the URL to test app loads
3. Test basic functionality (video upload, etc.)

**Files to create:**
- `Dockerfile` (new file)
- `.dockerignore` (new file, optional but recommended)

---

## Phase 2: Custom Domain Setup - 30-60 minutes

### 2.1 Configure Custom Domain in Cloud Run
1. Go to Cloud Run → Your Service → "Manage Custom Domains"
2. Click "Add Mapping"
3. Enter domain: `sop.mmautomates.com`
4. Cloud Run requires domain verification:
   - Add TXT record to DNS: `google-site-verification=xxxxx`
   - Verify in Google Search Console
5. After verification, Cloud Run provides DNS records (A or CNAME)
6. Add DNS records to Vercel (see Phase 2.2)

### 2.2 Update DNS in Vercel
1. Since Vercel handles DNS for mmautomates.com:
   - Go to Vercel dashboard → Your project → Settings → Domains
   - OR go directly to DNS settings for mmautomates.com
2. Add the DNS records provided by Cloud Run:
   - If CNAME: Add CNAME record with Name: `app` (or `sop`) and Value: Cloud Run-provided CNAME target
   - If A record: Add A record with provided IP addresses
3. Save changes

### 2.3 Wait for DNS Propagation
- DNS propagation: 10-60 minutes
- Check status: [whatsmydns.net](https://www.whatsmydns.net) or `dig sop.mmautomates.com`
- Cloud Run auto-provisions SSL certificate (5-10 minutes after DNS)

### 2.4 Verify Domain is Live
- Test: `https://sop.mmautomates.com`
- Verify HTTPS works (SSL auto-provisions)
- Test app functionality at new domain

**Files to update:**
- No code changes (domain configuration only)

---

## Phase 3: Update URLs Throughout App - 30 minutes

### 3.1 Update App URLs in `app.py`
- Line 50: Change `APP_URL` from `https://sop-ai.streamlit.app` to `https://sop.mmautomates.com`
- Line 51: Update `THUMBNAIL_URL` to new domain
- Update any hardcoded Streamlit Cloud URLs

### 3.2 Update Privacy Policy & Terms Links
- Update links in `app.py` (lines 1575-1576) to Squarespace URLs:
  - Privacy Policy: `https://mmautomates.com/privacy-policy`
  - Terms of Use: `https://mmautomates.com/terms-of-use`

**Files to modify:**
- `app.py` (lines 50-51, 1575-1576)

---

## Phase 4: Google OAuth Migration to mmautomates.com - 2-3 hours

### 4.1 Create New Google Cloud Project (or use existing)
1. Access Google Cloud Console with meredith@mmautomates.com account
   - If you don't have a Google account for mmautomates.com, you may need to:
     - Create Google Workspace account, OR
     - Use a Google account associated with your domain
2. Use the same project: `sop-ai-mmautomates` (or create new: "SOP AI - mmautomates")
3. Enable APIs:
   - Google Drive API
   - Google OAuth 2.0 API

### 4.2 Configure OAuth Consent Screen
1. Go to APIs & Services → OAuth consent screen
2. Settings:
   - Application type: External (or Internal if Workspace)
   - Application name: "SOP AI - Process Documentation Generator"
   - User support email: `meredith@mmautomates.com`
   - Application home page: `https://sop.mmautomates.com`
   - Privacy policy URL: `https://mmautomates.com/privacy-policy`
   - Terms of service URL: `https://mmautomates.com/terms-of-use`
   - Authorized domains: Add `mmautomates.com`
   - Developer contact: `meredith@mmautomates.com`
3. Scopes: Add `https://www.googleapis.com/auth/drive.file`
4. Save and continue

### 4.3 Create OAuth 2.0 Credentials
1. Go to APIs & Services → Credentials
2. Create OAuth 2.0 Client ID
3. Settings:
   - Application type: Web application
   - Name: "SOP AI Web Client - mmautomates"
   - Authorized JavaScript origins: `https://sop.mmautomates.com`
   - Authorized redirect URIs: `https://sop.mmautomates.com`
4. Save Client ID and Client Secret

### 4.4 Update Environment Variables in Cloud Run
1. Go to Cloud Run → Your Service → Edit & Deploy New Revision
2. Variables & Secrets tab:
   - Update `GOOGLE_OAUTH_CLIENT_ID`: New client ID
   - Update `GOOGLE_OAUTH_CLIENT_SECRET`: New client secret
   - Update `GOOGLE_OAUTH_REDIRECT_URI`: `https://sop.mmautomates.com`
3. Click "Deploy"

### 4.5 Update OAuth Code to Use Environment Variables
- Modify `app.py` `authenticate_google()` function (around line 797)
- Check environment variables first, then fall back to Streamlit secrets
- This allows OAuth to work on Cloud Run (no Streamlit secrets)

### 4.6 Submit for Google Verification
1. Go to OAuth consent screen → Publish App
2. Submit for verification
3. Provide:
   - App purpose and functionality
   - Video demonstration (if requested)
   - Privacy policy and terms URLs (must be on verified domain)
4. Domain verification automatic (you own mmautomates.com)

**Files to modify:**
- `app.py` (update `authenticate_google()` to support environment variables)

---

## Phase 5: Host Privacy Policy & Terms on Squarespace - 1 hour

### 5.1 Create Pages on Squarespace
1. Log into Squarespace dashboard
2. Create new pages:
   - Privacy Policy (`/privacy-policy`)
   - Terms of Use (`/terms-of-use`)
3. Ensure pages are published and publicly accessible

### 5.2 Copy Content to Squarespace
1. Copy content from `PRIVACY_POLICY.md` to Squarespace Privacy Policy page
2. Copy content from `TERMS_OF_USE.md` to Squarespace Terms of Use page
3. Format appropriately in Squarespace editor
4. Update any relative links to correct URLs

### 5.3 Verify URLs
- Test: `https://mmautomates.com/privacy-policy`
- Test: `https://mmautomates.com/terms-of-use`
- Ensure publicly accessible (not password protected)
- Verify URLs match Google OAuth consent screen exactly

**Files to modify:**
- No code changes (content goes into Squarespace)
- `app.py` links already updated in Phase 3

---

## Phase 6: Accessibility Improvements - 2-3 hours

### 6.1 Add Tab Indexing
- Add `tabindex` attributes to interactive elements
- Ensure logical tab order throughout app
- Make all buttons and interactive elements keyboard accessible

### 6.2 Improve Focus States
- Add visible focus indicators in CSS (lines 93-269 in `app.py`)
- Use `:focus-visible` for better keyboard navigation
- Ensure 3:1 contrast ratio for focus indicators (WCAG AA)

### 6.3 Screen Reader Support
- Add ARIA labels to all buttons and interactive elements
- Add `aria-describedby` for help text
- Ensure all images have alt text
- Add `role` attributes where appropriate
- Add `aria-live` regions for dynamic content updates

### 6.4 Keyboard Navigation
- Ensure all functionality works with keyboard only
- Add keyboard shortcuts documentation
- Test with screen readers (NVDA/JAWS/VoiceOver)

**Files to modify:**
- `app.py` (CSS section lines 93-269, add ARIA attributes throughout)

---

## Phase 7: Testing & Verification - 1-2 hours

### 7.1 Domain & OAuth Testing
- Verify app loads at `https://sop.mmautomates.com`
- Test Google OAuth flow end-to-end
- Verify redirect URIs work correctly
- Test Google Drive upload functionality

### 7.2 Accessibility Testing
- Run accessibility audit (using A11y MCP server)
- Test with keyboard navigation only
- Test with screen reader (NVDA/JAWS)
- Verify WCAG 2.1 AA compliance

### 7.3 Functional Testing
- Test video upload and processing
- Test all interactive elements
- Verify all links work correctly

---

## MCP Server Recommendations

### 1. A11y MCP Server ✅
- **Purpose**: Automated accessibility audits
- **Use cases**: 
  - Test Streamlit app for WCAG compliance
  - Check color contrast ratios
  - Validate ARIA attributes
  - Generate accessibility reports

### 2. Browser Extension MCP ✅
- **Purpose**: Automated browser testing
- **Use cases**:
  - Test OAuth flow end-to-end
  - Verify domain redirects work
  - Test accessibility with real browser
  - Take screenshots for documentation

### 3. Sequential Thinking MCP ✅
- **Purpose**: Complex problem-solving
- **Use cases**: Already using for complex workflows

---

## Timeline Estimate

- **Phase 1 (Self-Hosting on Cloud Run)**: 60-90 minutes
- **Phase 2 (Custom Domain)**: 30-60 minutes
- **Phase 3 (URL Updates)**: 30 minutes
- **Phase 4 (OAuth Migration)**: 2-3 hours
- **Phase 5 (Privacy/Terms)**: 1 hour
- **Phase 6 (Accessibility)**: 2-3 hours
- **Phase 7 (Testing)**: 1-2 hours

**Total: 7.5-11 hours** (doable today/tomorrow)

## Critical Path for Today

1. **Must do today**: Phases 1-2 (Self-hosting + Custom domain) - Get app live on your domain
2. **Should do today**: Phase 3 (URL updates) - Update app to use new domain
3. **Can do today**: Phase 5 (Privacy/Terms) - Required for OAuth verification
4. **Can do in parallel**: Phase 4 (OAuth migration) - Can start while testing deployment

## Notes for Beginners

- Use Cloud Shell in browser (no local installation needed)
- Cloud Run auto-scales and only charges for actual usage
- DNS propagation can take up to 60 minutes
- Test app at Cloud Run URL before adding custom domain
- All changes are reversible - you can redeploy previous versions

## Success Criteria

✅ App accessible at `https://sop.mmautomates.com`  
✅ OAuth works with mmautomates.com Google Cloud Console  
✅ Privacy policy and terms accessible at `https://mmautomates.com/privacy-policy` and `/terms-of-use`  
✅ All interactive elements keyboard accessible  
✅ WCAG 2.1 AA compliant  
✅ Screen reader friendly

