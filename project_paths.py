from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
DATASET_ROOT = PROJECT_ROOT / "dataset"
TRAIN_DATA_DIR = DATASET_ROOT / "train"
MODELS_DIR = PROJECT_ROOT / "models"
MEDIA_ROOT = PROJECT_ROOT / "media"
BOOK_CSV_PATH = PROJECT_ROOT / "book32-listing.csv"
CHATBOT_MODEL_PATH = PROJECT_ROOT / "chatbot_model.pkl"
VECTORIZER_PATH = PROJECT_ROOT / "vectorizer.pkl"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
TRAINING_SCRIPTS_DIR = SCRIPTS_DIR / "training"
DATA_SCRIPTS_DIR = SCRIPTS_DIR / "data"
