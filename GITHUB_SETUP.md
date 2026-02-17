# GitHub Setup Guide for Beginners

This guide will help you upload this project to GitHub.

## Prerequisites

1. Create a GitHub account at https://github.com if you don't have one
2. Install Git on your computer:
   - **Windows**: Download from https://git-scm.com/download/win
   - **Mac**: Install via Homebrew `brew install git` or download from https://git-scm.com
   - **Linux**: `sudo apt install git` (Ubuntu/Debian)

## Step 1: Configure Git (First Time Only)

Open terminal and set your name and email:
```bash
git config --global user.name "Your Name"
git config --global user.email "kindersplit@gmail.com"
```

## Step 2: Create a Repository on GitHub

1. Go to https://github.com
2. Click the "+" in the top right corner
3. Click "New repository"
4. Name it: `berkshire-monitor` (or whatever you like)
5. Add description: "Monitor Berkshire Hathaway 13F filings for new holdings"
6. Choose "Public" (so others can see it) or "Private"
7. **DO NOT** check "Initialize with README" (we already have one)
8. Click "Create repository"

## Step 3: Upload Your Project to GitHub

In your terminal, navigate to your project folder:
```bash
cd berkshire-monitor
```

Initialize git in your project:
```bash
git init
```

Add all files to git:
```bash
git add .
```

Create your first commit:
```bash
git commit -m "Initial commit: Berkshire Holdings Monitor"
```

Connect to your GitHub repository (replace YOUR-USERNAME):
```bash
git remote add origin https://github.com/YOUR-USERNAME/berkshire-monitor.git
```

Push your code to GitHub:
```bash
git push -u origin main
```

If it asks for a password, you'll need to use a Personal Access Token instead of your password:
- Go to GitHub → Settings → Developer Settings → Personal Access Tokens → Tokens (classic)
- Generate new token with "repo" permissions
- Copy the token and use it as your password

## Step 4: Verify

Go to https://github.com/YOUR-USERNAME/berkshire-monitor and you should see your project!

## Common Git Commands

After making changes to your code:
```bash
# See what files changed
git status

# Add all changed files
git add .

# Commit with a message
git commit -m "Description of what you changed"

# Push to GitHub
git push
```

## Important Notes

- Your `config.py` file with your email will NOT be uploaded (it's in .gitignore)
- The `venv/` folder will NOT be uploaded (it's in .gitignore)
- Anyone who downloads your project will need to create their own `config.py` from `config.example.py`

## Troubleshooting

**"Permission denied"**: You need to set up SSH keys or use a Personal Access Token

**"Fatal: not a git repository"**: Make sure you're in the right folder and ran `git init`

**"Remote origin already exists"**: Run `git remote remove origin` then try the `git remote add` command again

## Need Help?

- GitHub's documentation: https://docs.github.com
- Git basics: https://git-scm.com/book/en/v2/Getting-Started-Git-Basics
