# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Flask web system for automating ENEL electricity bill management. The system downloads emails from Microsoft Graph API, processes PDF attachments, extracts billing data, and generates Excel spreadsheets. All data is stored in OneDrive ENEL for treasury department access. Designed for Render deployment with zero local disk usage.

## Architecture

The codebase follows a web-based modular structure:

- **Entry Point**: `app.py` - Flask web application with all routes
- **Authentication**: `auth/microsoft_auth.py` - OAuth2 token management for Microsoft Graph
- **Core Processors**: `processor/` directory containing:
  - `sistema_enel.py` - Main orchestration system
  - `email_processor.py` - Downloads emails and attachments from ENEL folder  
  - `pdf_processor.py` - Removes PDF protection, extracts data
  - `planilha_manager.py` - Excel generation and management
  - `onedrive_manager.py` - OneDrive structure management
  - `database_enel.py` - SQLite database for processing control
- **ENEL Data**: `enel/` directory containing:
  - `relacionamento_enel.xlsx` - Casa de Oração → Instalação mapping
  - `config/` - OneDrive structure configurations

## Key Commands

### Environment Setup
```bash
# Install dependencies for Render
pip install -r requirements.txt

# Run Flask web application
python app.py

# Or via Gunicorn (Render production)
gunicorn app:app
```

### Testing Commands
```bash
# Verify core dependencies
python -c "import requests, flask; print('✅ Core dependencies OK')"

# Verify PDF processing dependencies
python -c "import PyPDF2, pdfplumber, openpyxl; print('✅ PDF dependencies OK')"

# Test module imports
python -c "from processor.sistema_enel import SistemaEnel; print('✅ Modules OK')"

# Test authentication
python -c "from auth.microsoft_auth import MicrosoftAuth; print('✅ Auth OK')"
```

## Dependencies

### Critical Dependencies
- `requests` - Microsoft Graph API communication
- `tkinter` - GUI (usually built-in with Python)

### Optional Dependencies for Full Functionality
- `PyPDF2` - PDF protection removal  
- `pdfplumber` - PDF data extraction
- `pandas` - Data manipulation and Excel generation
- `openpyxl` - Excel formatting
- `numpy` - Numerical computations

## Important Files

- `token.json` - OAuth2 authentication token (optional, can upload via web)
- `enel/relacionamento_enel.xlsx` - Casa de Oração → Instalação mapping
- `enel/config/onedrive_config.json` - OneDrive structure configuration

## Environment Variables (Render)

- `MICROSOFT_CLIENT_ID` - Microsoft Graph API client ID
- `PASTA_ENEL_ID` - Specific email folder ID in OneDrive
- `ONEDRIVE_ENEL_ID` - Root ENEL folder ID in OneDrive
- `SECRET_KEY` - Flask session secret

## Code Patterns

The system uses web-based imports with proper error handling:
- Flask routes handle web requests
- Processors work with OneDrive API exclusively
- No local file system dependencies
- All data stored in OneDrive for treasury access

## Typical Workflow

1. User accesses web interface at deployed URL
2. System authenticates via Microsoft OAuth or token upload
3. Web dashboard provides processing options
4. System processes: emails → PDF extraction → Excel generation → OneDrive storage
5. Treasury team accesses results directly from OneDrive

## Critical Design Principles

- **ZERO local disk usage** - All data in OneDrive ENEL
- **Treasury accessibility** - All files accessible by treasury team
- **Web-based interface** - No desktop dependencies
- **Render optimized** - Stateless, cloud-ready deployment