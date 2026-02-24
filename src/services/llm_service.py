import ollama
import json
from pydantic import create_model
from typing import List, Optional
from prompt_service import PromptService

"""
LLM Service: Extract information from text -> Return JSON output
"""

MODEL_LLM_NAME = 'gemma:2b'

class LLMService:
    def __init__(self, model_name = MODEL_LLM_NAME):
        self.name_model = model_name
        self.prompt_service = PromptService()
        
    def _call_llm(self, doc_type, context, template, model):
        # Get prompt by document type
        prompt = self.prompt_service.get_prompt_by_type(doc_type, context, template)
        
        try:
            response = ollama.chat(
                model=self.name_model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.0},
                format=model.model_json_schema()
            )
            
            return json.loads(response['message']['content'])
        
        except Exception as e:
            return {"error": f"Lỗi xử lý {doc_type}: {str(e)}"}
    
    # Doc type: Chu truong
    def extract_chu_truong(self, context, template):
        NguonVonItem = create_model('NguonVonItem', stt=(str, ...), nguon_von=(str, ...), gia_tri=(str, ...))
        Model = create_model('CHUTRUONG',
            so_quyet_dinh=(Optional[str], None), ngay_quyet_dinh=(Optional[str], None),
            ten_du_an=(Optional[str], None), chu_dau_tu=(Optional[str], None),
            tong_muc_dau_tu=(Optional[str], None), muc_tieu_du_an=(Optional[str], None),
            quy_mo_dau_tu=(Optional[str], None), thoi_gian_thuc_hien=(Optional[str], None),
            thoi_gian_khoi_cong=(Optional[str], None), thoi_gian_hoan_thanh=(Optional[str], None),
            thanh_phan_nguon_von=(List[NguonVonItem], [])
        )
        return self._call_llm("CHU_TRUONG", context, template, Model)

    
    def extract_ke_hoach_lcnt(self, context, template):
        Model = create_model('KEHOACHLCNT',
            so_quyet_dinh=(Optional[str], None), ngay_ky=(Optional[str], None),
            du_an=(Optional[str], None), giai_doan=(Optional[str], None),
            ten_ke_hoach_vn=(Optional[str], None), ten_ke_hoach_en=(Optional[str], None)
        )
        return self._call_llm("KE_HOACH_LCNT", context, template, Model)

    def extract_thong_tin_du_an(self, context, template):
        LocationItem = create_model('LocationItem', stt=(str, ...), tinh_thanh_pho=(str, ...), phuong_xa=(str, ...), dia_chi_chi_tiet=(str, ...))
        CostItem = create_model('CostItem', stt=(str, ...), thanh_phan=(str, ...), gia_tri=(str, ...))
        Model = create_model('THONGTINDUAN',
            so_quyet_dinh=(Optional[str], None), ngay_quyet_dinh=(Optional[str], None),
            ma_du_an=(Optional[str], None), ten_du_an=(Optional[str], None),
            chu_dau_tu=(Optional[str], None), chu_truong_dau_tu=(Optional[str], None),
            trang_thai_du_an=(Optional[str], None), trang_thai_thanh_tra=(Optional[str], None),
            nhom_du_an=(Optional[str], None), linh_vuc=(Optional[str], None),
            loai_cong_trinh=(Optional[str], None), hinh_thuc_quan_ly=(Optional[str], None),
            dia_diem_trien_khai=(List[LocationItem], []), thanh_phan_khoan_muc=(List[CostItem], [])
        )
        return self._call_llm("THONG_TIN_DU_AN", context, template, Model)

    def extract_quan_ly_goi_thau(self, context, template):
        Model = create_model('QUANLYGOITHAU',
            ma_goi_thau=(Optional[str], None), ten_goi_thau=(Optional[str], None),
            du_an=(Optional[str], None), ke_hoach_lcnt=(Optional[str], None),
            gia_du_toan=(Optional[str], None), gia_goi_thau=(Optional[str], None),
            hinh_thuc_lua_chon_nha_thau=(Optional[str], None), phuong_thuc_lua_chon_nha_thau=(Optional[str], None),
            cach_thuc_thuc_hien_dau_thau=(Optional[str], None), loai_nguon_von_du_an=(Optional[str], None),
            hinh_thuc_hop_dong=(Optional[str], None), linh_vuc_dau_thau=(Optional[str], None),
            thoi_gian_lua_chon_nha_thau=(Optional[str], None), thoi_gian_thuc_hien_hop_dong=(Optional[str], None)
        )
        return self._call_llm("QUAN_LY_GOI_THAU", context, template, Model)

    def extract_hop_dong(self, context, template):
        ContractorItem = create_model('ContractorItem', stt=(Optional[str], None), nt_chinh=(Optional[bool], None),
                                     nha_thau=(Optional[str], None), loai_nha_thau=(Optional[str], None), gia_tri_thuc_hien=(Optional[str], None))
        Model = create_model('HOPDONG',
            so_hop_dong=(Optional[str], None), ngay_ky_hop_dong=(Optional[str], None),
            du_an=(Optional[str], None), goi_thau=(Optional[str], None),
            ten_hop_dong=(Optional[str], None), dai_dien_chu_dau_tu=(Optional[str], None),
            chuc_vu=(Optional[str], None), loai_hop_dong=(Optional[str], None),
            ngay_hieu_luc_tu=(Optional[str], None), ngay_hieu_luc_den=(Optional[str], None),
            gia_tri_hop_dong=(Optional[str], None), gia_tri_bao_lanh_bao_hanh=(Optional[str], None),
            gia_tri_vat=(Optional[str], None), loai_hop_dong_nha_thau=(Optional[str], None),
            danh_sach_nha_thau=(List[ContractorItem], [])
        )
        return self._call_llm("HOP_DONG", context, template, Model)

    def extract_thanh_toan_tam_ung(self, context, template):
        FundingDetail = create_model('FundingDetail', von_trong_nuoc=(Optional[str], None), von_ngoai_nuoc=(Optional[str], None))
        Model = create_model('THANHTOANTAMUNG',
            du_an=(Optional[str], None), goi_thau=(Optional[str], None),
            so_chung_tu=(Optional[str], None), hop_dong=(Optional[str], None),
            chu_dau_tu=(Optional[str], None), ten_dot_thanh_toan=(Optional[str], None),
            loai_thanh_toan=(Optional[str], None), nguon_von=(Optional[str], None),
            noi_dung=(Optional[str], None), ngay_thanh_toan=(Optional[str], None),
            kho_luong_hoan_thanh=(Optional[str], None), thu_hoi_tam_ung=(Optional[FundingDetail], None),
            thue_gia_tri_gia_tang=(Optional[str], None), bao_lanh_bao_hanh=(Optional[str], None),
            so_tra_don_vi_thu_huong=(Optional[FundingDetail], None), giu_lai_cho_quyet_toan=(Optional[str], None)
        )
        return self._call_llm("THANH_TOAN_TAM_UNG", context, template, Model)
    
    def extract_document_info(self, doc_type, context, json_template):
        # Get Key by document type
        mapping = {
            "CHU_TRUONG": self.extract_chu_truong,
            "THONG_TIN_DU_AN": self.extract_thong_tin_du_an,
            "KE_HOACH_LCNT": self.extract_ke_hoach_lcnt,
            "QUAN_LY_GOI_THAU": self.extract_quan_ly_goi_thau,
            "HOP_DONG": self.extract_hop_dong,
            "THANH_TOAN_TAM_UNG": self.extract_thanh_toan_tam_ung
        }
        
        handler = mapping.get(doc_type)
        
        if not handler:
            return {"error": f"Doc type '{doc_type}' không được hỗ trợ."}
        
        return handler(context, json_template)