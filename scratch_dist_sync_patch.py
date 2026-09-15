import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Replace the hardcoded 23:59:59 in sync_google_form
new_loop = '''                    for index, row in df.iterrows():
                        ts = str(row.iloc[0]).strip()
                        khoa_val = row.iloc[1]
                        if pd.isna(khoa_val):
                            continue
                        khoa = str(khoa_val).strip()
                        
                        # Skip non-data rows
                        if khoa.lower() in SKIP_KHOA or khoa == '':
                            continue
                        if not ts or ts.lower() == 'nan':
                            continue
                        
                        ts_ymd = parse_ts_to_ymd(ts)
                        if not ts_ymd:
                            continue
                        
                        if ts_ymd != sel_ymd:
                            continue
                            
                        # Extract real time instead of 23:59:59
                        time_part = "23:59:59"
                        if ' ' in ts:
                            try:
                                t_str = ts.split(' ', 1)[1].strip()
                                parts = t_str.split(':')
                                if len(parts) == 2:
                                    time_part = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:00"
                                elif len(parts) >= 3:
                                    time_part = f"{parts[0].zfill(2)}:{parts[1].zfill(2)}:{parts[2][:2].zfill(2)}"
                            except: pass
                        
                        actual_time = f"{ts_ymd} {time_part}"
                        
                        # Insert one row per item that has quantity > 0
                        for col_name in item_cols:
                            val = row[col_name]
                            if pd.isna(val):
                                continue
                            try:
                                sl = int(float(str(val).replace(',', '.')))
                            except:
                                continue
                            if sl <= 0:
                                continue
                            
                            col_str = str(col_name).strip()
                            # Lookup mapping
                            mapped = mapping_dict.get(col_str)
                            if mapped:
                                ma_do = mapped['ma_do']
                                loai_ghi = mapped['loai'] or 'vai'
                            else:
                                ma_do = col_str[:100]
                                loai_ghi = 'khac'
                            
                            self.db.execute(
                                "INSERT INTO lich_su_giao_nhan (khoa_giao, ma_do, so_luong, thoi_gian, trang_thai) VALUES (%s, %s, %s, %s, %s)",
                                (khoa[:100], ma_do, sl, actual_time, 'CHO_TIEP_NHAN')
                            )
                            count += 1'''

c = re.sub(r'                    for index, row in df\.iterrows\(\).*?count \+= 1', new_loop, c, flags=re.DOTALL)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'w', encoding='utf-8') as f:
    f.write(c)
