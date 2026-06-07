from django.shortcuts import render
from django.http import HttpResponse

def home(request):
    return HttpResponse("Chatbot đã sẵn sàng!")

def upload_image(request):
    if request.method == 'POST' and request.FILES.get('image'):
        image = request.FILES['image']
        # TODO: xử lý bằng mô hình AI
        result = "Kết quả từ mô hình AI"
        return render(request, 'upload.html', {'response': result})
    return render(request, 'upload.html')
