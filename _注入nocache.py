# -*- coding: utf-8 -*-
r"""發布前自動幫「網站部署」資料夾底下所有 .html 注入 no-cache 標記。
   目的:手機/換網路不會卡在舊版(GitHub Pages 的 html 預設會被瀏覽器快取)。
   由 ★只上傳網頁.bat / ★每日發布上網.bat 在 git push 前呼叫;冪等(已有就跳過),
   涵蓋現在與未來所有頁(gap/主力選股/daytrade/回顧/week_holders/尾盤急拉/族群牆…)。
   用法:python _注入nocache.py        (雙擊會暫停)
         python _注入nocache.py auto  (排程/bat 呼叫不暫停)
"""
import os, sys, glob, traceback
try: sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception: pass
import warnings; warnings.filterwarnings('ignore')
HERE = os.path.dirname(os.path.abspath(__file__))
META = ('<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">'
        '<meta http-equiv="Pragma" content="no-cache"><meta http-equiv="Expires" content="0">')

def inject(fp):
    try:
        s = open(fp, encoding='utf-8', errors='ignore').read()
    except Exception:
        return False
    if 'no-store' in s[:3000]:      # 已注入 → 跳過(冪等)
        return False
    low = s.lower()
    pos = -1
    for tag in ('<meta charset', '<head', '<html', '<!doctype'):   # 依序找插入點
        i = low.find(tag)
        if i >= 0:
            j = s.find('>', i)
            if j >= 0:
                pos = j + 1
                break
    if pos < 0:
        pos = 0
    s2 = s[:pos] + META + s[pos:]
    try:
        open(fp, 'w', encoding='utf-8').write(s2)
        return True
    except Exception:
        return False


# 2026-10-17 使用者:「網頁變成 app」→ 每頁 <head> 加 App 標記(手機「加入主畫面」後全螢幕開、圖示是「交」)+ App 模式才出現的 ‹ 返回 / 🏠 總入口 浮動鈕
PWA = ('<!--PWA--><link rel="manifest" href="app.webmanifest" crossorigin="use-credentials"><meta name="theme-color" content="#0f1115">'
       '<link rel="apple-touch-icon" href="app-icon-180.png"><meta name="apple-mobile-web-app-capable" content="yes"><meta name="mobile-web-app-capable" content="yes">'
       '<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent"><meta name="apple-mobile-web-app-title" content="交易報表">'
       '<style>#appnav{display:none;position:fixed;right:12px;bottom:calc(14px + env(safe-area-inset-bottom));z-index:99999;gap:8px}'
       '#appnav a{display:flex;align-items:center;justify-content:center;width:44px;height:44px;border-radius:22px;background:rgba(20,22,30,.88);color:#ffd166;'
       'font:20px system-ui;text-decoration:none;border:1px solid #d63384;box-shadow:0 2px 10px rgba(0,0,0,.4)}'
       '@media (display-mode: standalone){#appnav{display:flex}}</style>'
       '<script>if(navigator.standalone)document.documentElement.classList.add("ios-app");'
       'document.addEventListener("DOMContentLoaded",function(){if(document.getElementById("appnav"))return;var n=document.createElement("div");n.id="appnav";'
       'n.innerHTML=\'<a href="javascript:history.back()" title="返回">‹</a><a href="app-start.html" title="總入口">🏠</a>\';document.body.appendChild(n);'
       'if(navigator.standalone)n.style.display="flex"});'
       'if("serviceWorker" in navigator)navigator.serviceWorker.register("sw.js").catch(function(){});</script><!--/PWA-->')


def inject_pwa(fp):
    if os.path.basename(fp) in ('app-start.html',): return False
    try: s = open(fp, encoding='utf-8', errors='ignore').read()
    except Exception: return False
    if '<!--PWA-->' in s: return False
    low = s.lower(); i = low.find('</head>')
    if i < 0: return False
    try: open(fp, 'w', encoding='utf-8').write(s[:i] + PWA + s[i:]); return True
    except Exception: return False

def main():
    n = 0; done = 0
    for fp in sorted(glob.glob(os.path.join(HERE, '*.html'))):
        n += 1
        try:
            if inject(fp):
                done += 1; print('  +no-cache', os.path.basename(fp), flush=True)
        except Exception as e:
            print('  略過', os.path.basename(fp), str(e)[:60], flush=True)
    print('no-cache 注入完成:掃 %d 個 html,補了 %d 個(其餘已有,跳過)' % (n, done), flush=True)
    k = sum(1 for fp in sorted(glob.glob(os.path.join(HERE, '*.html'))) if inject_pwa(fp))
    print('App 標記(網頁變 App)補了 %d 個' % k, flush=True)

if __name__ == '__main__':
    try:
        main()
    except Exception:
        err = traceback.format_exc(); print(err)
        try: open(os.path.join(HERE, '_注入nocache_錯誤.txt'), 'w', encoding='utf-8').write(err)
        except Exception: pass
    if os.name == 'nt' and 'auto' not in sys.argv[1:]:
        os.system('pause')
