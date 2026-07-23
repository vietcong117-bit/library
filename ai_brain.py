# ai_brain.py
import pickle
import os
from underthesea import word_tokenize
from dataset import RESPONSES

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "chatbot_model.pkl")
VEC_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

# Dưới ngưỡng này thì coi như model không đủ chắc chắn -> ép về "unknown".
# Lưu ý: với dataset nhỏ + CalibratedClassifierCV, xác suất thật của các câu
# ĐÚNG nghĩa thường chỉ rơi vào khoảng 0.4 - 0.6 (không cao ngất như model
# không calibrate), nên threshold để 0.35 là hợp lý hơn 0.4-0.45.
CONFIDENCE_THRESHOLD = 0.35

with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
with open(VEC_PATH, "rb") as f:
    vectorizer = pickle.load(f)


def get_chatbot_response(user_message):
    segmented_text = word_tokenize(user_message, format="text")
    user_tfidf = vectorizer.transform([segmented_text])

    # BƯỚC QUAN TRỌNG: nếu câu người dùng gõ không chứa BẤT KỲ từ nào nằm
    # trong từ vựng đã học (vector toàn số 0 - out-of-vocabulary), thì model
    # không thực sự "hiểu" gì cả, nó chỉ đang thiên vị theo nhãn có nhiều mẫu
    # train hơn. Trường hợp này phải ép "unknown" ngay, KHÔNG được tin vào
    # predict_proba() vì con số đó lúc này không phản ánh nội dung câu.
    if user_tfidf.nnz == 0:
        return "unknown", RESPONSES["unknown"]

    probabilities = model.predict_proba(user_tfidf)[0]
    max_prob = probabilities.max()
    predicted_intent = model.classes_[probabilities.argmax()]

    # Fallback: câu hỏi mơ hồ, model không đủ tự tin -> "unknown"
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

    underthesea đôi khi GỘP một stopword chung với từ kế bên thành một
    token duy nhất (vd: "truyện chí phèo" -> "truyện_chí" + "phèo", thay vì
    "truyện" + "chí_phèo"). Nếu chỉ lọc stopword ở cấp CẢ TOKEN, những
    trường hợp gộp lẫn này sẽ lọt lưới. Nên ở đây, mỗi token được tách nhỏ
    theo dấu "_", lọc stopword ở cấp TỪNG PHẦN, rồi mới ráp lại phần còn sót.

    Trả về chuỗi rỗng nếu không còn từ khóa nào có nghĩa.
    """
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
    """
    Tìm sách có tên CHỨA `query`, không phân biệt hoa/thường — xử lý ở
    tầng Python bằng str.lower() thay vì dựa vào Book.objects.filter(
    title__icontains=...).

    LÝ DO: SQLite (LIKE/icontains) chỉ case-fold đúng cho ký tự ASCII
    (a-z, A-Z). Với ký tự có dấu tiếng Việt như "Đ"/"đ", "Ư"/"ư"...,
    SQLite coi hoa và thường là 2 ký tự KHÁC NHAU, nên "đắc nhân tâm"
    sẽ không khớp được với "Đắc Nhân Tâm" dù về logic là cùng một chữ.
    str.lower() của Python xử lý Unicode đúng chuẩn nên không bị lỗi này.

    `book_queryset` là một QuerySet Book bất kỳ (vd: Book.objects.all()).
    Trả về đối tượng Book đầu tiên khớp, hoặc None nếu không tìm thấy.
    """
    query_lower = query.lower()
    for book in book_queryset.only("id", "title", "author", "available"):
        if query_lower in book.title.lower():
            return book
    return None


# ---------------------------------------------------------------------------
# Tìm sách theo TÊN TÁC GIẢ
# ---------------------------------------------------------------------------

# Các từ mang tính hư từ trong câu hỏi theo tác giả, KHÔNG phải tên tác giả.
STOPWORDS_AUTHOR = {
    "tìm", "sách", "cuốn", "truyện", "quyển", "tác", "phẩm", "tác_phẩm",
    "giả", "tác_giả", "của", "do", "viết", "bởi", "cho", "mình", "muốn",
    "xem", "hỏi", "có", "không", "là", "gì", "này", "những", "các",
    "liệt", "kê", "liệt_kê", "giúp", "nào", "nhé", "ạ"
}


def extract_author_query(user_message: str) -> str:
    """
    Tách tên tác giả ra khỏi câu người dùng gõ, dùng chung kỹ thuật với
    extract_search_query(): tokenize rồi lọc stopword ở cấp TỪNG PHẦN
    của token (tách theo dấu "_") để không bị lọt lưới khi underthesea
    gộp một stopword dính liền với tên riêng thành một token.
    """
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
    """
    Tìm TẤT CẢ sách có tên tác giả CHỨA `query`, không phân biệt hoa/thường
    (cùng lý do Unicode như find_book_by_query ở trên). Một tác giả có thể
    có nhiều tác phẩm, nên hàm này trả về LIST thay vì 1 object duy nhất.
    """
    query_lower = query.lower()
    return [
        book for book in book_queryset.only("id", "title", "author", "available")
        if query_lower in book.author.lower()
    ]
