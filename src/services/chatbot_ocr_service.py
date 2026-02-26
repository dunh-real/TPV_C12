from pathlib import Path
import pypdfium2 as pdfium
from vllm import LLM, SamplingParams

MODEL_NAME = "lightonai/LightOnOCR-2-1B"
INPUT_DIR = None
OUTPUT_DIR = None

class OCRService2:
    def __init__(self, model_name = MODEL_NAME):
        self.llm = LLM(
            model = model_name,
            trust_remote_code = True,
            dtype = "bfloat16",
            limit_mm_per_prompt = {"image": 1},
            mm_processor_cache_gb = 0,
            enable_prefix_caching = False,
            gpu_memory_utilization = 0.25,
            enforce_eager = True
        )
        
        self.sampling_params = SamplingParams(
            temperature = 0.2,
            top_p = 0.9,
            max_tokens = 4096
        )
    
    def process_file(self, file_path):
        file_path = Path(file_path)
        output_path = Path(OUTPUT_DIR) / (file_path.stem + ".md")
        
        # create output folder if not exist
        output_path.parent.mkdir(parents = True, exist_ok = True)
        
        try:
            pdf = pdfium.PdfDocument(file_path)
            num_pages = len(pdf)
            
            full_text = f"# OCR Results: {file_path.name}\n\n"
            
            # prepare input lists for vllm batch processing
            # process one page per time to avoid OOM
            for i in range(num_pages):
                print(f"    - Page {i+1}/{num_pages}...", end = " ", flush = True)
                
                # render page to image
                page = pdf[i]
                pil_image = page.render(scale = 2.77).to_pil()
                
                # create message format for vllm
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {"type": "image", "image": pil_image},
                            {"type": "text", "text": "Extract all text from this document and convert to markdown format."}
                        ]
                    }
                ]
                
                # call vllm
                outputs = self.llm.chat(
                    messages = messages,
                    sampling_params = self.sampling_params,
                    use_tqdm = False
                )
                
                # get results
                generated_text = outputs[0].outputs[0].text
                
                # append to full text
                full_text += f"## Page {i+1}\n\n{generated_text}\n\n---\n\n"
                
                # free memory
                pil_image.close()
                page.close()
            
            # write to output file
            with open(output_path, "w", encoding = "utf-8") as f:
                f.write(full_text)
            
        except Exception as e:
            print(f"\n[Error] Failed to process {file_path.name}: {e}")
        finally:
            if 'pdf' in locals():
                pdf.close()