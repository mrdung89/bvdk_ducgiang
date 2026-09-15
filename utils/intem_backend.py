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
    except Exception as e: print("Lỗi In", f"Lỗi máy in: {e}")

# =================================================================================
# 5. DESIGNER
# =================================================================================

