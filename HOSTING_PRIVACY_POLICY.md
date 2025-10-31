# Hosting the Privacy Policy on GitHub

The Privacy Policy is stored as `PRIVACY_POLICY.md` in your repository. GitHub will automatically render markdown files beautifully when viewed.

## How It Works

1. **Upload to GitHub**: The `PRIVACY_POLICY.md` file is already in your repository
2. **GitHub Renders It**: GitHub automatically renders markdown files with proper formatting
3. **Share the Link**: The privacy policy is accessible at:
   ```
   https://github.com/YOUR_USERNAME/YOUR_REPO_NAME/blob/main/PRIVACY_POLICY.md
   ```

## Updating the Link in the App

1. Find the Privacy & Data Security section in `app.py` (around line 1529)
2. Replace `YOUR_USERNAME` and `YOUR_REPO_NAME` with your actual GitHub repository details
3. Example: If your repo is `github.com/johnsmith/mmautomates_process_documentation`, use:
   ```
   https://github.com/johnsmith/mmautomates_process_documentation/blob/main/PRIVACY_POLICY.md
   ```

## Alternative: GitHub Pages (Optional)

If you want a cleaner URL like `https://yourusername.github.io/repo/privacy-policy`, you can:

1. Enable GitHub Pages in your repository settings
2. Use the `PRIVACY_POLICY.html` file instead
3. Access at: `https://yourusername.github.io/repository-name/PRIVACY_POLICY.html`

But the markdown file on GitHub works perfectly fine and is simpler!

## Important Notes

- Update the "Last Updated" date when you make changes
- Update the contact information if needed
- Ensure the URL is accessible without authentication
- Consider adding the privacy policy URL to your app's footer or about section

