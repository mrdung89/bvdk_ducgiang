import os
import sys
import json
import urllib.request
import zipfile
import shutil
import subprocess

GITHUB_USER = 'TEN_TAI_KHOAN_GITHUB'
GITHUB_REPO = 'TEN_REPO_GITHUB'
BRANCH = 'main'

VERSION_FILE = 'version.txt'
APP_MAIN = 'main.py'

def get_latest_commit():
    url = f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/commits/{BRANCH}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Ksnk-Updater'})
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode()).get('sha')
    except Exception as e:
        print('[!] Khong the kiem tra phien ban tren GitHub:', e)
        return None

def download_and_extract_zip():
    url = f'https://github.com/{GITHUB_USER}/{GITHUB_REPO}/archive/refs/heads/{BRANCH}.zip'
    zip_path = 'update.zip'
    print(f'[*] Dang tai ban cap nhat...')
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Ksnk-Updater'})
        with urllib.request.urlopen(req, timeout=30) as response, open(zip_path, 'wb') as out:
            shutil.copyfileobj(response, out)
        print('[*] Giai nen...')
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall('temp_update')
            extracted_folder = os.path.join('temp_update', os.listdir('temp_update')[0])
            for item in os.listdir(extracted_folder):
                if item in ['updater.py', '.gitignore', 'db_info.json']: continue # Skip replacing these
                s = os.path.join(extracted_folder, item)
                d = os.path.join(os.getcwd(), item)
                if os.path.isdir(s):
                    if os.path.exists(d): shutil.rmtree(d)
                    shutil.copytree(s, d)
                else:
                    shutil.copy2(s, d)
        shutil.rmtree('temp_update')
        os.remove(zip_path)
        print('[*] Cap nhat thanh cong!')
        return True
    except Exception as e:
        print('[!] Loi cap nhat:', e)
        return False

def main():
    print('=== LAUNCHER AUTO-UPDATE ===')
    current_sha = open(VERSION_FILE).read().strip() if os.path.exists(VERSION_FILE) else ''
    latest_sha = get_latest_commit()
    
    if latest_sha and latest_sha != current_sha:
        print(f'[!] Phat hien phien ban moi: {latest_sha[:7]}')
        if download_and_extract_zip():
            with open(VERSION_FILE, 'w') as f: f.write(latest_sha)
    else:
        print('[*] Dang su dung phien ban moi nhat hoac khong co ket noi.')
        
    print('[*] Khoi dong phan mem...')
    subprocess.Popen([sys.executable, APP_MAIN])

if __name__ == '__main__':
    main()
