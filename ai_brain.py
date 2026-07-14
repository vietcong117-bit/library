# ai_brain.py
import pickle
import os
from underthesea import word_tokenize
from dataset import RESPONSES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "chatbot_model.pkl")
VEC_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

# Dưới ngưỡng này (40%) thì coi như model không chắc chắn -> ép về "unknown"
CONFIDENCE_THRESHOLD = 0.4

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
with open(VEC_PATH, "rb") as f:
    vectorizer = pickle.load(f)


def get_chatbot_response(user_message):
    segmented_text = word_tokenize(user_message, format="text")
    user_tfidf = vectorizer.transform([segmented_text])

    # Lấy xác suất cho TỪNG intent thay vì chỉ nhãn dự đoán cứng
    probabilities = model.predict_proba(user_tfidf)[0]
    max_prob = probabilities.max()
    predicted_intent = model.classes_[probabilities.argmax()]

    # Fallback: câu hỏi vô nghĩa/linh tinh -> model không tự tin -> "unknown"
    if max_prob < CONFIDENCE_THRESHOLD:
        predicted_intent = "unknown"

    response = RESPONSES.get(predicted_intent, RESPONSES["unknown"])

    return predicted_intent, response


# ---------------------------------------------------------------------------
# Bóc tách từ khóa tìm sách "thông minh" (dùng chung cho mọi view trong views.py)
# ---------------------------------------------------------------------------

# Các từ mang tính "hành động/hư từ" trong câu tìm sách, KHÔNG phải tên sách.
# So với .replace() cũ, ở đây stopword được loại bỏ theo TỪNG TỪ (word-level),
# nên sẽ không bao giờ "cắn" nhầm vào một ký tự nằm bên trong tên sách
# (vd: chữ "a" trong "Clean Code" sẽ không bị đụng tới).
STOPWORDS_SEARCH = {
    "tìm", "kiếm", "sách", "cuốn", "truyện", "quyển", "giúp", "mình",
    "muốn", "hỏi", "cho", "về", "có", "là", "tên", "đọc", "mượn",
    "vậy", "không", "bạn", "ơi", "nhé", "giùm", "dùm", "ạ"
}

MIN_QUERY_LENGTH = 2  # từ khóa dưới 2 ký tự thì coi là quá ngắn, không tìm


def extract_search_query(user_message: str) -> str:
    """
    Tách tên sách / từ khóa tìm kiếm ra khỏi câu người dùng gõ.

    Cách làm: tokenize câu bằng underthesea (để "clean_code" không bị tách
    rời thành "clean" và "code"), sau đó loại bỏ từng TOKEN nằm trong
    STOPWORDS_SEARCH — khác hẳn cách cũ dùng .replace() theo chuỗi con,
    vốn có thể vô tình xóa nhầm ký tự nằm giữa tên sách.

    Trả về chuỗi rỗng nếu không còn từ khóa nào có nghĩa.
    """
    if not user_message:
        return ""

    segmented = word_tokenize(user_message.lower(), format="text")
    tokens = segmented.split()
    filtered = [t for t in tokens if t not in STOPWORDS_SEARCH]
    query = " ".join(filtered).replace("_", " ").strip()
    return query


def is_query_too_short(query: str) -> bool:
    """True nếu từ khóa tìm kiếm quá ngắn (< MIN_QUERY_LENGTH ký tự) để tránh tìm rác."""
    return len(query) < MIN_QUERY_LENGTH
