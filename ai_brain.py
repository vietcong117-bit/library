# ai_brain.py
import pickle
import os
from underthesea import word_tokenize
from dataset import RESPONSES

# Lấy đường dẫn tuyệt đối để không bao giờ bị lỗi Not Found
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.join(BASE_DIR, "chatbot_model.pkl")
VEC_PATH = os.path.join(BASE_DIR, "vectorizer.pkl")

# Nạp mô hình AI đã huấn luyện
with open(MODEL_PATH, "rb") as f:
    model = pickle.load(f)
with open(VEC_PATH, "rb") as f:
    vectorizer = pickle.load(f)

def get_chatbot_response(user_message):
    # Tiền xử lý câu hỏi của người dùng
    segmented_text = word_tokenize(user_message, format="text")
    
    # Chuyển câu hỏi thành vector số
    user_tfidf = vectorizer.transform([segmented_text])
    
    # AI dự đoán Ý định (Intent)
    predicted_intent = model.predict(user_tfidf)[0]
    
    # Lấy câu trả lời tương ứng
    response = RESPONSES.get(predicted_intent, "Xin lỗi, thư viện chưa hiểu ý bạn. Bạn có thể nói rõ hơn không?")
    
    return predicted_intent, response