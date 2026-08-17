# -*- coding: utf-8 -*-
"""產「差價區間選股」頁 gap.html(放在 網站部署,給 一鍵_日報2 一起發布)。
   讀 08_歷史股價下載: 股價一年.csv + 全市場1分K_A/B.csv(+ 補1分K_日期.csv 若有)。
"""
import os,sys,csv,glob,json,warnings
warnings.filterwarnings('ignore')
import pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__))
BASE=os.path.dirname(os.path.dirname(HERE))
HD=os.path.join(BASE,'08_歷史股價下載')
PX=os.path.join(HD,'股價一年.csv')
px=pd.read_csv(PX,encoding='utf-8-sig',dtype=str)
px=px[px['代碼'].str.match(r'^\d{4}$',na=False)].copy()
for c in ['開盤','最高','最低','收盤','昨收','漲跌幅%']: px[c]=pd.to_numeric(px[c],errors='coerce')
px=px.dropna(subset=['收盤']).sort_values(['代碼','日期'])
DATE=px['日期'].max()
# 第一根5分K(09:00~09:04):串流讀 A/B + 補檔
first={}
files=[os.path.join(HD,'全市場1分K_A.csv'),os.path.join(HD,'全市場1分K_B.csv')]+glob.glob(os.path.join(HD,'補1分K_%s.csv'%DATE))
for fp in files:
    if not os.path.exists(fp): continue
    with open(fp,encoding='utf-8-sig',errors='ignore') as f:
        next(f,None)
        for ln in f:
            p=ln.rstrip('\n').split(',')
            if len(p)<8 or p[1]!=DATE: continue
            t=p[2][:5]
            if t<'09:00' or t>'09:04': continue
            try: hi=float(p[4]); lo=float(p[5])
            except Exception: continue
            d=first.setdefault(p[0],[hi,lo]); 
            if hi>d[0]:d[0]=hi
            if lo<d[1]:d[1]=lo
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
CSS=open(os.path.join(HERE,'_gap_css.txt'),encoding='utf-8').read() if os.path.exists(os.path.join(HERE,'_gap_css.txt')) else ""
JS=open(os.path.join(HERE,'_gap_js.txt'),encoding='utf-8').read() if os.path.exists(os.path.join(HERE,'_gap_js.txt')) else ""
tpl=open(os.path.join(HERE,'_gap_tpl.html'),encoding='utf-8').read()
html=tpl.replace('__DATE__',DATE).replace('__CSS__',CSS).replace('__JS__',JS.replace('__DATA__',J))
open(os.path.join(HERE,'gap.html'),'w',encoding='utf-8').write(html)
print('gap.html 產出:%d 檔,日期 %s'%(len(data),DATE))
