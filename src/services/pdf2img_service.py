import fitz

pdf_path = "../../data/raw/QĐ 8327-QĐ-BCA-H01 30-10-19 phê duyệt chủ trương đầu tư 53r4534.pdf"
IMAGE_PATH = "../../data/images"

doc = fitz.open(pdf_path)
print(doc.page_count)
print(type(doc.page_count))

first_page = doc.load_page(0)
last_page = doc.load_page(doc.page_count - 1)

first_pix = first_page.get_pixmap(dpi = 200)
last_pix = last_page.get_pixmap(dpi = 200)

first_pix.save(f"{IMAGE_PATH}/first_page.png")
last_pix.save(f"{IMAGE_PATH}/last_page.png")
doc.close()