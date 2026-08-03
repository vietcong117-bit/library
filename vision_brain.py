import os
import cv2
import numpy as np
import tensorflow as tf
import easyocr
import re
from project_paths import MODELS_DIR

MODEL_PATH = str(MODELS_DIR / "book_cover_cnn.h5")

# Khởi tạo mô hình CNN nếu file tồn tại
model = None
if os.path.exists(MODEL_PATH):
    model = tf.keras.models.load_model(MODEL_PATH)

CATEGORIES = ["art", "tech", "fiction", "math", "literature", "history", "comic", "business", "food", "religion", "sport"] 
# Khởi tạo EasyOCR (Sử dụng GPU nếu có, không có sẽ fallback về CPU)
reader = easyocr.Reader(['vi', 'en'], gpu=tf.test.is_built_with_cuda())

def extract_text_from_image(image_path):
    """Trích xuất tất cả văn bản xuất hiện trên ảnh bìa"""
    if not os.path.exists(image_path):
        return ""
    try:
        results = reader.readtext(image_path, detail=0)
        raw_text = " ".join(results)
        # Làm sạch khoảng trắng thừa
        clean_text = re.sub(r'\s+', ' ', raw_text).strip()
        return clean_text
    except Exception as e:
        print(f"⚠️ Lỗi OCR: {e}")
        return ""

def process_image_for_chatbot(image_path):
    """
    [Đề xuất 1] Tạo câu truy vấn hoàn chỉnh từ OCR để gửi cho Chatbot
    Ví dụ: 'Tìm giúp mình cuốn sách Nhà Giả Kim'
    """
    extracted_text = extract_text_from_image(image_path)
    if not extracted_text:
        return None, "Không thể đọc được chữ trên bìa sách."
    
    # Tạo query tiêu chuẩn hóa để kích hoạt Intent tim_sach
    generated_query = f"Tìm sách {extracted_text}"
    return extracted_text, generated_query

def predict_book_category(image_path, threshold=0.6):
    """Dự đoán thể loại bằng CNN"""
    if model is None or not os.path.exists(image_path):
        return None

    try:
        with open(image_path, 'rb') as f:
            chunk = f.read()
        chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
        img = cv2.imdecode(chunk_arr, cv2.IMREAD_COLOR)

        if img is None:
            return None
        
        # Chuyển BGR sang RGB tương thích với lúc train
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = cv2.resize(img, (224, 224)) 
        img = np.expand_dims(img, axis=0) / 255.0

        prediction = model.predict(img, verbose=0)
        max_score = np.max(prediction)
        index = np.argmax(prediction)
        if max_score < threshold:
            return None

        return CATEGORIES[index]
    except Exception as e:
        print(f"⚠️ Lỗi dự đoán CNN: {e}")
        return None