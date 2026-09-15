import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\sterilization_controller.py', 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("trang_thai='DA_KHU_NHIEM'", "trang_thai IN ('DA_KHU_NHIEM', 'DA_DONG_GOI')")

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\controllers\sterilization_controller.py', 'w', encoding='utf-8') as f:
    f.write(c)
