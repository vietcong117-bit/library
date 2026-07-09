# dataset.py

INTENT_DATA = {
    "chao_hoi": [
        "chào bạn", "hi", "hello", "bot ơi", "chào buổi sáng", 
        "ê bot", "có ai ở đó không", "alo", "xin chào thư viện", "chào ad"
    ],
    "tam_biet": [
        "tạm biệt", "bye", "hẹn gặp lại", "out đây", "mình đi đây", 
        "chào nhé", "pai pai", "thôi mình nghỉ đây", "see you"
    ],
    "cam_on": [
        "cảm ơn", "thanks", "ok ngon", "tuyệt vời", "đã hiểu", 
        "cảm ơn bot nhiều nha", "đa tạ", "giỏi lắm bot", "thank ad"
    ],
    "tim_sach": [
        "tìm truyện", "sách ở đâu", "mượn cuốn này", "tìm sách", "có sách", "tìm truyện",
        "thư viện có cuốn", "mình muốn tìm", "hỏi sách", "tìm giúp cuốn", 
        "có quyển nào tên là", "cho mình hỏi cuốn", "tra cứu sách", "muốn đọc quyển"
    ],
  
    "hoi_thu_tuc": [
        "làm sao để mượn sách", "thủ tục mượn sách thế nào", "đăng ký thẻ thư viện", 
        "cần giấy tờ gì để mượn", "thẻ sinh viên có mượn được không", "hướng dẫn mượn",
        "muốn làm thẻ thư viện", "quy định mượn sách"
    ],
    "hoi_phat_tre": [
        "trả sách trễ bị phạt không", "phạt tiền bao nhiêu", "quá hạn trả sách", 
        "làm mất sách thì sao", "quên trả sách", "hư hỏng sách bị đền thế nào",
        "quá hạn mượn sách có sao không", "mất sách đền thế nào"
    ]
}

RESPONSES = {
    "chao_hoi": "Xin chào! Trợ lý ảo Thư viện Đại học Phan Thiết có thể giúp gì cho bạn?",
    "tam_biet": "Tạm biệt bạn nhé! Hẹn gặp lại bạn tại thư viện.",
    "cam_on": "Không có chi đâu nè! Rất vui được hỗ trợ bạn.",
    "tim_sach": "Bạn vui lòng nhập tên sách hoặc từ khóa nhé.", 
    "hoi_thu_tuc": "Để mượn sách, bạn chỉ cần mang Thẻ sinh viên đến quầy thủ thư để cán bộ hỗ trợ làm thủ tục mượn nha.",
    "hoi_phat_tre": "Sách trả quá hạn sẽ phạt 2.000đ/ngày. Trường hợp làm mất hoặc làm rách hỏng sách, bạn sẽ phải đền cuốn sách mới tương đương hoặc bồi thường theo giá trị của cuốn sách nha."
}