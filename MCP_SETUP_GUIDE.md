# MCP Server Setup Guide for Cursor IDE

## Quick Answers to Your Questions

**Q: Where do I look for MCP status in the UI?**  
A: Press `Ctrl + Shift + P`, type "MCP", select "View: Open MCP Settings". You'll see all configured servers and their status.

**Q: Do I need to configure this in every repository?**  
A: **No!** ✅ Configuration has been placed in `C:\Users\mered\.cursor\mcp.json` which makes it universal across ALL your projects. You're all set!

**Q: How do I use the Sequential Thinking MCP?**  
A: Just talk naturally! Ask complex questions like "Break down this problem step by step" and the AI will automatically use Sequential Thinking. No special commands needed.

---

## What are MCP Servers?

MCP (Model Context Protocol) Servers extend your AI's capabilities by providing additional tools and functions. The Sequential Thinking MCP Server helps with structured problem-solving and analytical thinking.

## Prerequisites ✓

- ✅ **Node.js**: v22.20.0 installed
- ✅ **npm**: v11.6.2 installed

## Completed Setup Steps ✓

Your workspace has been configured with the Sequential Thinking MCP Server!

### ✅ Step 1: Configuration File Created
- **Workspace Location**: `.vscode/mcp.json` (project-specific)
- **Global Location**: `C:\Users\mered\.cursor\mcp.json` (universal across all projects) ✓
- **Contents**: Configured to use Sequential Thinking server via npx

### ✅ Step 2: Server Verified
- The Sequential Thinking MCP Server has been tested and is working correctly

## Final Steps (Do This Now)

### Step 3: Restart Cursor IDE

**⚠️ IMPORTANT**: You need to restart Cursor IDE for the MCP server to be loaded.

1. Close Cursor IDE completely
2. Reopen Cursor IDE
3. The MCP server should automatically connect

### Step 4: Verify MCP Server is Running

After restarting Cursor:

**How to Check MCP Status:**
1. Open Command Palette: `Ctrl + Shift + P` (Windows)
2. Type: `MCP`
3. Select: **"View: Open MCP Settings"**
4. You should see "sequential-thinking" listed with a green/connected status

**Alternative method:**
- Click the gear icon ⚙️ (Settings) in lower-left corner
- Go to **Features** tab
- Scroll to **MCP Servers** section
- Check status of "sequential-thinking"

If you see red status or errors, check the troubleshooting section below.

## What the Sequential Thinking Server Does

The Sequential Thinking MCP Server provides structured thinking capabilities:
- Break down complex problems into sequential steps
- Create detailed plans with room for revision
- Maintain context over multiple reasoning steps
- Facilitate systematic problem-solving and analysis

## Configuration File Reference

Your MCP configuration is located at: `.vscode/mcp.json`

```json
{
  "mcpServers": {
    "sequential-thinking": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-sequential-thinking"
      ]
    }
  }
}
```

## How to Use the Sequential Thinking Server

Once configured and connected, you can use it in conversations:

**Method 1: Natural Conversation**
The AI will automatically use Sequential Thinking when appropriate:
- "Break down this complex problem step by step"
- "Let's analyze this systematically"
- "Help me think through this solution"

**Method 2: Explicit Invocation**
You can explicitly request structured thinking:
- "Use Sequential Thinking to analyze this code"
- "Apply Sequential Thinking to plan this feature"
- "Walk me through this problem using Sequential Thinking"

The server works behind the scenes - you don't need to call specific functions. Just have natural conversations about complex problems, and it will help structure the thinking process.

## Adding More MCP Servers

You can add more MCP servers by editing your global config file: `C:\Users\mered\.cursor\mcp.json`

Add additional entries to the `mcpServers` object:

```json
{
  "mcpServers": {
    "sequential-thinking": { ... },
    "your-new-server": {
      "command": "npx",
      "args": ["-y", "@package/server-name"]
    }
  }
}
```

Popular MCP servers include:
- **Filesystem**: File operations and search
- **Database**: SQL and database connections
- **Web scraping**: Extract data from websites
- **Code analysis**: Enhanced code understanding
- **Git**: Repository operations

Find more at: https://mcpdb.org/

## Troubleshooting

### Server Not Appearing After Restart

**Important:** Configuration files can be in TWO locations:

1. **Global (recommended)**: `C:\Users\mered\.cursor\mcp.json` - applies to ALL projects
2. **Project-specific**: `.vscode/mcp.json` or `.cursor/mcp.json` - only for current project

**If server disappeared after restart:**

1. **Check which file you edited**: Did you edit the global file or project file?
   - Global: `%USERPROFILE%\.cursor\mcp.json` 
   - Project: `.vscode/mcp.json` or `.cursor/mcp.json` in your workspace

2. **Verify Node.js is working**:
   ```powershell
   node --version
   ```

3. **Test server manually**:
   ```powershell
   npx a11y-mcp
   ```
   If you see "A11y Accessibility MCP server running on stdio", the package works!

4. **Check MCP Settings again**: Press `Ctrl + Shift + P`, type "MCP", select "View: Open MCP Settings"
   - Look for any red status indicators
   - Check error messages in the output panel

5. **Verify JSON syntax**: Use a JSON validator to ensure no syntax errors

### Configuration File Locations

- **Global location** (universal): `C:\Users\mered\.cursor\mcp.json` ✅
- **Project location** (optional): `.vscode/mcp.json` or `.cursor/mcp.json`

**Recommendation:** Use the global location for MCP servers you want everywhere.

## Resources

- [Sequential Thinking MCP Server Documentation](https://cursor.directory/mcp/sequential-thinking-1)
- [Model Context Protocol GitHub](https://github.com/modelcontextprotocol)
- [MCP Server Directory](https://mcpdb.org/)

---

**✅ Setup Complete!** Your Sequential Thinking MCP Server is configured and ready to use after restarting Cursor IDE.

