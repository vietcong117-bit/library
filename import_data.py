import os
import re
import django
import pandas as pd

# 1. Thiết lập môi trường Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_chatbot.settings')
django.setup()

# Định nghĩa bảng ánh xạ từ tên thư mục sang Tên hiển thị tiếng Việt mong muốn
CATEGORY_NAME_MAPPING = {
    'math': 'Toán học',
    'literature': 'Văn học',
    'business': 'Kinh doanh',
    'comic': 'Truyện tranh',
    'fiction': 'Tiểu thuyết / Viễn tưởng',
    'food': 'Ẩm thực & Nấu ăn',
    'history': 'Lịch sử',
    'manga': 'Truyện tranh Nhật Bản (Manga)',
    'religion': 'Tôn giáo & Tâm linh',
    'sport': 'Thể thao',
    'tech': 'Công nghệ thông tin',
    'vietcomic': 'Truyện tranh Việt Nam'
}

from chatbot.models import Book, Category

# 2. Đọc file CSV với header=None
csv_path = 'book32-listing.csv'  # Hoặc đường dẫn file CSV của bạn

df = None
if os.path.exists(csv_path):
    try:
        df = pd.read_csv(csv_path, encoding='latin-1', header=None)
        print("🎉 Đọc file CSV thành công!")
    except Exception as e:
        print(f"⚠️ Lỗi đọc file CSV: {e}")
else:
    print(f"❌ Không tìm thấy file CSV tại: {csv_path}")

# 3. Quét thư mục dataset để import ảnh và lọc bỏ sách không tên
dataset_dir = 'dataset/train'
imported_count = 0
skipped_count = 0

# 3. Quét thư mục dataset
if os.path.exists(dataset_dir):
    Book.objects.all().delete()
    print("🧹 Đã làm sạch dữ liệu cũ trong database.")

    for category_folder in os.listdir(dataset_dir):
        category_path = os.path.join(dataset_dir, category_folder)
        
        if os.path.isdir(category_path):
            # Lấy mã code chính là tên thư mục
            category_code = category_folder.strip().lower()
            
            # 👉 Lấy tên tiếng Việt từ bảng ánh xạ, nếu không có thì lấy mặc định viết hoa chữ cái đầu
            category_name = CATEGORY_NAME_MAPPING.get(category_code, category_folder.capitalize())

            # Tạo hoặc lấy Category với mã code và tên tiếng Việt chuẩn
            category_obj, created = Category.objects.get_or_create(
                code=category_code,
                defaults={'name': category_name}
            )

            for img_name in os.listdir(category_path):
                if img_name.lower().endswith(('.png', '.jpg', '.jpeg', '.webp')):
                    isbn_from_file = os.path.splitext(img_name)[0].strip()
                    
                    # Tìm thông tin sách từ CSV (nếu có)
                    book_title = None
                    book_author = "Unknown"
                    
                    if df is not None:
                        matched_row = df[df[0].astype(str).str.strip() == isbn_from_file]
                        if not matched_row.empty:
                            row = matched_row.iloc[0]
                            raw_title = str(row.get(3, '')).strip()
                            if raw_title and raw_title.lower() != 'nan':
                                book_title = raw_title
                                book_author = str(row.get(4, 'Unknown')).strip()
                    
                    # Nếu không có tên trong CSV thì bỏ qua
                    if not book_title:
                        skipped_count += 1
                        continue

                    img_relative_path = os.path.join('dataset/train', category_folder, img_name)
                    
                    Book.objects.create(
                        image=img_relative_path,
                        title=book_title,
                        author=book_author,
                        category=category_obj, # Gắn đúng Category có tên tiếng Việt
                        quantity=10,
                        published_year=2020,
                    )
                    imported_count += 1
                    print(f"✅ Đã import: {book_title} [{category_name}]")

    print(f"\n🎉 Hoàn tất! Đã import thành công: {imported_count} cuốn | Đã lọc bỏ (không có tên): {skipped_count} cuốn")
else:
    print(f"❌ Không tìm thấy thư mục dataset tại: {dataset_dir}")