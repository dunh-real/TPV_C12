import logging
import time
import re
import json
from PIL import Image
from vllm import LLM, SamplingParams
import torch

logger = logging.getLogger(__name__)

class OCRService:
    def __init__(self, model_path = 'lightonai/LightOnOCR-2-1B'):
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # cau hinh VLLM toi uu cho GPU < 10GB
        # model 1B chi ton khoang 2-3GB
        self.llm = LLM(
            model = model_path,
            dtype = "bfloat16",
            trust_remote_code = True,
            limit_mm_per_prompt = {"image": 1},
            mm_processor_cache_gb = 0,
            enable_prefix_caching = False,
            gpu_memory_utilization = 0.25,
            enforce_eager = True
        )
        
        # cau hinh sampling: temperature thap nhat de chinh xac
        self.sampling_params = SamplingParams(
            temperature = 0.2,
            max_tokens = 4096,
            top_p = 0.9,
            stop_token_ids = [151643, 151645],
            repetition_penalty = 1.05
        )
    
    def _resize_image(self, pil_image, max_dim = 1024):
        """Resize de tang toc do gap 3 lan ma van giu do net chu"""
        width, height = pil_image.size
        if max(width, height) <= max_dim:
            return pil_image
        
        scale = max_dim / max(width, height)
        new_w = int(width * scale)
        new_h = int(height * scale)
        return pil_image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    
    def ocr_image(self, pil_image):
        """Core function: Image -. Markdown Text"""
        start_time = time.perf_counter()
        
        # 1.resize
        proccessed_img = self._resize_image(pil_image)
        
        # 2. prepare prompt
        prompt = "Trích xuất toàn bộ nội dung văn bản từ hình ảnh này. Đây là tài liệu tiếng Việt. Giữ nguyên định dạng bullet points và số liệu. Đảm bảo không bỏ sót bất kỳ đoạn văn bản nào.<|vision_start|><|image_pad|><|vision_end|>"
        
        inputs = {
            "prompt": prompt,
            "multi_modal_data": {"image": proccessed_img},
        }
        
        # 3. inference
        outputs = self.llm.generate([inputs], sampling_params = self.sampling_params)
        generated_text = outputs[0].outputs[0].text.strip()
        
        # 4.clean tags
        generated_text = generated_text.replace("<|im_start|>", "").replace("<|im_end|>", "")
        
        elapsed = time.perf_counter() - start_time
        self.logger.info(f"LightOnOCR Inference: {elapsed:.4f}s")
        
        return generated_text
