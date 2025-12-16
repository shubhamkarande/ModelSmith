# ModelSmith

**Tame your data. Track your models. Stay sane.**

ModelSmith is a desktop AI dataset and experiment management tool built with Python and PyQt6. It provides a lightweight alternative to MLflow for ML practitioners who want to manage datasets, labels, experiments, and model metadata locally.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![PyQt6](https://img.shields.io/badge/PyQt6-6.6+-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## Features

- **📁 Dataset Manager** - Import CSV, JSON, and image datasets with schema preview, statistics, and class distribution charts
- **🏷️ Label Editor** - Add labels/tags to tabular data and image datasets, export annotations as JSON/CSV
- **🧪 Experiment Tracking** - Log experiments with hyperparameters, metrics, and notes; compare across runs
- **📊 Visual Analytics** - Distribution charts, confusion matrices, accuracy trends, and experiment comparisons
- **📦 Model Registry** - Register trained models with metadata, link to experiments, verify file locations
- **📴 Fully Offline** - No server, no cloud, no telemetry. Your data stays local.
- **🔄 Dataset Versioning** - Refresh and re-analyze datasets with automatic version tracking
- **📄 HTML Report Export** - Generate professional dark-themed experiment reports

## Tech Stack

- **Python 3.11+** - Core language
- **PyQt6** - Desktop UI framework
- **SQLite** - Local database for metadata
- **Pandas/NumPy** - Data processing
- **Matplotlib** - Visualization
- **scikit-learn** - ML metrics

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/modelsmith.git
cd modelsmith

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run the Application

```bash
python main.py
```

### Build Executable

```bash
# Install PyInstaller
pip install pyinstaller

# Build single-file executable
pyinstaller modelsmith.spec

# Or use simple command
pyinstaller --onefile --windowed --name ModelSmith main.py
```

The executable will be in the `dist/` folder.

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+I` | Import Dataset |
| `Ctrl+1` | Go to Datasets |
| `Ctrl+2` | Go to Labeling |
| `Ctrl+3` | Go to Experiments |
| `Ctrl+4` | Go to Models |
| `Ctrl+5` | Go to Analytics |
| `Ctrl+Q` | Exit |

## Project Structure

```text
modelsmith/
├── main.py                 # Application entry point
├── config.yaml             # Configuration file
├── requirements.txt        # Python dependencies
├── database/
│   ├── db_manager.py       # SQLite database manager
│   └── models.py           # Data models
├── services/
│   ├── dataset_service.py  # Dataset operations
│   ├── experiment_service.py
│   ├── model_service.py
│   ├── labeling_service.py
│   └── visualization_service.py
├── ui/
│   ├── main_window.py      # Main application window
│   ├── dataset_view.py
│   ├── experiment_view.py
│   ├── model_registry_view.py
│   ├── labeling_view.py
│   ├── visualization_view.py
│   ├── components/
│   │   └── widgets.py      # Reusable UI components
│   └── styles/
│       └── dark_theme.qss  # Dark theme stylesheet
└── assets/
```

## Data Storage

- **Database**: `~/ModelSmith/modelsmith.db` (SQLite)
- **Config**: `config.yaml` in application directory

## Privacy

ModelSmith is designed with privacy in mind:

- ✅ All data remains local
- ✅ No external API calls
- ✅ No telemetry or analytics
- ✅ No cloud sync
- ✅ Explicit file access only

## License

MIT License - See [LICENSE](LICENSE) for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---

Built with ❤️ for ML practitioners who value simplicity and data privacy.
