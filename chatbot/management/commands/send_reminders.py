from django.core.management.base import BaseCommand
# Dùng dấu chấm để trỏ ngược ra thư mục gốc của app ai_chatbot chứa file services.py
from ...services import process_due_date_reminders  

class Command(BaseCommand):
    help = 'Chạy lệnh kiểm tra và gửi thông báo hạn trả sách'

    def handle(self, *args, **kwargs):
        self.stdout.write("🔄 Đang quét dữ liệu mượn sách...")
        result_msg = process_due_date_reminders()
        self.stdout.write(self.style.SUCCESS(result_msg))