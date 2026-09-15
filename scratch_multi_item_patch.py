import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\multi_item_dialog.py', 'r', encoding='utf-8') as f:
    c = f.read()

new_search = '''        search_txt = self.txt_search.text().strip()
        if search_txt.startswith("ID:"):
            parts = search_txt.split(",")
            search_txt = parts[0].replace("ID:", "").strip()
        search_txt = remove_vietnamese_accents(search_txt)'''

c = c.replace('search_txt = remove_vietnamese_accents(self.txt_search.text())', new_search)

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\utils\multi_item_dialog.py', 'w', encoding='utf-8') as f:
    f.write(c)
