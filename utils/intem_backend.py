import qrcode
from PIL import Image, ImageDraw, ImageFont, ImageWin, ImageTk
import datetime
from datetime import timedelta
import os
import win32print
import win32ui
import json
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
    s = re.sub(r'[đ]', 'd', s)
    s = re.sub(r'[Đ]', 'D', s)
    return s

CONFIG_FILE = "print_settings.json"
TEMP_IMAGE = "temp_tem.png"

TEM_WIDTH_PX, TEM_HEIGHT_PX = 900, 240 

CURRENT_PRINTER_NAME = ""
CURRENT_USER_FULLNAME = "NV KSNK"

PRINTER_PROFILES = {}

def lay_cau_hinh():
    global PRINTER_PROFILES, CURRENT_PRINTER_NAME
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                PRINTER_PROFILES = data.get('printer_profiles', {})
                CURRENT_PRINTER_NAME = data.get('last_printer', '')
                if not CURRENT_PRINTER_NAME:
                    CURRENT_PRINTER_NAME = win32print.GetDefaultPrinter()
                return
        except: pass
    PRINTER_PROFILES = {}
    try: CURRENT_PRINTER_NAME = win32print.GetDefaultPrinter()
    except: CURRENT_PRINTER_NAME = ""

def luu_cau_hinh():
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump({
                'printer_profiles': PRINTER_PROFILES,
                'last_printer': CURRENT_PRINTER_NAME
            }, f, indent=4)
    except: pass

def get_current_profile(pname):
    if not PRINTER_PROFILES: lay_cau_hinh()
    return PRINTER_PROFILES.get(pname, {
        'scale_w': 1.0, 'scale_h': 1.0,
        'offset_x': 0, 'offset_y': 0,
        'labels_per_row': 1
    })

def tao_anh_tem(item_id, ten, khoa_id, ten_khoa, ngay_tk, han_tk, loai_dung_cu, ten_nhan_vien, phuong_phap):
    type_code = 'bo'
    if loai_dung_cu is not None:
        loai_str = str(loai_dung_cu).lower()
        if 'lẻ' in loai_str or 'le' in loai_str or str(loai_dung_cu) == 'True':
            type_code = 'LE'
        elif 'thủ thuật' in loai_str or 'thu_thuat' in loai_str:
            type_code = 'thu_thuat'

    if type_code == 'bo':
        qr_content = str(item_id)
    elif type_code == 'LE':
        khoa_str = khoa_id if khoa_id else remove_vn_accents(str(ten_khoa)).strip()
        qr_content = f"ID:{item_id}, KHOA:{khoa_str}, LOAI:LE"
    elif type_code == 'thu_thuat':
        khoa_str = khoa_id if khoa_id else remove_vn_accents(str(ten_khoa)).strip()
        qr_content = f"ID:{item_id}, KHOA:{khoa_str}, LOAI:THU_THUAT"
    else:
        qr_content = str(item_id)

    qr = qrcode.make(qr_content).resize((135, 135))
    img_full = Image.new('RGB', (TEM_WIDTH_PX, TEM_HEIGHT_PX), 'white')
    draw = ImageDraw.Draw(img_full)
    
    try:
        font_large = ImageFont.truetype('arialbd.ttf', 16)
        font_small = ImageFont.truetype('arial.ttf', 18)
    except:
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()
        
    img_full.paste(qr, (220, 8))

    def draw_text(x, y, text, font):
        draw.text((x, y), text, font=font, fill='black')
        
    text_x, start_y, line_h = (360, 15, 25)
    display_ten = str(ten) if len(str(ten)) <= 25 else str(ten)[:22] + '...'
    
    draw_text(text_x, start_y, f'Tên: {display_ten}', font_large)
    draw_text(text_x, start_y + line_h, f'Khoa: {ten_khoa}', font_small)
    draw_text(text_x, start_y + line_h * 2, f'Ngày TK: {ngay_tk}', font_small)
    draw_text(text_x, start_y + line_h * 3, f'Hạn TK: {han_tk}', font_small)
    draw_text(text_x, start_y + line_h * 4, f'TK: {phuong_phap}', font_small)
    draw_text(text_x, start_y + line_h * 5, f'NV: {ten_nhan_vien}', font_small)
    
    draw_text(230, 145, 'BVĐK Đức Giang', font_large)
    
    img_full.save(TEMP_IMAGE)
    return TEMP_IMAGE

def thuc_hien_in(path_anh, printer_name=None):
    if not printer_name:
        printer_name = CURRENT_PRINTER_NAME or win32print.GetDefaultPrinter()
        
    profile = get_current_profile(printer_name)
    scale_w, scale_h = (float(profile.get('scale_w', 1.0)), float(profile.get('scale_h', 1.0)))
    off_x, off_y = (int(profile.get('offset_x', 0)), int(profile.get('offset_y', 0)))
    
    try:
        hprinter = win32print.OpenPrinter(printer_name)
        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)
        hdc.StartDoc('Tem KSNK')
        hdc.StartPage()
        
        img = Image.open(path_anh)
        dib = ImageWin.Dib(img)
        w_new, h_new = (int(TEM_WIDTH_PX * scale_w), int(TEM_HEIGHT_PX * scale_h))
        dib.draw(hdc.GetHandleOutput(), (off_x, off_y, off_x + w_new, off_y + h_new))
        
        hdc.EndPage()
        hdc.EndDoc()
        hdc.DeleteDC()
        win32print.ClosePrinter(hprinter)
    except Exception as e:
        print(f"Lỗi in tem: {e}")
