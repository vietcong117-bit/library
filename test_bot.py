import easyocr
try:
    print("Đang khởi động não bộ (Lần chạy ĐẦU TIÊN sẽ mất vài phút để tải AI model về máy)...")
    
    reader = easyocr.Reader(['vi', 'en'])
    
    print("Bot đang căng mắt ra nhìn ảnh test.jpg...")
    results = reader.readtext('media/bia_truyen/dora1.jpg')
    
    print("\n--- KẾT QUẢ BOT ĐỌC ĐƯỢC ---")
    for (khung_hinh, chu_viet, do_chinh_xac) in results:
        print(f"- {chu_viet}")
        
except Exception as e:
    print("Oops, có lỗi xảy ra:", e)