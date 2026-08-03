import os
import json
import sys
import numpy as np
import tensorflow as tf
from tensorflow.keras.utils import load_img, img_to_array
import easyocr
from project_paths import MODELS_DIR, MEDIA_ROOT

# 1. Load mô hình và nhãn chuẩn
model = tf.keras.models.load_model(str(MODELS_DIR / 'book_cover_cnn.h5'))

with open(MODELS_DIR / "categories.json", "r", encoding="utf-8") as f:
    class_names = json.load(f)

print(f"🏷️ Nhãn chuẩn đang dùng: {class_names}")

# 2. Lấy đường dẫn ảnh từ Terminal hoặc mặc định
img_path = str(MEDIA_ROOT / 'temp' / 's-l1600.webp')
if len(sys.argv) > 1:
    img_path = sys.argv[1]

# 3. Dự đoán thể loại bằng CNN (Kích thước 224x224)
img = load_img(img_path, target_size=(224, 224)) 
img_array = img_to_array(img) / 255.0
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = predictions[0]

predicted_class = class_names[np.argmax(score)]
confidence = 100 * np.max(score)

print(f"🎯 Kết quả dự đoán thể loại (CNN): {predicted_class}")
print(f"📊 Độ tự tin: {confidence:.2f}%")

# 4. Trích xuất văn bản tiếng Việt trên bìa bằng OCR
print("📖 Đang quét và đọc chữ trên bìa sách bằng OCR...")
reader = easyocr.Reader(['vi', 'en'], gpu=False)
ocr_results = reader.readtext(img_path, detail=0)
extracted_text = " ".join(ocr_results)

print(f"🔤 Văn bản đọc được trên bìa (OCR): '{extracted_text if extracted_text else 'Không phát hiện rõ chữ'}'")