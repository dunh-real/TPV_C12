import fitz

"""
PDF to IMG Service
PDF file -> Convert to IMG (first page and last page) -> Save in folder data/images
"""

def PDF2IMG(PDF_PATH, IMAGE_DIR_PATH, first_idx_page, last_idx_page):
    doc = fitz.open(PDF_PATH)
    
    # Convert first page and last page to IMG
    first_page = doc.load_page(first_idx_page)
    last_page = doc.load_page(last_idx_page)

    first_pix = first_page.get_pixmap(dpi = 200)
    last_pix = last_page.get_pixmap(dpi = 200)
    
    # Save IMG 
    first_pix.save(f"{IMAGE_DIR_PATH}/{first_idx_page}.png")
    last_pix.save(f"{IMAGE_DIR_PATH}/{last_idx_page}.png")
    
    doc.close()