import os
import cv2
import numpy as np
import tensorflow as tf
import easyocr

MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "book_cover_cnn.h5")
model = tf.keras.models.load_model(MODEL_PATH)
CATEGORIES = ["tech", "fiction", "selfhelp", "business"]

# Khởi tạo reader đọc tiếng Việt và tiếng Anh
reader = easyocr.Reader(['vi', 'en'], gpu=False)

def extract_text_from_image(image_path):
    """Trích xuất tất cả văn bản xuất hiện trên ảnh bìa"""
    try:
        results = reader.readtext(image_path, detail=0)
        text = " ".join(results).lower()
        return text
    except Exception:
        return ""

def predict_book_category(image_path, threshold=0.6):
    """Dự đoán thể loại bằng CNN"""
    if not os.path.exists(image_path):
        return None

    with open(image_path, 'rb') as f:
        chunk = f.read()
    chunk_arr = np.frombuffer(chunk, dtype=np.uint8)
    img = cv2.imdecode(chunk_arr, cv2.IMREAD_COLOR)

    if img is None:
        return None
    
    img = cv2.resize(img, (128, 128))
    img = np.expand_dims(img, axis=0) / 255.0

    prediction = model.predict(img)
    max_score = np.max(prediction)
    index = np.argmax(prediction)

    if max_score < threshold:
        return None

    return CATEGORIES[index]