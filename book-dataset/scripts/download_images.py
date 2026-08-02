import os
import argparse
import pandas as pd
import urllib.request
from urllib.error import HTTPError, URLError
import socket
from joblib import Parallel, delayed
from tqdm import trange

def download_image(i):
    try:
        filename = csv.iloc[i]['Filename']
        category = csv.iloc[i]['Category']
        inner_output_dirpath = os.path.join(args.output_dirpath, category)
        
        # Tự động tạo thư mục thể loại nếu chưa có
        os.makedirs(inner_output_dirpath, exist_ok=True)
        output_filepath = os.path.join(inner_output_dirpath, filename)

        url = csv.iloc[i]['Image URL']
        
        # Nếu file chưa tồn tại thì tiến hành tải về
        if not os.path.isfile(output_filepath):
            request_obj = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            with urllib.request.urlopen(request_obj, timeout=5) as response:
                image_data = response.read()
                
            with open(output_filepath, 'wb') as f:
                f.write(image_data)
                
    except (HTTPError, URLError, socket.timeout, Exception) as e:
        # Bỏ qua các link lỗi 404 hoặc sự cố mạng để script tiếp tục chạy suôn sẻ
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download book dataset images.')
    parser.add_argument('output_dirpath', type=str, help='Directory to save downloaded images')
    parser.add_argument('csv_filepath', type=str, help='Path to the CSV file')
    args = parser.parse_args()

    os.makedirs(args.output_dirpath, exist_ok=True)
    
    print(f'[Download images into "{args.output_dirpath}"]')
    csv = pd.read_csv(args.csv_filepath, encoding='latin-1')
    # Đặt n_jobs=1 để chạy tuần tự an toàn trên Windows
    Parallel(n_jobs=1)(delayed(download_image)(i) for i in trange(len(csv)))