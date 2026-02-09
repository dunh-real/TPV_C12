from ocr_service import OCRService
from extractor_service import extract_metadata_rules
from vllm import LLM, SamplingParams
from PIL import Image
import time
import logging
from pathlib import Path
from llm_service import extract_document_info
import json
from prompt_service import PromptService

# Load service
ocr_service = OCRService()
prompt_service = PromptService()

def processing_img(img_files, result_json):
    
    start_time = time.perf_counter()
    
    for img_file in img_files:
        img = Image.open(img_file).convert("RGB")
        
        img_resized = ocr_service._resize_image(img)
        
        text = ocr_service.ocr_image(img_resized)
        
        # Get prompt by document type
        context_prompt = prompt_service.get_prompt_by_type(result_json["doc_type"], text, result_json)
        
        result_json = extract_document_info(context_prompt)
        
        check_value = json.loads(result_json)
        
        if None not in check_value.values():
            break

    ex_time = time.perf_counter() - start_time

    print(f"Executed time: {ex_time:.4f} seconds")
    
    final_result = json.loads(result_json)
    
    return final_result

PATH_FILE_IMG = "../../data/images"

# List imgs
img_files = list(Path(PATH_FILE_IMG).glob("*.png"))

# img_files = "/home/dell/C12/data/images/first_page.png"
    
print("Enter Key Value:")
user_input = input()
    
key = user_input.split()
    
input_json = {
    "doc_type": key[0]
}
    
for i in range(1, len(key)):
    input_json[key[i]] = None

# Before result extraction
print(input_json)
        
result = processing_img(img_files, input_json)
    
# After result extraction
print(result)
print(type(result))