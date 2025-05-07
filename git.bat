@echo off
setlocal EnableDelayedExpansion

REM GitHub Upload Script for Discord Bot
title LVBot GitHub Upload Tool

echo ===================================
echo    LVBot GitHub Upload Tool
echo ===================================
echo.

REM Check if git is installed
where git >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Git is not installed or not in your PATH.
    echo Please install Git from https://git-scm.com/downloads
    goto :end
)

REM Create .gitignore file to exclude sensitive files
echo Step 1: Creating .gitignore file...
(
echo # Sensitive files
echo .env
echo config.json
echo user_balances.json
echo feedback_config.json
echo welcome_config.json
echo reaction_roles.json
echo 
echo # Python cache files
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo env/
echo venv/
echo ENV/
) > .gitignore
echo Done.
echo.

REM Create README file
echo Step 2: Creating README.md file...
(
echo # LVBot
echo.
echo A feature-rich Discord bot for the Unreal Engine Asset Marketplace community.
echo.
echo ## Features
echo.
echo - Currency system for asset purchases
echo - Ticket management system
echo - Shop with visual embeds and interactive buttons
echo - Role reaction system
echo - Feedback collection system
echo - Welcome messages
) > README.md
echo Done.
echo.

REM Initialize Git repository
echo Step 3: Initializing Git repository...
git init
echo Done.
echo.

REM Add all files
echo Step 4: Adding files to repository...
git add .
echo Done.
echo.

REM Initial commit
echo Step 5: Creating initial commit...
git commit -m "Initial commit - Discord bot upload"
echo Done.
echo.

REM Set main branch
echo Step 6: Setting main branch...
git branch -M main
echo Done.
echo.

REM Add remote origin
echo Step 7: Adding remote repository...
git remote add origin https://github.com/Antivirus3052/lvbot.git
echo Done.
echo.

REM Push to GitHub
echo Step 8: Pushing to GitHub...
git push -u origin main

echo.
if %ERRORLEVEL% neq 0 (
    echo There was an error pushing to GitHub.
    echo Please check your internet connection and repository permissions.
) else (
    echo Success! The bot has been uploaded to GitHub.
    echo Repository: https://github.com/Antivirus3052/lvbot
)

:end
echo.
echo Press any key to exit...
pause > nul
exit /b