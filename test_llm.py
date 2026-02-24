import ollama
import time

model_name = 'qwen2.5:latest'

start = time.perf_counter()
response = ollama.chat(
    model=model_name,
    messages=[{'role': 'user', 'content': 'Xin chào, bạn có thể giải thích cho tôi về cấu trúc, xuất xứ, lịch sử hình thành, và công dụng của U-net không?'}])
print(response['message']['content'])
end = time.perf_counter()
print(f"Time taken: {end - start:.2f} seconds")
