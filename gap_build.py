# -*- coding: utf-8 -*-
"""產「差價區間選股」頁 gap-a0cc38.html(放 網站部署,一鍵_日報2 一起發布)。自足單檔。"""
import os,sys,glob,json,warnings
warnings.filterwarnings('ignore')
import pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); BASE=os.path.dirname(os.path.dirname(HERE))
HD=os.path.join(BASE,'08_歷史股價下載')
px=pd.read_csv(os.path.join(HD,'股價一年.csv'),encoding='utf-8-sig',dtype=str)
px=px[px['代碼'].str.match(r'^\d{4}$',na=False)].copy()
px=px[~px['交易所'].astype(str).str.contains('興櫃',na=False)].copy()  # ★排除興櫃(XQ鐵律)
for c in ['開盤','最高','最低','收盤','昨收','漲跌幅%','成交量']: px[c]=pd.to_numeric(px[c],errors='coerce')
px=px.dropna(subset=['收盤']).sort_values(['代碼','日期'])
DATE=px['日期'].max()
# ★第一根5分K(09:00~09:04 高/低):近 22 個交易日全部算(給回看/回測用差價%與R),快取在 第一根5分K_歷史.csv,只補缺的日期
_alld=sorted(px['日期'].unique()); NEEDD=set(_alld[-22:])|{DATE}
_cacheF=os.path.join(HD,'第一根5分K_歷史.csv'); FIRST={}
if os.path.exists(_cacheF):
    try:
        _cd=pd.read_csv(_cacheF,dtype={'代碼':str,'日期':str})
        for _c,_d,_h,_l in zip(_cd['代碼'],_cd['日期'],_cd['h5'],_cd['l5']): FIRST[(_c,_d)]=[float(_h),float(_l)]
    except Exception as _e: print('  [warn] 第一根5分K快取讀取略過',_e)
_haved={d for (_,d) in FIRST}
MISSD={d for d in NEEDD if d not in _haved}|{DATE}     # 今天永遠重掃(補1分K_今日 可能後到)
print('  第一根5分K:需要 %d 日,快取已有 %d 日,重掃 %d 日'%(len(NEEDD),len(NEEDD-MISSD),len(MISSD)))
_new={}
for fp in [os.path.join(HD,'全市場1分K_A.csv'),os.path.join(HD,'全市場1分K_B.csv')]+glob.glob(os.path.join(HD,'補1分K_*.csv')):
    if not os.path.exists(fp) or not MISSD: continue
    with open(fp,encoding='utf-8-sig',errors='ignore') as f:
        next(f,None)
        for ln in f:
            p=ln.split(',')
            if len(p)<8 or p[1] not in MISSD: continue
            t=p[2][:5]
            if t<'09:00' or t>'09:04': continue
            try: hi=float(p[4]); lo=float(p[5])
            except Exception: continue
            d=_new.setdefault((p[0],p[1]),[hi,lo])
            if hi>d[0]: d[0]=hi
            if lo<d[1]: d[1]=lo
if _new:
    for k,v in _new.items(): FIRST[k]=v
    try:
        _rows=[(c,d,v[0],v[1]) for (c,d),v in FIRST.items() if d in NEEDD or d>DATE]
        pd.DataFrame(_rows,columns=['代碼','日期','h5','l5']).to_csv(_cacheF,index=False,encoding='utf-8-sig')
        print('  第一根5分K 快取更新:%d 筆'%len(_rows))
    except Exception as _e: print('  [warn] 快取寫入略過',_e)
first={c:v for (c,d),v in FIRST.items() if d==DATE}
g=px.groupby('代碼')
_ma=g['收盤'].transform(lambda s:s.rolling(20).mean()); _sd=g['收盤'].transform(lambda s:s.rolling(20).std(ddof=0))
px['布上']=_ma+2*_sd
px['中軌']=_ma
px['MA5']=g['收盤'].transform(lambda s:s.rolling(5).mean())
px['MA10']=g['收盤'].transform(lambda s:s.rolling(10).mean())
_lo9=g['最低'].transform(lambda s:s.rolling(9).min()); _hi9=g['最高'].transform(lambda s:s.rolling(9).max())
_rsv=(px['收盤']-_lo9)/(_hi9-_lo9)*100
px['K']=_rsv.groupby(px['代碼']).transform(lambda s:s.ewm(alpha=1/3,adjust=False).mean())
r=px[px['日期']==DATE].copy()
r['h5']=r['代碼'].map(lambda c:first.get(c,[None,None])[0]); r['l5']=r['代碼'].map(lambda c:first.get(c,[None,None])[1])
r['R']=r['h5']-r['l5']; r['gap']=r['R']/r['開盤']*100
# ★波段壓 X = 最近一段(≥3根)連紅 的最低 + (該段高−低)×2 (呂冠霖波段:起漲底+R×2)
def _wave_x(_g):
    import pandas as _pd
    o=_g['開盤'].tolist(); c=_g['收盤'].tolist(); h=_g['最高'].tolist(); l=_g['最低'].tolist()
    n=len(c); baseLo=None; baseHi=None; i=0
    while i<n:
        if _pd.notna(c[i]) and _pd.notna(o[i]) and c[i]>=o[i]:
            j=i; rl=l[i]; rh=h[i]
            while j+1<n and _pd.notna(c[j+1]) and _pd.notna(o[j+1]) and c[j+1]>=o[j+1]:
                j+=1
                if _pd.notna(l[j]) and l[j]<rl: rl=l[j]
                if _pd.notna(h[j]) and h[j]>rh: rh=h[j]
            if (j-i+1)>=3: baseLo=rl; baseHi=rh
            i=j+1
        else:
            i+=1
    if baseLo is None or baseHi is None: return None
    return round(float(baseLo+2*(baseHi-baseLo)),2)
bx_map={_code:_wave_x(_g) for _code,_g in px.groupby('代碼')}
r['bx']=r['代碼'].map(bx_map)
DISP={}
_dispF=os.path.join(HD,'處置股歷史.csv')
if os.path.exists(_dispF):
    import datetime as _dtm
    try: _near=(_dtm.date.fromisoformat(DATE)+_dtm.timedelta(days=7)).isoformat()
    except Exception: _near=DATE
    _mm={'二':'2','五':'5','十':'10','二十':'20'}
    try:
        _dz=pd.read_csv(_dispF,encoding='utf-8-sig',dtype=str).fillna('')
        for _,_zr in _dz.iterrows():
            _c=str(_zr.get('代碼','')).strip();_d1=str(_zr.get('處置起日','')).strip();_d2=str(_zr.get('處置迄日','')).strip()
            if not(_c and _d1 and _d2):continue
            if _d2<=DATE or _d1>_near:continue
            _m=str(_zr.get('撮合分鐘','')).strip();_m=_mm.get(_m,_m)
            _cur=DISP.get(_c)
            if _cur is None or _d1>_cur[0]:DISP[_c]=(_d1,_d2,_m)
    except Exception as _e: print('  [warn]處置略過',_e)
print('  處置中:%d 檔'%len(DISP))
# ★雙重撐壓:日5/10/20MA、布林上軌 落在 R1/2/3 壓撐(現價×0.75%容差,同價去重)
def _dualstr(px,R,ma5,ma10,ma20,bu):
    if px is None or R is None or R<=0: return ''
    up=px*1.1; dn=px*0.9; tol=px*0.0075
    P=[min(px+n*R,up) for n in (1,2,3)]; S=[max(px-n*R,dn) for n in (1,2,3)]
    LN=[('5MA',ma5),('10MA',ma10),('20MA',ma20),('上軌',bu)]
    lv=[('壓R%d'%(i+1),P[i]) for i in range(3)]+[('撐R%d'%(j+1),S[j]) for j in range(3)]
    mp={}
    for nm,v in LN:
        if v is None: continue
        best=None; bd=1e18
        for kk,pv in lv:
            d=abs(v-pv)
            if d<bd: bd=d; best=kk
        if best is not None and bd<=tol: mp.setdefault(best,[]).append(nm)
    order=['壓R1','壓R2','壓R3','撐R1','撐R2','撐R3']
    return ' '.join(k+'·'+'+'.join(mp[k]) for k in order if k in mp)
data=[]
for _,x in r.iterrows():
    zt=bool(x['漲跌幅%']>=9.5); zb=bool(x['收盤']>x['布上']); lb=bool((x['收盤']<=x['布上']) and (x['收盤']>=x['布上']*0.98))
    _nb=bool(pd.notna(x['布上']) and x['收盤']>=x['布上']*0.95)   # ★收錄到上軌下方5%(給網頁可調臨近%,預設2%用)
    k=x['K']; gap=x['gap']
    if pd.isna(k): continue
    if not (zt or _nb or k>75 or (pd.notna(gap) and gap>2)): continue
    data.append({'c':x['代碼'],'nm':str(x['商品']),'mk':str(x['交易所']),'disp':(('處置'+DISP[x['代碼']][0][5:]+'~'+DISP[x['代碼']][1][5:]+((' '+DISP[x['代碼']][2]+'分') if DISP[x['代碼']][2] else '')) if x['代碼'] in DISP else ''),'op':round(float(x['開盤']),2),'px':round(float(x['收盤']),2),'chg':round(float(x['漲跌幅%']),2),'vol':round(float(x['成交量'])/1000) if pd.notna(x['成交量']) else None,
        'k':round(float(k),1),'bu':round(float(x['布上']),2) if pd.notna(x['布上']) else None,
        'gap':round(float(gap),2) if pd.notna(gap) else None,
        'h5':round(float(x['h5']),2) if pd.notna(x['h5']) else None,'l5':round(float(x['l5']),2) if pd.notna(x['l5']) else None,
        'R':round(float(x['R']),2) if pd.notna(x['R']) else None,
        'gvol':(round(float(x['成交量'])/1000) if (pd.notna(x['成交量']) and pd.notna(x['收盤']) and pd.notna(x['開盤']) and x['收盤']<x['開盤']) else None),'bx':(round(float(x['bx']),2) if pd.notna(x['bx']) else None),'ma5':(round(float(x['MA5']),2) if pd.notna(x['MA5']) else None),'ma10':(round(float(x['MA10']),2) if pd.notna(x['MA10']) else None),'mid':(round(float(x['中軌']),2) if pd.notna(x['中軌']) else None),'dual':_dualstr(round(float(x['收盤']),2),(round(float(x['R']),2) if pd.notna(x['R']) else None),(round(float(x['MA5']),2) if pd.notna(x['MA5']) else None),(round(float(x['MA10']),2) if pd.notna(x['MA10']) else None),(round(float(x['中軌']),2) if pd.notna(x['中軌']) else None),(round(float(x['布上']),2) if pd.notna(x['布上']) else None)),'zt':zt,'ztk':bool(x['開盤']>=x['昨收']*1.095),'xh':bool((x['收盤']>x['開盤']) and (x['收盤']>x['昨收'])),'zb':zb,'lb':lb})
_bt_all=sorted(px['日期'].unique()); _btd=set(_bt_all[-22:])
def _tick(p): return 0.01 if p<10 else 0.05 if p<50 else 0.1 if p<100 else 0.5 if p<500 else 1.0 if p<1000 else 5.0
def _limup(p):
    import math; tk=_tick(p*1.1); return math.floor(p*1.1/tk+1e-9)*tk
def _wave_series(o,c,h,l):
    """每個索引 i 的波段壓X(只看到 i 為止):最後一段>=3根連紅(含正在進行中的)的 低+(高-低)*2"""
    n=len(c); out=[None]*n; lastLo=lastHi=None; runLo=runHi=None; runN=0
    for i in range(n):
        red=(pd.notna(c[i]) and pd.notna(o[i]) and c[i]>=o[i])
        if red:
            runN+=1; runLo=l[i] if (runLo is None or (pd.notna(l[i]) and l[i]<runLo)) else runLo; runHi=h[i] if (runHi is None or (pd.notna(h[i]) and h[i]>runHi)) else runHi
        else:
            if runN>=3: lastLo,lastHi=runLo,runHi
            runN=0; runLo=runHi=None
        if runN>=3 and runLo is not None: out[i]=round(float(runLo+2*(runHi-runLo)),2)
        elif lastLo is not None: out[i]=round(float(lastLo+2*(lastHi-lastLo)),2)
    return out
def _r2(v): return round(float(v),2) if pd.notna(v) else None
HIST={}   # 日期 -> [row...] 欄位與今日 data 相同 + 隔日結果(n1o/n1h/n1l/n1c/n1hl/n3c/n5c)+ 碰R1/R2(t1/t2)
for _code,_g in px.sort_values(['代碼','日期']).groupby('代碼'):
    _g=_g.reset_index(drop=True); _n=len(_g)
    _cl=_g['收盤'].tolist();_op=_g['開盤'].tolist();_hi=_g['最高'].tolist();_lo=_g['最低'].tolist();_vo=_g['成交量'].tolist()
    _dt=_g['日期'].tolist();_k=_g['K'].tolist();_bu=_g['布上'].tolist();_ch=_g['漲跌幅%'].tolist();_yc=_g['昨收'].tolist();_nm=str(_g['商品'].iloc[0]);_mk=str(_g['交易所'].iloc[0])
    _m5=_g['MA5'].tolist();_m10=_g['MA10'].tolist();_mid=_g['中軌'].tolist()
    _bxs=_wave_series(_op,_cl,_hi,_lo)
    for i in range(_n):
        d=_dt[i]
        if d not in _btd: continue
        cl=_cl[i]
        if pd.isna(cl) or pd.isna(_k[i]): continue
        f5=FIRST.get((_code,d)); R=(f5[0]-f5[1]) if f5 else None; gap=(R/_op[i]*100) if (R is not None and pd.notna(_op[i]) and _op[i]) else None
        zt=bool(_ch[i]>=9.5); zb=bool(pd.notna(_bu[i]) and cl>_bu[i]); lb=bool(pd.notna(_bu[i]) and cl<=_bu[i] and cl>=_bu[i]*0.98)
        ztk=bool(pd.notna(_yc[i]) and _op[i]>=_yc[i]*1.095); xh=bool(pd.notna(_yc[i]) and cl>_op[i] and cl>_yc[i])
        _nb=bool(pd.notna(_bu[i]) and cl>=_bu[i]*0.95)
        if not (zt or _nb or _k[i]>75 or (gap is not None and gap>2)): continue     # ★與今日表同一個收錄範圍
        row={'d':d,'c':_code,'nm':_nm,'mk':_mk,'disp':'','op':_r2(_op[i]),'px':_r2(cl),'chg':_r2(_ch[i]),'vol':(int(round(_vo[i]/1000)) if pd.notna(_vo[i]) else None),
             'k':round(float(_k[i]),1),'bu':_r2(_bu[i]),'gap':(round(gap,2) if gap is not None else None),'h5':(_r2(f5[0]) if f5 else None),'l5':(_r2(f5[1]) if f5 else None),'R':(_r2(R) if R is not None else None),
             'bx':_bxs[i],'ma5':_r2(_m5[i]),'ma10':_r2(_m10[i]),'mid':_r2(_mid[i]),'zt':zt,'ztk':ztk,'xh':xh,'zb':zb,'lb':lb}
        if i+1<_n and pd.notna(_op[i+1]) and pd.notna(_cl[i+1]):
            row['n1o']=round((_op[i+1]/cl-1)*100,2);row['n1h']=round((_hi[i+1]/cl-1)*100,2);row['n1l']=round((_lo[i+1]/cl-1)*100,2);row['n1c']=round((_cl[i+1]/cl-1)*100,2);row['n1hl']=bool(_op[i+1]>cl and _cl[i+1]>_op[i+1])
            if R is not None and R>0:
                _lu=_limup(cl); _p1=min(cl+R,_lu); _p2=min(cl+2*R,_lu)
                row['t1']=bool(_hi[i+1]>=_p1-1e-9); row['t2']=bool(_hi[i+1]>=_p2-1e-9); row['o1']=bool(_op[i+1]<_p1)
        else:
            row['n1o']=None;row['n1h']=None;row['n1l']=None;row['n1c']=None;row['n1hl']=False
        row['n3c']=round((_cl[i+3]/cl-1)*100,2) if i+3<_n and pd.notna(_cl[i+3]) else None
        row['n5c']=round((_cl[i+5]/cl-1)*100,2) if i+5<_n and pd.notna(_cl[i+5]) else None
        HIST.setdefault(d,[]).append(row)
print('  回看 %d 天:%s'%(len(HIST),', '.join('%s=%d'%(k[5:],len(v)) for k,v in sorted(HIST.items()))))
HJSON=json.dumps(HIST,ensure_ascii=False)
J=json.dumps(data,ensure_ascii=False)
CSS="*{box-sizing:border-box}body{margin:0;background:#0d1826;color:#e8f0fb;font:14px/1.5 -apple-system,'Noto Sans TC',Segoe UI,sans-serif}\n.wrap{max-width:100%;margin:0 auto;padding:10px}\n.top{background:linear-gradient(90deg,#16324f,#132437);border-radius:12px;padding:14px 20px;margin-bottom:12px}\n.top h1{margin:0;font-size:20px}.top .d{color:#8aa1bd;font-size:13px;margin-top:4px}\n.panel{background:#132437;border:1px solid #22384f;border-radius:10px;padding:12px 16px;margin-bottom:12px}\n.presets{display:flex;gap:8px;margin-bottom:10px;flex-wrap:wrap;align-items:center}\n.presets button{background:#1c3a59;color:#e8f0fb;border:1px solid #2b4a68;border-radius:8px;padding:6px 14px;cursor:pointer}\n.presets button:hover{background:#245079}\n.conds{display:flex;gap:12px 20px;flex-wrap:wrap;align-items:center}\nlabel.ck{display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}label.ck input{width:17px;height:17px;accent-color:#4aa3ff}\n.num{display:flex;align-items:center;gap:6px}.num input{width:54px;background:#0f2135;border:1px solid #2b4a68;color:#e8f0fb;border-radius:6px;padding:4px 6px;text-align:right}\n.cnt{color:#ffd24a;font-weight:700}\n.tb-scroll{overflow-x:auto;border-radius:10px}\ntable{border-collapse:collapse;background:#132437;font-size:12px;min-width:0;width:100%}\nth{background:#0f2135;color:#8aa1bd;text-align:right;padding:4px 6px;cursor:pointer;white-space:nowrap;position:sticky;top:0}\nth:first-child,th:nth-child(2){text-align:left}\ntd{padding:4px 6px;border-top:1px solid #22384f;white-space:nowrap}\ntd.c{color:#4aa3ff;font-weight:600}td.n{text-align:right;font-variant-numeric:tabular-nums}\n.up{color:#ff5b6a}.dn{color:#4bd07f}.hl{color:#ffd24a;font-weight:700}\n.press{color:#ff8a95}.supp{color:#7fe0a3}.yiz{background:#ffd24a;color:#12233a;font-weight:800;border-radius:4px}\nth.pg{color:#ff8a95}th.sg{color:#7fe0a3}\ntbody tr:nth-child(even){background:#0f2033}\n.foot,.leg{color:#8aa1bd;font-size:12px;margin-top:10px}.vcb{width:16px;height:16px;cursor:pointer;accent-color:#4aa3ff;vertical-align:middle}tr.vlock{background:#20344a !important}tr.vlock td:nth-child(2){border-left:3px solid #ffd24a}.vbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-top:10px;padding-top:10px;border-top:1px solid #22384f;color:#8aa1bd;font-size:13px}.vbtn{background:#1c3a59;color:#e8f0fb;border:1px solid #2b4a68;border-radius:8px;padding:5px 12px;cursor:pointer;font-weight:700}.vbtn.on{background:#ffd24a;color:#12233a}.vbtn2{background:#132437;color:#8aa1bd;border:1px solid #2b4a68;border-radius:8px;padding:5px 12px;cursor:pointer}#bt{margin-top:12px}#bt table{border-collapse:collapse;width:100%;font-size:12px;background:#132437}#bt th{background:#0f2135;color:#8aa1bd;padding:6px 7px;position:sticky;top:0;white-space:nowrap}#bt td{padding:5px 7px;border-top:1px solid #22384f;text-align:right;white-space:nowrap}"
JS="\nvar DATA0=__DATA__;var DATE0=__DATE__;var HIST=__HIST__;var DATA=DATA0;var DATE=DATE0;var VKEY='V選股';function vGet(){try{return JSON.parse(localStorage.getItem(VKEY)||'{}')}catch(e){return {}}}function vSave(x){try{localStorage.setItem(VKEY,JSON.stringify(x))}catch(e){}}var VSEL=vGet(),VONLY=false,LASTROWS=[],NL=String.fromCharCode(10),Q=String.fromCharCode(34);var VDB=' <span style='+Q+'color:#ff8a95;font-size:11px'+Q+'>處</span>';function vtd(c){return '<td class='+Q+'l'+Q+'><input type='+Q+'checkbox'+Q+' class='+Q+'vcb'+Q+' data-c='+Q+c+Q+(VSEL[c]?' checked':'')+'></td>';}function vtr(c){return VSEL[c]?' class='+Q+'vlock'+Q:'';}function tvSym(s){return (String(s.mk).indexOf('櫃')>=0?'TPEX:':'TWSE:')+s.c;}function tvSyms(a){return a.map(tvSym);}function dlTV(a,tag){if(!a.length){alert('清單是空的');return;}var t='###差價區間 '+DATE+(tag?' '+tag:'')+NL+tvSyms(a).join(',')+NL;var el=document.createElement('a');el.href=URL.createObjectURL(new Blob([t],{type:'text/plain'}));el.download='差價區間_'+DATE+'_'+(tag||'')+'_TV.txt';document.body.appendChild(el);el.click();el.remove();}\nfunction dualOf(s){if(s.dual!=null)return s.dual;var px=s.px,R=s.R;if(px==null||R==null||R<=0)return '';var up=px*1.1,dn=px*0.9,tol=px*0.0075;var P=[1,2,3].map(function(n){return Math.min(px+n*R,up)}),S=[1,2,3].map(function(n){return Math.max(px-n*R,dn)});var LN=[['5MA',s.ma5],['10MA',s.ma10],['20MA',s.mid],['上軌',s.bu]];var lv=[['壓R1',P[0]],['壓R2',P[1]],['壓R3',P[2]],['撐R1',S[0]],['撐R2',S[1]],['撐R3',S[2]]];var mp={};LN.forEach(function(x){if(x[1]==null)return;var best=null,bd=1e18;lv.forEach(function(y){var d=Math.abs(x[1]-y[1]);if(d<bd){bd=d;best=y[0];}});if(best!=null&&bd<=tol){(mp[best]=mp[best]||[]).push(x[0]);}});return ['壓R1','壓R2','壓R3','撐R1','撐R2','撐R3'].filter(function(k){return mp[k]}).map(function(k){return k+'·'+mp[k].join('+')}).join(' ');}\nfunction fmp(v){return v==null?'—':(v>0?'+':'')+v.toFixed(2)+'%'}function clp(v){return v==null?'':v>0?'up':v<0?'dn':''}function yn(v){return v==null?'—':(v?'是':'否')}\nfunction setDate(d){DATE=d;DATA=(d===DATE0?DATA0:(HIST[d]||[]));var m=document.getElementById('meta');if(m)m.textContent=(d===DATE0?'':'回看 ')+d+' · R=第一根5分K高−低 · 起點=收盤 · R1~R3壓/撐 · 開=收(一字)反白'+(d===DATE0?'':' · 隔日欄位=該日訊號的隔天結果(處置欄僅最新日有)');render();}\nfunction on(id){return document.getElementById(id).checked}\nfunction val(id){return parseFloat(document.getElementById(id).value)||0}\nfunction zbHit(pr,bu){return bu!=null&&pr!=null&&pr>bu*(1+val('zbv')/100)}\nfunction lbHit(pr,bu){return bu!=null&&pr!=null&&pr<=bu&&pr>=bu*(1-val('lbv')/100)}\nfunction pass(s){\n if(on('zb')&&!zbHit(s.px,s.bu))return false; if(on('lb')&&!lbHit(s.px,s.bu))return false;\n if(on('zt')&&!s.zt)return false; if(on('nzt')&&s.zt)return false;\n if(on('ztk')&&!s.ztk)return false; if(on('xh')&&!s.xh)return false;\n if(on('kd')&&!(s.k>val('kv')))return false;\n if(on('gp')&&!(s.gap!=null&&s.gap>val('gv')))return false;\n if(on('gk')&&!(s.vol!=null&&s.vol>=val('gkv')))return false;\n if(on('yz')&&!(s.op===s.px))return false; if(on('hd')&&s.disp)return false; return true;\n}\nfunction lv(s){ if(s.R==null)return null; var up=s.px*1.1,dn=s.px*0.9;\n return {P:[1,2,3].map(function(n){return Math.min(s.px+n*s.R,up)}),S:[1,2,3].map(function(n){return Math.max(s.px-n*s.R,dn)})};}\nfunction f(v){return v==null?'-':v.toFixed(2)}\nfunction pct(v,base){if(v==null||base==null||base==0)return '';var d=(v/base-1)*100;return ' <span style=color:#8aa1bd;font-size:11px>('+(d>=0?'+':'')+d.toFixed(1)+'%)</span>';}\nvar sortKey='gap',sortDir=-1;\nfunction keyval(s,k){\n if(k=='p1'||k=='p2'||k=='p3'){var L=lv(s);return L?L.P[{p1:0,p2:1,p3:2}[k]]:null;}\n if(k=='s1'||k=='s2'||k=='s3'){var L=lv(s);return L?L.S[{s1:0,s2:1,s3:2}[k]]:null;}\n return s[k];\n}\nfunction render(){\n var rows=DATA.filter(function(s){return pass(s)&&(!VONLY||VSEL[s.c]);});\n rows.sort(function(a,b){var x=keyval(a,sortKey),y=keyval(b,sortKey);if(x==null)x=-1e9;if(y==null)y=-1e9;return (x>y?1:x<y?-1:0)*sortDir});rows.sort(function(a,b){return (VSEL[b.c]?1:0)-(VSEL[a.c]?1:0);});LASTROWS=rows;\n var h='';\n for(var i=0;i<rows.length;i++){var s=rows[i];var L=lv(s);var yz=(s.op===s.px);var oc=yz?' yiz':'';\n  var P=L?L.P:[null,null,null],S=L?L.S:[null,null,null];\n  h+='<tr'+vtr(s.c)+'>'+vtd(s.c)+'<td class=\"c\">'+s.c+'</td><td>'+s.nm+(yz?' <span class=\"yiz\" style=\"padding:0 4px\">一字</span>':'')+(s.disp?VDB:'')+'</td>'+\n     '<td class=\"n'+oc+'\">'+f(s.op)+'</td><td class=\"n'+oc+'\">'+f(s.px)+'</td>'+\n     '<td class=\"n '+(s.chg>0?'up':'dn')+'\">'+(s.chg>0?'+':'')+s.chg.toFixed(2)+'</td>'+'<td class=\"n\">'+(s.vol!=null?s.vol.toLocaleString():'-')+'</td>'+\n     '<td class=\"n\">'+s.k.toFixed(1)+'</td><td class=\"n hl\">'+(s.gap!=null?s.gap.toFixed(2):'-')+'</td>'+\n     '<td class=\"n\">'+f(s.h5)+'</td><td class=\"n\">'+f(s.l5)+'</td><td class=\"n hl\">'+f(s.R)+'</td>'+'<td class=\"n\" style=\"color:#b388ff\">'+f(s.bx)+pct(s.bx,s.px)+'</td>'+'<td class=\"l\" style=\"color:#7b4bd0;font-weight:600;white-space:normal;font-size:11px;line-height:1.2;max-width:150px\">'+(dualOf(s)||'-')+'</td>'+\n     '<td class=\"n press\">'+f(P[0])+pct(P[0],s.px)+'</td><td class=\"n press\">'+f(P[1])+pct(P[1],s.px)+'</td><td class=\"n press\">'+f(P[2])+pct(P[2],s.px)+'</td>'+\n     '<td class=\"n supp\">'+f(S[0])+pct(S[0],s.px)+'</td><td class=\"n supp\">'+f(S[1])+pct(S[1],s.px)+'</td><td class=\"n supp\">'+f(S[2])+pct(S[2],s.px)+'</td></tr>';\n }\n document.getElementById('tb').innerHTML=h||'<tr><td colspan=20 style=\"text-align:center;color:#8aa1bd;padding:14px\">— 無符合,放寬條件 —</td></tr>';\n document.getElementById('cnt').textContent=rows.length;document.querySelectorAll('.vcb').forEach(function(cb){cb.onchange=function(){VSEL=vGet();var c=cb.getAttribute('data-c');if(cb.checked)VSEL[c]=1;else delete VSEL[c];vSave(VSEL);render();};});var ve=document.getElementById('vcnt');if(ve)ve.textContent='  已打V '+Object.keys(VSEL).length+' 檔(釘最上·瀏覽器記住)';\n}\nfunction preset(p){\n ['zb','lb','zt','nzt','ztk','xh','kd','gp','yz'].forEach(function(i){document.getElementById(i).checked=false});\n if(p=='5.1'){lb.checked=true;lbv.value=2;gp.checked=true;gv.value=3;hd.checked=true;}\n if(p=='5.2'){zb.checked=true;zbv.value=2;gp.checked=true;gv.value=3;hd.checked=true;}\n \n render();\n}\nfunction sortBy(k){if(sortKey==k)sortDir*=-1;else{sortKey=k;sortDir=-1}render();}\nfunction passBT(r){return pass(r);}function lblBT(r){return r.zt?'漲停':zbHit(r.px,r.bu)?'站上布林':lbHit(r.px,r.bu)?'臨近布林':r.k>75?'KD高':'其他';}function rate(a,k){var v=a.filter(function(r){return r[k]!=null});return v.length?Math.round(v.filter(function(r){return r[k]}).length/v.length*100):null;}function runBT(){var all=[];for(var d in HIST){HIST[d].forEach(function(r){if(passBT(r))all.push(r);});}var has1=all.filter(function(r){return r.n1c!=null;});var grp={};has1.forEach(function(r){var k=lblBT(r);(grp[k]=grp[k]||[]).push(r);});function avg(a,k){var v=a.filter(function(r){return r[k]!=null}).map(function(r){return r[k]});return v.length?v.reduce(function(x,y){return x+y},0)/v.length:null;}function win(a,k){var v=a.filter(function(r){return r[k]!=null});return v.length?Math.round(v.filter(function(r){return r[k]>0}).length/v.length*100):null;}function fm(v){return v==null?'—':(v>0?'+':'')+v.toFixed(2)+'%';}function cl(v){return v==null?'':v>0?'up':v<0?'dn':'';}function wp(v){return v==null?'—':v+'%';}var keys=Object.keys(grp).sort(function(a,b){return grp[b].length-grp[a].length});keys.push('__all__');var h='<tr><th style='+Q+'text-align:left'+Q+'>訊號</th><th>筆數</th><th>隔日開>收</th><th>隔日收>收</th><th>開高走高</th><th>平均隔日收</th><th>平均隔日高</th><th>平均隔日低</th><th>碰R1</th><th>碰R2</th><th>3日勝</th><th>平均3日</th><th>5日勝</th><th>平均5日</th></tr>';keys.forEach(function(k){var a=k==='__all__'?has1:grp[k];if(!a.length)return;var hl=Math.round(a.filter(function(r){return r.n1hl}).length/a.length*100);h+='<tr'+(k==='__all__'?' style='+Q+'font-weight:700;background:#0f2033'+Q:'')+'><td style='+Q+'text-align:left'+Q+'>'+(k==='__all__'?'全部':k)+'</td><td>'+a.length+'</td><td>'+wp(win(a,'n1o'))+'</td><td>'+wp(win(a,'n1c'))+'</td><td>'+hl+'%</td><td class='+Q+cl(avg(a,'n1c'))+Q+'>'+fm(avg(a,'n1c'))+'</td><td class='+Q+'up'+Q+'>'+fm(avg(a,'n1h'))+'</td><td class='+Q+'dn'+Q+'>'+fm(avg(a,'n1l'))+'</td><td>'+wp(rate(a,'t1'))+'</td><td>'+wp(rate(a,'t2'))+'</td><td>'+wp(win(a,'n3c'))+'</td><td class='+Q+cl(avg(a,'n3c'))+Q+'>'+fm(avg(a,'n3c'))+'</td><td>'+wp(win(a,'n5c'))+'</td><td class='+Q+cl(avg(a,'n5c'))+Q+'>'+fm(avg(a,'n5c'))+'</td></tr>';});document.getElementById('btS').innerHTML=h;all.sort(function(a,b){return a.d<b.d?1:a.d>b.d?-1:0;});var g='<tr><th style='+Q+'text-align:left'+Q+'>訊號日</th><th style='+Q+'text-align:left'+Q+'>代碼</th><th style='+Q+'text-align:left'+Q+'>名稱</th><th>訊號</th><th>收</th><th>K</th><th>差價%</th><th>R</th><th>隔開</th><th>隔高</th><th>隔低</th><th>隔收</th><th>開高走高</th><th>碰R1</th><th>碰R2</th><th>3日</th><th>5日</th></tr>';g+=all.slice(0,400).map(function(r){return '<tr><td style='+Q+'text-align:left'+Q+'>'+r.d+'</td><td style='+Q+'text-align:left'+Q+'>'+r.c+'</td><td style='+Q+'text-align:left'+Q+'>'+r.nm+'</td><td>'+lblBT(r)+'</td><td>'+r.px.toFixed(2)+'</td><td>'+r.k.toFixed(1)+'</td><td>'+(r.gap==null?'—':r.gap.toFixed(2))+'</td><td>'+(r.R==null?'—':r.R.toFixed(2))+'</td><td class='+Q+cl(r.n1o)+Q+'>'+fm(r.n1o)+'</td><td class='+Q+'up'+Q+'>'+fm(r.n1h)+'</td><td class='+Q+'dn'+Q+'>'+fm(r.n1l)+'</td><td class='+Q+cl(r.n1c)+Q+'>'+fm(r.n1c)+'</td><td>'+(r.n1c==null?'—':(r.n1hl?'是':'否'))+'</td><td>'+yn(r.t1)+'</td><td>'+yn(r.t2)+'</td><td class='+Q+cl(r.n3c)+Q+'>'+fm(r.n3c)+'</td><td class='+Q+cl(r.n5c)+Q+'>'+fm(r.n5c)+'</td></tr>';}).join('');document.getElementById('btD').innerHTML=g;document.getElementById('btT').textContent='近一個月回測(套用上面同一組篩選;共 '+all.length+' 筆訊號,'+has1.length+' 筆有隔日資料)';document.getElementById('bt').style.display='block';document.getElementById('bt').scrollIntoView({behavior:'smooth'});}function bindBtns(){document.getElementById('bBT').onclick=runBT;var b=document.getElementById('bOnlyV');b.onclick=function(){VONLY=!VONLY;b.className=VONLY?'vbtn on':'vbtn';b.textContent=VONLY?'只看打V(開)':'只看打V';render();};document.getElementById('bClrV').onclick=function(){if(!confirm('清除所有打V？'))return;VSEL={};vSave(VSEL);render();};document.getElementById('bTvList').onclick=function(){dlTV(LASTROWS,'目前');};document.getElementById('bTvV').onclick=function(){dlTV(DATA.filter(function(s){return VSEL[s.c];}),'打V');};document.getElementById('bTvCopy').onclick=function(){var t=tvSyms(LASTROWS).join(',');if(!t){alert('清單是空的');return;}(navigator.clipboard?navigator.clipboard.writeText(t):Promise.reject()).then(function(){alert('已複製 '+LASTROWS.length+' 檔');},function(){prompt('手動複製：',t);});};}window.addEventListener('storage',function(e){if(e.key===VKEY){VSEL=vGet();render();}});window.onload=function(){document.querySelectorAll('input').forEach(function(el){el.addEventListener('input',render)});bindBtns();var sel=document.getElementById('fDate');if(sel){var ds=Object.keys(HIST).filter(function(d){return d!==DATE0}).sort().reverse();var o='<option value='+Q+DATE0+Q+'>'+DATE0+'(最新) '+DATA0.length+'檔</option>';ds.forEach(function(d){o+='<option value='+Q+d+Q+'>'+d+' '+HIST[d].length+'檔</option>';});sel.innerHTML=o;sel.onchange=function(){setDate(sel.value);};}render();};\n"
H=('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
 '<meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate"><meta http-equiv="Pragma" content="no-cache"><meta http-equiv="Expires" content="0">'
 '<title>差價區間選股 · '+DATE+'</title><style>'+CSS+'</style><div class="wrap">'
 '<div class="top"><h1>差價區間選股</h1><div class="d" id="meta">'+DATE+' · R=第一根5分K高−低 · 起點=收盤 · R1~R3壓/撐 · 開=收(一字)反白</div></div>'
 '<div class="panel"><div class="presets"><span class="num"><label>日期(回看)</label><select id="fDate" style="background:#0f2135;border:1px solid #2b4a68;color:#e8f0fb;border-radius:6px;padding:4px 6px"></select></span>一鍵套用:<button onclick="preset(\'5.1\')">5.1</button><button onclick="preset(\'5.2\')">5.2</button><span style="color:#8aa1bd">符合 <span class="cnt" id="cnt">0</span> 檔</span></div>'
 '<div class="conds">'
 '<span class="num"><label class="ck"><input type="checkbox" id="zb">站上布林 超</label><input id="zbv" value="3">%</span>'
 '<span class="num"><label class="ck"><input type="checkbox" id="lb" checked>臨近布林 距</label><input id="lbv" value="2">%</span>'
 '<label class="ck"><input type="checkbox" id="zt">漲停</label><label class="ck"><input type="checkbox" id="nzt">非漲停</label>'
 '<label class="ck"><input type="checkbox" id="ztk">漲停開門</label><label class="ck"><input type="checkbox" id="xh">隔日續紅</label>'
 '<label class="ck"><input type="checkbox" id="yz">一字(開=收)</label><label class="ck"><input type="checkbox" id="hd" checked>隱藏處置中</label>'
 '<span class="num"><label class="ck"><input type="checkbox" id="kd">KD&gt;</label><input id="kv" value="80"></span>'
 '<span class="num"><label class="ck"><input type="checkbox" id="gp" checked>差價%&gt;</label><input id="gv" value="4"></span>'
 '<span class="num"><label class="ck"><input type="checkbox" id="gk">總量(張)&ge;</label><input id="gkv" value="10000"></span>'
 '</div><div class="vbar"><button class="vbtn2" id="bBT">📊 近一個月回測</button><button class="vbtn" id="bOnlyV">只看打V</button><button class="vbtn2" id="bClrV">清除全部V</button><span id="vcnt"></span><span style="flex:1"></span><span>匯入TradingView自選：</span><button class="vbtn2" id="bTvList">下載目前清單</button><button class="vbtn2" id="bTvV">下載打V</button><button class="vbtn2" id="bTvCopy">複製</button></div></div><div class="tb-scroll"><table><thead><tr><th class="l">V</th>'
 '<th onclick="sortBy(\'c\')">代碼</th><th>名稱</th><th onclick="sortBy(\'op\')">開盤</th><th onclick="sortBy(\'px\')">收盤</th><th onclick="sortBy(\'chg\')">漲跌%</th><th onclick="sortBy(&#39;vol&#39;)">量(張)</th>'
 '<th onclick="sortBy(\'k\')">K</th><th onclick="sortBy(\'gap\')">差價%</th>'
 '<th onclick="sortBy(\'h5\')">5K高</th><th onclick="sortBy(\'l5\')">5K低</th><th onclick="sortBy(\'R\')">R價差</th><th class="pg" onclick="sortBy(\'bx\')">波段壓</th><th onclick="sortBy(\'dual\')">雙重撐壓</th>'
 '<th class="pg" onclick="sortBy(\'p1\')">R1壓</th><th class="pg" onclick="sortBy(\'p2\')">R2壓</th><th class="pg" onclick="sortBy(\'p3\')">R3壓</th>'
 '<th class="sg" onclick="sortBy(\'s1\')">R1撐</th><th class="sg" onclick="sortBy(\'s2\')">R2撐</th><th class="sg" onclick="sortBy(\'s3\')">R3撐</th>'
 '</tr></thead><tbody id="tb"></tbody></table></div><div id="bt" style="display:none"><div style="font-weight:700;color:#e8f0fb;padding:4px 0"><span id="btT">近一個月回測</span></div><div class="tb-scroll" style="max-height:40vh"><table id="btS"></table></div><div class="tb-scroll" style="max-height:50vh;margin-top:8px"><table id="btD"></table></div></div>'
 '<script>'+JS.replace('__DATA__',J).replace('__DATE__',json.dumps(DATE)).replace('__HIST__',HJSON)+'</script></div></html>')
open(os.path.join(HERE,'gap-a0cc38.html'),'w',encoding='utf-8').write(H)
print('gap-a0cc38.html 產出:%d 檔,日期 %s'%(len(data),DATE))
