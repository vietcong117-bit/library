import os
import django
import cv2
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense

# 1. Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_chatbot.settings')
django.setup()
from chatbot.models import Book

# 2. Lấy dữ liệu thực từ Database
X_train, y_train = [], []
# Các nhãn tương ứng với CATEGORY_CHOICES trong models.py
categories = ["tech", "fiction", "selfhelp", "business"] 

for book in Book.objects.exclude(image=''):
    img_path = book.image.path # Lấy đường dẫn ảnh từ database
    img = cv2.imread(img_path)
    if img is not None:
        img = cv2.resize(img, (128, 128)) # Chuẩn hóa kích thước ảnh[cite: 1]
        X_train.append(img)
        y_train.append(categories.index(book.category))

X_train = np.array(X_train) / 255.0
y_train = np.array(y_train)

# 3. Xây dựng CNN (Giữ nguyên cấu trúc chuẩn trong tài liệu)[cite: 1]
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
    MaxPooling2D((2, 2)),
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    Flatten(),
    Dense(128, activation='relu'),
    Dense(len(categories), activation='softmax') # Dùng softmax cho đa phân loại
])

# 4. Huấn luyện[cite: 1]
model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=10, batch_size=16)

# 5. Lưu mô hình để chatbot sử dụng
model.save("models/book_cover_cnn.h5")
print("✅ Huấn luyện thành công!")