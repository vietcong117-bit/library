# train.py
import sys
from pathlib import Path
root_path = Path(file).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path)) 
import pickle
from underthesea import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC
from sklearn.calibration import CalibratedClassifierCV
from dataset import INTENT_DATA
from project_paths import PROJECT_ROOT

print("1. Đang tự động phân bóc dữ liệu và tách từ tiếng Việt...")
X_train = []
y_train = []

for intent, phrases in INTENT_DATA.items():
    for phrase in phrases:
        segmented_text = word_tokenize(phrase, format="text")
        X_train.append(segmented_text)
        y_train.append(intent)

print(f"-> Tổng số câu huấn luyện đã nạp: {len(X_train)} câu.")

print("2. Đang số hóa văn bản (TF-IDF)...")
# ngram_range=(1, 2): thêm cụm 2 từ (bigram) để model phân biệt được
# "tìm sách" và "tìm thủ tục" thay vì chỉ nhìn từ "tìm" đơn lẻ.
vectorizer = TfidfVectorizer(ngram_range=(1, 2))
X_train_tfidf = vectorizer.fit_transform(X_train)

print("3. Đang huấn luyện mô hình SVM có hỗ trợ xác suất...")
# QUAN TRỌNG: SVC(probability=True) đã bị deprecated từ sklearn 1.9 (sẽ gỡ ở 1.11).
# Cách khuyến nghị hiện tại: KHÔNG bật probability trên SVC gốc, mà bọc nó
# bằng CalibratedClassifierCV để lấy predict_proba() cho Confidence Threshold.
# class_weight='balanced' giúp mô hình không thiên vị nhóm có nhiều câu mẫu hơn.
base_svc = SVC(kernel='linear', class_weight='balanced', random_state=42)
model = CalibratedClassifierCV(base_svc, method='sigmoid', cv=3)
model.fit(X_train_tfidf, y_train)

print("4. Đang lưu mô hình ra file .pkl...")
with open(PROJECT_ROOT / "chatbot_model.pkl", "wb") as f:
    pickle.dump(model, f)
with open(PROJECT_ROOT / "vectorizer.pkl", "wb") as f:
    pickle.dump(vectorizer, f)

print("Đã huấn luyện xong! Model giờ hỗ trợ predict_proba() cho Confidence Threshold.")
