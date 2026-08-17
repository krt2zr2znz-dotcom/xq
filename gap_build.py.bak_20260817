# -*- coding: utf-8 -*-
"""產「差價區間選股」頁 gap.html(放 網站部署,一鍵_日報2 一起發布)。自足單檔。"""
import os,sys,glob,json,warnings
warnings.filterwarnings('ignore')
import pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.dirname(os.path.dirname(HERE))
HD=os.path.join(BASE,'08_歷史股價下載')
px=pd.read_csv(os.path.join(HD,'股價一年.csv'),encoding='utf-8-sig',dtype=str)
px=px[px['代碼'].str.match(r'^\d{4}$',na=False)].copy()
for c in ['開盤','最高','最低','收盤','昨收','漲跌幅%']: px[c]=pd.to_numeric(px[c],errors='coerce')
px=px.dropna(subset=['收盤']).sort_values(['代碼','日期'])
DATE=px['日期'].max()
first={}
for fp in [os.path.join(HD,'全市場1分K_A.csv'),os.path.join(HD,'全市場1分K_B.csv')]+glob.glob(os.path.join(HD,'補1分K_%s.csv'%DATE)):
    if not os.path.exists(fp): continue
    with open(fp,encoding='utf-8-sig',errors='ignore') as f:
        next(f,None)
        for ln in f:
            p=ln.split(',')
            if len(p)<8 or p[1]!=DATE: continue
            t=p[2][:5]
            if t<'09:00' or t>'09:04': continue
            try: hi=float(p[4]); lo=float(p[5])
            except Exception: continue
            d=first.setdefault(p[0],[hi,lo])
            if hi>d[0]: d[0]=hi
            if lo<d[1]: d[1]=lo
def feats(d):
    ma=d['收盤'].rolling(20).mean(); sd=d['收盤'].rolling(20).std(ddof=0); d['布上']=ma+2*sd
    low9=d['最低'].rolling(9).min(); high9=d['最高'].rolling(9).max()
    d['K']=((d['收盤']-low9)/(high9-low9)*100).ewm(alpha=1/3,adjust=False).mean(); return d
px=px.groupby('代碼',group_keys=False).apply(feats)
r=px[px['日期']==DATE].copy()
r['h5']=r['代碼'].map(lambda c:first.get(c,[None,None])[0]); r['l5']=r['代碼'].map(lambda c:first.get(c,[None,None])[1])
r['R']=r['h5']-r['l5']; r['gap']=r['R']/r['開盤']*100
data=[]
for _,x in r.iterrows():
    zt=bool(x['漲跌幅%']>=9.5); zb=bool(x['收盤']>x['布上']); lb=bool((x['收盤']<=x['布上']) and (x['收盤']>=x['布上']*0.98))
    k=x['K']; gap=x['gap']
    if pd.isna(k): continue
    if not (zt or zb or lb or k>75 or (pd.notna(gap) and gap>2)): continue
    data.append({'c':x['代碼'],'nm':str(x['商品']),'op':round(float(x['開盤']),2),'px':round(float(x['收盤']),2),'chg':round(float(x['漲跌幅%']),2),
        'k':round(float(k),1),'bu':round(float(x['布上']),2) if pd.notna(x['布上']) else None,
        'gap':round(float(gap),2) if pd.notna(gap) else None,
        'h5':round(float(x['h5']),2) if pd.notna(x['h5']) else None,'l5':round(float(x['l5']),2) if pd.notna(x['l5']) else None,
        'R':round(float(x['R']),2) if pd.notna(x['R']) else None,
        'zt':zt,'ztk':bool(x['開盤']>=x['昨收']*1.095),'xh':bool((x['收盤']>x['開盤']) and (x['收盤']>x['昨收'])),'zb':zb,'lb':lb})
J=json.dumps(data,ensure_ascii=False)
CSS="*{box-sizing:border-box}body{margin:0;background:#0d1826;color:#e8f0fb;font:14px/1.5 -apple-system,'Noto Sans TC',Segoe UI,sans-serif}\n.wrap{max-width:1500px;margin:0 auto;padding:16px}\n.top{background:linear-gradient(90deg,#16324f,#132437);border-radius:12px;padding:14px 20px;margin-bottom:12px}\n.top h1{margin:0;font-size:20px}.top .d{color:#8aa1bd;font-size:13px;margin-top:4px}\n.panel{background:#132437;border:1px solid #22384f;border-radius:10px;padding:12px 16px;margin-bottom:12px}\n.presets{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}\n.presets button{background:#1c3a59;color:#e8f0fb;border:1px solid #2b4a68;border-radius:8px;padding:6px 14px;cursor:pointer}\n.presets button:hover{background:#245079}\n.conds{display:flex;gap:12px 20px;flex-wrap:wrap;align-items:center}\nlabel.ck{display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}label.ck input{width:17px;height:17px;accent-color:#4aa3ff}\n.num{display:flex;align-items:center;gap:6px}.num input{width:54px;background:#0f2135;border:1px solid #2b4a68;color:#e8f0fb;border-radius:6px;padding:4px 6px;text-align:right}\n.cnt{color:#ffd24a;font-weight:700}\n.tb-scroll{overflow-x:auto;border-radius:10px}\ntable{border-collapse:collapse;background:#132437;font-size:13px;min-width:1460px;width:100%}\nth{background:#0f2135;color:#8aa1bd;text-align:right;padding:7px 9px;cursor:pointer;white-space:nowrap;position:sticky;top:0}\nth:first-child,th:nth-child(2){text-align:left}\ntd{padding:6px 9px;border-top:1px solid #22384f;white-space:nowrap}\ntd.c{color:#4aa3ff;font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums}\n.up{color:#ff5b6a}.dn{color:#4bd07f}.hl{color:#ffd24a;font-weight:700}\n.press{color:#ff8a95}.supp{color:#7fe0a3}.yiz{background:#ffd24a;color:#12233a;font-weight:800;border-radius:4px}\nth.pg{color:#ff8a95}th.sg{color:#7fe0a3}\ntbody tr:nth-child(even){background:#0f2033}\n.foot,.leg{color:#8aa1bd;font-size:12px;margin-top:10px}"
JS="\nvar DATA=__DATA__;\nfunction on(id){return document.getElementById(id).checked}\nfunction val(id){return parseFloat(document.getElementById(id).value)||0}\nfunction pass(s){\n if(on('zb')&&!s.zb)return false; if(on('lb')&&!s.lb)return false;\n if(on('zt')&&!s.zt)return false; if(on('nzt')&&s.zt)return false;\n if(on('ztk')&&!s.ztk)return false; if(on('xh')&&!s.xh)return false;\n if(on('kd')&&!(s.k>val('kv')))return false;\n if(on('gp')&&!(s.gap!=null&&s.gap>val('gv')))return false;\n if(on('yz')&&!(s.op===s.px))return false; return true;\n}\nfunction lv(s){ if(s.R==null)return null; var up=s.px*1.1,dn=s.px*0.9;\n return {P:[1,2,3].map(function(n){return Math.min(s.px+n*s.R,up)}),S:[1,2,3].map(function(n){return Math.max(s.px-n*s.R,dn)})};}\nfunction f(v){return v==null?'-':v.toFixed(2)}\nvar sortKey='gap',sortDir=-1;\nfunction keyval(s,k){\n if(k=='p1'||k=='p2'||k=='p3'){var L=lv(s);return L?L.P[{p1:0,p2:1,p3:2}[k]]:null;}\n if(k=='s1'||k=='s2'||k=='s3'){var L=lv(s);return L?L.S[{s1:0,s2:1,s3:2}[k]]:null;}\n return s[k];\n}\nfunction render(){\n var rows=DATA.filter(pass);\n rows.sort(function(a,b){var x=keyval(a,sortKey),y=keyval(b,sortKey);if(x==null)x=-1e9;if(y==null)y=-1e9;return (x>y?1:x<y?-1:0)*sortDir});\n var h='';\n for(var i=0;i<rows.length;i++){var s=rows[i];var L=lv(s);var yz=(s.op===s.px);var oc=yz?' yiz':'';\n  var P=L?L.P:[null,null,null],S=L?L.S:[null,null,null];\n  h+='<tr><td class=\"c\">'+s.c+'</td><td>'+s.nm+(yz?' <span class=\"yiz\" style=\"padding:0 4px\">一字</span>':'')+'</td>'+\n     '<td class=\"n'+oc+'\">'+f(s.op)+'</td><td class=\"n'+oc+'\">'+f(s.px)+'</td>'+\n     '<td class=\"n '+(s.chg>0?'up':'dn')+'\">'+(s.chg>0?'+':'')+s.chg.toFixed(2)+'</td>'+\n     '<td class=\"n\">'+s.k.toFixed(1)+'</td><td class=\"n hl\">'+(s.gap!=null?s.gap.toFixed(2):'-')+'</td>'+\n     '<td class=\"n\">'+f(s.h5)+'</td><td class=\"n\">'+f(s.l5)+'</td><td class=\"n hl\">'+f(s.R)+'</td>'+\n     '<td class=\"n press\">'+f(P[0])+'</td><td class=\"n press\">'+f(P[1])+'</td><td class=\"n press\">'+f(P[2])+'</td>'+\n     '<td class=\"n supp\">'+f(S[0])+'</td><td class=\"n supp\">'+f(S[1])+'</td><td class=\"n supp\">'+f(S[2])+'</td></tr>';\n }\n document.getElementById('tb').innerHTML=h||'<tr><td colspan=16 style=\"text-align:center;color:#8aa1bd;padding:14px\">— 無符合,放寬條件 —</td></tr>';\n document.getElementById('cnt').textContent=rows.length;\n}\nfunction preset(p){\n ['zb','lb','zt','nzt','ztk','xh','kd','gp','yz'].forEach(function(i){document.getElementById(i).checked=false});\n if(p=='5.1'){zb.checked=zt.checked=kd.checked=gp.checked=true;kv.value=80;gv.value=4;}\n if(p=='5.2'){zb.checked=xh.checked=nzt.checked=kd.checked=gp.checked=true;kv.value=85;gv.value=4;}\n if(p=='5.3'){lb.checked=ztk.checked=zt.checked=kd.checked=gp.checked=true;kv.value=80;gv.value=4;}\n render();\n}\nfunction sortBy(k){if(sortKey==k)sortDir*=-1;else{sortKey=k;sortDir=-1}render();}\nwindow.onload=function(){document.querySelectorAll('input').forEach(function(el){el.addEventListener('input',render)});render();};\n"
H=('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
 '<title>差價區間選股 · '+DATE+'</title><style>'+CSS+'</style><div class="wrap">'
 '<div class="top"><h1>差價區間選股</h1><div class="d">'+DATE+' · R=第一根5分K高−低 · 起點=收盤 · R1~R3壓/撐 · 開=收(一字)反白</div></div>'
 '<div class="panel"><div class="presets">一鍵套用:<button onclick="preset(\'5.1\')">5.1</button><button onclick="preset(\'5.2\')">5.2</button><button onclick="preset(\'5.3\')">5.3</button><span style="color:#8aa1bd">符合 <span class="cnt" id="cnt">0</span> 檔</span></div>'
 '<div class="conds">'
 '<label class="ck"><input type="checkbox" id="zb">站上布林</label><label class="ck"><input type="checkbox" id="lb">臨近布林</label>'
 '<label class="ck"><input type="checkbox" id="zt">漲停</label><label class="ck"><input type="checkbox" id="nzt">非漲停</label>'
 '<label class="ck"><input type="checkbox" id="ztk">漲停開門</label><label class="ck"><input type="checkbox" id="xh">隔日續紅</label>'
 '<label class="ck"><input type="checkbox" id="yz">一字(開=收)</label>'
 '<span class="num"><label class="ck"><input type="checkbox" id="kd">KD&gt;</label><input id="kv" value="80"></span>'
 '<span class="num"><label class="ck"><input type="checkbox" id="gp">差價%&gt;</label><input id="gv" value="4"></span>'
 '</div></div><div class="tb-scroll"><table><thead><tr>'
 '<th onclick="sortBy(\'c\')">代碼</th><th>名稱</th><th onclick="sortBy(\'op\')">開盤</th><th onclick="sortBy(\'px\')">收盤</th><th onclick="sortBy(\'chg\')">漲跌%</th>'
 '<th onclick="sortBy(\'k\')">K</th><th onclick="sortBy(\'gap\')">差價%</th>'
 '<th onclick="sortBy(\'h5\')">5K高</th><th onclick="sortBy(\'l5\')">5K低</th><th onclick="sortBy(\'R\')">R價差</th>'
 '<th class="pg" onclick="sortBy(\'p1\')">R1壓</th><th class="pg" onclick="sortBy(\'p2\')">R2壓</th><th class="pg" onclick="sortBy(\'p3\')">R3壓</th>'
 '<th class="sg" onclick="sortBy(\'s1\')">R1撐</th><th class="sg" onclick="sortBy(\'s2\')">R2撐</th><th class="sg" onclick="sortBy(\'s3\')">R3撐</th>'
 '</tr></thead><tbody id="tb"></tbody></table></div>'
 '<script>'+JS.replace('__DATA__',J)+'</script></div></html>')
open(os.path.join(HERE,'gap.html'),'w',encoding='utf-8').write(H)
print('gap.html 產出:%d 檔,日期 %s'%(len(data),DATE))
