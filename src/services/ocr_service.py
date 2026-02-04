INPUT_PATH = "../../data/raw/QĐ 8327-QĐ-BCA-H01 30-10-19 phê duyệt chủ trương đầu tư 53r4534.pdf"
IMAGE_PATH = "../../data/images/"

class OCRService:
    def __init__(self):
        self.model = None
        
    def get_input(self, input_path):
        return None


from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor
import torch
from pdf2image import convert_from_path
import os
import time
import fitz

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# print(device)

dtype = torch.bfloat16

model = LightOnOcrForConditionalGeneration.from_pretrained('lightonai/LightOnOCR-2-1B', torch_dtype = dtype).to(device)
processor = LightOnOcrProcessor.from_pretrained('lightonai/LightOnOCR-2-1B')

def convert_pdf_to_img(input_path):
    doc = fitz.open(input_path)
    for page_num in range(doc.page_count):
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)
        image_path = os.path.join(IMAGE_PATH, f"page_{page_num+1}.png")
        pix.save(image_path)
        print(f"Saved {image_path}")
        
    doc.close()


img_path = "../../data/images/page_2.png"
conversation = [{"role": "user", "content": [{"type": "image", "path": img_path}]}]

start_time = time.perf_counter()

inputs = processor.apply_chat_template(
    conversation,
    add_generation_prompt=True,
    tokenize=True,
    return_dict=True,
    return_tensors="pt",
)
inputs = {k: v.to(device=device, dtype=dtype) if v.is_floating_point() else v.to(device) for k, v in inputs.items()}

output_ids = model.generate(**inputs, max_new_tokens=1024)
generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
output_text = processor.decode(generated_ids, skip_special_tokens=False)

end_time = time.perf_counter()
ex_time = end_time - start_time

print(output_text)
print(f"Executed time: {ex_time:.4f} seconds")
