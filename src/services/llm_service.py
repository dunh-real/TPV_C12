import ollama
import json
from pydantic import BaseModel, Field
from typing import List, Optional
from prompt_service import PromptService

# DOC_TYPE: CHU_TRUONG
class NguonVonItem(BaseModel):
    stt: str
    nguon_von: str
    gia_tri: str
    
class CHUTRUONG(BaseModel):
    so_quyet_dinh: Optional[str] = None
    ngay_quyet_dinh: Optional[str] = None
    ten_du_an: Optional[str] = None
    chu_dau_tu: Optional[str] = None
    tong_muc_dau_tu: Optional[str] = None
    muc_tieu_du_an: Optional[str] = None
    quy_mo_dau_tu: Optional[str] = None
    thoi_gian_thuc_hien: Optional[str] = None
    thoi_gian_khoi_cong: Optional[str] = None
    thoi_gian_hoan_thanh: Optional[str] = None
    thanh_phan_nguon_von: List[NguonVonItem] = []
    
# DOC_TYPE: KE_HOACH_LCNT
class KEHOACHLCNT(BaseModel):
    so_quyet_dinh: Optional[str] = None
    ngay_ky: Optional[str] = None
    du_an: Optional[str] = None
    giai_doan: Optional[str] = None
    ten_ke_hoach_vn: Optional[str] = None
    ten_ke_hoach_en: Optional[str] = None
    
# DOC_TYPE: THONG_TIN_DU_AN
class LocationItem(BaseModel):
    stt: str
    tinh_thanh_pho: str
    phuong_xa: str
    dia_chi_chi_tiet: str

class CostItem(BaseModel):
    stt: str
    thanh_phan: str
    gia_tri: str
    
class THONGTINDUAN(BaseModel):
    so_quyet_dinh: Optional[str] = None
    ngay_quyet_dinh: Optional[str] = None
    ma_du_an: Optional[str] = None
    ten_du_an: Optional[str] = None
    chu_dau_tu: Optional[str] = None
    chu_truong_dau_tu: Optional[str] = None
    trang_thai_du_an: Optional[str] = None
    trang_thai_thanh_tra: Optional[str] = None
    nhom_du_an: Optional[str] = None
    linh_vuc: Optional[str] = None
    loai_cong_trinh: Optional[str] = None
    hinh_thuc_quan_ly: Optional[str] = None
    dia_diem_trien_khai: List[LocationItem] = []
    thanh_phan_khoan_muc: List[CostItem] = []
    
    
# DOC_TYPE: QUAN LY GOI THAU
class QUANLYGOITHAU(BaseModel):
    ma_goi_thau: Optional[str] = None
    ten_goi_thau: Optional[str] = None
    du_an: Optional[str] = None
    ke_hoach_lcnt: Optional[str] = None
    gia_du_toan: Optional[str] = None
    gia_goi_thau: Optional[str] = None
    hinh_thuc_lua_chon_nha_thau: Optional[str] = None
    phuong_thuc_lua_chon_nha_thau: Optional[str] = None
    cach_thuc_thuc_hien_dau_thau: Optional[str] = None
    loai_nguon_von_du_an: Optional[str] = None
    hinh_thuc_hop_dong: Optional[str] = None
    linh_vuc_dau_thau: Optional[str] = None
    thoi_gian_lua_chon_nha_thau: Optional[str] = None
    thoi_gian_thuc_hien_hop_dong: Optional[str] = None
    
# DOC_TYPE: HOP_DONG
class ContractorItem(BaseModel):
    stt: Optional[str] = None
    nt_chinh: Optional[bool] = None
    nha_thau: Optional[str] = None
    loai_nha_thau: Optional[str] = None
    gia_tri_thuc_hien: Optional[str] = None

class HOPDONG(BaseModel):
    so_hop_dong: Optional[str] = None
    ngay_ky_hop_dong: Optional[str] = None
    du_an: Optional[str] = None
    goi_thau: Optional[str] = None
    ten_hop_dong: Optional[str] = None
    dai_dien_chu_dau_tu: Optional[str] = None
    chuc_vu: Optional[str] = None
    loai_hop_dong: Optional[str] = None
    ngay_hieu_luc_tu: Optional[str] = None
    ngay_hieu_luc_den: Optional[str] = None
    gia_tri_hop_dong: Optional[str] = None
    gia_tri_bao_lanh_bao_hanh: Optional[str] = None
    gia_tri_vat: Optional[str] = None
    loai_hop_dong_nha_thau: Optional[str] = None
    danh_sach_nha_thau: List[ContractorItem] = []
    
# DOC_TYPE: THANH_TOAN_TAM_UNG
class FundingDetail(BaseModel):
    von_trong_nuoc: Optional[str] = None
    von_ngoai_nuoc: Optional[str] = None

class THANHTOANTAMUNG(BaseModel):
    du_an: Optional[str] = None
    goi_thau: Optional[str] = None
    so_chung_tu: Optional[str] = None
    hop_dong: Optional[str] = None
    chu_dau_tu: Optional[str] = None
    ten_dot_thanh_toan: Optional[str] = None
    loai_thanh_toan: Optional[str] = None
    nguon_von: Optional[str] = None
    noi_dung: Optional[str] = None
    ngay_thanh_toan: Optional[str] = None
    khoi_luong_hoan_thanh: Optional[str] = None
    thu_hoi_tam_ung: Optional[FundingDetail] = None
    thue_gia_tri_gia_tang: Optional[str] = None
    bao_lanh_bao_hanh: Optional[str] = None
    so_tra_don_vi_thu_huong: Optional[FundingDetail] = None
    giu_lai_cho_quyet_toan: Optional[str] = None
    
EXTRACTION_CONFIG = {
    "CHU_TRUONG": {
        "model": CHUTRUONG
    },
    "THONG_TIN_DU_AN": {
        "model": THONGTINDUAN
    },
    "KE_H0ACH_LCNT": {
        "model": KEHOACHLCNT
    },
    "QUAN_LY_GOI_THAU": {
        "model": QUANLYGOITHAU
    }, 
    "HOP_DONG": {
        "model": HOPDONG
    },
    "THANH_TOAN_TAM_UNG": {
        "model": THANHTOANTAMUNG
    }
}

Model_llm_name = 'qwen2.5:latest'
prompt_service = PromptService()

def extract_document_info(doc_type, context, json_tempalte):
    # Get keys by document type
    extraction_config = EXTRACTION_CONFIG.get(doc_type)
    model_schema = extraction_config['model']
    
    # Get prompt by document type
    context_prompt = prompt_service.get_prompt_by_type(doc_type, context, json_tempalte)
    
    try:
        response = ollama.chat(
            model = Model_llm_name,
            messages = [
                {'role': 'user', 'content': context_prompt},
            ],
            options = {
                'temperature': 0.0,
            },
            format=model_schema.model_json_schema()
        )
        
        content = response['message']['content']
        
        return json.loads(content)
    
    except Exception as e:
        return f"Error: {str(e)}"
    
    
    """
    format output llm thanh str co dau markdown de nhan dien tung phan, tach text cho de
    ##Item1
    #Itemname
    tenvanban
    #ItemContent
    Congvancudan36
    
    ##Item2
    
    viet ham xu ly convert output text -> json
    """