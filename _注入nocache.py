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

if __name__ == '__main__':
    try:
        main()
    except Exception:
        err = traceback.format_exc(); print(err)
        try: open(os.path.join(HERE, '_注入nocache_錯誤.txt'), 'w', encoding='utf-8').write(err)
        except Exception: pass
    if os.name == 'nt' and 'auto' not in sys.argv[1:]:
        os.system('pause')
