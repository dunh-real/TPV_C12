import ollama
import time

model_name = 'gemma:2b'

start = time.perf_counter()
response = ollama.chat(
    model=model_name,
    messages=[{'role': 'user', 'content': 'Xin chào, bạn có thể giải thích cho tôi về cấu trúc, xuất xứ, lịch sử hình thành, và công dụng của U-net không?'}])
print(response['message']['content'])
end = time.perf_counter()
print(f"Time taken: {end - start:.2f} seconds")

# from transformers import AutoTokenizer, AutoModelForCausalLM
# import torch

# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# tokenizer = AutoTokenizer.from_pretrained("vinai/PhoGPT-4B-Chat", trust_remote_code = True)
# model = AutoModelForCausalLM.from_pretrained("vinai/PhoGPT-4B-Chat", trust_remote_code = True).to(device)
# messages = [
#     {'role': 'user', 'content': 'Xin chào, bạn có thể giải thích cho tôi về cấu trúc, xuất xứ, lịch sử hình thành, và công dụng của U-net không?'},
# ]
# inputs = tokenizer.apply_chat_template(
#     messages,
#     add_generation_prompt = True,
#     tokenize = True,
#     return_dict = True,
#     return_tensors = 'pt',
# ).to(model.device)

# outputs = model.generate(**inputs, max_new_tokens = 2040)
# print(tokenizer.decode(outputs[0][inputs['input_ids'].shape[-1]:]))