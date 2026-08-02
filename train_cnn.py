import os
import json
import cv2
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.optimizers import Adam

# 1. Đường dẫn tới thư mục dataset gốc
train_dir = 'dataset/train'

if not os.path.exists(train_dir):
    raise ValueError(f"❌ Không tìm thấy thư mục dataset tại: {train_dir}")

# 2. Tự động lấy danh sách mã thể loại từ tên các thư mục con
CATEGORIES = sorted([d for d in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, d))])
print(f"🏷️ Danh sách mã thể loại quét được từ thư mục: {CATEGORIES}")

if not CATEGORIES:
    raise ValueError("❌ Thư mục dataset/train không chứa thư mục thể loại nào!")

X_train, y_train = [], []

# 3. Quét trực tiếp các file ảnh trong từng thư mục thể loại
for category_code in CATEGORIES:
    category_path = os.path.join(train_dir, category_code)
    for img_name in os.listdir(category_path):
        if img_name.lower().endswith(('.png', '.jpg', '.jpeg')):
            img_path = os.path.join(category_path, img_name)
            try:
                # Đọc ảnh bằng OpenCV
                img = cv2.imread(img_path)
                if img is not None:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    img = cv2.resize(img, (128, 128))
                    
                    X_train.append(img)
                    y_train.append(CATEGORIES.index(category_code))
            except Exception as e:
                print(f"⚠️ Lỗi đọc ảnh {img_path}: {e}")

X_train = np.array(X_train, dtype="float32") / 255.0
y_train = np.array(y_train)

print(f"📊 Tổng số ảnh hợp lệ đưa vào huấn luyện: {len(X_train)}")

if len(X_train) == 0:
    raise ValueError("❌ Không có dữ liệu ảnh hợp lệ để huấn luyện trong thư mục!")

# 4. Xây dựng cấu trúc mô hình CNN
model = Sequential([
    Conv2D(32, (3, 3), activation='relu', input_shape=(128, 128, 3)),
    MaxPooling2D((2, 2)),
    
    Conv2D(64, (3, 3), activation='relu'),
    MaxPooling2D((2, 2)),
    
    Flatten(),
    Dense(128, activation='relu'),
    Dropout(0.3),
    Dense(len(CATEGORIES), activation='softmax')
])

# 5. Thiết lập thông số và tiến hành huấn luyện
model.compile(optimizer=Adam(learning_rate=0.0001), loss='sparse_categorical_crossentropy', metrics=['accuracy'])
model.fit(X_train, y_train, epochs=20, batch_size=16, shuffle=True)

# 6. Lưu mô hình và danh sách CATEGORIES vào file json để dự đoán sau này
os.makedirs("models", exist_ok=True)
model.save("models/book_cover_cnn.h5")

with open("models/categories.json", "w", encoding="utf-8") as f:
    json.dump(CATEGORIES, f, ensure_ascii=False)

print("✅ Huấn luyện trực tiếp từ thư mục, lưu mô hình và file categories thành công!")