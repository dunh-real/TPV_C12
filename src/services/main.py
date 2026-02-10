import fitz
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

# Check Value is None
def has_none(data):
    if data is None:
        return True
    if isinstance(data, dict):
        return any(has_none(v) for k, v in data.items() if k != 'doc_type')
    if isinstance(data, list):
        return any(has_none(i) for i in data)
    return False

def processing_img(img_files, json_template):
    
    doc_type = json_template['doc_type']
    
    for img_file in img_files:
        # Open IMG -> Resize -> OCR Model -> Text 
        img = Image.open(img_file).convert("RGB")
        
        img_resized = ocr_service._resize_image(img)
        
        text = ocr_service.ocr_image(img_resized)
        
        # Text -> LLM Extractor -> JSON Output
        json_template = llm_service.extract_document_info(doc_type, text, json_template)
        
        if not has_none(json_template): 
            break
    
    return json_template

def main():
    # API return pdf file
    PDF_PATH = "../../data/raw/QĐ 8327-QĐ-BCA-H01 30-10-19 phê duyệt chủ trương đầu tư 53r4534.pdf"
    
    # Path img folder
    IMAGE_DIR_PATH = "../../data/images"
    
    document = fitz.open(PDF_PATH)
    
    first_idx_page = 0
    last_idx_page = document.page_count - 1
    
    # API return json template
    json_template = None
    
    """
    Struct JSON:
    {
        'doc_type': One of the list [CHU_TRUONG, THONG_TIN_DU_AN, KE_H0ACH_LCNT, QUAN_LY_GOI_THAU, HOP_DONG, THANH_TOAN_TAM_UNG] (must have)
        'key_1' : None
        'key_2' : None
        ...
    }
    """
    
    # Before result extraction
    print(f"Kết quả trước khi trích xuất:\n {json_template}")
    
    while first_idx_page <= last_idx_page:     
        # Convert PDF to IMG and save IMG
        PDF2IMG(PDF_PATH, IMAGE_DIR_PATH, first_idx_page, last_idx_page)
        
        # List IMG from folder
        if first_idx_page < last_idx_page:
            img_files = [Path(IMAGE_DIR_PATH) / f"{first_idx_page}.png", 
                            Path(IMAGE_DIR_PATH) / f"{last_idx_page}.png"]
        else:
            img_files = [Path(IMAGE_DIR_PATH) / f"{first_idx_page}.png"]
                
        # Extracting
        json_template = processing_img(img_files, json_template)
        
        if not has_none(json_template):
            break
        
        first_idx_page += 1
        last_idx_page -= 1
            
    # After result extraction
    print(f"Kết quả sau khi trích xuất:\n {json_template}")
    print(type(json_template))
    
    return json_template
    
if __name__ == "__main__":
    main()
    