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

    # -------------------------------------------------------------
    # LƯU Ý QUAN TRỌNG (chống Intent Overlap):
    # - tim_sach: LUÔN đi kèm một cái TÊN SÁCH/TỪ KHÓA CỤ THỂ sau động từ
    #   tìm/mượn/đọc. Không dùng câu mẫu "tìm" trơ trọi.
    # - hoi_thu_tuc: LUÔN đi kèm cụm "thủ tục / quy định / quy trình / đăng ký thẻ".
    #   Kể cả khi có chữ "tìm" (vd: "tìm thủ tục mượn sách"), câu vẫn phải nằm ở
    #   nhóm này chứ không phải tim_sach, để model học đúng ranh giới.
    # - Việc thêm bigram (xem train.py) sẽ giúp model phân biệt cụm 2 từ
    #   "tìm sách" vs "tìm thủ tục" thay vì chỉ nhìn từ "tìm" đơn lẻ.
    # -------------------------------------------------------------
    "tim_sach": [
        "tìm truyện conan",
        "sách clean code ở đâu",
        "mượn cuốn harry potter",
        "tìm sách lập trình python",
        "có sách toán cao cấp không",
        "thư viện có cuốn đắc nhân tâm không",
        "mình muốn tìm cuốn atomic habits",
        "hỏi sách kinh tế học",
        "tìm giúp mình cuốn nhà giả kim",
        "có quyển nào tên là clean code không",
        "cho mình hỏi cuốn tư duy nhanh và chậm",
        "tra cứu sách văn học việt nam",
        "muốn đọc quyển doraemon",
        "tôi muốn tìm sách lịch sử việt nam",
        "tôi cần mượn sách toán rời rạc",
        "bạn tìm giúp mình cuốn sách nhà giả kim",
        "sách đắc nhân tâm có trong thư viện không",
        "tìm truyện tranh doraemon tập 5",

        # --- Câu mẫu ĐỐI TRỌNG: tên sách trùng với từ chỉ thể loại/tác giả ---
        # (giúp model không nhầm "tên sách chứa từ thể loại" với ý định
        # tìm-theo-thể-loại, khi câu KHÔNG có "thể loại"/"loại" đi kèm)
        "tìm sách công nghệ 8",
        "mượn sách công nghệ 10",
        "có sách khoa học tự nhiên 6 không",
        "tìm cuốn công nghệ lớp 8",
        "sách công nghệ 8 có trong thư viện không",
        "cho mình mượn cuốn khoa học tự nhiên 7"
    ],

    "hoi_thu_tuc": [
        "làm sao để mượn sách",
        "thủ tục mượn sách thế nào",
        "đăng ký thẻ thư viện",
        "cần giấy tờ gì để mượn sách",
        "thẻ sinh viên có mượn được sách không",
        "hướng dẫn thủ tục mượn sách",
        "muốn làm thẻ thư viện",
        "quy định mượn sách của thư viện",
        "tìm hiểu thủ tục mượn sách",
        "tìm thủ tục mượn sách",
        "cho mình hỏi thủ tục mượn trả sách",
        "thủ tục đăng ký thẻ thư viện như thế nào",
        "mình muốn tìm hiểu về thủ tục mượn sách",
        "quy trình mượn sách ra sao",
        "cách đăng ký làm thẻ thư viện",
        "tìm quy định mượn sách của trường"
    ],

  

    # -------------------------------------------------------------
    # Tìm sách theo TÊN TÁC GIẢ. Luôn có cụm "tác giả" / "viết bởi" / "của"
    # + TÊN NGƯỜI đi kèm, để phân biệt rõ với tim_sach (vốn đi với TÊN SÁCH).
    # -------------------------------------------------------------
    "tim_theo_tac_gia": [
        "tìm tác phẩm của tác giả nam cao",
        "sách của tác giả dale carnegie",
        "sách của bộ giáo dục",
        "tác phẩm của robert martin",
        "tìm sách do tác giả alec ross viết",
        "có sách nào của tác giả nam cao không",
        "cho mình xem sách của c.s. lewis",
        "tìm truyện của tác giả nam cao",
        "sách viết bởi dale carnegie",
        "tác giả nam cao có những sách nào",
        "liệt kê sách của tác giả dale carnegie",
        "tìm giúp mình sách của tác giả robert martin",
        "mình muốn xem các tác phẩm của nam cao",
        "sách nào do alec ross viết",
        "cho mình hỏi tác giả c.s. lewis có sách gì"
    ],

    # -------------------------------------------------------------
    # Hướng dẫn TRẢ sách (khác hoi_phat_tre: chỉ hỏi phạt/quá hạn/mất sách).
    # Luôn có "trả sách" nhưng KHÔNG có từ trễ/phạt/quá hạn/mất/hư hỏng.
    # -------------------------------------------------------------
    "huong_dan_tra_sach": [
        "tôi muốn trả sách",
        "cách trả sách như thế nào",
        "trả sách ở đâu",
        "quy trình trả sách ra sao",
        "làm sao để trả sách",
        "hướng dẫn trả sách",
        "trả sách cần mang theo gì",
        "tôi cần trả cuốn sách đã mượn",
        "muốn trả lại sách đã mượn",
        "trả sách như thế nào vậy",
        "cho mình hỏi cách trả sách",
        "tôi trả sách ở quầy nào",
        "thủ tục trả sách thế nào"
    ],

    # -------------------------------------------------------------
    # Tìm sách theo THỂ LOẠI. Luôn có cụm "thể loại" / "loại" đi kèm
    # tên thể loại, để phân biệt với tim_sach (tên sách cụ thể).
    # -------------------------------------------------------------
    "tim_theo_the_loai": [
        "tìm sách thể loại văn học",
        "sách thể loại trinh thám",
        "có sách thể loại khoa học không",
        "tìm truyện thể loại ngôn tình",
        "sách loại kỹ năng sống có không",
        "cho mình xem sách thể loại kinh tế",
        "thể loại văn học có sách gì",
        "liệt kê sách thể loại thiếu nhi",
        "tìm sách thuộc thể loại lịch sử",
        "mình muốn tìm sách thể loại tâm lý",
        "có sách nào thể loại kinh doanh không",
        "sách thể loại công nghệ có gì"
    ]
}

RESPONSES = {
    "chao_hoi": "Xin chào! Trợ lý ảo Thư viện Đại học Phan Thiết có thể giúp gì cho bạn?",
    "tam_biet": "Tạm biệt bạn nhé! Hẹn gặp lại bạn tại thư viện.",
    "cam_on": "Không có chi đâu nè! Rất vui được hỗ trợ bạn.",
    "tim_sach": "Bạn vui lòng nhập tên sách hoặc từ khóa nhé.",
    "hoi_thu_tuc": "Để mượn sách, bạn chỉ cần mang Thẻ sinh viên đến quầy thủ thư để cán bộ hỗ trợ làm thủ tục mượn nha.",
    "tim_theo_tac_gia": "Bạn vui lòng cho mình biết tên tác giả nhé.",
    "huong_dan_tra_sach": "Bạn mang sách cùng Thẻ sinh viên đến quầy thủ thư để trả sách nha. Nhớ trả đúng hạn để tránh bị phạt nhé!",
    "tim_theo_the_loai": "Bạn vui lòng cho mình biết thể loại sách bạn muốn tìm nhé.",
    # Fallback khi độ tin cậy dự đoán thấp hơn CONFIDENCE_THRESHOLD (xem ai_brain.py)
    "unknown": "Xin lỗi, thư viện chưa hiểu ý bạn lắm . Bạn có thể nói rõ hơn được không?"
}
