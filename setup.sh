#!/bin/bash

# GitHub Profile Setup Script for amarzeus
echo "🚀 Setting up your enhanced GitHub profile..."

# Create necessary directories
mkdir -p .github/workflows
mkdir -p assets

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git repository initialized"
fi

# Add all files
git add .

# Commit changes
git commit -m "🎨 Enhanced GitHub profile with animations and interactive elements

- Added dynamic typing animation header
- Enhanced tech stack visualization
- Improved stats dashboard
- Added GitHub Actions for auto-updates
- Integrated contribution snake animation
- Added professional badges and metrics"

echo "✅ Changes committed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Push to GitHub: git push origin main"
echo "2. Enable GitHub Actions in your repository settings"
echo "3. Add secrets if needed for external integrations"
echo "4. Update social links and project repositories"
echo ""
echo "🎉 Your GitHub profile is now enhanced!"