import json, re, os, base64, argparse
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes


def encrypt_json(data_str: str, password: str) -> str:
    salt = os.urandom(16)
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=100000)
    key = kdf.derive(password.encode('utf-8'))
    iv = os.urandom(12)
    ct = AESGCM(key).encrypt(iv, data_str.encode('utf-8'), None)
    return json.dumps({
        'salt': base64.b64encode(salt).decode(),
        'iv':   base64.b64encode(iv).decode(),
        'ct':   base64.b64encode(ct).decode(),
    })


parser = argparse.ArgumentParser()
parser.add_argument('--password', required=True, help='대시보드 접근 비밀번호')
args = parser.parse_args()

with open('D:/voc_20260424/data.json', encoding='utf-8') as f:
    data = json.load(f)
data_str = json.dumps(data, ensure_ascii=False)

encrypted_str = encrypt_json(data_str, args.password)

with open('D:/voc_20260424/template.html', encoding='utf-8') as f:
    html = f.read()

new_line = 'const VOC_ENCRYPTED = ' + encrypted_str + ';'
html_new = re.sub(r'const VOC_ENCRYPTED = .*;', new_line, html)

if html_new == html:
    print('ERROR: VOC_ENCRYPTED 패턴을 찾지 못했습니다.')
else:
    with open('D:/voc_20260424/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html_new)
    print('OK: 암호화 완료 → dashboard.html 빌드 완료')
