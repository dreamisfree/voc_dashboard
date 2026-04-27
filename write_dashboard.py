"""
빌드 스크립트: style.css / app.js / template.html 을 각각 생성합니다.
수정 흐름:
  1. 이 파일의 CSS_CONTENT / JS_CONTENT / HTML_TEMPLATE 섹션을 편집
  2. python write_dashboard.py  →  style.css, app.js, template.html 생성
  3. python embed_data.py --password <비번>  →  dashboard.html 빌드
  4. git push  →  GitHub Pages 배포
"""

BASE = 'D:/voc_20260424'

# ──────────────────────────────────────────────
# 1. CSS  (style.css)
# ──────────────────────────────────────────────
CSS_CONTENT = """\
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: "Apple SD Gothic Neo", "Malgun Gothic", "나눔고딕", sans-serif; background: #f0f2f7; color: #222; min-width: 320px; }
/* ── 로그인 ── */
#loginOverlay { position: fixed; inset: 0; background: #1a1a2e; display: flex; align-items: center; justify-content: center; z-index: 999; }
.login-box { background: #fff; border-radius: 16px; padding: 48px 40px; width: 360px; text-align: center; box-shadow: 0 8px 40px rgba(0,0,0,.4); }
.login-box h2 { font-size: 1.2rem; font-weight: 700; color: #1a1a2e; margin-bottom: 6px; }
.login-box p { font-size: .82rem; color: #888; margin-bottom: 28px; }
.login-box input { width: 100%; padding: 12px 16px; border: 1.5px solid #ddd; border-radius: 8px; font-size: .95rem; outline: none; transition: border-color .18s; margin-bottom: 12px; }
.login-box input:focus { border-color: #3f51b5; }
.login-box button { width: 100%; padding: 12px; background: #3f51b5; color: #fff; border: none; border-radius: 8px; font-size: .95rem; font-weight: 700; cursor: pointer; transition: background .18s; }
.login-box button:hover { background: #303f9f; }
.login-box button:disabled { background: #aaa; cursor: default; }
#pwError { font-size: .8rem; color: #e53935; margin-top: 10px; min-height: 18px; }
#pwLoading { font-size: .8rem; color: #3f51b5; margin-top: 10px; min-height: 18px; }
/* ── 앱 ── */
#app { display: none; min-width: 1280px; }
header { background: #1a1a2e; color: #fff; padding: 16px 36px; display: flex; align-items: center; }
header h1 { font-size: 1.15rem; font-weight: 700; }
header span { margin-left: auto; font-size: .78rem; color: #8888aa; }
.brand-tabs { background: #fff; border-bottom: 2px solid #e0e0e0; padding: 0 36px; display: flex; gap: 2px; position: sticky; top: 0; z-index: 100; box-shadow: 0 2px 6px rgba(0,0,0,.08); }
.brand-tab { padding: 13px 20px; cursor: pointer; font-size: .88rem; font-weight: 600; color: #777; border-bottom: 3px solid transparent; transition: all .18s; white-space: nowrap; }
.brand-tab:hover { color: #333; }
.brand-tab.active { color: #1a1a2e; border-bottom-color: #3f51b5; }
.main { padding: 20px 36px; }
.summary-bar { display: flex; gap: 16px; margin-bottom: 16px; align-items: center; }
.stat-chip { background: #fff; border-radius: 8px; padding: 10px 18px; font-size: .82rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); }
.stat-chip strong { font-size: 1.1rem; margin-left: 6px; color: #1a1a2e; }
.item-tabs-wrap { overflow-x: auto; margin-bottom: 18px; padding-bottom: 4px; }
.item-tabs { display: flex; gap: 8px; flex-wrap: nowrap; }
.item-tab { flex-shrink: 0; background: #fff; border: 2px solid #ddd; border-radius: 10px; padding: 10px 16px; cursor: pointer; font-size: .85rem; font-weight: 600; color: #666; transition: all .18s; box-shadow: 0 1px 4px rgba(0,0,0,.06); display: flex; flex-direction: column; gap: 3px; }
.item-tab:hover { border-color: #9fa8da; color: #3f51b5; }
.item-tab.active { background: #3f51b5; border-color: #3f51b5; color: #fff; box-shadow: 0 3px 10px rgba(63,81,181,.3); }
.item-tab-name { font-size: .88rem; }
.item-tab-codes { font-size: .67rem; font-weight: 400; opacity: .75; }
.panels { display: grid; grid-template-columns: 260px 1fr; gap: 18px; align-items: start; }
.cat-panel { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.08); overflow: hidden; display: flex; flex-direction: column; max-height: 600px; }
.cat-panel-title { padding: 13px 18px; font-size: .78rem; font-weight: 700; color: #888; background: #f8f9fc; border-bottom: 1px solid #eee; letter-spacing: .3px; text-transform: uppercase; flex-shrink: 0; }
.cat-panel-list { overflow-y: auto; flex: 1; }
.cat-row { display: flex; flex-direction: column; padding: 13px 18px; cursor: pointer; border-bottom: 1px solid #f0f0f0; border-left: 4px solid transparent; transition: background .15s; gap: 5px; }
.cat-row:last-child { border-bottom: none; }
.cat-row:hover { background: #f5f7ff; }
.cat-row.active { background: #eef0fb; border-left-color: #3f51b5; }
.cat-row-top { display: flex; align-items: baseline; gap: 6px; }
.cat-row-name { font-size: .9rem; font-weight: 700; color: #1a1a2e; }
.cat-row-cnt { font-size: .74rem; color: #999; margin-left: auto; white-space: nowrap; }
.sent-bar { height: 5px; border-radius: 3px; background: #eee; overflow: hidden; }
.sent-bar-inner { height: 100%; border-radius: 3px; }
.sent-labels { display: flex; justify-content: space-between; font-size: .68rem; }
.lbl-neg { color: #e53935; font-weight: 600; }
.lbl-pos { color: #43a047; font-weight: 600; }
.review-panel { background: #fff; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,.08); padding: 22px 26px; min-height: 420px; }
.review-panel-title { font-size: 1rem; font-weight: 700; color: #1a1a2e; margin-bottom: 18px; padding-bottom: 14px; border-bottom: 2px solid #eef0fb; display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.badge { font-size: .7rem; font-weight: 700; padding: 3px 9px; border-radius: 20px; }
.badge-neg { background: #ffebee; color: #c62828; }
.badge-pos { background: #e8f5e9; color: #2e7d32; }
.section-label { font-size: .74rem; font-weight: 700; color: #aaa; letter-spacing: .6px; text-transform: uppercase; margin: 16px 0 10px; }
.section-label:first-of-type { margin-top: 0; }
.review-card { border-radius: 8px; padding: 14px 16px; margin-bottom: 10px; border-left: 4px solid #eee; font-size: .85rem; line-height: 1.75; color: #333; }
.review-card.neg { background: #fff8f8; border-left-color: #ef9a9a; }
.review-card.pos { background: #f6fff6; border-left-color: #a5d6a7; }
.review-text { margin-bottom: 8px; word-break: keep-all; }
.review-meta { display: flex; gap: 6px; flex-wrap: wrap; }
.tag { font-size: .68rem; font-weight: 600; padding: 2px 7px; border-radius: 20px; }
.tag.channel { background: #e3f2fd; color: #1565c0; }
.tag.season  { background: #f3e5f5; color: #7b1fa2; }
.tag.product { background: #fff8e1; color: #e65100; }
.divider { border: none; border-top: 1px dashed #e8e8e8; margin: 18px 0; }
.no-data { color: #ccc; font-size: .85rem; text-align: center; padding: 40px 0; }
"""

# ──────────────────────────────────────────────
# 2. JS 로직  (app.js)
# ──────────────────────────────────────────────
JS_CONTENT = open('D:/voc_20260424/app.js', encoding='utf-8').read()

# ──────────────────────────────────────────────
# 3. HTML 골격  (template.html)
# ──────────────────────────────────────────────
HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<title>VOC 인사이트 대시보드</title>
<link rel="stylesheet" href="style.css">
</head>
<body>

<!-- 로그인 화면 -->
<div id="loginOverlay">
  <div class="login-box">
    <h2>VOC 인사이트 대시보드</h2>
    <p>이랜드 패션사업부 · 아이템별 고객 리뷰 분석</p>
    <input type="password" id="pwInput" placeholder="비밀번호를 입력하세요" onkeydown="if(event.key==='Enter')unlock()">
    <button id="unlockBtn" onclick="unlock()">확인</button>
    <div id="pwLoading"></div>
    <div id="pwError"></div>
  </div>
</div>

<!-- 대시보드 -->
<div id="app">
  <header><h1>VOC 인사이트 대시보드</h1><span>이랜드 패션사업부 · 아이템별 고객 리뷰 분석</span></header>
  <div class="brand-tabs" id="brandTabs"></div>
  <div class="main" id="mainContent"></div>
</div>

<script>
const VOC_ENCRYPTED = {};
</script>
<script src="app.js"></script>
</body>
</html>
"""

# ──────────────────────────────────────────────
# 파일 쓰기
# ──────────────────────────────────────────────
import os

files = {
    'style.css': CSS_CONTENT,
    'app.js': JS_CONTENT,
    'template.html': HTML_TEMPLATE,
}

for name, content in files.items():
    path = os.path.join(BASE, name)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f'OK: {name} ({len(content.splitlines())}줄)')

print()
print('다음 단계: python embed_data.py --password <비번>')
