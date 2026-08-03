import sys
from pathlib import Path
root_path = Path(__file__).resolve().parent.parent.parent
if str(root_path) not in sys.path:
    sys.path.append(str(root_path)) 
import os
import json
import tensorflow as tf
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.layers import Dense, GlobalAveragePooling2D, Dropout
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from project_paths import PROJECT_ROOT, TRAIN_DATA_DIR, MODELS_DIR

# 1. Đường dẫn tới thư mục dataset gốc
train_dir = str(TRAIN_DATA_DIR)

if not os.path.exists(train_dir):
    raise ValueError(f"❌ Không tìm thấy thư mục dataset tại: {train_dir}")

# NÂNG ĐỘ PHÂN GIẢI LÊN 224x224
IMG_SIZE = (224, 224)
BATCH_SIZE = 16

# 2. Tăng cường dữ liệu (Data Augmentation)
train_datagen = ImageDataGenerator(
    rescale=1.0 / 255.0,
    rotation_range=20,
    width_shift_range=0.2,
    height_shift_range=0.2,
    shear_range=0.2,
    zoom_range=0.2,
    horizontal_flip=True,
    fill_mode='nearest'
)

train_generator = train_datagen.flow_from_directory(
    train_dir,
    target_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    class_mode='sparse',
    shuffle=True
)

# Lấy danh sách tên thể loại tự động từ cấu trúc thư mục
class_indices = train_generator.class_indices
CATEGORIES = sorted(class_indices.keys(), key=lambda x: class_indices[x])
print(f"🏷️ Danh sách thể loại quét được: {CATEGORIES}")

num_classes = len(CATEGORIES)
if num_classes == 0:
    raise ValueError("❌ Thư mục dataset/train không chứa thư mục thể loại nào!")

print(f"📊 Tổng số ảnh trong generator: {train_generator.samples}")

# 3. Xây dựng mô hình MobileNetV2 với Fine-Tuning ở độ phân giải 224x224
base_model = MobileNetV2(input_shape=(224, 224, 3), include_top=False, weights='imagenet')

# Mở băng 30 lớp cuối cùng để mô hình học đặc trưng chi tiết
base_model.trainable = True
for layer in base_model.layers[:-30]:
    layer.trainable = False

x = base_model.output
x = GlobalAveragePooling2D()(x)
x = Dense(256, activation='relu')(x)
x = Dropout(0.5)(x)
outputs = Dense(num_classes, activation='softmax')(x)

model = Model(inputs=base_model.input, outputs=outputs)

# 4. Compile với Learning Rate cực nhỏ
model.compile(
    optimizer=Adam(learning_rate=1e-5),
    loss='sparse_categorical_crossentropy',
    metrics=['accuracy']
)

epochs = 30
print(f"🚀 Bắt đầu huấn luyện Fine-Tuning với 224x224 trong {epochs} epochs...")
model.fit(
    train_generator,
    epochs=epochs
)

# 5. Lưu mô hình và danh sách thể loại
MODELS_DIR.mkdir(parents=True, exist_ok=True)
model.save(str(MODELS_DIR / "book_cover_cnn.h5"))

with open(MODELS_DIR / "categories.json", "w", encoding="utf-8") as f:
    json.dump(CATEGORIES, f, ensure_ascii=False)

print("✅ Hoàn tất! Đã lưu mô hình mới với độ phân giải 224x224.")