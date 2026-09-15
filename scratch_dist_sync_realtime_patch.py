import sys

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'r', encoding='utf-8') as f:
    c = f.read()

import re

# Find the parsing block
c = c.replace('time_part = "23:59:59"', 'from datetime import datetime\n                        time_part = datetime.now().strftime("%H:%M:%S")')

with open(r'C:\Users\Admin\Desktop\bvdkdg\bvdk_ducgiang\views\distribution.py', 'w', encoding='utf-8') as f:
    f.write(c)
