import os
import shutil

# Định nghĩa bảng quy đổi từ tên thư mục gốc sang tên thư mục chuẩn trong Django của bạn
# (Bên trái là tên thư mục do script tải về, bên phải là tên folder bạn muốn gom vào)
category_mapping = {
    
    "Business & Money": "business",
    "Computers & Technology": "tech",
    "History": "history",
    "Literature & Fiction": "literature", 
    "Science Fiction & Fantasy": "fiction",
    "Science & Math": "math",
    "Cookbooks, Food & Wine": "food",
    "Sports & Outdoors": "sport",
    "Religion & Spirituality": "religion",
    "Comics & Graphic Novels": "comic",
    "Arts & Photography": "art",
}

SOURCE_DIR = "book-dataset/images"  # Thư mục chứa ảnh vừa tải
TARGET_DIR = "dataset/train"        # Thư mục train đích của bạn

for src_folder_name, target_folder_name in category_mapping.items():
    src_path = os.path.join(SOURCE_DIR, src_folder_name)
    target_path = os.path.join(TARGET_DIR, target_folder_name)
    
    if os.path.exists(src_path):
        # Tạo thư mục đích nếu chưa có
        os.makedirs(target_path, exist_ok=True)
        
        # Copy toàn bộ ảnh sang thư mục chuẩn
        count = 0
        for img_file in os.listdir(src_path):
            src_file_path = os.path.join(src_path, img_file)
            target_file_path = os.path.join(target_path, img_file)
            
            if os.path.isfile(src_file_path):
                shutil.copy(src_file_path, target_file_path)
                count += 1
                
        print(f"Đã chuyển thành công {count} ảnh từ '{src_folder_name}' sang '{target_folder_name}'")
    else:
        print(f"Không tìm thấy thư mục nguồn: {src_folder_name}")

print("Hoàn tất gom dữ liệu!")