# -*- coding: utf-8 -*-
"""一次性:把舊網址的四個頁面從 git 移除(讓舊連結 404)。用 git ls-files -z 精準比對,避開中文檔名編碼問題。"""
import subprocess, os
os.chdir(os.path.dirname(os.path.abspath(__file__)))
def sh(a): return subprocess.run(a, capture_output=True, text=True)
tracked = sh(['git','ls-files','-z']).stdout.split('\0')
targets = {'gap.html','daytrade.html','hub-5c8e2a.html','主力選股.html'}
hit = 0
for t in tracked:
    if t and os.path.basename(t) in targets:
        r = sh(['git','rm','-f','--',t])
        print(('  移除 %s' % t) if r.returncode==0 else ('  略過 %s (%s)' % (t, (r.stderr or '').strip())))
        hit += 1 if r.returncode==0 else 0
print('舊頁移除完成:%d 個(待 add/commit/push)' % hit if hit else '沒有找到要移除的舊頁(可能已移除)')
