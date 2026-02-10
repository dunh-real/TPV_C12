import json

"""Prompt Service: Build list prompt for document type"""

context = ""
result_json = {}

CHU_TRUONG_PROMPT = """
#ROLE: Bạn là một chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam. Nhiệm vụ của bạn là hoàn thiện một cấu trúc JSON dựa trên văn bản <context> được cung cấp.
JSON INPUT bao gồm các trường thông tin sau:
    FIELDS:
        - so_quyet_dinh: Doc number (after "Số:", "Số QĐ:", "Số TTr:", "Số BC:").
        - ngay_quyet_dinh: Date (dd/MM/yyyy). Keep original format if unsure.
        - ten_du_an: Full project name. KEEP prefix "Dự án", "Công trình", "Tên dự án" if present. Extract EXACTLY as written (e.g. "Dự án: Cầu A" -> "Dự án: Cầu A"). DO NOT remove prefix.
        - chu_dau_tu: Primary investor. If multiple, pick main one.
        - tong_muc_dau_tu: Total investment. PRIORITY 1: Find explicit "Tổng mức đầu tư:" OR "Tổng cộng:" OR "Cộng:" OR "TMĐT:" line. PRIORITY 2: Sum components if needed. WARNING: CALCULATE SLOWLY AND PRECISELY digit-by-digit. FORMAT: INTEGER ONLY string (VNĐ). Handle all units: "trăm nghìn tỷ"->x10^15,"chục nghìn tỷ"->x10^14,"nghìn tỷ"->x10^12, "trăm tỷ" ->x10^11, "chục tỷ" ->x10^10, "tỷ"->x10^9,"trăm triệu"->x10^8,"chục triệu"->x10^7, "triệu"->x10^6, "trăm nghìn"->x10^5,"chục nghìn"->x10^4, "nghìn"->x10^3, "trăm"->x100, "chục"->x10. REMOVE dots/commas/text. Ex: "401 tỷ" -> "401000000000".
        - muc_tieu_du_an: Goals/objectives text.
        - quy_mo_dau_tu: Scale/scope text. Preserve units.
        - thoi_gian_thuc_hien: Duration/timeline info.
        - thoi_gian_khoi_cong: Start date/time. If explicit start missing, extract from thoi_gian_thuc_hien (e.g., "Quý III, IV/2019" -> "Quý III/2019"; "từ X đến Y" -> X).
        - thoi_gian_hoan_thanh: Completion date/time. If explicit end missing, extract from thoi_gian_thuc_hien (e.g., "Quý III, IV/2019" -> "Quý IV/2019"; "từ X đến Y" -> Y).
        - thanh_phan_nguon_von: List [{{"stt": "1", "nguon_von": "", "gia_tri": ""}}].
        CRITICAL: ALWAYS create at least 1 entry. NEVER return empty array [].

#RULE: 
    1. **DUY TRÌ TÍNH NHẤT QUÁN**: Đối với mỗi cặp Key-Value trong JSON input:
    - Nếu Value **KHÔNG PHẢI null**: Tuyệt đối giữ nguyên giá trị cũ. Không được tìm kiếm, không được thay thế, không được suy luận lại thông tin này. Hãy coi đó là "Hằng số" (Constant).
    - Nếu Value **LÀ null**: Chỉ khi đó bạn mới được phép đọc <context> để tìm thông tin điền vào.
    2. **Nguyên tắc "TÌM THẤY LÀ DỪNG"**: 
    - Một khi đã trích xuất được giá trị hợp lệ cho một trường null, hãy chuyển sang trường null tiếp theo ngay lập tức.
    - Không thực hiện các bước kiểm tra chéo dư thừa giữa các trường đã có dữ liệu.
  
EXTRACTION ALGORITHM (Step-by-step):  
    STEP 1 - LOCATE FUNDING SOURCE:
    - Search for numbered item "8." or "9." near end of document
    - Look for keywords: "Nguồn vốn đầu tư" OR "Nguồn vốn" OR "Nguồn kinh phí"
    - Example patterns:
        * "8. Nguồn vốn đầu tư: Ngân sách UBND TP Hà Nội bổ sung năm 2019"
        * "9. Nguồn vốn: Ngân sách nhà nước"
    
    STEP 2 - NORMALIZE nguon_von (scan ENTIRE funding line for keywords):
    - If contains "Ngân sách"/"NSNN"/"Nhà nước"/"UBND"/"Ủy ban nhân dân"/"Trung ương"/"Địa phương" → "Vốn trong nước"
    - If contains "ODA"/"Vay ODA"/"Hỗ trợ phát triển" → "VỐN ODA"
    - If contains "PPP"/"Đối tác công tư" → "VỐN PPP"
    - If no keywords found → "Vốn khác"
    
    STEP 3 - EXTRACT gia_tri:
    - ALWAYS use tong_muc_dau_tu value (already extracted above)
    - FORMAT: INTEGER ONLY string (same format as tong_muc_dau_tu)
    - If ONLY 1 source (99% of cases) → gia_tri = tong_muc_dau_tu
    - If MULTIPLE sources with individual amounts → extract each amount
    
    STEP 4 - BUILD ARRAY:
    - ALWAYS create array with at least 1 entry
    - Set stt = "1" for first entry
    - If multiple sources, increment stt: "1", "2", "3"...
  
    EXAMPLES:
        Example 1:
            Text: "7. Giá trị tổng mức đầu tư: 2.809.035.000 đồng"
                    "8. Nguồn vốn đầu tư: Ngân sách UBND TP Hà Nội bổ sung năm 2019"
            Output: [{{"stt": "1", "nguon_von": "Vốn trong nước", "gia_tri": "2809035000"}}]
        
        Example 2:
            Text: "Tổng mức đầu tư: 500 tỷ"
                    "Nguồn vốn: Ngân sách nhà nước"
            Output: [{{"stt": "1", "nguon_von": "Vốn trong nước", "gia_tri": "500000000000"}}]
        
        Example 3:
            Text: "Tổng mức: 1 tỷ"
                    "Nguồn vốn: - Ngân sách TW: 600 triệu"
                    "           - Ngân sách địa phương: 400 triệu"
            Output: [{{"stt": "1", "nguon_von": "Vốn trong nước", "gia_tri": "600000000"}},
                    {{"stt": "2", "nguon_von": "Vốn trong nước", "gia_tri": "400000000"}}]
        
        Example 4 (No explicit source):
            Text: "Tổng mức: 2 tỷ" (no funding source mentioned)
            Output: [{{"stt": "1", "nguon_von": "Vốn khác", "gia_tri": "2000000000"}}]
        
#OUTPUT FORMAT:
    - Chỉ trả về duy nhất định dạng JSON. BẮT BUỘC tuân theo định dạng đầu vào của JSON. TUYỆT ĐỐI không thay đổi trên trường (key) trong JSON.
    - Nếu tìm thấy VALUE của một KEY, hãy thay thế giá trị 'null' bằng thông tin vừa được trích xuất.
    - Nếu không tìm thấy VALUE, CẦN GIỮ NGUYÊN GIÁ TRỊ 'null', KHÔNG TỰ Ý BỊA RA KẾT QUẢ.
    - Không thêm bất kỳ lời dẫn hay lời giải thích nào.
  
CONTEXT:
{context}

JSON INPUT:
{json_template}

"""


KE_HOACH_LCNT_PROMPT = """
#ROLE: Bạn là một chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam. Nhiệm vụ của bạn là hoàn thiện một cấu trúc JSON dựa trên văn bản <context> được cung cấp.
JSON INPUT bao gồm các trường thông tin sau:
    FIELDS:
        - so_quyet_dinh: Doc number (top left).
        - ngay_ky: Date (top right).
        - du_an: Project name. KEEP prefix "Dự án", "Công trình". Extract EXACTLY as written. DO NOT remove prefix.
        - giai_doan: Phase/scope. Example: "giai_doan: giai đoạn chuẩn bị đầu tư" or further
        - ten_ke_hoach_vn: Extract string starting "Kế hoạch lựa chọn nhà thầu..." including project name lines. Stop before "Phê duyệt"/"Quyết định". CLEAN HTML/Tags. Merge to single string.
        - ten_ke_hoach_en: English plan name (null if missing).
        
#RULE: 
    1. **DUY TRÌ TÍNH NHẤT QUÁN**: Đối với mỗi cặp Key-Value trong JSON input:
    - Nếu Value **KHÔNG PHẢI null**: Tuyệt đối giữ nguyên giá trị cũ. Không được tìm kiếm, không được thay thế, không được suy luận lại thông tin này. Hãy coi đó là "Hằng số" (Constant).
    - Nếu Value **LÀ null**: Chỉ khi đó bạn mới được phép đọc <context> để tìm thông tin điền vào.
    2. **Nguyên tắc "TÌM THẤY LÀ DỪNG"**: 
    - Một khi đã trích xuất được giá trị hợp lệ cho một trường null, hãy chuyển sang trường null tiếp theo ngay lập tức.
    - Không thực hiện các bước kiểm tra chéo dư thừa giữa các trường đã có dữ liệu.

**SIGNATURE EXTRACTION (ULTRA-STRICT LINE-BY-LINE ALGORITHM)**

    nguoi_ky: Signer's name.
    **STRICT EXTRACTION RULES**:
    1. **Location**: Go to LAST 15 lines of document
    2. **Marker**: Find "Nơi nhận:" → Signature block is ABOVE this line
    3. **Search Area**: Scan lines ABOVE "Nơi nhận:" and BELOW title line
    4. **Pattern**: Look for full name (2-4 words, proper noun capitalization)
        - Format 1: "Rank + Full Name" (e.g., "Thiếu tá Nguyễn Hải Sơn")
        - Format 2: "Full Name" (e.g., "Nguyễn Văn Hùng")
    5. **Position**: Name appears 1-3 lines BELOW chuc_vu line
    6. **Validation**: Name is typically the LAST proper noun before "Nơi nhận:"
    
    **EXCLUDE** (False Positives):
    ❌ Names in "Kính gửi:" section (document top)
    ❌ Names in "Nơi nhận:" distribution list
    ❌ Names appearing BEFORE the title/position line

    chuc_vu: Signer's title.
    **CRITICAL RULE FOR KT/TM/TL**:
    
    **KT/TM/TL Meaning**:
    - "KT." = "Ký thay" - Shows BOSS's title, NOT signer's
    - "TM." = "Thay mặt" - On behalf of
    - "TL." = "Thừa lệnh" - By order of
    
    **Extraction Algorithm**:
    
    1. Find "Nơi nhận:" in last 15 lines
    2. Scan signature block ABOVE "Nơi nhận:"
    
    3. **IF line contains "KT." or "TM." or "TL."**:
        
        **CASE A - Same block (separated by <br/>)**:
        If format is: "KT. [BOSS_TITLE]<br/>[ACTUAL_TITLE]"
        - Example: "KT. BỘ TRƯỞNG<br/>CHỦ TRƯỞNG"
        - Example 2: "KT. BỘ TRƯỞNG<br/>THỨ TRƯỞNG"
        - Take the SECOND title after <br/> ("CHỦ TRƯỞNG")
        - This is the actual signer's title
        
        **CASE B - Separate lines**:
        If format is two separate lines:
        ```
        Line 1: KT. VIỆN TRƯỞNG
        Line 2: PHÓ VIỆN TRƯỞNG
        ```
        - Skip Line 1 (has KT)
        - Take Line 2 (actual signer's title)
    
    4. **IF no KT/TM/TL**: Take first line with position keyword
    
    5. Clean: Keep only position keyword (remove agency)
    6. Normalize to Title Case
    
    **Examples**:
    ```
    "KT. BỘ TRƯỞNG<br/>CHỦ TRƯỞNG"     → "Chủ trưởng"
    "KT. VIỆN TRƯỞNG<br/>PHÓ VIỆN TRƯỞNG" → "Phó Viện trưởng"
    "VIỆN TRƯỞNG" (no KT)                  → "Viện trưởng"
    ```
    
    Position keywords: CHỦ TRƯỞNG, PHÓ VIỆN TRƯỞNG, VIỆN TRƯỞNG, PHÓ GIÁM ĐỐC, GIÁM ĐỐC, PHÓ TRƯỞNG PHÒNG, TRƯỞNG PHÒNG, CHỦ TỊCH, BỘ TRƯỞNG, THỨ TRƯỞNG, etc.

    co_quan_ban_hanh: Issuing agency (top left). IGNORE first line. Take from 2nd line down. MERGE lines. REMOVE HTML tags.
    
#OUTPUT FORMAT:
    - Chỉ trả về duy nhất định dạng JSON. BẮT BUỘC tuân theo định dạng đầu vào của JSON. TUYỆT ĐỐI không thay đổi trên trường (key) trong JSON.
    - Nếu tìm thấy thông tin của một trường, hãy thay thế giá trị 'null' bằng thông tin vừa được trích xuất.
    - Nếu không tìm thấy thông tin, CẦN GIỮ NGUYÊN GIÁ TRỊ 'null', KHÔNG TỰ Ý BỊA RA KẾT QUẢ.
    - Không thêm bất kỳ lời dẫn hay lời giải thích nào.

CONTEXT:
{context}

JSON INPUT:
{json_template}

"""


THONG_TIN_DU_AN_PROMPT = """
#ROLE: Bạn là một chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam. Nhiệm vụ của bạn là hoàn thiện một cấu trúc JSON dựa trên văn bản <context> được cung cấp.
JSON INPUT bao gồm các trường thông tin sau:
    FIELDS:
        - so_quyet_dinh: Document number.
        - ngay_quyet_dinh: Date.
        - ma_du_an: Project code.
        - ten_du_an: Full name. KEEP prefix "Dự án", "Công trình" if present. Extract EXACTLY as written. DO NOT remove prefix.
        - chu_dau_tu: Primary investor only. If multiple, pick main one.
        - chu_truong_dau_tu: Investment policy name.
        - trang_thai_du_an: Implementation status.
        - trang_thai_thanh_tra: Inspection status.
        - trang_thai_kiem_toan: Audit status.
        - nhom_du_an: Project group (from "Nhóm:").
        - linh_vuc: Sector/field.
        - don_vi_xu_ly_quyet_toan: Settlement unit.
        - loai_cong_trinh: Type of construction. Look for "Hình thức đầu tư:" section.
        - cap_cong_trinh: Grade/level.
        - hinh_thuc_quan_ly: Management method. Look for "Hình thức ", "Quản lý ", "Quản lý dự án "  section
        - thoi_gian_thuc_hien: Start info. If explicit start missing, extract from duration strings (e.g. "from X to Y" -> X).
        - thoi_gian_ket_thuc: End info. If explicit end missing, extract from duration strings (e.g. "from X to Y" -> Y).
        - dia_diem_trien_khai: List locations [{{"stt": "", "tinh_thanh_pho": "", "phuong_xa": "", "dia_chi_chi_tiet": ""}}]. Split address string smart.
        - thanh_phan_khoan_muc: List major costs [{{"stt": "", "thanh_phan": "", "gia_tri": ""}}]
        
#RULE: 
    1. **DUY TRÌ TÍNH NHẤT QUÁN**: Đối với mỗi cặp Key-Value trong JSON input:
    - Nếu Value **KHÔNG PHẢI null**: Tuyệt đối giữ nguyên giá trị cũ. Không được tìm kiếm, không được thay thế, không được suy luận lại thông tin này. Hãy coi đó là "Hằng số" (Constant).
    - Nếu Value **LÀ null**: Chỉ khi đó bạn mới được phép đọc <context> để tìm thông tin điền vào.
    2. **Nguyên tắc "TÌM THẤY LÀ DỪNG"**: 
    - Một khi đã trích xuất được giá trị hợp lệ cho một trường null, hãy chuyển sang trường null tiếp theo ngay lập tức.
    - Không thực hiện các bước kiểm tra chéo dư thừa giữa các trường đã có dữ liệu.

**CRITICAL: MANDATORY ABBREVIATION REQUIREMENT**

**THE #1 RULE**: ONLY extract rows that have abbreviation in parentheses like (Gxd), (G_XD), (Gtb), etc.
**IF NO ABBREVIATION → SKIP THE ROW (even if it looks like a major item)**

EXTRACTION SCOPE:
- Target "Tổng mức đầu tư" or "Dự toán" section
- GOAL: Extract ONLY Major Cost Items with abbreviations

**STEP 1 - IDENTIFY MAJOR ITEM ROWS (STRICT CRITERIA)**:

**MANDATORY PATTERN**: Row MUST have abbreviation in format "(G...)" or "(g...)"

**Valid Abbreviation Patterns**:
- (Gxd), (G_XD), (GXD) → Chi phí xây dựng
- (Gtb), (G_TB), (GTB) → Chi phí thiết bị
- (Gqlda), (G_QLDA), (GQLDA) → Chi phí quản lý dự án
- (Gtv), (G_TV), (GTV) → Chi phí tư vấn
- (Gdp), (G_DP), (GDP) → Chi phí dự phòng
- (Gk), (G_K), (GK) → Chi phí khác
- (Gbttc), (G_BTTC) → Chi phí bồi thường giải phóng mặt bằng

**Recognition Algorithm**:
1. Scan "Nội dung" column for text containing "(G" or "(g"
2. Verify it ends with ")"
3. If pattern matches → This is a MAJOR ITEM
4. If pattern NOT found → SKIP this row entirely

**STEP 2 - STT VALIDATION (Additional Check)**:

Major items typically have simple STT:
- Roman numerals: I, II, III, IV, V, VI, VII
- Single letters: a, b, c, d, e, f, g, h
- Simple numbers: 1, 2, 3, 4, 5 (WITHOUT decimals)

**FORBIDDEN STT patterns** (these are sub-items):
❌ 1.1, 1.2, 2.1, 2.2 → Sub-indexed items
❌ a.1, a.2, b.1 → Sub-indexed items
❌ "-" or "+" prefix → Detail items
❌ i, ii, iii (lowercase Roman) → Usually sub-items

**STEP 3 - EXCLUSION CRITERIA (CRITICAL - Always Skip)**:

❌ **SKIP if "Nội dung" does NOT contain abbreviation in parentheses**
   Examples of rows to SKIP (no abbreviation):
   - "Cọc khoan nhồi"
   - "Phá dỡ"
   - "San lấp mặt bằng"
   - "Móng, cột, dầm"
   - "Hạng mục chung"
   - "Chi phí lán trại"
   - "Công tác chuẩn bị"

❌ **SKIP if "Diễn giải" contains formulas** (even if they mention G_XD):
   - "1%*G_XD"
   - "2.5%*G_XD"
   - "10% chi phí xây dựng"
   
❌ **SKIP if STT has decimal/sub-index**:
   - STT = "1.1" → SKIP
   - STT = "2.3" → SKIP
   - STT = "a.1" → SKIP

❌ **SKIP if row is indented or has "-" prefix**

**STEP 4 - VALUE EXTRACTION (SAME-ROW ONLY)**:

**MANDATORY RULE**: Value MUST come from the SAME ROW as the abbreviation

1. Find row with abbreviation in "Nội dung"
2. Remember this row's STT: [ROW_STT]
3. Extract value from VALUE column of row [ROW_STT] ONLY
4. ❌ DO NOT extract from row [ROW_STT + 1] or [ROW_STT - 1]
5. If value cell is empty on the abbreviation row → Skip this item entirely

**Column Priority** (for value extraction):
1. "Giá trị sau thuế"
2. "Giá trị"
3. "Thành tiền"
4. "Tổng cộng"

**EXAMPLE TABLE - What to Extract vs. Skip**:

```
| STT | Nội dung                          | Diễn giải | Giá trị       |
|-----|-----------------------------------|-----------|---------------|
| I   | CHI PHÍ XÂY DỰNG (G_XD)          |           | 2.494.526.468 | ← EXTRACT ✓
| 1   | Cải tạo sân                       |           | 1.482.500.500 | ← SKIP (no abbr)
| 1.1 | Phá dỡ                            |           |   100.000.000 | ← SKIP (sub-index)
| 1.2 | San lấp                           |           |   150.000.000 | ← SKIP (sub-index)
| 2   | Cải tạo vệ sinh                   |           |   303.805.183 | ← SKIP (no abbr)
| II  | CHI PHÍ THIẾT BỊ (G_TB)          |           |   500.000.000 | ← EXTRACT ✓
| a   | Máy móc                           |           |   300.000.000 | ← SKIP (no abbr)
| b   | Công cụ                           |           |   200.000.000 | ← SKIP (no abbr)
| III | Chi phí tư vấn (Gtv)              |           |   227.200.394 | ← EXTRACT ✓
| IV  | Chi phí khác (Gk)                 |           |    87.308.425 | ← EXTRACT ✓
| V   | Chi phí dự phòng (Gdp)            |           |    45.005.614 | ← EXTRACT ✓
|     | - Dự phòng phí                    | 1%*G_XD   |       525.511 | ← SKIP (no STT + formula)
|     | - Dự phòng vật tư                 |           |       480.000 | ← SKIP (no STT)
```

**Expected Extraction Result**:
```json
[
  {{"stt": "1", "thanh_phan": "CHI PHÍ XÂY DỰNG", "gia_tri": "2494526468"}},
  {{"stt": "2", "thanh_phan": "CHI PHÍ THIẾT BỊ", "gia_tri": "500000000"}},
  {{"stt": "3", "thanh_phan": "Chi phí tư vấn", "gia_tri": "227200394"}},
  {{"stt": "4", "thanh_phan": "Chi phí khác", "gia_tri": "87308425"}},
  {{"stt": "5", "thanh_phan": "Chi phí dự phòng", "gia_tri": "45005614"}}
]
```

**STEP 5 - NAME NORMALIZATION**:

After extraction, clean the name:
1. Remove abbreviation suffix: "CHI PHÍ XÂY DỰNG (G_XD)" → "CHI PHÍ XÂY DỰNG"
2. Keep original case (uppercase or Title Case as written)
3. Trim whitespace

**STEP 6 - FINAL VALIDATION CHECKLIST**:

Before adding an item to the list, verify:
✓ "Nội dung" contains abbreviation in parentheses (Gxd), (G_XD), etc.?
✓ STT is simple (Roman numeral or single letter), NOT sub-indexed?
✓ Value extracted from SAME row as abbreviation?
✓ Value is not empty/zero?
✓ Row is NOT indented or sub-item?

If ANY check fails → DO NOT add this item

**CRITICAL REMINDERS**:
❌ NEVER extract rows without abbreviations
❌ NEVER extract from sub-indexed rows (1.1, 2.1, a.1)
❌ NEVER extract from rows with formulas in "Diễn giải"
❌ NEVER extract from rows with "-" prefix
❌ NEVER take value from a different row than the abbreviation row

**When in doubt → SKIP the row (better to miss an item than extract wrong data)**

FORMAT: INTEGER ONLY (remove dots, commas, currency symbols)
        - Only extract a value if the SAME row contains the major-item keyword + its abbreviation token:
          "Chi phí dự phòng" + ("(Gdp)" / "(G_DP)" / "Gdp" / "G_DP").
        - Never take a number from rows above/below that do not contain "Chi phí dự phòng" (or the abbreviation).
     3. **Wrapped-row handling**:
        - If the number is wrapped to the next line due to OCR, it MUST be the immediate next line and MUST look like a continuation (no leading "-", no sub-index like "6.1", no new item name).
     4. **If multiple numbers are captured for the same major row due to OCR noise**:
        - Choose the **LARGEST** number that belongs to the "Chi phí dự phòng" row.
     5. **Final sanity check**:
        - "Chi phí dự phòng (Gdp)" is a category total, so it should not be smaller than small administrative/fee sub-items nearby. If you extracted a tiny value AND a larger value exists on the same "Chi phí dự phòng" row, pick the larger one.

   **STEP 4.2: LAST-ROW-GUARD (CRITICAL - Enhanced for Last Major Item)**:
   - **SPECIFIC PROBLEM**: The LAST major item before "TỔNG MỨC ĐẦU TƯ" is highly prone to extraction errors.
   
   - **COMMON ERROR PATTERN**:
     ```
     | g | Chi phí dự phòng (Gdp)     |              | 45.005.614   | ← CORRECT (major item)
     |   | - Dự phòng phí             | 1%*G_XD      | 525.511      | ← WRONG (sub-item with formula)
     |   | - Chi phí quản lý          |              | 325.000      | ← WRONG (sub-item)
     | h | TỔNG MỨC ĐẦU TƯ           |              | 4.500.561.400| ← Total
     ```
   
   - **STRICT EXTRACTION FOR LAST MAJOR ITEM**:
     1. **Identify the row**: Must have abbreviation (Gdp) or (G_DP) in "Nội dung" column
     2. **Scan that specific row for ALL numbers**: May contain multiple values due to OCR formatting
     3. **Apply MAX-VALUE heuristic**: If multiple numbers found on the SAME row → Take the LARGEST
     4. **Ignore sub-rows completely**:
        - Any row starting with "-" → SKIP
        - Any row with formula in "Diễn giải" (1%*G_XD, 2%*...) → SKIP
        - Any row with sub-index (g.1, g.2, 6.1) → SKIP
     5. **Magnitude validation**:
        - Last major item should be reasonable (typically 1-20% of TỔNG MỨC ĐẦU TƯ)
        - If extracted value is < 1% of total AND there's a larger value on the abbreviation row → Use the larger value
   
   - **CONCRETE EXAMPLE**:
     ✓ CORRECT: Row "g | Chi phí dự phòng (Gdp) | | 45.005.614" → Extract 45.005.614
     ✗ WRONG: Row "| - Dự phòng phí | 1%*G_XD | 525.511" → SKIP (has "-" prefix + formula)
     ✗ WRONG: Row "| - Chi phí quản lý | | 325.000" → SKIP (has "-" prefix, no abbreviation)

   - Always ensure the last major item before "TỔNG MỨC ĐẦU TƯ / Tổng cộng" is the correct major-row value (not a sub-row fee).

5. NAME NORMALIZATION:
   - Remove abbreviation suffix: "CHI PHÍ XÂY DỰNG (G_XD)" → "CHI PHÍ XÂY DỰNG"
   - Keep UPPERCASE if original is uppercase
   - Trim whitespace and special chars

**EXPECTED OUTPUT STRUCTURE**:
[
  {{"stt": "1", "thanh_phan": "CHI PHÍ XÂY DỰNG", "gia_tri": "2494526468"}},
  {{"stt": "2", "thanh_phan": "Chi phí khác", "gia_tri": "87308425"}},
  {{"stt": "3", "thanh_phan": "CHI PHÍ TƯ VẤN", "gia_tri": "227200394"}}
]

#OUTPUT FORMAT:
    - Chỉ trả về duy nhất định dạng JSON. BẮT BUỘC tuân theo định dạng đầu vào của JSON. TUYỆT ĐỐI không thay đổi trên trường (key) trong JSON.
    - Nếu tìm thấy thông tin của một trường, hãy thay thế giá trị 'null' bằng thông tin vừa được trích xuất.
    - Nếu không tìm thấy thông tin, CẦN GIỮ NGUYÊN GIÁ TRỊ 'null', KHÔNG TỰ Ý BỊA RA KẾT QUẢ.
    - Không thêm bất kỳ lời dẫn hay lời giải thích nào.

CONTEXT:
{context}

JSON INPUT:
{json_template}

"""

QUAN_LY_GOI_THAU_PROMPT = """
#ROLE: Bạn là một chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam. Nhiệm vụ của bạn là hoàn thiện một cấu trúc JSON dựa trên văn bản <context> được cung cấp. 
JSON INPUT bao gồm các trường thông tin sau:
    FIELDS:
        - ma_goi_thau: Bid code ("Mã gói thầu:").
        - ten_goi_thau: Package name. KEEP prefix "Gói thầu", "Gói thầu số". Extract EXACTLY as written. (e.g. "Gói thầu số 01: XL" -> "Gói thầu số 01: XL").
        - du_an: Project name. KEEP prefix. Extract EXACTLY as written. DO NOT remove prefix.
        - ke_hoach_lcnt: Plan number/name.
        - gia_du_toan: FORMAT: INTEGER ONLY string (VNĐ). PRIORITY 1: Find explicit "Dự toán:" OR "Tổng dự toán:" OR "Tổng cộng:" line. PRIORITY 2: Sum if needed. WARNING: CALCULATE SLOWLY AND PRECISELY. Handle all units: "trăm nghìn tỷ"->x10^15,"chục nghìn tỷ"->x10^14,"nghìn tỷ"->x10^12, "trăm tỷ" ->x10^11, "chục tỷ" ->x10^10, "tỷ"->x10^9,"trăm triệu"->x10^8,"chục triệu"->x10^7, "triệu"->x10^6, "trăm nghìn"->x10^5,"chục nghìn"->x10^4, "nghìn"->x10^3, "trăm"->x100, "chục"->x10. REMOVE dots/commas/text. Ex: "401 tỷ" -> "401000000000".
        - gia_goi_thau: FORMAT: INTEGER ONLY string (VNĐ). PRIORITY 1: Find explicit "Giá gói thầu:" OR "Giá:" OR "Tổng cộng:" line. PRIORITY 2: Sum if needed. WARNING: CALCULATE SLOWLY AND PRECISELY. Same units as gia_du_toan.
        - hinh_thuc_lua_chon_nha_thau: Method (e.g. "Đấu thầu rộng rãi").
        - phuong_thuc_lua_chon_nha_thau: Mode (e.g. "1 giai đoạn 1 túi hồ sơ").
        - cach_thuc_thuc_hien_dau_thau: Approach (e.g. "Qua mạng").
        - loai_nguon_von_du_an: Funding source.
        - hinh_thuc_hop_dong: Contract type.
        - linh_vuc_dau_thau: Field (e.g. "Xây lắp").
        - thoi_gian_lua_chon_nha_thau: Selection time.
        - thoi_gian_thuc_hien_hop_dong: Duration.
        
#RULE: 
    1. **DUY TRÌ TÍNH NHẤT QUÁN**: Đối với mỗi cặp Key-Value trong JSON input:
    - Nếu Value **KHÔNG PHẢI null**: Tuyệt đối giữ nguyên giá trị cũ. Không được tìm kiếm, không được thay thế, không được suy luận lại thông tin này. Hãy coi đó là "Hằng số" (Constant).
    - Nếu Value **LÀ null**: Chỉ khi đó bạn mới được phép đọc <context> để tìm thông tin điền vào.
    2. **Nguyên tắc "TÌM THẤY LÀ DỪNG"**: 
    - Một khi đã trích xuất được giá trị hợp lệ cho một trường null, hãy chuyển sang trường null tiếp theo ngay lập tức.
    - Không thực hiện các bước kiểm tra chéo dư thừa giữa các trường đã có dữ liệu.
    
#OUTPUT FORMAT:
    - Chỉ trả về duy nhất định dạng JSON. BẮT BUỘC tuân theo định dạng đầu vào của JSON. TUYỆT ĐỐI không thay đổi trên trường (key) trong JSON.
    - Nếu tìm thấy thông tin của một trường, hãy thay thế giá trị 'null' bằng thông tin vừa được trích xuất.
    - Nếu không tìm thấy thông tin, CẦN GIỮ NGUYÊN GIÁ TRỊ 'null', KHÔNG TỰ Ý BỊA RA KẾT QUẢ.
    - Không thêm bất kỳ lời dẫn hay lời giải thích nào.

CONTEXT:
{context}

JSON INPUT:
{json_template}

"""

HOP_DONG_PROMPT = """
#ROLE: Bạn là một chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam. Nhiệm vụ của bạn là hoàn thiện một cấu trúc JSON dựa trên văn bản <context> được cung cấp.
JSON INPUT bao gồm các trường thông tin sau:
    FIELDS:
        - so_hop_dong: Contract number. Look for "Số:", "No.", "Hợp đồng số:" in header or first paragraph.
        - ngay_ky_hop_dong: Date signed. Look for "ngày ... tháng ... năm ..." in preamble (e.g. "Hà Nội, ngày 18 tháng 09 năm 2019") or signature block. Format: dd/mm/yyyy.
        - du_an: Project name. KEEP prefix. Extract EXACTLY as written. DO NOT remove prefix.
        - goi_thau: Package name. KEEP prefix. Extract EXACTLY as written.
        - ten_hop_dong: Contract name (e.g. "Hợp đồng thi công...", "Hợp đồng tư vấn...").
            PARTIES EXTRACTION STRATEGY:
            - "Bên A" (or "Bên Giao Thầu", "Chủ đầu tư") -> Investor Info.
            - "Bên B" (or "Bên Nhận Thầu", "Nhà thầu", "Tư vấn") -> Contractor Info.
            - Look in 2 places:
                1. INTRODUCTION section (beginning of doc).
                2. SIGNATURE block (end of doc).

        - dai_dien_chu_dau_tu: Rep Name (Party A).
        - chuc_vu: Rep Title (Party A). PROXY RULE: If line starts with "KT.", "TM.", "TL.", STRICTLY IGNORE it and extract the NEXT LINE as the title. Ex: "TM. UBND..." -> take "CHỦ TỊCH" (from line below).
        - loai_hop_dong: Contract type (e.g. "Trọn gói", "Theo đơn giá cố định", "Theo thời gian"). Look in "Giá trị hợp đồng" or "Hình thức hợp đồng" section.
        - ngay_hieu_luc_tu: Start date (dd/mm/yyyy). If explicit date missing, check "Thời gian thực hiện" (duration) -> Start.
        - ngay_hieu_luc_den: End date (dd/mm/yyyy). If explicit date missing, check "Thời gian thực hiện" (duration) -> End.
        - gia_tri_hop_dong: FORMAT: INTEGER ONLY string (VNĐ). PRIORITY 1: Find explicit "Giá trị hợp đồng:" OR "Tổng giá trị:" OR "Tổng cộng:" line. PRIORITY 2: Sum if needed. WARNING: CALCULATE SLOWLY AND PRECISELY. Handle all units: "trăm nghìn tỷ"->x10^15,"chục nghìn tỷ"->x10^14,"nghìn tỷ"->x10^12, "trăm tỷ" ->x10^11, "chục tỷ" ->x10^10, "tỷ"->x10^9,"trăm triệu"->x10^8,"chục triệu"->x10^7, "triệu"->x10^6, "trăm nghìn"->x10^5,"chục nghìn"->x10^4, "nghìn"->x10^3, "trăm"->x100, "chục"->x10. REMOVE dots/commas/text. Ex: "401 tỷ" -> "401000000000".
        - gia_tri_bao_lanh_bao_hanh: Guarantee value. FORMAT: INTEGER ONLY (same units as gia_tri_hop_dong).
        - gia_tri_vat: VAT value/percent.
        - loai_hop_dong_nha_thau: "Liên doanh" (if "Bên B" lists >=2 distinct companies or mentions "Liên danh"), else "Không liên doanh".
        - danh_sach_nha_thau: Array [{{"stt": "1", "nt_chinh": "true/false", "nha_thau": "Name", "loai_nha_thau": "Tổ chức/Cá nhân", "gia_tri_thuc_hien": "INTEGER ONLY"}}].
            RULES:
            - Find "Đại diện Nhà thầu" or "Bên B" section
            - nha_thau: Extract from "Tên giao dịch:" or company name after "Đại diện Nhà thầu"
            - loai_nha_thau: "Tổ chức" if contains "Công ty"/"TNHH"/"Cổ phần", else "Cá nhân"
            - nt_chinh: "true" for first/only contractor, "false" for others
            - gia_tri_thuc_hien: Use gia_tri_hop_dong if only 1 contractor, else extract individual value
            - If multiple contractors ("Liên danh"), create separate entries
            Example: "Tên giao dịch: Công ty TNHH Kiểm toán APEC" → {{"nha_thau": "Công ty TNHH Kiểm toán APEC", "loai_nha_thau": "Tổ chức"}}
            
#RULE: 
    1. **DUY TRÌ TÍNH NHẤT QUÁN**: Đối với mỗi cặp Key-Value trong JSON input:
    - Nếu Value **KHÔNG PHẢI null**: Tuyệt đối giữ nguyên giá trị cũ. Không được tìm kiếm, không được thay thế, không được suy luận lại thông tin này. Hãy coi đó là "Hằng số" (Constant).
    - Nếu Value **LÀ null**: Chỉ khi đó bạn mới được phép đọc <context> để tìm thông tin điền vào.
    2. **Nguyên tắc "TÌM THẤY LÀ DỪNG"**: 
    - Một khi đã trích xuất được giá trị hợp lệ cho một trường null, hãy chuyển sang trường null tiếp theo ngay lập tức.
    - Không thực hiện các bước kiểm tra chéo dư thừa giữa các trường đã có dữ liệu.
        
#OUTPUT FORMAT:
    - Chỉ trả về duy nhất định dạng JSON. BẮT BUỘC tuân theo định dạng đầu vào của JSON. TUYỆT ĐỐI không thay đổi trên trường (key) trong JSON.
    - Nếu tìm thấy thông tin của một trường, hãy thay thế giá trị 'null' bằng thông tin vừa được trích xuất.
    - Nếu không tìm thấy thông tin, CẦN GIỮ NGUYÊN GIÁ TRỊ 'null', KHÔNG TỰ Ý BỊA RA KẾT QUẢ.
    - Không thêm bất kỳ lời dẫn hay lời giải thích nào.

CONTEXT:
{context}

JSON INPUT:
{json_template}
"""

THANH_TOAN_TAM_UNG_PROMPT = """
#ROLE: Bạn là một chuyên gia trích xuất dữ liệu từ văn bản hành chính Việt Nam. Nhiệm vụ của bạn là hoàn thiện một cấu trúc JSON dựa trên văn bản <context> được cung cấp.
#RULE: 
    1. **DUY TRÌ TÍNH NHẤT QUÁN**: Đối với mỗi cặp Key-Value trong JSON input:
    - Nếu Value **KHÔNG PHẢI null**: Tuyệt đối giữ nguyên giá trị cũ. Không được tìm kiếm, không được thay thế, không được suy luận lại thông tin này. Hãy coi đó là "Hằng số" (Constant).
    - Nếu Value **LÀ null**: Chỉ khi đó bạn mới được phép đọc <context> để tìm thông tin điền vào.
    2. **Nguyên tắc "TÌM THẤY LÀ DỪNG"**: 
    - Một khi đã trích xuất được giá trị hợp lệ cho một trường null, hãy chuyển sang trường null tiếp theo ngay lập tức.
    - Không thực hiện các bước kiểm tra chéo dư thừa giữa các trường đã có dữ liệu.

**CRITICAL: ANTI-SKEW EXTRACTION FOR TILTED/SKEWED PDFs**

This document is a FORM (not a table), with labeled fields like "Dự án:", "Gói thầu:", etc.
When PDFs are tilted, OCR may place text from different lines onto the same line or split single-line text across multiple lines.

**🚨 GLOBAL CRITICAL RULE - SAME-ROW EXTRACTION FOR ALL NUMERIC FIELDS 🚨**

**THE #1 PROBLEM**: When PDFs are skewed, OCR often places numbers from different rows onto the same line, causing the model to extract values from WRONG rows.

**MANDATORY RULE FOR ALL NUMERIC FIELDS**:
- khoi_luong_hoan_thanh
- thu_hoi_tam_ung (von_trong_nuoc, von_ngoai_nuoc)
- thue_gia_tri_gia_tang
- bao_lanh_bao_hanh
- so_tra_don_vi_thu_huong (von_trong_nuoc, von_ngoai_nuoc)
- giu_lai_cho_quyet_toan

**EXTRACTION PROTOCOL**:
1. Find the label/category name (e.g., "Khối lượng hoàn thành")
2. Identify the ROW NUMBER (STT) or LINE NUMBER where this label appears
3. Extract value ONLY from THAT EXACT ROW/LINE
4. ❌ FORBIDDEN: NEVER extract from row [STT + 1] or [STT - 1]
5. ❌ FORBIDDEN: NEVER extract from a different row, even if the value looks correct
6. If the correct row has NO value or EMPTY cell → Return null for that field

**EXAMPLE OF WRONG EXTRACTION (FORBIDDEN)**:
```
Table:
| STT | Nội dung                    | Vốn trong nước | Vốn ngoài nước | Tổng cộng    |
|-----|----------------------------|----------------|----------------|--------------|
| 5   | Bảo lãnh bảo hành          |                |                |              |  ← Row 5 is EMPTY
| 6   | Giữ lại cho quyết toán     | 50.000.000     | 0              | 50.000.000   |  ← Row 6 has value
```

WRONG: Extracting 50.000.000 for "bao_lanh_bao_hanh" from row 6
RIGHT: Return null for "bao_lanh_bao_hanh" because row 5 is empty

**WHY THIS MATTERS**:
- Each category has its OWN row with its OWN value
- Taking a value from a different row means you're extracting the WRONG category's data
- Better to return null than to return wrong data

**VALIDATION CHECKLIST** (Before extracting any number):
✓ I found the label/category name
✓ I identified the exact STT/row number for this category
✓ The number I'm extracting is from THIS row, not adjacent rows
✓ I did NOT skip to the next row to find a value
✓ If the correct row is empty, I returned null

**IF YOU VIOLATE THIS RULE → THE ENTIRE EXTRACTION IS WRONG**

---

**CORE EXTRACTION STRATEGY: LABEL-ANCHORED PAIRING**

STEP 1 - IDENTIFY FIELD LABELS (These are your anchors):
  
  Search the ENTIRE document text for these label patterns (case-insensitive):
  
  - "Dự án:" or "Tên dự án:" → Marks du_an field
  - "Gói thầu:" or "Tên gói thầu:" → Marks goi_thau field  
  - "Số:" followed by numbers (in header) → Marks so_chung_tu field
  - "Hợp đồng số:" or "Căn cứ hợp đồng số:" → Marks hop_dong field
  - "Chủ đầu tư:" or "Đơn vị:" → Marks chu_dau_tu field
  - "Thanh toán" or "Tạm ứng" or "Quyết toán" (in title) → Marks ten_dot_thanh_toan field
  - "Nguồn vốn:" → Marks nguon_von field
  - "Ngày" followed by date pattern → Marks ngay_thanh_toan field
  
  **CRITICAL LABEL RECOGNITION RULES**:
  - Labels typically end with ":" (colon)
  - Labels appear BEFORE their values (in Vietnamese documents)
  - Labels are often bold or uppercase (but not required)
  - A label may span multiple OCR lines if PDF is tilted

STEP 2 - VALUE EXTRACTION USING PROXIMITY PAIRING:
  
  **PROXIMITY-BASED PAIRING ALGORITHM**:
  
  For each field label found:
  1. **Locate the label position** in the OCR text
  2. **Extract value using these rules** (in priority order):
  
     **Rule A - Same Line**: 
     - Look for text IMMEDIATELY AFTER the label on the same OCR line
     - Extract everything between the label and the next label (or end of line)
     - Example: "Dự án: Xây dựng cầu ABC" → value = "Xây dựng cầu ABC"
     
     **Rule B - Next Line** (if same line has no value or only whitespace):
     - Take text from the NEXT OCR line after the label
     - Continue reading lines until you hit another label or empty line
     - Example:
       ```
       Line 1: "Dự án:"
       Line 2: "Xây dựng cầu ABC"
       ```
       → value = "Xây dựng cầu ABC"
     
     **Rule C - Wrapped Multi-Line** (if value is split across lines):
     - Merge all consecutive lines that:
       * Don't start with a new label (ending in ":")
       * Are indented or aligned with the value start position
       * Don't start with "Số:", "Ngày:", or other label keywords
     - Example:
       ```
       Line 1: "Dự án: Xây dựng cầu vượt"
       Line 2: "tại xã ABC, huyện XYZ"
       Line 3: "Gói thầu:"
       ```
       → value = "Xây dựng cầu vượt tại xã ABC, huyện XYZ"

STEP 3 - ANTI-CROSS-CONTAMINATION (Prevent mixing fields):
  
  **BOUNDARY DETECTION**:
  - A field value ENDS when you encounter:
    1. Another field label (text ending with ":")
    2. A hard separator (horizontal line, "---", "___")
    3. A section heading (all caps, underlined, or numbered like "I.", "II.")
    4. An empty line followed by a different content type (table, signature)
  
  **SPATIAL VALIDATION** (for tilted PDFs):
  - If extracted value contains text that looks like ANOTHER field's label → Stop before that text
  - Example (WRONG extraction):
    ```
    "Dự án: Xây dựng ABC Gói thầu: GT-01"
    ```
    If you extract "Xây dựng ABC Gói thầu: GT-01" for du_an → WRONG
    Correct: Stop at "Gói thầu:" → value = "Xây dựng ABC"
  
  **NUMBER VALIDATION** (for numeric fields):
  - For fields expecting numbers (khoi_luong_hoan_thanh, amounts):
    * Extract ONLY numeric values (digits, dots, commas)
    * Ignore text before/after the number
    * Example: "Khối lượng: 1.234.567.890 đồng" → "1234567890"

STEP 4 - TABLE-BASED FIELDS (Special handling):

Some fields come from a table section (if present). Use hybrid approach:
  
  **TABLE DETECTION**:
  - Look for repeated pattern of "STT | Nội dung | Vốn trong nước | Vốn ngoài nước | Tổng cộng"
  - If found → Use table extraction (Step 4A)
  - If NOT found → Use label-based extraction (Step 4B)
  
  **Step 4A - TABLE EXTRACTION** (if table exists):
  - Apply previous table parsing rules (row-by-row with STT anchoring)
  - Use row's "Nội dung" column as the label anchor
  - Extract values from corresponding columns
  
  **Step 4B - LABEL-BASED EXTRACTION** (if no table, just text):
  - Search for field labels in plain text format:
    * "Khối lượng hoàn thành:" → Extract number after this
    * "Thu hồi tạm ứng:" → Extract number after this
    * "Thuế GTGT:" or "Thuế giá trị gia tăng:" → Extract number after this
    * "Bảo lãnh bảo hành:" → Extract number after this (ONLY if this label exists)
    * "Số trả đơn vị thụ hưởng:" → Extract number after this
    * "Giữ lại cho quyết toán:" → Extract number after this

STEP 5 - MULTI-LINE VALUE RECONSTRUCTION (for skewed text):
  
  **When label and value are on different lines due to tilt**:
  
  Example of skewed OCR:
  ```
  Original PDF line: "Dự án: Xây dựng cầu ABC tại Hà Nội"
  
  Skewed OCR output:
  Line 1: "Dự án: Xây dựn"
  Line 2: "g cầu ABC tạ"
  Line 3: "i Hà Nội"
  ```
  
  **RECONSTRUCTION ALGORITHM**:
  1. Find label "Dự án:"
  2. Capture text on same line: "Xây dựn"
  3. Check next line: Does it start with a label? NO → It's continuation
  4. Append next line: "Xây dựn" + "g cầu ABC tạ" = "Xây dựng cầu ABC tạ"
  5. Check line 3: No label → Continuation
  6. Append: "Xây dựng cầu ABC tạ" + "i Hà Nội" = "Xây dựng cầu ABC tại Hà Nội"
  7. Check line 4: Starts with "Gói thầu:" → STOP
  8. Final value: "Xây dựng cầu ABC tại Hà Nội"
  
  **WORD BOUNDARY REPAIR**:
  - If a word is split mid-character, merge it intelligently
  - Look for incomplete words at line boundaries
  - Example: "Xây dựn" + "g" → "Xây dựng"

FIELDS (Detailed Extraction Instructions):

du_an: Project name.
  - Label: "Dự án:" or "Tên dự án:"
  - Location: Usually near the top of document
  - KEEP prefix if present in extracted value
  - Extract EXACTLY as written, merge multi-line if needed
  - Example: "Dự án: Xây dựng..." → "Dự án: Xây dựng..."

goi_thau: Package name.
  - Label: "Gói thầu:" or "Tên gói thầu:"
  - Location: Usually after du_an
  - KEEP prefix if present
  - Extract EXACTLY as written

so_chung_tu: Document/Voucher number.
  - Label: "Số:" (in document header, top right)
  - Format: Numbers, may have slashes or hyphens (e.g., "123/TB-VP")
  - Extract the number only, exclude "Số:" prefix

hop_dong: Contract number.
  - Label: "Hợp đồng số:" or "Căn cứ hợp đồng số:"
  - Location: Usually in "Căn cứ" section
  - Extract the contract number only
  - Extract EXACTLY as written, merge multi-line if needed

chu_dau_tu: Primary investor/owner.
  - Label: "Chủ đầu tư:" or "Đơn vị:"
  - Location: Usually near top or in intro section
  - Extract organization or agency name

ten_dot_thanh_toan: Payment batch name.
  - Payment batch description
  - If "V/v" exists: extract content immediately after "V/v", exclude "V/v", "v/v", "v/V"
  - If no "V/v": extract phrases clearly showing "Payment batch ...", "Advance payment round ...", "Final settlement ..."
  - Keywords: "Thanh toán", "Tạm ứng", "Quyết toán"
  - Example: "thanh toán đợt ...." or "tạm ứng lần....." or "quyết toán ...."
  - Extract EXACTLY as written, merge multi-line if needed

loai_thanh_toan: Payment type.
  - Determine from ten_dot_thanh_toan or noi_dung
  - "tạm ứng" if contains "tạm ứng"
  - "quyết toán" if contains "quyết toán"  
  - Otherwise "thanh toán"

nguon_von: Source of fund.
  - Label: "Nguồn vốn:" or similar
  - Examples: "Vốn ngân sách", "Vốn ODA", "Vốn đầu tư công"

noi_dung: Content description.
  - If table exists: Concatenate "Nội dung" column values (major items only)
  - If no table: Extract from description section or paragraph after "Nội dung:"

ngay_thanh_toan: Payment date.
  - Label: "Ngày" followed by date pattern
  - Format: dd/mm/yyyy or "ngày DD tháng MM năm YYYY"
  - Convert to dd/mm/yyyy format
  - Location: Usually in header or signature section

khoi_luong_hoan_thanh: Completed volume/payment amount.
  **STRICT SAME-ROW EXTRACTION**:
  
  **TABLE FORMAT**:
  1. Find row where "Nội dung" contains "Khối lượng hoàn thành" or "Giá trị khối lượng"
  2. Remember this row's STT number: [ROW_NUM]
  3. Extract ONLY from "Tổng cộng" column of row [ROW_NUM]
  4. ❌ DO NOT extract from row [ROW_NUM + 1] or [ROW_NUM - 1]
  5. If "Tổng cộng" cell is empty for this row → Return null
  
  **TEXT FORMAT**:
  1. Find line containing "Khối lượng hoàn thành:"
  2. Extract number on SAME line (within 50 chars after ":")
  3. ❌ DO NOT take number from next line
  
  **VALIDATION**:
  - Number must be from SAME row/line as label
  - If uncertain → Return null
  
  Format: INTEGER ONLY (remove dots, commas, currency)

thu_hoi_tam_ung: Advance payment/recovery (has 2 sub-fields: von_trong_nuoc, von_ngoai_nuoc).
  
  **SIMPLE EXTRACTION RULE**:
  
  Search for EITHER of these patterns:
  - Pattern A: "Thu hồi tạm ứng" (recovery - use NEGATIVE sign)
  - Pattern B: "Thanh toán đề nghị tạm ứng" (new advance - use POSITIVE sign)
  - Pattern C: "Tạm ứng" (advance - use POSITIVE sign)
  
  After finding the pattern, look at the NEXT 2-3 lines:
  - If you see "+ Vốn trong nước: [NUMBER]" → Extract NUMBER for von_trong_nuoc
  - If you see "+ Vốn ngoài nước: [NUMBER]" → Extract NUMBER for von_ngoai_nuoc
  - If "Vốn ngoài nước" has dots "...." instead of number → von_ngoai_nuoc = null
  
  **CRITICAL**: The lines with "+ Vốn trong nước:" and "+ Vốn ngoài nước:" are ALWAYS the child lines of the main pattern.
  
  Format: INTEGER ONLY (remove dots, commas, "đồng")
  
  **CONCRETE EXAMPLE FROM YOUR DATA**:
  ```
  Input text:
  "- Thanh toán đề nghị tạm ứng (bằng số): 123.000.000 đồng
  + Vốn trong nước: 123.000.000 đồng
  + Vốn ngoài nước ...................."
  
  Step 1: Found "Thanh toán đề nghị tạm ứng" → This is Pattern B (new advance)
  Step 2: Next line has "+ Vốn trong nước: 123.000.000 đồng" → Extract 123000000
  Step 3: Next line has "+ Vốn ngoài nước .........." → No number, return null
  
  Output:
  {{
    "von_trong_nuoc": 100000000,
    "von_ngoai_nuoc": null
  }}
  ```
  
  **SIGN RULE**:
  - If pattern contains "Thu hồi" → Make number NEGATIVE (add "-" prefix)
  - Otherwise → Keep number POSITIVE

thue_gia_tri_gia_tang: VAT amount.
  **STRICT SAME-ROW EXTRACTION**:
  
  **TABLE FORMAT**:
  1. Find row where "Nội dung" contains "Thuế GTGT" or "Thuế giá trị gia tăng"
  2. Remember STT: [ROW_NUM]
  3. Extract from "Tổng cộng" column of row [ROW_NUM] ONLY
  4. ❌ DO NOT extract from other rows
  5. If cell empty → Return null
  
  **TEXT FORMAT**:
  1. Find line with "Thuế GTGT:" or "Thuế giá trị gia tăng:"
  2. Extract number on SAME line (max 50 chars after ":")
  3. ❌ DO NOT take from next line
  
  **VALIDATION**:
  - Typically 5-10% of khoi_luong_hoan_thanh
  - Must be from SAME row as label
  
  Format: INTEGER ONLY

bao_lanh_bao_hanh: Guarantee/Warranty amount.
  **CRITICAL - COMMON MISTAKE**: This field is often missed. Pay special attention.
  
  **KEYWORDS** (Search for ANY of these):
  - "Chuyển tiền bảo hành" (MOST COMMON - appears as "- Chuyển tiền bảo hành (bằng số):")
  - "Bảo lãnh bảo hành"
  - "Bảo hành"
  - "Bảo lãnh"
  
  **EXTRACTION STEPS**:
  1. Search text for "Chuyển tiền bảo hành" (case-insensitive)
  2. If found: Extract number IMMEDIATELY after ":" on SAME line
  3. If not found: Try other keywords
  4. If still not found: Return null
  
  **EXAMPLE**:
  Input: "Chuyển tiền bảo hành (bằng số): 347.455 đồng"
  Output: 347.455
  
  Format: INTEGER ONLY like Example's output

so_tra_don_vi_thu_huong: Amount paid to beneficiary (has 2 sub-fields).
  **STRICT SAME-ROW EXTRACTION**:
  
  **TABLE FORMAT**:
  1. Find row where "Nội dung" contains "Số trả đơn vị thụ hưởng" or "Số trả ĐV thụ hưởng"
  2. Remember STT: [ROW_NUM]
  3. Extract from row [ROW_NUM] ONLY:
     - von_trong_nuoc: From "Vốn trong nước" column of THIS row
     - von_ngoai_nuoc: From "Vốn ngoài nước" column of THIS row
  4. ❌ CRITICAL: DO NOT take from row [ROW_NUM ± 1]
  5. If cells empty → Return null
  
  **TEXT FORMAT**:
  1. Find line with "Số trả đơn vị thụ hưởng:"
  2. Extract numbers from SAME line:
     - von_trong_nuoc: First number after ":"
     - von_ngoai_nuoc: Second number (if present)
  3. ❌ DO NOT look at adjacent lines
  
  **VALIDATION**:
  - Usually largest amount after khoi_luong_hoan_thanh
  - Must be from SAME row as label
  
  Format: INTEGER ONLY

giu_lai_cho_quyet_toan: Amount retained for settlement.
  **STRICT SAME-ROW EXTRACTION**:
  
  **TABLE FORMAT**:
  1. Find row where "Nội dung" contains "Giữ lại cho quyết toán" or "Giữ lại QT"
  2. Remember STT: [ROW_NUM]
  3. Extract from "Tổng cộng" column of row [ROW_NUM] ONLY
  4. ❌ DO NOT extract from row [ROW_NUM + 1] or [ROW_NUM - 1]
  5. If cell empty → Return null
  
  **TEXT FORMAT**:
  1. Find line with "Giữ lại cho quyết toán:"
  2. Extract number on SAME line (within 50 chars after ":")
  3. ❌ DO NOT take from next line
  
  **VALIDATION**:
  - Typically 3-5% of total payment
  - Must be from SAME row as label
  - If uncertain → Return null
  
  Format: INTEGER ONLY

**NUMBER FORMATTING RULE** (All numeric fields):
- FORMAT: INTEGER ONLY string (VNĐ)
- REMOVE: dots (.), commas (,), currency symbols (đ, đồng, VNĐ), text
- KEEP: negative sign "-" if present (for deductions)
- Handle Vietnamese units:
  * "tỷ" or "tỉ" → multiply by 10^9
  * "triệu" → multiply by 10^6
  * "nghìn" → multiply by 10^3
  * "trăm" → multiply by 10^2
- Examples:
  * "1.234.567.890 đồng" → "1234567890"
  * "-500.000.000" → "-500000000"
  * "123 triệu" → "123000000"
  * "45,5 tỷ" → "45500000000"

**ANTI-SKEW VALIDATION CHECKLIST**:
✓ Used label as anchor (not position-based extraction)
✓ Merged multi-line values that belong together
✓ Stopped at next label boundary (no cross-contamination)
✓ Verified numbers match their labels
✓ Returned null when uncertain (no guessing)

#OUTPUT FORMAT:
    - Chỉ trả về duy nhất định dạng JSON. BẮT BUỘC tuân theo định dạng đầu vào của JSON. TUYỆT ĐỐI không thay đổi trên trường (key) trong JSON.
    - Nếu tìm thấy thông tin của một trường, hãy thay thế giá trị 'null' bằng thông tin vừa được trích xuất.
    - Nếu không tìm thấy thông tin, CẦN GIỮ NGUYÊN GIÁ TRỊ 'null', KHÔNG TỰ Ý BỊA RA KẾT QUẢ.
    - Không thêm bất kỳ lời dẫn hay lời giải thích nào.

CONTEXT:
{context}

JSON INPUT:
{json_template}

"""

class PromptService():
    def __init__(self):
        self.prompt_template = {
            "CHU_TRUONG": CHU_TRUONG_PROMPT,
            "THONG_TIN_DU_AN": THONG_TIN_DU_AN_PROMPT,
            "KE_HOACH_LCNT": KE_HOACH_LCNT_PROMPT,
            "QUAN_LY_GOI_THAU": QUAN_LY_GOI_THAU_PROMPT,
            "HOP_DONG": HOP_DONG_PROMPT,
            "THANH_TOAN_TAM_UNG": THANH_TOAN_TAM_UNG_PROMPT
        }
        
    def get_prompt_by_type(self, doc_type, context, json_template):
        """
        Tìm kiếm prompt tương ứng với doc_type và fill dữ liệu vào template.
        """
        
        template = self.prompt_template.get(doc_type)
        
        context_prompt = template.format(context = context, json_template = json_template)
        
        return context_prompt