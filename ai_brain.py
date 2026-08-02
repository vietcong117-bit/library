# ai_brain.py
import pickle
import os
import random
from underthesea import word_tokenize
from dataset import RESPONSES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "chatbot_model.pkl")
VEC_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")


CONFIDENCE_THRESHOLD = 0.3

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
with open(VEC_PATH, "rb") as f:
    vectorizer = pickle.load(f)


def get_chatbot_response(user_message):
    segmented_text = word_tokenize(user_message, format="text")
    user_tfidf = vectorizer.transform([segmented_text])


    if user_tfidf.nnz == 0:
        return "unknown", random.choice(RESPONSES["unknown"])

    probabilities = model.predict_proba(user_tfidf)[0]
    max_prob = probabilities.max()
    predicted_intent = model.classes_[probabilities.argmax()]

    if max_prob < CONFIDENCE_THRESHOLD:
        predicted_intent = "unknown"


    response_options = RESPONSES.get(predicted_intent, RESPONSES["unknown"])
    response = random.choice(response_options)

    return predicted_intent, response



STOPWORDS_SEARCH = {
    "tìm", "kiếm", "sách", "cuốn", "truyện", "quyển", "giúp", "mình",
    "muốn", "hỏi", "cho", "về", "có", "là", "tên", "đọc", "mượn",
    "vậy", "không", "bạn", "ơi", "nhé", "giùm", "dùm", "ạ","?","!",".",","
}

MIN_QUERY_LENGTH = 2  


def extract_search_query(user_message: str) -> str:
    
    if not user_message:
        return ""

    segmented = word_tokenize(user_message.lower(), format="text")
    tokens = segmented.split()

    filtered_tokens = []
    for token in tokens:
        parts = token.split("_")
        kept_parts = [p for p in parts if p not in STOPWORDS_SEARCH]
        if kept_parts:
            filtered_tokens.append("_".join(kept_parts))

    query = " ".join(filtered_tokens).replace("_", " ").strip()
    return query


def is_query_too_short(query: str) -> bool:
    """True nếu từ khóa tìm kiếm quá ngắn (< MIN_QUERY_LENGTH ký tự) để tránh tìm rác."""
    return len(query) < MIN_QUERY_LENGTH


def find_book_by_query(query: str, book_queryset):
   
    query_lower = query.lower()
    for book in book_queryset.only("id", "title", "author", "available"):
        if query_lower in book.title.lower():
            return book
    return None



STOPWORDS_AUTHOR = {
    "tìm", "sách", "cuốn", "truyện", "quyển", "tác", "phẩm", "tác_phẩm",
    "giả", "tác_giả", "của", "do", "viết", "bởi", "cho", "mình", "muốn",
    "xem", "hỏi", "có", "không", "là", "gì", "này", "những", "các",
    "liệt", "kê", "liệt_kê", "giúp", "nào", "nhé", "ạ","của","bạn","?","!",".",","
}


def extract_author_query(user_message: str) -> str:
    
    if not user_message:
        return ""

    segmented = word_tokenize(user_message.lower(), format="text")
    tokens = segmented.split()

    filtered_tokens = []
    for token in tokens:
        parts = token.split("_")
        kept_parts = [p for p in parts if p not in STOPWORDS_AUTHOR]
        if kept_parts:
            filtered_tokens.append("_".join(kept_parts))

    query = " ".join(filtered_tokens).replace("_", " ").strip()
    return query


def find_books_by_author(query: str, book_queryset):
  
    query_lower = query.lower()
    return [
        book for book in book_queryset.only("id", "title", "author", "available")
        if query_lower in book.author.lower()
    ]




STOPWORDS_CATEGORY = {
    "tìm", "sách", "cuốn", "truyện", "quyển", "thể", "loại", "thể_loại",
    "thuộc", "cho", "mình", "muốn", "xem", "hỏi", "có", "không", "là",
    "gì", "này", "những", "các", "liệt", "kê", "liệt_kê", "giúp", "nào",
    "nhé", "ạ","thuộc","?","!",".",","
}


def extract_category_query(user_message: str) -> str:
    
    if not user_message:
        return ""

    segmented = word_tokenize(user_message.lower(), format="text")
    tokens = segmented.split()

    filtered_tokens = []
    for token in tokens:
        parts = token.split("_")
        kept_parts = [p for p in parts if p not in STOPWORDS_CATEGORY]
        if kept_parts:
            filtered_tokens.append("_".join(kept_parts))

    query = " ".join(filtered_tokens).replace("_", " ").strip()
    return query


def find_books_by_category(query: str, book_queryset):
    
    resolved_code = resolve_category_code(query)
    match_target = resolved_code if resolved_code else query.lower()

    
    try:
        book_queryset = book_queryset.select_related("category")
    except Exception:
        pass  

    result = []
    for book in book_queryset:
        if not book.category:
            continue
        category_str = str(book.category)  
        if match_target in category_str.lower():
            result.append(book)
    return result



CATEGORY_ALIASES = {
    "tech": ["công nghệ", "khoa học", "kỹ thuật", "cntt", "tin học", "lập trình", "công nghiệp"],
    "fiction": ["văn học", "tiểu thuyết", "truyện", "trinh thám", "ngôn tình", "văn chương"],
    "business": ["kinh doanh", "kinh tế", "kỹ năng sống", "quản trị", "tài chính"],
}


def resolve_category_code(query: str):
   
    query_lower = query.lower()

    if query_lower in CATEGORY_ALIASES:
        return query_lower

    
    for code, aliases in CATEGORY_ALIASES.items():
        for alias in aliases:
            if alias in query_lower or query_lower in alias:
                return code

    return None
