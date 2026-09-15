import sys, re

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Delete the duplicated old ones
match = re.search(r'    def get_kpi_sterilized_drilldown\(self, date_str\):\n        sql = """\n            SELECT ma_phien.*?return bos', text, re.DOTALL)
if match:
    text = text.replace(match.group(0), '')
    
with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\models\db_manager.py', 'w', encoding='utf-8') as f:
    f.write(text)
