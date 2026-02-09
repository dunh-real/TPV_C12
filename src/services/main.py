from ocr_service import OCRService
from extractor_service import extract_metadata_rules
from vllm import LLM, SamplingParams
from PIL import Image
import time
from pathlib import Path
from llm_service import LLMService
from pdf2img_service import PDF2IMG

"""
def main:
step 1: Convert pdf file (first and last page) to images --> save in data/images folder

step 2: extract text from converted images using OCRService from src/services/ocr_service.py --> return TEXT

step 3: extract wanted informatino from TEXT using extract_document_info from src/services/llm_service (model name: qwen2.5:latest) --> return json format with key-value pairs
"""

# Load service
ocr_service = OCRService()
llm_service = LLMService()

def processing_img(img_files, json_template):
    
    start_time = time.perf_counter()
    
    doc_type = json_template['doc_type']
    
    for img_file in img_files:
        # Open IMG -> Resize -> OCR Model -> Text 
        img = Image.open(img_file).convert("RGB")
        
        img_resized = ocr_service._resize_image(img)
        
        text = ocr_service.ocr_image(img_resized)
        
        # Text -> LLM Extractor -> JSON Output
        json_template = llm_service.extract_document_info(doc_type, text, json_template)
        
        if None not in json_template.values(): 
            break

    ex_time = time.perf_counter() - start_time

    print(f"Executed time: {ex_time:.4f} seconds")
    
    return json_template

def main(): 
    # Path pdf file and img folder
    PDF_PATH = "../../data/raw/QĐ 8327-QĐ-BCA-H01 30-10-19 phê duyệt chủ trương đầu tư 53r4534.pdf"
    IMAGE_DIR_PATH = "../../data/images"
    
    # Convert PDF to IMG and save IMG
    PDF2IMG(PDF_PATH, IMAGE_DIR_PATH)
    
    # List IMG from folder
    img_files = list(Path(IMAGE_DIR_PATH).glob("*.png"))
    
    # Key string need extract from text   
    print("Enter Key Value:")
    user_input = input()
     
    # Create JSON template  
    key = user_input.split() 
    json_template = {
        "doc_type": key[0]
    }   
    for i in range(1, len(key)):
        json_template[key[i]] = None

    # Before result extraction
    print(f"Kết quả trước khi trích xuất:\n {json_template}")
            
    # Extracting
    result_json = processing_img(img_files, json_template)
        
    # After result extraction
    print(f"Kết quả sau khi trích xuất:\n {result_json}")
    print(type(result_json))
    
if __name__ == "__main__":
    main()

"""
sửa lại trong llm_service hoặc prompt_service:
output format là markdown:
Như hôm trước anh nói, dùng các dấu header để phân biệt từng item, tên item, nội dung item cụ thể
Sau đó trong file main, em mới xử lý split cái string đó, rồi áp từng nội dung vào json

Đoạn lấy text ra, nhớ phải để nó append được đủ text từ 2 trang (trang đầu + trang cuối) rồi mới xử lý bằng con LLM nhé.
test thì thấy nó sai 4/11 trơờng rồi này, accuracy của nó đang thấp quá.
"""