# import pytesseract
# from PIL import Image
# import time

# def extract_text_from_image(image_path):
#     try:
#         img = Image.open(image_path)
#         text = pytesseract.image_to_string(img)
#         return text
    
#     except Exception as e:
#         print(f"Vl con vo code yeu tay the :))")
#         return str(e)

# img_path = "./data/images/page_1.png"
# start_time = time.perf_counter()
# extracted_text = extract_text_from_image(img_path)
# end_time = time.perf_counter()
# ex_time = end_time - start_time
# print("Extracted text:\n", extracted_text)
# print(f"Executed time: {ex_time:.4f} seconds")
import json

a = "##Item1"