from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import easyocr
import difflib # Công cụ tìm chữ "na ná" nhau
from thuvien_app.models import Truyen # Gọi kho truyện ra

def chatbot_view(request):
    chu_doc_duoc = ""
    truyen_tim_thay = None # Biến để lưu cuốn truyện nếu tìm thấy
    
    if request.method == 'POST' and request.FILES.get('anh_upload'):
        # 1. Lưu ảnh
        anh = request.FILES['anh_upload']
        fss = FileSystemStorage()
        file_path = fss.save(anh.name, anh)
        duong_dan_anh = fss.path(file_path)
        
        # 2. Đọc ảnh
        reader = easyocr.Reader(['vi', 'en'])
        results = reader.readtext(duong_dan_anh)
        
        # Ghép các chữ đọc được thành 1 chuỗi
        for (khung_hinh, chu_viet, do_chinh_xac) in results:
            chu_doc_duoc += chu_viet + " "
            
        # 3. THUẬT TOÁN TÌM TRUYỆN THÔNG MINH
        if chu_doc_duoc:
            # Lấy tên của tất cả các cuốn truyện đang có trong kho
            tat_ca_truyen = Truyen.objects.all()
            danh_sach_ten = [t.ten_truyen for t in tat_ca_truyen]
            
            # Tìm tên truyện giống với chữ đọc được nhất (chấp nhận sai chính tả)
            ket_qua_giong_nhat = difflib.get_close_matches(chu_doc_duoc, danh_sach_ten, n=1, cutoff=0.3)
            
            # Nếu tìm thấy cuốn nào na ná
            if ket_qua_giong_nhat:
                ten_sach_chuan = ket_qua_giong_nhat[0]
                # Lôi toàn bộ thông tin cuốn truyện đó từ kho ra
                truyen_tim_thay = Truyen.objects.get(ten_truyen=ten_sach_chuan)

    # Gửi cả chữ đọc được và thông tin truyện ra ngoài web
    return render(request, 'chat.html', {
        'chu_doc_duoc': chu_doc_duoc,
        'truyen': truyen_tim_thay
    })