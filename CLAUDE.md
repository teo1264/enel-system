# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modular Python system for automating ENEL electricity bill management. The system downloads emails from Microsoft Graph API, processes PDF attachments, extracts billing data, and generates Excel spreadsheets organized by location groups (PIA vs others). It's designed for treasury departments that use the SIGA system for bill management.

## Architecture

The codebase follows a modular structure to avoid circular imports and maintain clear separation of concerns:

- **Entry Point**: `main.py` - Single execution point with dependency checking
- **Configuration**: `config/settings.py` - Centralized constants including API credentials and PDF password
- **Authentication**: `src/auth/token_manager.py` - OAuth2 token management for Microsoft Graph
- **Email Processing**: `src/download/email_handler.py` - Downloads emails and attachments from specific ENEL folder
- **PDF Processing**: `src/pdf/processor.py` - Removes PDF protection, extracts data, generates Excel files, renames PDFs
- **User Interface**: `src/ui/menu.py` - Tkinter GUI with custom dialog functions

## Key Commands

### Environment Setup
```bash
# Create dedicated conda environment (recommended)
conda create -n enel python=3.9
conda activate enel

# Install dependencies
pip install -r requirements.txt

# Run the system
python main.py
```

### Testing Commands
```bash
# Verify critical dependencies
python -c "import requests, tkinter; print('✅ Critical dependencies OK')"

# Verify optional dependencies
python -c "import pdfplumber, pandas, openpyxl, PyPDF2; print('✅ Optional dependencies OK')"

# Test module structure
python -c "from src.ui.menu import mostrar_menu_principal; print('✅ Modules OK')"
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

- `token.json` - OAuth2 authentication token (required, not in git)
- `config/settings.py:14` - CLIENT_ID for Microsoft Graph API
- `config/settings.py:18` - PASTA_ENEL_ID for specific email folder
- `config/settings.py:21` - SENHA_PADRAO_PDF for PDF decryption ("05150")

## Code Patterns

The system uses local imports to prevent circular dependencies:
- UI functions are imported only when needed
- Each module imports dependencies at function level when required
- The `tk_messagebox()` function in `src/ui/menu.py:25` provides custom dialog handling

## Typical Workflow

1. User runs `python main.py`
2. System checks dependencies and token.json
3. Tkinter GUI opens with 5 options
4. Each option calls specific module functions via local imports
5. System provides automatic flow: download → ask to remove protection → ask to extract data → ask to rename files

## Render Deployment Considerations

This desktop application needs significant modifications for web deployment:
- Replace Tkinter GUI with web interface
- Handle file uploads/downloads differently
- Modify OAuth flow for web authentication
- Consider background job processing for PDF operations