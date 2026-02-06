import re

def extract_metadata_rules(first_page_text, last_page_text):
    """
    Thay the LLM bang Rule-based Parsing.
    Toc do: < 0.05s
    Do chinh xac: cao hon 1B vi tuan thu luat cung
    """
    
    metadata = {
        "ten_don_vi": None,
        "so_quyet_dinh": None,
        "ten_van_ban": None,
        "chuc_vu": None,
        "nguoi_ky": None
    }
    
    # --- 1. Xu ly trang dau (Header info) ---
    lines_p1 = [line.strip() for line in first_page_text.split("\n") if line.strip()]
    
    # A. Ten don vi (goc trai tren cung)
    # Lay dong thu 2 (bo qua dong 1 thuong la ten co quan chu quan cap cao)
    # Vi du: BO CONG AN -> CUC CANH SAT... (Lay Cuc Canh Sat)
    if len(lines_p1) > 1:
        # tim cac dong viet hoa o dau van ban (truoc khi den phan so hieu)
        for i in range(min(5, len(lines_p1))):
            if "số:" in lines_p1[i].lower() or "số" in lines_p1[i].lower():
                break
            # uu tien dong thu 2 neu dong 1 ngan
            if i == 1:
                metadata["ten_don_vi"] = lines_p1[i]
        if not metadata["ten_don_vi"] and lines_p1:
            metadata["ten_don_vi"] = lines_p1[0]
    
    # B. So quyet dinh
    # Regex bat: So: 123/Qd-BCA hoac So 123/TTr...
    match_so = re.search(r"(Số|Số QĐ|Số TTr|Số BC)\s*[:\.]?\s*([^\n]+)", first_page_text, re.IGNORECASE)
    if match_so:
        metadata["so_quyet_dinh"] = match_so.group(2).strip()
        
    # C. Ten van ban
    # tim keyword loai van ban
    doc_types = ["QUYẾT ĐỊNH", "TỜ TRÌNH", "THÔNG TƯ", "NGHỊ ĐỊNH", "KẾ HOẠCH", "BÁO CÁO"]
    start_idx = -1
    
    for idx, line in enumerate(lines_p1):
        upper_line = line.upper()
        # neu dong bat dau bang loai van ban
        for dt in doc_types:
            if upper_line.startswith(dt):
                start_idx = idx
                break
        if start_idx != -1:
            break
    
    if start_idx != -1:
        # gom tat ca dong tu start_idx cho den khi gap tu khoa dung
        content_lines = []
        stop_keywords = ["căn cứ", "kính gửi", "bộ trưởng", "điều 1", "xét đề nghị"]
        
        for i in range(start_idx, len(lines_p1)):
            line_val = lines_p1[i]
            if any(k in line_val.lower() for k in stop_keywords):
                break
            content_lines.append(line_val)
        
        metadata["ten_van_ban"] = " ".join(content_lines).strip()
    
    # --- 2. Xu ly trang cuoi (Signature Info) ---
    # cat bo phan "SAO Y BAN CHINH" neu co
    if "SAO Y BẢN CHÍNH" in last_page_text:
        last_page_text = last_page_text.split("SAO Y BẢN CHÍNH")[0]
    
    lines_p2 = [line.strip() for line in last_page_text.split("\n") if line.strip()]
    
    # tim vung chu ky: Thuong nam tren "Noi nhan"
    noi_nhan_idx = -1
    for i in range(len(lines_p2) -1, -1, -1):
        if "nơi nhận" in lines_p2[i].lower() or "nội nhận" in lines_p2[i].lower():
            noi_nhan_idx = i
            break
    
    if noi_nhan_idx != -1:
        # vung chu ky la khoang 10 dong phia tren "Noi nhan"
        # Nhung phai duoi dong dia diem ngay thang (Ha Noi, ngay ...)
        sig_block = lines_p2[max(0, noi_nhan_idx - 10) : noi_nhan_idx]
    else:
        sig_block = lines_p2[-10:] # fallback lay 10 dong cuoi
    
    # logic xu ly KT, TM, TL
    raw_title = ""
    signer_name = ""
    
    # tim nguoi ky (dong viet hoa, ten rieng o cuoi block)
    # thuong ten nguoi ky la dong cuoi cung hoac gan cuoi viet hoa toan bo
    for line in reversed(sig_block):
        if len(line) > 3 and line.isupper() and len(line.split()) >= 2:
            # loai tru cac tu khoa chuc vu neu co bi lan vao
            keywords = ["TRƯỞNG", "GIÁM ĐỐC", "CHỦ TỊCH", "KÝ", "THAY", "MẶT"]
            if not any(k in line for k in keywords):
                signer_name = line
                break
    
    # tim chuc vu (dong chua KT., TM., TL., hoac chuc danh)
    # quet tu tren xuong trong block chu ky
    clean_title = ""
    for line in sig_block:
        line_upper = line.upper()
        if "KT." in line_upper or "TM." in line_upper or "TL." in line_upper or "QUYỀN" in line_upper:
            # case A: KT. BO TRUONG (dong nay la chuc vu boss)
            # can xem dong ke tiep co phai la chuc vu nguoi ky khong (THU TRUONG)
            current_idx = sig_block.index(line)
            if current_idx + 1 < len(sig_block):
                next_line = sig_block[current_idx + 1]
                # neu dong tiep theo viet hoa va khong phai ten nguoi ky -> no la chuc danh
                if next_line.isupper() and next_line != signer_name:
                    clean_title = next_line
                else:
                    # neu khong, lay chuc vu sau chu KT. (VD: KT. CHU TICH)
                    clean_title = line
            else:
                clean_title = line
            break
        elif any(k in line_upper for k in ["TRƯỞNG", "GIÁM ĐỐC", "CHỦ TỊCH"]):
            if not clean_title:
                clean_title = line
    
    # cleanup chuc vu
    # xu ly: "KT. BO TRUONG" -> Bo qua
    if clean_title:
        metadata["chuc_vu"] = clean_title.title()
    
    if signer_name:
        metadata["nguoi_ky"] = signer_name.title()
    
    return metadata