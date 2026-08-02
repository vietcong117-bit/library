import json
import tensorflow as tf
import numpy as np
from tensorflow.keras.utils import load_img, img_to_array

# 1. Load mô hình
model = tf.keras.models.load_model('models/book_cover_cnn.h5')

# 2. LOAD ĐÚNG DANH SÁCH NHÃN ĐÃ LƯU KHI TRAIN 
with open("models/categories.json", "r", encoding="utf-8") as f:
    class_names = json.load(f)

print(f"🏷️ Nhãn chuẩn đang dùng: {class_names}")

# 3. Đọc và dự đoán ảnh
img_path = 'dataset/train/religion/9652930695.jpg'
img = load_img(img_path, target_size=(128, 128)) 
img_array = img_to_array(img) / 255.0
img_array = tf.expand_dims(img_array, 0)

predictions = model.predict(img_array)
score = tf.nn.softmax(predictions[0])

predicted_class = class_names[np.argmax(score)]
confidence = 100 * np.max(score)

print(f"🎯 Kết quả dự đoán: {predicted_class}")
print(f"📊 Độ tự tin: {confidence:.2f}%")