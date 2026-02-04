INPUT_PATH = "./data/raw/QĐ 8327-QĐ-BCA-H01 30-10-19 phê duyệt chủ trương đầu tư 53r4534.pdf"
IMAGE_PATH = "./data/processed/"

class OCRService:
    def __init__(self):
        self.model = None
        
    def get_input(self, input_path):
        return None


from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor
import torch
from pdf2image import convert_from_path
import os
import fitz

device = "mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu"
# print(device)

dtype = torch.bfloat16

model = LightOnOcrForConditionalGeneration.from_pretrained('lightonai/LightOnOCR-2-1B', torch_dtype = dtype).to(device)
processor = LightOnOcrProcessor.from_pretrained('lightonai/LightOnOCR-2-1B')

# def convert_pdf_to_img(pdf_path):
#     return None

# images = convert_from_path(INPUT_PATH)
# for i, image in enumerate(images):
#     image_path = os.path.join(IMAGE_PATH, f"page_{i+1}.jpg")
#     image.save(image_path, "JPEG")
#     print(f"Saved page {image_path}")


doc = fitz.open(INPUT_PATH)
for page_num in range(doc.page_count):
    page = doc.load_page(page_num)
    pix = page.get_pixmap(dpi=300)
    image_path = os.path.join(IMAGE_PATH, f"page_{page_num+1}.png")
    pix.save(image_path)
    print(f"Saved {image_path}")
    
doc.close()