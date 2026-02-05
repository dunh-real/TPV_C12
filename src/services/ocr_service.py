# INPUT_PATH = "../../data/raw/QĐ 8327-QĐ-BCA-H01 30-10-19 phê duyệt chủ trương đầu tư 53r4534.pdf"
# IMAGE_PATH = "../../data/images/"

# from transformers import LightOnOcrForConditionalGeneration, LightOnOcrProcessor
# import torch
# from pdf2image import convert_from_path
# import os
# import time
# import fitz
# from llm_service import extract_document_info
# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
# # print(device)

# dtype = torch.bfloat16

# model = LightOnOcrForConditionalGeneration.from_pretrained('lightonai/LightOnOCR-2-1B', torch_dtype = dtype).to(device)
# processor = LightOnOcrProcessor.from_pretrained('lightonai/LightOnOCR-2-1B')

# def convert_pdf_to_img(input_path):
#     doc = fitz.open(input_path)
#     for page_num in range(doc.page_count):
#         page = doc.load_page(page_num)
#         pix = page.get_pixmap(dpi=300)
#         image_path = os.path.join(IMAGE_PATH, f"page_{page_num+1}.png")
#         pix.save(image_path)
#         print(f"Saved {image_path}")
        
#     doc.close()


# img_path = "../../data/images/page_2.png"
# conversation = [{"role": "user", "content": [{"type": "image", "path": img_path}]}]

# start_time = time.perf_counter()

# inputs = processor.apply_chat_template(
#     conversation,
#     add_generation_prompt=True,
#     tokenize=True,
#     return_dict=True,
#     return_tensors="pt",
# )
# inputs = {k: v.to(device=device, dtype=dtype) if v.is_floating_point() else v.to(device) for k, v in inputs.items()}

# output_ids = model.generate(**inputs, max_new_tokens=1024)
# generated_ids = output_ids[0, inputs["input_ids"].shape[1]:]
# output_text = processor.decode(generated_ids, skip_special_tokens=False)

# print(output_text)
# # print(f"Executed time: {ex_time:.4f} seconds")

# json_str = extract_document_info(output_text)
# end_time = time.perf_counter()
# ex_time = end_time - start_time
# print(f"Executed time: {ex_time:.4f} seconds")
# print(json_str)

from vllm import LLM, SamplingParams
from PIL import Image
import time
import os
import fitz

IMAGE_PATH = "../../data/images/page_1.png"
MODEL_ID = "lightonai/LightOnOCR-2-1B"
MAX_DIMENSION = 1024

if not os.path.exists(IMAGE_PATH):
    raise FileNotFoundError(f"Khong tim thay anh tai: {IMAGE_PATH}")

# 1. Khoi tao model
llm = LLM(
    model = MODEL_ID,
    dtype = "bfloat16",
    trust_remote_code = True,
    limit_mm_per_prompt = {"image": 1},
    gpu_memory_utilization = 0.9,
    enforce_eager = True
)

# 2. Ham toi uu kich thuoc anh
def resize_image(image_path, max_dim = 1024):
    img = Image.open(image_path).convert("RGB")
    width, heigth = img.size
    if max(width, heigth) <= max_dim:
        return img
    
    # tinh ty le scale
    scale = max_dim / max(width, heigth)
    new_width = int(width * scale)
    new_height = int(heigth * scale)
    
    # resize (LANCZOS giu chat luong anh tot nhat)
    img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    print(f"Original size: {width}x{heigth} -> Resizes: {new_width}x{new_height}")
    return img_resized

# 3. Chuan bi du lieu
image = resize_image(IMAGE_PATH, MAX_DIMENSION)
prompt = "<|vision_start|><|image_pad|><|vision_end|>"
sampling_params = SamplingParams(
    temperature = 0.01,
    max_tokens = 2048,
    stop_token_ids = [151643, 151645]
)
inputs = {
    "prompt": prompt,
    "multi_modal_data": {"image": image},
}

# 4. Chay warmup
print('-'*70)
llm.generate([inputs], sampling_params = SamplingParams(max_tokens = 10))
print('-'*70)


# 5. Chay that
start_time = time.perf_counter()
outputs = llm.generate([inputs], sampling_params = sampling_params)
end_time = time.perf_counter()
ex_time = end_time - start_time

# in ket qua
for o in outputs:
    print(o.outputs[0].text.strip())
    
print(f"Executed time: {ex_time:.4f} seconds")



class OCRService:
    def __init__(self):
        self.image_dir = "../../data/images"
        self.model_name = "lightonai/LightOnOCR-2-1B"
        self.model = LLM(
            model = self.model_name,
            dtype = "bfloat16",
            trust_remote_code = True,
            limit_mm_per_prompt = {"image": 1},
            gpu_memory_utilization = 0.9,
            enforce_eager = True
        )
    
    def convert_pdf_to_img(self, image_path):
        doc = fitz.open(image_path)
        for page_num in range(doc.page_count):
            page = doc.load_page(page_num)
            pix = page.get_pixmap(dpi=300)
            image_path = os.path.join(IMAGE_PATH, f"page_{page_num+1}.png")
            pix.save(image_path)
            print(f"Saved {image_path}")
        
            doc.close()
        return None
    
    def image_preprocess(self, image):
        return None
    
    def run_ocr(self, image):
        return None