from ocr_service import OCRService
from extractor_service import extract_metadata_rules
from vllm import LLM, SamplingParams
from PIL import Image
import time
from pathlib import Path
from llm_service import extract_document_info

"""
def main:
step 1: Convert pdf file (first and last page) to images --> save in data/images folder

step 2: extract text from converted images using OCRService from src/services/ocr_service.py --> return TEXT

step 3: extract wanted informatino from TEXT using extract_document_info from src/services/llm_service (model name: qwen2.5:latest) --> return json format with key-value pairs
"""


# Load service
ocr_service = OCRService()

def processing_img(img_files, json_template):
    
    start_time = time.perf_counter()
    
    doc_type = json_template['doc_type']
    
    for img_file in img_files:
        img = Image.open(img_file).convert("RGB")
        
        img_resized = ocr_service._resize_image(img)
        
        text = ocr_service.ocr_image(img_resized)
        
        json_template = extract_document_info(doc_type, text, json_template)
        
        if None not in json_template.values(): 
            break

    ex_time = time.perf_counter() - start_time

    print(f"Executed time: {ex_time:.4f} seconds")
    
    return json_template

PATH_FILE_IMG = "../../data/images"

# List imgs
img_files = list(Path(PATH_FILE_IMG).glob("*.png"))
    
print("Enter Key Value:")
user_input = input()
    
key = user_input.split()
    
json_template = {
    "doc_type": key[0]
}
    
for i in range(1, len(key)):
    json_template[key[i]] = None

# Before result extraction
print(json_template)
        
result_json = processing_img(img_files, json_template)
    
# After result extraction
print(result_json)
print(type(result_json))

"""
sửa lại trong llm_service hoặc prompt_service:
output format là markdown:
Như hôm trước anh nói, dùng các dấu header để phân biệt từng item, tên item, nội dung item cụ thể
Sau đó trong file main, em mới xử lý split cái string đó, rồi áp từng nội dung vào json

Đoạn lấy text ra, nhớ phải để nó append được đủ text từ 2 trang (trang đầu + trang cuối) rồi mới xử lý bằng con LLM nhé.
test thì thấy nó sai 4/11 trơờng rồi này, accuracy của nó đang thấp quá.
"""