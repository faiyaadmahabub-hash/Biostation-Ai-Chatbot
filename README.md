# BioStation AI - Statistical Analysis Assistant for Bioscience Students

A privacy-first, local AI chatbot that helps bioscience students with statistical analysis in R.

## Features

- **Statistical Test Advisor**: Guides you through flowchart-based test selection
- **R Code Generation**: Creates ready-to-run R code for your analysis
- **Code Debugger**: Explains errors and suggests fixes
- **Interactive Guidebook**: Learn about statistical tests with examples
- **Complete Privacy**: All processing happens on your local machine

## System Requirements

- Windows 10/11 or macOS 10.15+
- 16GB RAM (minimum)
- 10GB free disk space
- Intel i5/i7 or equivalent

## Quick Start (Development)

### 1. Install Prerequisites

**Python 3.10+**
```bash
python --version
```

**R 4.0+** (optional)
```bash
R --version
```

**Ollama** (LLM runtime)
- Download from: https://ollama.ai
- Install and verify:
```bash
ollama --version
```

### 2. Download LLM Model

```bash
ollama pull phi3:mini
```

### 3. Install Python Dependencies

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 4. Install R Packages (if using system R)

```bash
Rscript install_r_packages.R
```

### 5. Run the Application

```bash
python run_biostation.py
```

Open your browser to: http://127.0.0.1:5000

## Project Structure

```
Biostation-Ai-Chatbot/
├── run_biostation.py          # Main entry point
├── config.py                  # Application configuration
├── requirements.txt           # Python dependencies
├── install_r_packages.R       # R package installer
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes/               # API endpoints
│   ├── advisor/              # Statistical test advisor
│   ├── code_gen/             # R code generation
│   ├── debugger/             # Error debugging
│   ├── guidebook/            # Educational content
│   ├── llm/                  # LLM integration
│   ├── static/               # CSS, JS, images
│   └── templates/            # HTML templates
├── data/
│   ├── temp_uploads/         # Temporary file storage
│   └── sample_datasets/      # Example datasets
└── logs/                      # Application logs
```

## Development Status

Currently in active development. See `task.md` for progress tracking.

## License

TBD

## Contact

TBD
