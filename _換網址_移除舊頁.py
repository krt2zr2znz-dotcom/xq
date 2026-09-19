# -*- coding: utf-8 -*-
"""換網址一次性處理(UTF-8,避開 cp950/中文檔名問題):
   1) 把現有舊頁內容複製成新檔名(新網址立刻可用)
   2) 重產 hub(連結指向新檔名)
   3) 從 git 移除舊的四個頁面(舊網址 404)
   之後由 bat 做 git add/commit/push 與 wrangler deploy。"""
import subprocess, os, shutil, sys
HERE = os.path.dirname(os.path.abspath(__file__))              # 04_輸出結果/網站部署
BASE = os.path.dirname(os.path.dirname(HERE))                  # 專案根
os.chdir(HERE)
def sh(a): return subprocess.run(a, capture_output=True)       # bytes,自己 decode

# 1) 舊頁 -> 新檔名(內容一致,先讓新網址能開)
for old, new in [('gap.html','gap-a0cc38.html'),
                 ('主力選股.html','主力選股-8259b2.html'),
                 ('daytrade.html','daytrade-98f13b.html')]:
    if os.path.exists(old):
        shutil.copy2(old, new); print('  複製 %s -> %s' % (old, new))
    else:
        print('  (找不到 %s,略過複製;之後排程會自己產新檔)' % old)

# 2) 重產 hub(卡片連結=新檔名)
hubgen = os.path.join(BASE, '07_自動化腳本', '總入口網頁.py')
r = subprocess.run([sys.executable, hubgen], capture_output=True)
print('  hub 重產:', 'OK -> hub-7e9b59.html' if r.returncode == 0
      else 'FAIL ' + r.stderr.decode('utf-8', 'replace')[:200])

# 3) git 移除舊四頁(用 ls-files -z 精準比對,decode utf-8)
old_all = {'gap.html','daytrade.html','hub-5c8e2a.html','主力選股.html'}
tracked = sh(['git','ls-files','-z']).stdout.decode('utf-8','replace').split('\0')
hit = 0
for t in tracked:
    if t and os.path.basename(t) in old_all:
        rr = sh(['git','rm','-f','--',t]); ok = rr.returncode == 0
        print(('  移除 %s' % t) if ok else ('  略過 %s (%s)' % (t, rr.stderr.decode('utf-8','replace').strip())))
        hit += 1 if ok else 0
print('舊頁移除:%d 個(待 add/commit/push)' % hit)
