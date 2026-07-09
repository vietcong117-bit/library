# train.py
import pickle
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from dataset import INTENT_DATA

print("1. Đang tự động phân bóc dữ liệu và tách từ tiếng Việt...")
X_train = []
y_train = []

# Vòng lặp tự động duyệt qua từng nhóm ý định trong Dictionary
for intent, phrases in INTENT_DATA.items():
    for phrase in phrases:
        # Tách từ bằng underthesea ("xin chào" -> "xin_chào")
        segmented_text = word_tokenize(phrase, format="text")
        X_train.append(segmented_text)
        y_train.append(intent)

print(f"-> Tổng số câu huấn luyện đã nạp: {len(X_train)} câu.")

print("2. Đang số hóa văn bản (TF-IDF)...")
vectorizer = TfidfVectorizer()
X_train_tfidf = vectorizer.fit_transform(X_train)

print("3. Đang huấn luyện mô hình học máy SVM (LinearSVC)...")
model = LinearSVC()
model.fit(X_train_tfidf, y_train)

print("4. Đang lưu mô hình ra file .pkl...")
with open("chatbot_model.pkl", "wb") as f:
    pickle.dump(model, f)
with open("vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("✅ Đã huấn luyện bộ dữ liệu đa dạng thành công!")