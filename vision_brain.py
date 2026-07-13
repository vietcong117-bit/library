# vision_brain.py
import cv2
import numpy as np
from tensorflow.keras.models import load_model
import os

# Nạp mô hình đã train
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "book_cover_cnn.h5")
model = load_model(MODEL_PATH)
CATEGORIES = ["tech", "fiction", "selfhelp", "business"]

def predict_book_category(image_path):
    # Đọc và tiền xử lý ảnh giống hệt lúc train
    img = cv2.imread(image_path)
    if img is None: return None
    
    img = cv2.resize(img, (128, 128))
    img = np.expand_dims(img, axis=0) / 255.0 # Chuẩn hóa
    
    # Dự đoán
    prediction = model.predict(img)
    index = np.argmax(prediction)
    return CATEGORIES[index]