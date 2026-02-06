from ocr_service import OCRService
from extractor_service import extract_metadata_rules
from vllm import LLM, SamplingParams
from PIL import Image
import time
import logging

first_img_path = "../../data/images/first_page.png"
last_img_path = "../../data/images/last_page.png"

first_image = Image.open(first_img_path).convert("RGB")
last_image = Image.open(last_img_path).convert("RGB")

ocr_service = OCRService()

first_image_resized = ocr_service._resize_image(first_image)
last_image_resized = ocr_service._resize_image(last_image)

text_p1 = ocr_service.ocr_image(first_image_resized)
text_end = ocr_service.ocr_image(last_image_resized)

start_time = time.perf_counter()
result_json = extract_metadata_rules(text_p1, text_end)
ex_time = time.perf_counter() - start_time
print(result_json)
print(f"Executed time: {ex_time:.4f} seconds")