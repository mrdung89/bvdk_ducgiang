import tkinter as tk
from tkinter import messagebox, ttk, filedialog, simpledialog
import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageWin, ImageTk
import pymysql # Đã thay đổi từ mysql.connector
import datetime
from datetime import timedelta
import os
import win32print
import win32ui
import json
import math

import re

def remove_vn_accents(s):
    if not s: return s
    s = re.sub(r'[àáạảãâầấậẩẫăằắặẳẵ]', 'a', s)
    s = re.sub(r'[ÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴ]', 'A', s)
    s = re.sub(r'[èéẹẻẽêềếệểễ]', 'e', s)
    s = re.sub(r'[ÈÉẸẺẼÊỀẾỆỂỄ]', 'E', s)
    s = re.sub(r'[òóọỏõôồốộổỗơờớợởỡ]', 'o', s)
    s = re.sub(r'[ÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠ]', 'O', s)
    s = re.sub(r'[ìíịỉĩ]', 'i', s)
    s = re.sub(r'[ÌÍỊỈĨ]', 'I', s)
    s = re.sub(r'[ùúụủũưừứựửữ]', 'u', s)
    s = re.sub(r'[ÙÚỤỦŨƯỪỨỰỬỮ]', 'U', s)
    s = re.sub(r'[ỳýỵỷỹ]', 'y', s)
    s = re.sub(r'[ỲÝỴỶỸ]', 'Y', s)
    s = re.sub(r'[Đđ]', 'd', s)
    return s

# =================================================================================
# 1. CẤU HÌNH & HẰNG SỐ
# =================================================================================

CONFIG_FILE = "config.json"
LOGIN_FILE = "login.json"
FONT_PATH = "arial.ttf"
TEMP_IMAGE = "temp_tem.png"
DESIGN_IMAGE = "temp_design.png"

# Kích thước Canvas thiết kế
TEM_WIDTH_PX, TEM_HEIGHT_PX = 900, 240 

DEFAULT_HAN_DAYS_DO_DONG_LE = 30
DEFAULT_HAN_DAYS_THU_THAT = 90
DEFAULT_HAN_DAYS_BO_DUNG_CU = 30

# DANH SÁCH KHOA PHẪU THUẬT
LIST_PHAU_THUAT = ["GMHS", "GMHSTM", "GMHS S"]

DEFAULT_DB_CONFIG = {
    'host': '10.0.80.9',
    'user': 'root',
    'password': '',
    'database': 'qrcode_dungcu',
    'charset': 'utf8mb4'
}

DEFAULT_PRINTER_PROFILE = {
    'scale_w': 1.0, 'scale_h': 1.0,
    'offset_x': 0, 'offset_y': 0,
    'labels_per_row': 1
}

DB_CONFIG = {}
PRINTER_PROFILES = {}
CURRENT_PRINTER_NAME = ""
CURRENT_USER_FULLNAME = "Admin"

FONT_MAP = {
    "Arial": {"R": "arial.ttf", "B": "arialbd.ttf", "I": "ariali.ttf", "BI": "arialbi.ttf"},
    "Times New Roman": {"R": "times.ttf", "B": "timesbd.ttf", "I": "timesi.ttf", "BI": "timesbi.ttf"},
    "Courier New": {"R": "cour.ttf", "B": "courbd.ttf", "I": "couri.ttf", "BI": "courbi.ttf"},
    "Verdana": {"R": "verdana.ttf", "B": "verdanab.ttf", "I": "verdanai.ttf", "BI": "verdanaz.ttf"}
}

# =================================================================================
# 2. HỆ THỐNG
# =================================================================================

def lay_cau_hinh():
    global DB_CONFIG, PRINTER_PROFILES, CURRENT_PRINTER_NAME
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                DB_CONFIG = DEFAULT_DB_CONFIG.copy()
                if 'db_config' in data: DB_CONFIG.update(data['db_config'])
                PRINTER_PROFILES = data.get('printer_profiles', {})
                CURRENT_PRINTER_NAME = data.get('last_printer', win32print.GetDefaultPrinter())
                return
        except: pass
    DB_CONFIG = DEFAULT_DB_CONFIG.copy()
    PRINTER_PROFILES = {}
    try: CURRENT_PRINTER_NAME = win32print.GetDefaultPrinter()
    except: CURRENT_PRINTER_NAME = ""

def luu_cau_hinh():
    data = {'db_config': DB_CONFIG, 'printer_profiles': PRINTER_PROFILES, 'last_printer': CURRENT_PRINTER_NAME}
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f, indent=4)
    except: pass

def get_current_profile(printer_name):
    if printer_name not in PRINTER_PROFILES:
        PRINTER_PROFILES[printer_name] = DEFAULT_PRINTER_PROFILE.copy()
    return PRINTER_PROFILES[printer_name]

def ket_noi_db():
    # Đã thay đổi thành pymysql.connect
    return pymysql.connect(**DB_CONFIG)

lay_cau_hinh()

# =================================================================================
# 3. LOGIC DB
# =================================================================================

def kiem_tra_dang_nhap(username, password):
    try:
        conn = ket_noi_db(); cursor = conn.cursor()
        sql = "SELECT full_name FROM employees WHERE username = %s AND password_hash = %s LIMIT 1"
        cursor.execute(sql, (username, password))
        result = cursor.fetchone()
        conn.close()
        if result: return result[0]
        return None
    except: return None 

def luu_thong_tin_dang_nhap(username, password, remember=False):
    data = {'username': username, 'password': password, 'remember': True} if remember else {'username': '', 'password': '', 'remember': False}
    try:
        with open(LOGIN_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)
    except: pass

def lay_thong_tin_dang_nhap_luu():
    if os.path.exists(LOGIN_FILE):
        try:
            with open(LOGIN_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: pass
    return {'username': '', 'password': '', 'remember': False}

def get_suggestions(text):
    if not text or len(text) < 1: return []
    suggestions = []
    try:
        conn = ket_noi_db(); cur = conn.cursor()
        search = f"%{text}%"
        cur.execute("SELECT ten_bo FROM danh_muc_bo_dung_cu WHERE ten_bo LIKE %s LIMIT 5", (search,))
        suggestions.extend([f"[BỘ] {r[0]}" for r in cur.fetchall()])
        cur.execute("SELECT ten_khoa, ma_khoa FROM danh_muc_khoa WHERE ten_khoa LIKE %s OR ma_khoa LIKE %s LIMIT 5", (search, search))
        for r in cur.fetchall():
            ten, ma = r
            ma_str = f" ({ma})" if ma else ""
            suggestions.append(f"[KHOA] {ten}{ma_str}")
        conn.close()
    except: pass
    return suggestions

def xu_ly_qr_thong_minh(qr_input):
    qr = qr_input.strip()
    if qr.startswith("[BỘ] "): qr = qr.replace("[BỘ] ", "")
    if qr.startswith("[KHOA] "): qr = qr.split("(")[0].replace("[KHOA] ", "").strip()
    
    # --- 1. KIỂM TRA MÃ QR ĐỒ LẺ / THỦ THUẬT (CHUỖI JSON) ---
    try:
        data = json.loads(qr)
        item_id = data.get("id")
        khoa = data.get("khoa", "")
        loai = data.get("loai")
        
        conn = ket_noi_db(); cur = conn.cursor()
        if loai == "LE":
            cur.execute("SELECT ten_dc, COALESCE(han_tiet_khuan, 90), COALESCE(phuong_phap_tiet_khuan, 'EO') FROM danh_muc_dung_cu WHERE id = %s", (item_id,))
            res = cur.fetchone()
            if res:
                conn.close()
                return "LE", (item_id, res[0], khoa, res[1], res[2], True)
                
        elif loai == "thu_thuat":
            cur.execute("SELECT ten_dc, COALESCE(han_tiet_khuan, 90), COALESCE(phuong_phap_tiet_khuan, 'EO') FROM danh_muc_dung_cu WHERE id = %s", (item_id,))
            res = cur.fetchone()
            if res:
                conn.close()
                return "LE", (item_id, res[0], khoa, res[1], res[2], "thu_thuat")
        conn.close()
    except Exception:
        pass # Không phải JSON, bỏ qua để truy vấn chuỗi thường bên dưới

    # --- 2. XỬ LÝ MÃ BỘ DỤNG CỤ VÀ KHOA ---
    qr_lower = qr.lower()
    try:
        conn = ket_noi_db(); cur = conn.cursor()
        for col in ["id", "ten_bo"]:
            cur.execute(f"SELECT id, ten_bo, khoa_su_dung, COALESCE(han_tiet_khuan, {DEFAULT_HAN_DAYS_BO_DUNG_CU}), COALESCE(phuong_phap_tiet_khuan, 'Hơi nước') FROM danh_muc_bo_dung_cu WHERE LOWER(CAST({col} AS CHAR)) = %s LIMIT 1", (qr_lower,))
            res = cur.fetchone()
            if res: 
                conn.close(); return "BO", res
                
        cur.execute("SELECT ten_khoa FROM danh_muc_khoa WHERE LOWER(ten_khoa) = %s OR LOWER(ma_khoa) = %s LIMIT 1", (qr_lower, qr_lower))
        res = cur.fetchone()
        if res: 
            conn.close(); return "KHOA", res[0]
            
        for k in LIST_PHAU_THUAT:
            if k.lower() == qr_lower: 
                conn.close(); return "KHOA", k
        conn.close()
    except Exception as e: 
        print(f"Lỗi truy vấn QR: {e}")
    return None, None

def load_ds_phien_formatted(filter_type="ALL"):
    display_list = []
    mapping = {}
    try:
        conn = ket_noi_db(); cur = conn.cursor()
        sql = """
            SELECT ma_phieu as ma_phien, khoa_nhan as ten_khoa, thoi_gian as last_time
            FROM phieu_cap_phat
            WHERE ma_phieu IS NOT NULL AND ma_phieu <> ''
            ORDER BY last_time DESC
            LIMIT 100
        """
        cur.execute(sql); rows = cur.fetchall(); conn.close()
        for r in rows:
            ma_phien, khoa, thoi_gian = r
            khoa_upper = str(khoa).upper() if khoa else "KHAC"
            is_phau_thuat = khoa_upper in [k.upper() for k in LIST_PHAU_THUAT]
            if filter_type == "PT" and not is_phau_thuat: continue
            if filter_type == "TT" and is_phau_thuat: continue
            time_str = thoi_gian.strftime("%H:%M %d/%m") if thoi_gian else "??"
            display_str = f"{khoa} : {time_str}"
            if display_str in mapping: display_str = f"{khoa} : {time_str} ({ma_phien[-4:]})"
            display_list.append(display_str); mapping[display_str] = ma_phien
    except Exception as e: print(f"Lỗi load phiên: {e}")
    return display_list, mapping

def lay_ds_theo_ma_phien_goc(ma):
    try:
        conn = ket_noi_db(); cur = conn.cursor()
        
        # SQL BÂY GIỜ CỰC KỲ SẠCH: CHỈ LẤY CỘT RAW, KHÔNG CAST, KHÔNG STRING LITERAL
        sql = """
            SELECT 
                COALESCE(bd.id, dl.id) as id, 
                COALESCE(bd.ten_bo, dl.ten_dc) as ten, 
                1.0 as qt, 
                SUM(ct.so_luong) as sl, 
                COALESCE(bd.phuong_phap_tiet_khuan, dl.phuong_phap_tiet_khuan, 'EO') as pp, 
                CASE WHEN bd.id IS NOT NULL THEN FALSE ELSE TRUE END as is_le,
                NULL as k_id, 
                COALESCE(bd.han_tiet_khuan, dl.han_tiet_khuan, 90) as han,
                p.khoa_nhan as ten_khoa
            FROM chi_tiet_cap_phat ct
            JOIN phieu_cap_phat p ON p.ma_phieu = ct.ma_phieu
            LEFT JOIN danh_muc_bo_dung_cu bd ON ct.ma_do = bd.ma_bo 
            LEFT JOIN danh_muc_dung_cu dl ON ct.ma_do = dl.ma_dc
            WHERE ct.ma_phieu = %s 
            GROUP BY id, ten, is_le, pp, ten_khoa
            HAVING SUM(ct.so_luong) > 0
        """
        cur.execute(sql, (ma,))
        rows = cur.fetchall()
        conn.close()
        
        # --- PYTHON ĐẢM NHẬN LOGIC XỬ LÝ (0% LỖI COLLATION) ---
        result = []
        for r in rows:
            id_item = r[0]
            ten = r[1]
            qt = float(r[2]) if r[2] else 1.0
            sl = int(r[3])
            pp_db = r[4]
            is_le = r[5]
            k_id = r[6] # Là số INT hoặc None
            han_db = r[7]
            ten_khoa = str(r[8]) if r[8] else ""
            
            # 1. Fallback Phương pháp Tiệt khuẩn & Hạn
            pp = pp_db if pp_db else ('EO' if is_le else 'Hơi nước')
            han = int(han_db) if han_db else (90 if is_le else 30)
            
            # 2. Định tuyến ID Khoa
            if ten_khoa.upper() in ('GMHS', 'GMHSTM', 'GMHS S'):
                khoa_id_final = ten_khoa.upper()
            else:
                khoa_id_final = str(k_id) if k_id else ten_khoa
                
            result.append((id_item, ten, qt, sl, pp, is_le, khoa_id_final, han, ten_khoa))
            
        return result
        
    except Exception as e:
        print(f"Lỗi: {e}")
        return []
def lay_ds_khoa_all():
    try:
        conn = ket_noi_db(); cur = conn.cursor()
        cur.execute("SELECT ten_khoa FROM danh_muc_khoa ORDER BY ten_khoa"); l = [r[0] for r in cur.fetchall()]; conn.close()
        for k in LIST_PHAU_THUAT: 
            if k not in l: l.insert(0, k)
        return l
    except: return LIST_PHAU_THUAT

def lay_danh_sach_tong_hop(khoa):
    try:
        conn = ket_noi_db()
        cur = conn.cursor()
        today = datetime.date.today().strftime('%Y-%m-%d')
        
        q = f"""
            SELECT 
                COALESCE(bd.id, dl.id) as id, 
                COALESCE(bd.ten_bo, dl.ten_dc) as ten, 
                1.0 as qt, 
                COALESCE(SUM(ct.so_luong), 0) as sl, 
                COALESCE(bd.phuong_phap_tiet_khuan, dl.phuong_phap_tiet_khuan, 'EO') as pp, 
                COALESCE(bd.han_tiet_khuan, dl.han_tiet_khuan, 90) as han
            FROM chi_tiet_cap_phat ct
            JOIN phieu_cap_phat p ON p.ma_phieu = ct.ma_phieu
            LEFT JOIN danh_muc_bo_dung_cu bd ON ct.ma_do = bd.ma_bo 
            LEFT JOIN danh_muc_dung_cu dl ON ct.ma_do = dl.ma_dc
            WHERE p.khoa_nhan = %s AND DATE(p.thoi_gian) = %s
            GROUP BY id, ten, pp
            HAVING SUM(ct.so_luong) > 0 
            ORDER BY ten ASC
        """
        cur.execute(q, (khoa, today))
            
        rows = cur.fetchall()
        conn.close()
        # Trả về tuple có ID: (id, ten, quy_tac, sl, pp, han)
        return [(r[0], r[1], float(r[2]), int(r[3]), r[4], int(r[5])) for r in rows]
    except Exception as e:
        print(f"Lỗi lấy danh sách tổng hợp khoa {khoa}: {e}")
        return []

# =================================================================================
# 4. IN ẤN
# =================================================================================

def get_font_path_by_style(family, bold, italic):
    style_key = "R"
    if bold and italic: style_key = "BI"
    elif bold: style_key = "B"
    elif italic: style_key = "I"
    return FONT_MAP.get(family, FONT_MAP["Arial"]).get(style_key, "arial.ttf")

def tao_anh_tem(item_id, ten, khoa_id, ten_khoa, ngay_tk, han_tk, loai_dung_cu, ten_nhan_vien, phuong_phap):
    # --- 1. CHUẨN HÓA LOẠI DỤNG CỤ ---
    type_code = "bo"
    if loai_dung_cu is not None:
        loai_str = str(loai_dung_cu).lower()
        if "lẻ" in loai_str or "le" in loai_str or str(loai_dung_cu) == "True":
            type_code = "LE"
        elif "thủ thuật" in loai_str or "thu_thuat" in loai_str:
            type_code = "thu_thuat"

    # --- 2. ĐÓNG GÓI CHUẨN THEO 5 QUY TẮC MÃ QR ---
    if type_code == "bo":
        # Quy tắc 1: Mã QR của Bộ là số nguyên (int)
        qr_content = str(item_id)
        
    elif type_code == "LE":
        # Quy tắc 3: Đồ lẻ (JSON gồm id, khoa, loai="LE")
        khoa_str = khoa_id if khoa_id else remove_vn_accents(str(ten_khoa)).strip()
        qr_data = {"id": item_id, "khoa": khoa_str, "loai": "LE"}
        qr_content = json.dumps(qr_data, ensure_ascii=False)
        
    elif type_code == "thu_thuat":
        # Quy tắc 5: Dụng cụ thủ thuật (JSON gồm id, khoa là id_khoa, loai="thu_thuat")
        khoa_str = khoa_id if khoa_id else remove_vn_accents(str(ten_khoa)).strip()
        qr_data = {"id": item_id, "khoa": khoa_str, "loai": "thu_thuat"}
        qr_content = json.dumps(qr_data, ensure_ascii=False)
        
    else:
        qr_content = str(item_id)

    # Khởi tạo mã QR
    qr = qrcode.make(qr_content).resize((135, 135))
   
    # --- 3. VẼ TEM HIỂN THỊ (DÀNH CHO NGƯỜI ĐỌC) ---
    img_full = Image.new("RGB", (TEM_WIDTH_PX, TEM_HEIGHT_PX), "white")
    draw = ImageDraw.Draw(img_full)
    
    try: 
        font_large = ImageFont.truetype("arialbd.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 18)
    except: 
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    img_full.paste(qr, (220, 8))
    
    def draw_text(x, y, text, font): 
        draw.text((x, y), text, font=font, fill="black")
        
    text_x, start_y, line_h = 360, 15, 25
    display_ten = str(ten) if len(str(ten)) <= 25 else str(ten)[:22] + "..."
    
    draw_text(text_x, start_y, f"Tên: {display_ten}", font_large)
    # Vẫn in TÊN KHOA bằng chữ lên tem để mắt người đọc dễ nhìn
    draw_text(text_x, start_y + line_h, f"Khoa: {ten_khoa}", font_small) 
    draw_text(text_x, start_y + line_h*2, f"Ngày TK: {ngay_tk}", font_small)
    draw_text(text_x, start_y + line_h*3, f"Hạn TK: {han_tk}", font_small)
    draw_text(text_x, start_y + line_h*4, f"TK: {phuong_phap}", font_small)
    draw_text(text_x, start_y + line_h*5, f"NV: {ten_nhan_vien}", font_small)
    
    draw_text(230, 145, "BVĐK Đức Giang", font_large)
    
    img_full.save(TEMP_IMAGE)
    return TEMP_IMAGE
def thuc_hien_in(path_anh, printer_name=None):
    if not printer_name: printer_name = CURRENT_PRINTER_NAME or win32print.GetDefaultPrinter()
    profile = get_current_profile(printer_name)
    scale_w, scale_h = float(profile.get('scale_w', 1.0)), float(profile.get('scale_h', 1.0))
    off_x, off_y = int(profile.get('offset_x', 0)), int(profile.get('offset_y', 0))
    try:
        hprinter = win32print.OpenPrinter(printer_name)
        hdc = win32ui.CreateDC(); hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc("Tem Oneshoot"); hdc.StartPage()
        img = Image.open(path_anh)
        dib = ImageWin.Dib(img)
        w_new, h_new = int(TEM_WIDTH_PX * scale_w), int(TEM_HEIGHT_PX * scale_h)
        dib.draw(hdc.GetHandleOutput(), (off_x, off_y, off_x + w_new, off_y + h_new))
        hdc.EndPage(); hdc.EndDoc(); hdc.DeleteDC(); win32print.ClosePrinter(hprinter)
        # LƯU Ý: KHÔNG XÓA FILE TẠI ĐÂY ĐỂ TRÁNH LỖI FILE NOT FOUND TRONG VÒNG LẶP
    except Exception as e: messagebox.showerror("Lỗi In", f"Lỗi máy in: {e}")

# =================================================================================
# 5. DESIGNER
# =================================================================================

class LabelDesignerPopup:
    def __init__(self, parent):
        self.top = tk.Toplevel(parent); self.top.title("THIẾT KẾ TEM"); self.top.geometry("1100x700")
        self.objs = []; self.selected_idx = None; self.drag_mode = None; self.drag_data = {"x": 0, "y": 0, "start_w": 0, "start_h": 0}
        toolbar = tk.Frame(self.top, bg="#eee", padx=10, pady=10); toolbar.pack(side="top", fill="x")
        tk.Button(toolbar, text="📂 ẢNH NỀN", bg="#3498db", fg="white", command=self.load_image).pack(side="left", padx=5)
        tk.Button(toolbar, text="➕ THÊM CHỮ", bg="#e67e22", fg="white", command=self.add_text).pack(side="left", padx=5)
        tk.Button(toolbar, text="❌ XÓA", bg="#c0392b", fg="white", command=self.delete_obj).pack(side="left", padx=5)
        tk.Button(toolbar, text="🖨 IN NGAY", bg="#27ae60", fg="white", command=self.print_design).pack(side="right", padx=10)
        self.canvas = tk.Canvas(self.top, bg="white", width=TEM_WIDTH_PX, height=TEM_HEIGHT_PX); self.canvas.pack(pady=20, padx=20)
        self.canvas.config(highlightbackground="black", highlightthickness=1)
        self.canvas.bind("<Button-1>", self.on_press); self.canvas.bind("<B1-Motion>", self.on_drag); self.canvas.bind("<ButtonRelease-1>", self.on_release)
        prop_fr = tk.LabelFrame(self.top, text="Thuộc Tính", font=("Arial", 10, "bold"), padx=10, pady=10); prop_fr.pack(side="bottom", fill="x", padx=20, pady=10)
        tk.Label(prop_fr, text="Nội dung:").grid(row=0, column=0); self.ent_txt = tk.Entry(prop_fr, width=30); self.ent_txt.grid(row=0, column=1, padx=5)
        tk.Label(prop_fr, text="Font:").grid(row=0, column=2, padx=(10,0)); self.cb_font = ttk.Combobox(prop_fr, values=list(FONT_MAP.keys()), width=15); self.cb_font.set("Arial"); self.cb_font.grid(row=0, column=3)
        self.var_bold = tk.BooleanVar(); tk.Checkbutton(prop_fr, text="B", variable=self.var_bold).grid(row=0, column=4)
        self.var_italic = tk.BooleanVar(); tk.Checkbutton(prop_fr, text="I", variable=self.var_italic).grid(row=0, column=5)
        tk.Button(prop_fr, text="CẬP NHẬT", bg="#3498db", fg="white", command=self.update_properties).grid(row=0, column=6, padx=20)

    def load_image(self):
        path = filedialog.askopenfilename(parent=self.top, filetypes=[("Images", "*.jpg;*.png")])
        if not path: return
        raw = Image.open(path).convert("RGBA"); r = TEM_HEIGHT_PX / raw.size[1] * 0.8; nw, nh = int(raw.size[0]*r), int(raw.size[1]*r)
        self.add_obj({'type': 'img', 'raw': raw, 'x': 50, 'y': 50, 'w': nw, 'h': nh})
    def add_text(self):
        txt = simpledialog.askstring("Nhập", "Nội dung:", parent=self.top)
        if txt: self.add_obj({'type': 'text', 'text': txt, 'size': 24, 'x': 50, 'y': 50, 'w': 0, 'h': 0, 'font': 'Arial', 'bold': False, 'italic': False})
    def add_obj(self, data): self.objs.append(data); self.selected_idx = len(self.objs) - 1; self.redraw()
    def delete_obj(self):
        if self.selected_idx is not None: del self.objs[self.selected_idx]; self.selected_idx = None; self.redraw()
    def redraw(self):
        self.canvas.delete("all")
        for idx, obj in enumerate(self.objs):
            x, y = obj['x'], obj['y']
            if obj['type'] == 'img':
                img_resized = obj['raw'].resize((int(obj['w']), int(obj['h'])), Image.Resampling.NEAREST)
                tk_img = ImageTk.PhotoImage(img_resized, master=self.top); obj['tk_cache'] = tk_img
                self.canvas.create_image(x, y, anchor="nw", image=tk_img, tags=f"obj_{idx}")
            elif obj['type'] == 'text':
                style = "roman"
                if obj['bold'] and obj['italic']: style = "bold italic"
                elif obj['bold']: style = "bold"
                elif obj['italic']: style = "italic"
                f = (obj['font'], int(obj['size']), style)
                tid = self.canvas.create_text(x, y, text=obj['text'], font=f, anchor="nw", tags=f"obj_{idx}", fill="black")
                bbox = self.canvas.bbox(tid)
                if bbox: obj['w'], obj['h'] = bbox[2]-bbox[0], bbox[3]-bbox[1]
            if idx == self.selected_idx:
                w, h = obj['w'], obj['h']
                self.canvas.create_rectangle(x-2, y-2, x+w+2, y+h+2, outline="blue", dash=(4,4))
                self.canvas.create_rectangle(x+w-8, y+h-8, x+w, y+h, fill="blue") 
    def on_press(self, event):
        x, y = event.x, event.y
        if self.selected_idx is not None:
            obj = self.objs[self.selected_idx]
            if (obj['x'] + obj['w'] - 10 <= x <= obj['x'] + obj['w'] + 5) and (obj['y'] + obj['h'] - 10 <= y <= obj['y'] + obj['h'] + 5):
                self.drag_mode = "RESIZE"; self.drag_data = {'x': x, 'y': y, 'start_w': obj['w'], 'start_h': obj['h'], 'start_sz': obj.get('size', 20)}; return
        items = self.canvas.find_overlapping(x, y, x+1, y+1); sel = None
        for item in items:
            tags = self.canvas.gettags(item)
            for t in tags:
                if t.startswith("obj_"): sel = int(t.split("_")[1])
        if sel is not None:
            self.selected_idx = sel; self.drag_mode = "MOVE"; self.drag_data = {'x': x, 'y': y, 'obj_x': self.objs[sel]['x'], 'obj_y': self.objs[sel]['y']}
            obj = self.objs[sel]
            if obj['type'] == 'text': self.ent_txt.delete(0, tk.END); self.ent_txt.insert(0, obj['text']); self.cb_font.set(obj['font']); self.var_bold.set(obj['bold']); self.var_italic.set(obj['italic'])
            else: self.ent_txt.delete(0, tk.END); self.ent_txt.insert(0, "[IMAGE]")
            self.redraw()
        else: self.selected_idx = None; self.redraw()
    def on_drag(self, event):
        if self.selected_idx is None: return
        obj = self.objs[self.selected_idx]; dx = event.x - self.drag_data['x']; dy = event.y - self.drag_data['y']
        if self.drag_mode == "MOVE": obj['x'] = self.drag_data['obj_x'] + dx; obj['y'] = self.drag_data['obj_y'] + dy; self.redraw()
        elif self.drag_mode == "RESIZE":
            if obj['type'] == 'img': obj['w'] = max(10, self.drag_data['start_w'] + dx); obj['h'] = max(10, self.drag_data['start_h'] + dy)
            elif obj['type'] == 'text': scale = 1 + (dy / 100.0); obj['size'] = max(8, int(self.drag_data['start_sz'] * scale))
            self.redraw()
    def on_release(self, event): self.drag_mode = None
    def update_properties(self):
        if self.selected_idx is not None:
            obj = self.objs[self.selected_idx]
            if obj['type'] == 'text': obj['text'] = self.ent_txt.get(); obj['font'] = self.cb_font.get(); obj['bold'] = self.var_bold.get(); obj['italic'] = self.var_italic.get(); self.redraw()
    def print_design(self):
        final = Image.new("RGB", (TEM_WIDTH_PX, TEM_HEIGHT_PX), "white"); draw = ImageDraw.Draw(final)
        for obj in self.objs:
            x, y = int(obj['x']), int(obj['y'])
            if obj['type'] == 'img': rz = obj['raw'].resize((int(obj['w']), int(obj['h'])), Image.Resampling.LANCZOS); final.paste(rz, (x, y), rz if rz.mode=='RGBA' else None)
            elif obj['type'] == 'text':
                font_file = get_font_path_by_style(obj['font'], obj['bold'], obj['italic'])
                try: f = ImageFont.truetype(font_file, int(obj['size']))
                except: f = ImageFont.load_default()
                draw.text((x, y), obj['text'], font=f, fill="black")
        final.save(DESIGN_IMAGE); thuc_hien_in(DESIGN_IMAGE); messagebox.showinfo("OK", "Đã gửi lệnh in", parent=self.top)

# =================================================================================
# 6. VISUAL ADJUSTMENT & UI
# =================================================================================

class VisualAdjustWindow:
    def __init__(self, parent, settings_window):
        self.top = tk.Toplevel(parent); self.top.title(f"Căn Chỉnh: {CURRENT_PRINTER_NAME}"); self.top.geometry("1000x700"); self.settings_window = settings_window
        profile = get_current_profile(CURRENT_PRINTER_NAME)
        self.scale_w, self.scale_h = float(profile.get('scale_w', 1.0)), float(profile.get('scale_h', 1.0))
        self.off_x, self.off_y = int(profile.get('offset_x', 0)), int(profile.get('offset_y', 0))
        self.img_path = tao_anh_tem("DỤNG CỤ TEST", "KHOA TEST", "01/01/2026", "01/02/2026", "TEST", "ADMIN", "Hơi nước")
        self.original_image = Image.open(self.img_path)
        ctrl_frame = tk.Frame(self.top, bg="#eee", padx=10, pady=10); ctrl_frame.pack(side="top", fill="x")
        fr_s = tk.LabelFrame(ctrl_frame, text="Co Giãn Ảnh (Scale)", font=("Arial", 10, "bold"), bg="#eee"); fr_s.pack(side="left", padx=10)
        tk.Label(fr_s, text="Ngang (W):", bg="#eee").grid(row=0, column=0); self.var_w = tk.DoubleVar(value=self.scale_w); tk.Scale(fr_s, variable=self.var_w, from_=0.1, to=3.0, resolution=0.01, orient="horizontal", length=150, command=self.update_preview).grid(row=0, column=1)
        tk.Label(fr_s, text="Dọc (H):", bg="#eee").grid(row=1, column=0); self.var_h = tk.DoubleVar(value=self.scale_h); tk.Scale(fr_s, variable=self.var_h, from_=0.1, to=3.0, resolution=0.01, orient="horizontal", length=150, command=self.update_preview).grid(row=1, column=1)
        fr_m = tk.LabelFrame(ctrl_frame, text="Di Chuyển (Offset)", font=("Arial", 10, "bold"), bg="#eee"); fr_m.pack(side="left", padx=10)
        bg = tk.Frame(fr_m, bg="#eee"); bg.pack(pady=5)
        tk.Button(bg, text="⬆", width=4, command=lambda: self.move(0, -5)).grid(row=0, column=1); tk.Button(bg, text="⬅", width=4, command=lambda: self.move(-5, 0)).grid(row=1, column=0); tk.Button(bg, text="➡", width=4, command=lambda: self.move(5, 0)).grid(row=1, column=2); tk.Button(bg, text="⬇", width=4, command=lambda: self.move(0, 5)).grid(row=2, column=1)
        tk.Button(ctrl_frame, text="LƯU CÀI ĐẶT", bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=15, height=3, command=self.save_and_close).pack(side="right", padx=20)
        self.canvas = tk.Canvas(self.top, bg="gray", width=900, height=500); self.canvas.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas.create_rectangle(50, 50, 950, 550, fill="white", outline="black"); self.canvas.create_line(50, 50, 950, 50, fill="red", width=2); self.canvas.create_line(50, 50, 50, 550, fill="blue", width=2)
        self.tk_img = None; self.update_preview()
    def move(self, dx, dy): self.off_x += dx; self.off_y += dy; self.update_preview()
    def update_preview(self, _=None):
        self.scale_w, self.scale_h = self.var_w.get(), self.var_h.get(); w_n, h_n = int(TEM_WIDTH_PX * self.scale_w), int(TEM_HEIGHT_PX * self.scale_h)
        if w_n > 0 and h_n > 0:
            resized = self.original_image.resize((w_n, h_n), Image.Resampling.LANCZOS); self.tk_img = ImageTk.PhotoImage(resized, master=self.top)
            self.canvas.delete("img_tag"); self.canvas.create_image(50+self.off_x, 50+self.off_y, anchor="nw", image=self.tk_img, tags="img_tag")
    def save_and_close(self): self.settings_window.update_ui_from_visual(self.scale_w, self.scale_h, self.off_x, self.off_y); self.top.destroy()

class LoginWindow:
    def __init__(self, root, on_success):
        self.root = root; self.on_success = on_success; self.root.title("Đăng Nhập"); self.root.geometry("400x320")
        fr = tk.Frame(root, bg="white", padx=20, pady=20, relief="raised", bd=1); fr.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(fr, text="HỆ THỐNG IN TEM", font=("Arial", 16, "bold"), bg="white", fg="#333").pack(pady=(0, 20))
        tk.Label(fr, text="Tài khoản:", bg="white", font=("Arial", 11)).pack(anchor="w"); self.ent_u = tk.Entry(fr, font=("Arial", 12), width=30); self.ent_u.pack(pady=(0, 10))
        tk.Label(fr, text="Mật khẩu:", bg="white", font=("Arial", 11)).pack(anchor="w"); self.ent_p = tk.Entry(fr, show="*", font=("Arial", 12), width=30); self.ent_p.pack(pady=(0, 10))
        self.var_r = tk.BooleanVar(); tk.Checkbutton(fr, text="Ghi nhớ", variable=self.var_r, bg="white").pack(anchor="w")
        tk.Button(fr, text="ĐĂNG NHẬP", font=("Arial", 12, "bold"), bg="#0078d7", fg="white", width=25, command=self.login).pack(pady=20)
        saved = lay_thong_tin_dang_nhap_luu()
        if saved.get('remember'): self.ent_u.insert(0, saved['username']); self.ent_p.insert(0, saved['password']); self.var_r.set(True)
    def login(self):
        u, p = self.ent_u.get().strip(), self.ent_p.get().strip(); name = kiem_tra_dang_nhap(u, p)
        if name: global CURRENT_USER_FULLNAME; CURRENT_USER_FULLNAME = name; luu_thong_tin_dang_nhap(u, p, self.var_r.get()); self.on_success()
        else: messagebox.showerror("Lỗi", "Sai thông tin!")

class MainApp:
    def __init__(self, root, is_subscreen=False):
        self.root = root; self.root.title("Oneshoot Pro - In Tem & Thiết Kế"); self.root.state("zoomed")
        self.fr_side = tk.Frame(root, bg="#2c3e50", width=260); self.fr_side.pack(side="left", fill="y"); self.fr_side.pack_propagate(False)
        self.fr_main = tk.Frame(root, bg="#ecf0f1"); self.fr_main.pack(side="right", fill="both", expand=True)
        tk.Label(self.fr_side, text="Oneshoot\nSystem", font=("Arial", 20, "bold"), fg="white", bg="#2c3e50").pack(pady=40)
        tk.Label(self.fr_side, text=f"NV: {CURRENT_USER_FULLNAME}", font=("Arial", 12, "italic"), fg="#bdc3c7", bg="#2c3e50").pack(pady=(0, 20))
        self.mk_btn(self.fr_side, "🏠  TRANG CHỦ", self.show_home); self.mk_btn(self.fr_side, "🎨  THIẾT KẾ TEM", lambda: LabelDesignerPopup(self.root)); self.mk_btn(self.fr_side, "⚙  CÀI ĐẶT MÁY IN", self.show_settings)
        tk.Frame(self.fr_side, bg="#2c3e50").pack(fill="y", expand=True); if is_subscreen: self.mk_btn(self.fr_side, "⬅  QUAY LẠI", self.root.destroy, bg="#c0392b")
        else: self.mk_btn(self.fr_side, "🚪  ĐĂNG XUẤT", self.logout, bg="#c0392b")
        self.current_khoa = None; self.selected_tk = ""; self.list_items = []; self.map_ma_phien = {}; self.show_home()
    def mk_btn(self, parent, text, cmd, bg="#34495e"): btn = tk.Button(parent, text=text, font=("Arial", 12, "bold"), bg=bg, fg="white", relief="flat", anchor="w", padx=20, command=cmd); btn.pack(fill="x", pady=2)
    def clear_main(self):
        for w in self.fr_main.winfo_children(): w.destroy()
    def show_home(self):
        self.clear_main()
        fr_head = tk.Frame(self.fr_main, bg="white", pady=10, padx=20); fr_head.pack(side="top", fill="x")
        tk.Label(fr_head, text="IN TEM TỰ ĐỘNG", font=("Arial", 22, "bold"), fg="#2c3e50", bg="white").pack(anchor="w")
        fr_body = tk.Frame(self.fr_main, bg="#ecf0f1", padx=20, pady=20); fr_body.pack(fill="both", expand=True)
        fr_qr = tk.LabelFrame(fr_body, text="Quét Mã / Nhập Tên", font=("Arial", 12, "bold"), bg="white", padx=10, pady=5); fr_qr.pack(fill="x", pady=(0, 10))
        self.cb_qr = ttk.Combobox(fr_qr, font=("Arial", 20)); self.cb_qr.pack(fill="x", ipady=5); self.cb_qr.bind("<KeyRelease>", self.on_type_qr); self.cb_qr.bind("<Return>", self.on_scan); self.cb_qr.focus()
        fr_opt = tk.Frame(fr_body, bg="#ecf0f1"); fr_opt.pack(fill="x", pady=5)
        tk.Label(fr_opt, text="Hạn:", bg="#ecf0f1").pack(side="left"); self.cb_h = ttk.Combobox(fr_opt, values=["","7","30","90","180"], width=5); self.cb_h.pack(side="left", padx=5)
        tk.Label(fr_opt, text="PP:", bg="#ecf0f1").pack(side="left", padx=(20,0)); self.cb_p = ttk.Combobox(fr_opt, values=["","EO","Plasma","Hơi nước"], width=10); self.cb_p.pack(side="left", padx=5)
        self.cb_p.bind("<<ComboboxSelected>>", lambda e: setattr(self, 'selected_tk', self.cb_p.get()))
        fr_ph = tk.Frame(fr_body, bg="#ecf0f1"); fr_ph.pack(fill="x", pady=5); self.var_filter = tk.StringVar(value="ALL")
        tk.Label(fr_ph, text="Lọc:", bg="#ecf0f1").pack(side="left")
        tk.Radiobutton(fr_ph, text="Tất cả", variable=self.var_filter, value="ALL", bg="#ecf0f1", command=self.refresh_session_cb).pack(side="left")
        tk.Radiobutton(fr_ph, text="Phẫu thuật", variable=self.var_filter, value="PT", bg="#ecf0f1", command=self.refresh_session_cb).pack(side="left")
        tk.Radiobutton(fr_ph, text="Thủ thuật", variable=self.var_filter, value="TT", bg="#ecf0f1", command=self.refresh_session_cb).pack(side="left", padx=(0, 10))
        tk.Label(fr_ph, text="Chọn Phiên:", bg="#ecf0f1").pack(side="left"); self.cb_ph_display = ttk.Combobox(fr_ph, width=40, font=("Arial", 12)); self.cb_ph_display.pack(side="left", padx=5)
        tk.Button(fr_ph, text="TẢI DS", bg="#2980b9", fg="white", font=("Arial", 10, "bold"), command=self.tai_ds_phien).pack(side="left", padx=10)
        self.refresh_session_cb()
        self.fr_act = tk.Frame(fr_body, bg="#bdc3c7", pady=5); self.fr_act.pack(fill="x", pady=10)
        
        # --- ĐÃ THÊM 2 NÚT "IN BỘ" VÀ "IN ĐỒ LẺ" VÀO ĐÂY ---
        self.mk_act("TOÀN BỘ", "#2980b9")
        self.mk_act("BỘ", "#16a085")
        self.mk_act("ĐỒ LẺ", "#d35400")
        self.mk_act("Hơi nước", "#27ae60")
        self.mk_act("EO", "#f39c12")
        self.mk_act("Plasma", "#8e44ad")
        
        fr_lst = tk.Frame(fr_body, bg="white", bd=2, relief="sunken"); fr_lst.pack(fill="both", expand=True)
        self.cv_lst = tk.Canvas(fr_lst, bg="white"); sc = tk.Scrollbar(fr_lst, command=self.cv_lst.yview)
        self.fr_l = tk.Frame(self.cv_lst, bg="white"); self.cv_lst.create_window((0,0), window=self.fr_l, anchor="nw")
        self.cv_lst.configure(yscrollcommand=sc.set); self.cv_lst.pack(side="left", fill="both", expand=True); sc.pack(side="right", fill="y")
        self.fr_l.bind("<Configure>", lambda e: self.cv_lst.configure(scrollregion=self.cv_lst.bbox("all")))
        fr_b = tk.Frame(fr_body, bg="#ecf0f1"); fr_b.pack(fill="x", pady=10); self.lbl_s = tk.Label(fr_b, text="Sẵn sàng...", font=("Arial", 12, "italic"), fg="gray", bg="#ecf0f1"); self.lbl_s.pack(side="left")
        tk.Button(fr_b, text="IN THỦ CÔNG", bg="#e67e22", fg="white", font=("Arial", 10, "bold"), command=self.mo_form_thu_cong).pack(side="right")
    def mk_act(self, t, c): tk.Button(self.fr_act, text=f"IN {t}", bg=c, fg="white", font=("Arial", 11, "bold"), padx=10, command=lambda: self.print_bulk(t)).pack(side="left", padx=5)
    def refresh_session_cb(self):
        ft = self.var_filter.get(); ds_display, map_data = load_ds_phien_formatted(ft)
        self.map_ma_phien = map_data; self.cb_ph_display['values'] = ds_display
        if ds_display: self.cb_ph_display.current(0)
        else: self.cb_ph_display.set('')
    def on_type_qr(self, e): 
        v = self.cb_qr.get()
        if len(v)>=1: 
            s = get_suggestions(v)
            if s: self.cb_qr['values'] = s
    def on_scan(self, e):
        qr = self.cb_qr.get().strip()
        if not qr: return
        self.cb_qr.set('')
        
        t, d = xu_ly_qr_thong_minh(qr)
        
        if t == "BO":
            # d lúc này chứa 5 biến: id, ten, khoa, han, pp
            i_id, tb, k, h, p = d
            hu = int(self.cb_h.get()) if self.cb_h.get() else h
            pu = self.selected_tk if self.selected_tk else p
            
            # Cấp đủ 8 tham số: item_id, is_le, t, k_id, k_ten, h_db, pp_db, n
            self.do_print(i_id, False, tb, k, k, hu, pu, 1)
            self.lbl_s.config(text=f"Đã in: {tb}", fg="green")
            
        elif t == "LE":
            # Xử lý đồ lẻ / thủ thuật trả về từ json
            i_id, tb, k, h, p, is_le = d
            hu = int(self.cb_h.get()) if self.cb_h.get() else h
            pu = self.selected_tk if self.selected_tk else p
            
            self.do_print(i_id, is_le, tb, k, k, hu, pu, 1)
            self.lbl_s.config(text=f"Đã in: {tb}", fg="green")
            
        elif t == "KHOA": 
            self.render_table(d, lay_danh_sach_tong_hop(d))
            
        else: 
            self.lbl_s.config(text="Không tìm thấy dữ liệu!", fg="red")

    def render_table(self, k_title, ds):
        for w in self.fr_l.winfo_children(): w.destroy()
        self.list_items = []
        
        is_phau_thuat = k_title.upper() in ["GMHS", "GMHSTM", "GMHS S"]
        
        if is_phau_thuat:
            ds_bo = []
            ds_le = []
            for r in ds:
                is_le = True
                if len(r) == 9: is_le = r[5]
                if is_le: ds_le.append(r)
                else: ds_bo.append(r)
            
            # --- HIỂN THỊ KHỐI BỘ ---
            if ds_bo:
                tk.Label(self.fr_l, text="[ DANH SÁCH BỘ DỤNG CỤ ]", font=("Arial", 14, "bold"), bg="white", fg="#2980b9").pack(pady=(10, 5), anchor="w", padx=10)
                self._render_rows(ds_bo, k_title)
            
            # --- HIỂN THỊ KHỐI ĐỒ LẺ ---
            if ds_le:
                tk.Label(self.fr_l, text="[ DANH SÁCH ĐỒ ĐÓNG LẺ ]", font=("Arial", 14, "bold"), bg="white", fg="#e67e22").pack(pady=(15, 5), anchor="w", padx=10)
                self._render_rows(ds_le, k_title)
        else:
            tk.Label(self.fr_l, text=f"DANH SÁCH: {k_title}", font=("Arial", 14, "bold"), bg="white", fg="#2c3e50").pack(pady=10, anchor="w", padx=10)
            self._render_rows(ds, k_title)

    def _render_rows(self, ds_sub, k_title):
        for i, r in enumerate(ds_sub):
            bg = "#f9f9f9" if i%2==0 else "white"
            fr = tk.Frame(self.fr_l, bg=bg, pady=5, padx=5)
            fr.pack(fill="x")
            
            if len(r) == 9: 
                id_item, t, qt, sl, pp, is_le, k_id, h, k_ten = r
            elif len(r) == 6: 
                id_item, t, qt, sl, pp, h = r
                
                # Kiểm tra xem danh sách 6 cột này là của Phẫu thuật (đồ lẻ) hay Thủ thuật
                is_phau_thuat = k_title.upper() in ["GMHS", "GMHSTM", "GMHS S"]
                is_le = True if is_phau_thuat else "thu_thuat"
                
                k_id = k_title
                k_ten = k_title
            else: continue

            tk.Label(fr, text=t, font=("Arial", 12), width=40, anchor="w", bg=bg).pack(side="left")
            tk.Label(fr, text=pp, width=10, bg=bg, fg="gray").pack(side="left")
            tk.Label(fr, text=f"SL:{sl}", font=("Arial", 11, "bold"), width=8, bg=bg).pack(side="left")
            
            sl_in = math.ceil(sl/qt) if qt else sl
            e = tk.Entry(fr, width=5, font=("Arial", 12), justify="center")
            e.insert(0, str(sl_in))
            e.pack(side="left", padx=10)
            
            self.list_items.append({
                'id': id_item, 'is_le': is_le, 'ten': t, 
                'khoa_id': k_id, 'khoa_ten': k_ten, 
                'han': h, 'pp': pp, 'entry': e
            })
            
            def _p_one(i_id=id_item, l=is_le, ten_dc=t, kid=k_id, kten=k_ten, han_dc=h, pp_dc=pp, en=e):
                try: n=int(en.get())
                except: n=0
                if n>0: 
                    self.do_print(i_id, l, ten_dc, kid, kten, han_dc, pp_dc, n)
                    en.config(bg="#2ecc71")
                    
            tk.Button(fr, text="IN", bg="#3498db", fg="white", font=("Arial", 9, "bold"), command=_p_one).pack(side="left")
    def do_print(self, item_id, is_le, t, k_id, k_ten, h_db, pp_db, n):
        prof = get_current_profile(CURRENT_PRINTER_NAME)
        pr = int(prof.get('labels_per_row', 1))
        today = datetime.date.today()
        han = today + timedelta(days=h_db)
        pp = self.selected_tk if self.selected_tk else pp_db
        
        loai_str = "thu_thuat" if str(is_le) == "thu_thuat" else ("LẺ" if is_le else "BỘ")
        
        # Đã cập nhật truyền cả k_id và k_ten
        path = tao_anh_tem(item_id, t, k_id, k_ten, today.strftime('%d/%m/%Y'), han.strftime('%d/%m/%Y'), loai_str, CURRENT_USER_FULLNAME, pp)
        
        for _ in range(math.ceil(n/pr)): 
            thuc_hien_in(path)
            
        try: 
            if os.path.exists(path): os.remove(path)
        except: 
            pass
    def print_bulk(self, m):
        c = 0
        for i in self.list_items:
            try: n=int(i['entry'].get())
            except: n=0
            
            if n > 0:
                should_print = False
                # Bóc tách điều kiện in theo nút được bấm
                if m == "TOÀN BỘ": should_print = True
                elif m == "BỘ" and not i['is_le']: should_print = True
                elif m == "ĐỒ LẺ" and i['is_le']: should_print = True
                elif i['pp'] == m: should_print = True # Lọc theo phương pháp (EO, Hơi nước...)
                
                if should_print: 
                    self.do_print(i['id'], i['is_le'], i['ten'], i['khoa_id'], i['khoa_ten'], i['han'], i['pp'], n)
                    i['entry'].config(bg="#2ecc71")
                    c += n
                    
        self.lbl_s.config(text=f"Đã in xong {c} tem ({'HOÀN THÀNH' if m=='TOÀN BỘ' else m})", fg="blue")
    def tai_ds_phien(self):
        d_str = self.cb_ph_display.get()
        if not d_str: return
        real_ma = self.map_ma_phien.get(d_str)
        if not real_ma: 
            messagebox.showwarning("Lỗi", "Mã phiên không tồn tại!")
            return
            
        ds = lay_ds_theo_ma_phien_goc(real_ma)
        if ds: 
            # Bắt đúng Index 8 (Tên Khoa) để hiển thị lên chữ "DANH SÁCH: ..."
            ten_khoa_hien_thi = ds[0][8] if len(ds[0]) == 9 else ds[0][6]
            self.render_table(ten_khoa_hien_thi, ds)
        else: 
            messagebox.showinfo("TB", "Phiên trống")
    def show_settings(self):
        self.clear_main(); fr = tk.Frame(self.fr_main, bg="#ecf0f1", padx=30, pady=30); fr.pack(fill="both", expand=True)
        tk.Label(fr, text="CẤU HÌNH MÁY IN", font=("Arial", 20, "bold"), bg="#ecf0f1", fg="#2c3e50").pack(anchor="w", pady=(0, 20))
        pr = [p[2] for p in win32print.EnumPrinters(win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS)]
        cb = ttk.Combobox(fr, values=pr, font=("Arial", 12), width=40); global CURRENT_PRINTER_NAME
        if not CURRENT_PRINTER_NAME and pr: CURRENT_PRINTER_NAME = win32print.GetDefaultPrinter()
        cb.set(CURRENT_PRINTER_NAME); cb.pack(anchor="w", pady=5)
        fr_p = tk.LabelFrame(fr, text="Thông số", font=("Arial", 12, "bold"), bg="white", padx=20, pady=20); fr_p.pack(fill="x", pady=20)
        p = get_current_profile(CURRENT_PRINTER_NAME)
        tk.Label(fr_p, text="Scale W:", bg="white").grid(row=0,column=0,sticky="w",pady=5); ew=tk.Entry(fr_p); ew.insert(0,str(p.get('scale_w',1.0))); ew.grid(row=0,column=1,padx=10)
        tk.Label(fr_p, text="Scale H:", bg="white").grid(row=0,column=2,sticky="w",pady=5); eh=tk.Entry(fr_p); eh.insert(0,str(p.get('scale_h',1.0))); eh.grid(row=0,column=3,padx=10)
        tk.Label(fr_p, text="Off X:", bg="white").grid(row=1,column=0,sticky="w",pady=5); ex=tk.Entry(fr_p); ex.insert(0,str(p.get('offset_x',0))); ex.grid(row=1,column=1,padx=10)
        tk.Label(fr_p, text="Off Y:", bg="white").grid(row=1,column=2,sticky="w",pady=5); ey=tk.Entry(fr_p); ey.insert(0,str(p.get('offset_y',0))); ey.grid(row=1,column=3,padx=10)
        tk.Label(fr_p, text="Tem/Hàng:", bg="white").grid(row=2,column=0,sticky="w",pady=5); el=tk.Entry(fr_p); el.insert(0,str(p.get('labels_per_row',1))); el.grid(row=2,column=1,padx=10)
        def _up(e):
            p=get_current_profile(cb.get())
            for en,k in zip([ew,eh,ex,ey,el], ['scale_w','scale_h','offset_x','offset_y','labels_per_row']): en.delete(0,tk.END); en.insert(0,str(p.get(k,1.0)))
        cb.bind("<<ComboboxSelected>>", _up)
        def _sv():
            global CURRENT_PRINTER_NAME; CURRENT_PRINTER_NAME=cb.get()
            try: PRINTER_PROFILES[CURRENT_PRINTER_NAME]={'scale_w':float(ew.get()),'scale_h':float(eh.get()),'offset_x':int(ex.get()),'offset_y':int(ey.get()),'labels_per_row':int(el.get())}; luu_cau_hinh(); messagebox.showinfo("OK","Đã lưu!")
            except: pass
        tk.Button(fr, text="LƯU", font=("Arial", 12, "bold"), bg="#2980b9", fg="white", padx=20, command=_sv).pack(pady=10, anchor="w")
        def _v(sw, sh, ox, oy): ew.delete(0,tk.END); ew.insert(0,str(sw)); eh.delete(0,tk.END); eh.insert(0,str(sh)); ex.delete(0,tk.END); ex.insert(0,str(ox)); ey.delete(0,tk.END); ey.insert(0,str(oy)); _sv()
        tk.Button(fr, text="🔧 CĂN CHỈNH TRỰC QUAN", font=("Arial", 12, "bold"), bg="#e67e22", fg="white", padx=20, command=lambda: VisualAdjustWindow(self.root, self)).pack(pady=5, anchor="w")
        self.update_ui_from_visual = _v
    def mo_form_thu_cong(self):
        top = tk.Toplevel(self.root)
        top.geometry("500x400")
        top.title("In Thủ Công")
        f = tk.Frame(top, padx=20, pady=20)
        f.pack(fill="both", expand=True)
        
        tk.Label(f, text="Tên DC:", font=("Arial", 12)).grid(row=0,column=0,sticky="w",pady=5)
        et=tk.Entry(f, width=30, font=("Arial", 12)); et.grid(row=0,column=1,pady=5)
        
        tk.Label(f, text="Khoa:", font=("Arial", 12)).grid(row=1,column=0,sticky="w",pady=5)
        ek=ttk.Combobox(f, values=lay_ds_khoa_all(), width=28); ek.grid(row=1,column=1,pady=5)
        
        tk.Label(f, text="Hạn:", font=("Arial", 12)).grid(row=2,column=0,sticky="w",pady=5)
        eh=ttk.Combobox(f, values=["7","30","90","180"], width=10); eh.grid(row=2,column=1,sticky="w",pady=5)
        
        tk.Label(f, text="PP:", font=("Arial", 12)).grid(row=3,column=0,sticky="w",pady=5)
        ep=ttk.Combobox(f, values=["EO","Plasma","Hơi nước"], width=15); ep.grid(row=3,column=1,sticky="w",pady=5)
        
        tk.Label(f, text="SL:", font=("Arial", 12)).grid(row=4,column=0,sticky="w",pady=5)
        es=tk.Entry(f, width=10, font=("Arial", 12)); es.insert(0,"1"); es.grid(row=4,column=1,sticky="w",pady=5)
        
        def _in():
            try: 
                sl = int(es.get())
            except ValueError: 
                return
            h = int(eh.get()) if eh.get().isdigit() else 30
            p = ep.get() if ep.get() else "EO"
            
            # Truyền ID khoa bằng 0 để nó tự lấy Tên khoa nạp vào QR
            self.do_print(0, True, et.get(), 0, ek.get(), h, p, sl)

        # BỔ SUNG NÚT THỰC HIỆN IN Ở ĐÂY
        btn_in = tk.Button(f, text="🖨 THỰC HIỆN IN", font=("Arial", 12, "bold"), bg="#27ae60", fg="white", command=_in)
        btn_in.grid(row=5, column=0, columnspan=2, pady=25)
    def logout(self): self.root.destroy(); start_app()

def start_app():
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == '--subscreen':
        global CURRENT_USER, CURRENT_USER_FULLNAME
        CURRENT_USER = 'NV'
        CURRENT_USER_FULLNAME = 'Nhân viên (Từ App Chính)'
        main_root = tk.Tk()
        MainApp(main_root, is_subscreen=True)
        main_root.mainloop()
    else:
        def on_login_success(login_root): login_root.destroy(); main_root = tk.Tk(); MainApp(main_root); main_root.mainloop()
        root = tk.Tk(); LoginWindow(root, lambda: on_login_success(root)); root.mainloop()

if __name__ == "__main__":
    start_app()