# debug_full.py
# =============================================================================
# BỘ TEST TOÀN DIỆN cho chatbot thư viện — gộp tất cả các loại kiểm tra đã
# làm rời rạc trước đó (dataset, phân loại intent, tách từ khóa, tra DB) vào
# 1 chỗ, tự động chấm PASS/FAIL thay vì phải đọc số liệu bằng mắt.
#
# CÁCH CHẠY: (bắt buộc chạy qua manage.py shell vì có phần tra DB)
#   1. Mở terminal, gõ:  py manage.py shell
#   2. Copy TOÀN BỘ nội dung file này, paste vào, Enter thêm 1 lần cuối
#
# Nếu chỉ muốn test phần intent (không cần DB), có thể chạy thẳng:
#   py debug_full.py
# (phần tra DB ở PHẦN 4 sẽ tự động bỏ qua nếu không có Django context)
# =============================================================================

import pickle
from underthesea import word_tokenize

print("=" * 70)
print("PHẦN 1: KIỂM TRA TÍNH TOÀN VẸN CỦA dataset.py")
print("=" * 70)

from dataset import INTENT_DATA, RESPONSES

total = 0
for intent, phrases in INTENT_DATA.items():
    dup = len(phrases) - len(set(phrases))
    total += len(phrases)
    flag = "  <-- CÓ TRÙNG LẶP!" if dup else ""
    print(f"  {intent}: {len(phrases)} câu{flag}")
print(f"  TỔNG: {total} câu")

seen = {}
cross_dup = 0
for intent, phrases in INTENT_DATA.items():
    for p in phrases:
        if p in seen and seen[p] != intent:
            cross_dup += 1
            print(f"  !! TRÙNG CHÉO: '{p}' ở cả {seen[p]} và {intent}")
        seen[p] = intent
print(f"  Trùng chéo giữa các intent: {cross_dup}" + ("  <-- SỬA NGAY!" if cross_dup else "  OK"))

missing_resp = [i for i in INTENT_DATA if i not in RESPONSES]
print(f"  Intent thiếu RESPONSES: {missing_resp if missing_resp else 'Không có, OK'}")

bad_type = [i for i, v in RESPONSES.items() if not isinstance(v, list)]
print(f"  RESPONSES không phải list: {bad_type if bad_type else 'Không có, OK'}")

too_few = [i for i, p in INTENT_DATA.items() if len(p) < 10]
print(f"  Intent quá ít câu (<10): {too_few if too_few else 'Không có, OK'}")


print()
print("=" * 70)
print("PHẦN 2: KIỂM TRA PHÂN LOẠI INTENT (model .pkl)")
print("=" * 70)

with open("chatbot_model.pkl", "rb") as f:
    model = pickle.load(f)
with open("vectorizer.pkl", "rb") as f:
    vectorizer = pickle.load(f)

# Danh sách test case: (câu hỏi, intent ĐÚNG mong đợi)
# Gồm các câu đã từng gây lỗi trong quá trình phát triển + câu mới chưa
# từng thấy (để kiểm tra khả năng tổng quát hóa, không phải học thuộc lòng)
INTENT_TEST_CASES = [
    # chao_hoi
    ("hello", "chao_hoi"),
    ("hi", "chao_hoi"),
    ("chào bạn", "chao_hoi"),
    ("chào buổi sáng", "chao_hoi"),
    # tam_biet
    ("tạm biệt", "tam_biet"),
    ("bye", "tam_biet"),
    ("hẹn gặp lại", "tam_biet"),
    # cam_on
    ("cảm ơn nha", "cam_on"),
    ("thanks", "cam_on"),
    # tim_sach
    ("tìm sách chí phèo", "tim_sach"),
    ("tìm truyện chí phèo", "tim_sach"),          # lỗi tokenizer gộp từ (đã fix)
    ("tìm sách công nghệ 8", "tim_sach"),           # lỗi overlap với thể loại (đã fix)
    ("mượn sách clean code", "tim_sach"),
    ("tìm sách đắc nhân tâm cho mình", "tim_sach"),
    ("có sách toán rời rạc không", "tim_sach"),
    # tim_theo_tac_gia
    ("sách của tác giả nam cao", "tim_theo_tac_gia"),
    ("tìm sách có tác giả bộ giáo dục", "tim_theo_tac_gia"),  # lỗi pattern "có tác giả" (đã fix)
    ("tác phẩm của dale carnegie", "tim_theo_tac_gia"),
    # tim_theo_the_loai
    ("tìm sách thể loại công nghệ", "tim_theo_the_loai"),
    ("sách thể loại văn học", "tim_theo_the_loai"),
    ("có sách thể loại kinh tế không", "tim_theo_the_loai"),
    # hoi_thu_tuc
    ("thủ tục mượn sách thế nào", "hoi_thu_tuc"),
    ("tìm thủ tục mượn sách", "hoi_thu_tuc"),        # lỗi overlap với tim_sach (đã fix)
    ("làm thẻ thư viện cần gì", "hoi_thu_tuc"),
    # huong_dan_tra_sach
    ("tôi muốn trả sách", "huong_dan_tra_sach"),      # lỗi rơi vào hoi_phat_tre (đã fix)
    ("cách trả sách như thế nào", "huong_dan_tra_sach"),
    # hoi_phat_tre
    ("trả sách trễ bị phạt không", "hoi_phat_tre"),
    ("phạt tiền bao nhiêu", "hoi_phat_tre"),
    ("làm mất sách thì sao", "hoi_phat_tre"),
    # unknown (câu vô nghĩa / ngoài phạm vi)
    ("abc xyz 123", "unknown"),
    ("qwerty asdfgh zxcvbn", "unknown"),
    ("hôm nay trời đẹp quá", "unknown"),
]

CONFIDENCE_THRESHOLD = 0.3  # SỬA số này nếu ai_brain.py bạn đang dùng threshold khác

passed, failed = 0, 0
fail_list = []

for text, expected in INTENT_TEST_CASES:
    segmented = word_tokenize(text.lower(), format="text")
    vec = vectorizer.transform([segmented])

    if vec.nnz == 0:
        predicted = "unknown"
        prob = None
    else:
        probs = model.predict_proba(vec)[0]
        top_idx = probs.argmax()
        prob = probs[top_idx]
        predicted = model.classes_[top_idx] if prob >= CONFIDENCE_THRESHOLD else "unknown"

    ok = predicted == expected
    passed += ok
    failed += not ok
    prob_str = f"{prob:.3f}" if prob is not None else "N/A"
    status = "PASS" if ok else "FAIL"
    line = f"  [{status}] '{text}' -> dự đoán: {predicted} (mong đợi: {expected}, xác suất: {prob_str})"
    print(line)
    if not ok:
        fail_list.append(line)

print(f"\n  KẾT QUẢ PHẦN 2: {passed}/{passed + failed} câu đúng")
if fail_list:
    print("  Các câu SAI:")
    for l in fail_list:
        print(" ", l)


print()
print("=" * 70)
print("PHẦN 3: KIỂM TRA TÁCH TỪ KHÓA (extract_*)")
print("=" * 70)

try:
    from ai_brain import extract_search_query, extract_author_query, extract_category_query

    EXTRACT_TEST_CASES = [
        (extract_search_query, "tìm sách chí phèo", "chí phèo"),
        (extract_search_query, "tìm truyện chí phèo", "chí phèo"),
        (extract_search_query, "tìm sách đắc nhân tâm cho mình", "đắc nhân tâm"),
        (extract_author_query, "sách của tác giả nam cao", "nam cao"),
        (extract_author_query, "tìm sách có tác giả bộ giáo dục", "bộ giáo dục"),
        (extract_category_query, "tìm sách thể loại công nghệ", "công nghệ"),
    ]

    ok_count = 0
    for func, text, expected in EXTRACT_TEST_CASES:
        result = func(text)
        ok = result.strip() == expected
        ok_count += ok
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {func.__name__}('{text}') -> '{result}' (mong đợi: '{expected}')")
    print(f"\n  KẾT QUẢ PHẦN 3: {ok_count}/{len(EXTRACT_TEST_CASES)} đúng")
except ImportError as e:
    print(f"  Bỏ qua (không import được ai_brain.py ở đây): {e}")


print()
print("=" * 70)
print("PHẦN 4: KIỂM TRA TRA CỨU DATABASE (cần chạy qua 'py manage.py shell')")
print("=" * 70)

try:
    from ai_brain import find_book_by_query, find_books_by_author, find_books_by_category
    from chatbot.models import Book  # ĐỔI "chatbot" thành đúng tên app của bạn nếu khác

    all_books = Book.objects.all()
    print(f"  Tổng số sách trong DB: {all_books.count()}")

    DB_TEST_CASES = [
        ("find_book_by_query", find_book_by_query, "chí phèo", "phải tìm thấy 1 sách"),
        ("find_book_by_query", find_book_by_query, "sách không tồn tại xyz123", "phải KHÔNG tìm thấy (None)"),
        ("find_books_by_author", find_books_by_author, "nam cao", "phải tìm thấy >=1 sách"),
        ("find_books_by_category", find_books_by_category, "công nghệ", "phải tìm thấy >=1 sách (qua CATEGORY_ALIASES)"),
    ]

    for name, func, query, note in DB_TEST_CASES:
        result = func(query, all_books)
        if name == "find_book_by_query":
            found = result is not None
            print(f"  {name}('{query}') -> {'Tìm thấy: ' + result.title if found else 'Không tìm thấy'}  ({note})")
        else:
            print(f"  {name}('{query}') -> {len(result)} sách: {[b.title for b in result][:5]}  ({note})")

except ImportError as e:
    print(f"  Bỏ qua PHẦN 4 (cần chạy qua 'py manage.py shell' để có Django + DB): {e}")
except Exception as e:
    print(f"  Lỗi khi tra DB: {e}")
    print("  -> Kiểm tra lại tên app trong 'from chatbot.models import Book' cho đúng.")


print()
print("=" * 70)
print("XONG. Đọc lại các dòng [FAIL] (nếu có) để biết chỗ cần sửa.")
print("=" * 70)