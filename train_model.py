import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

data = [
    ("chào bạn", "chao_hoi"), ("hi", "chao_hoi"), ("hello", "chao_hoi"), ("bot ơi", "chao_hoi"),
    ("tạm biệt", "tam_biet"), ("bye", "tam_biet"), ("hẹn gặp lại", "tam_biet"),
    ("cảm ơn", "cam_on"), ("thanks", "cam_on"), ("ok ngon", "cam_on"),
    ("tìm truyện ", "tim_sach"), ("sách ở đâu", "tim_sach"), ("mượn cuốn này", "tim_sach"), ("tìm sách", "tim_sach"),("có sách", "tim_sach"),
    ("mấy giờ đóng cửa", "hoi_gio_lam"), ("thư viện mở cửa", "hoi_gio_lam"), ("lịch làm việc", "hoi_gio_lam")
]

X = [text for text, label in data]
y = [label for text, label in data]

model_pipeline = Pipeline([
    ('tfidf', TfidfVectorizer()),
    ('clf', LogisticRegression())
])

model_pipeline.fit(X, y)
joblib.dump(model_pipeline, 'intent_model.pkl')
print("Train xong! Đã xuất file intent_model.pkl")