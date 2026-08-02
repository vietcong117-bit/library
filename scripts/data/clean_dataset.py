# xóa file ảnh lỗi trong dataset 
import os
from PIL import Image

train_dir = 'dataset/train'

if not os.path.exists(train_dir):
    print(f"❌ Không tìm thấy thư mục {train_dir}")
else:
    print("🔍 Đang quét các file lỗi hoặc không phải ảnh trong dataset...")
    count = 0
    for root, dirs, files in os.walk(train_dir):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Thử mở và kiểm tra tính hợp lệ của ảnh bằng PIL
                with Image.open(file_path) as img:
                    img.verify()
            except (IOError, SyntaxError, ValueError) as e:
                print(f"🗑️ Phát hiện file lỗi/không hợp lệ, đang xóa: {file_path}")
                os.remove(file_path)
                count += 1
            except Exception as e:
                # Xử lý các file ẩn hệ thống không đọc được
                print(f"🗑️ Xóa file hệ thống/rác: {file_path}")
                os.remove(file_path)
                count += 1

    print(f"✅ Hoàn tất! Đã dọn dẹp thành công {count} file lỗi khỏi dataset.")