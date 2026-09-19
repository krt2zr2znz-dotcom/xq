# -*- coding: utf-8 -*-
"""綜合選股正式頁:布林位置/站上·臨近布林%/漲跌停·打開/連紅綠K/量/差價% + 大戶(集保 400/600/800/1000張 近6週&本週增減) + 主力集中度(5/10/20日,可選CSV)。
   底稿=gap-a0cc38.html(全市場);連紅綠&漲跌停由 股價一年.csv 算;大戶由 集保股權分散.csv 算;集中度讀 集中度_5_10_20.csv(有才顯示)。
   輸出:04_輸出結果/網站部署/綜合選股-57f14b.html   用法:python 產生綜合選股.py
"""
import os, json, csv, io, math, datetime
HERE = os.path.dirname(os.path.abspath(__file__))            # 網站部署
BASE = os.path.dirname(os.path.dirname(HERE))                # 專案根
HD   = os.path.join(BASE, '08_歷史股價下載')
GAPF = os.path.join(HERE, 'gap-a0cc38.html')
PXF  = os.path.join(HD, '股價一年.csv')
CBF  = os.path.join(HD, '集保股權分散.csv')
CONCF= os.path.join(HD, '集中度_5_10_20.csv')                # 可選:代碼,c5,c10,c20
SUFFIX = '57f14b'
OUT  = os.path.join(HERE, '綜合選股-%s.html' % SUFFIX)

def f_tick(p):
    return 0.01 if p<10 else 0.05 if p<50 else 0.1 if p<100 else 0.5 if p<500 else 1.0 if p<1000 else 5.0

# 1) gap 底稿(全市場)
gh = io.open(GAPF, encoding='utf-8').read()
gi = gh.find('DATA=')
gdata,_ = json.JSONDecoder().raw_decode(gh, gi+len('DATA='))
grows = gdata if isinstance(gdata,list) else gdata.get('rows',[])
G = {r['c']: r for r in grows if r.get('c')}
print('gap 底稿 %d 檔' % len(G))

# 2) 股價一年 → 連紅綠、漲跌停/打開(用最新一根 + 昨收)
bars = {}
with io.open(PXF, encoding='utf-8-sig', newline='') as f:
    rd=csv.reader(f); next(rd,None)
    for r in rd:
        if len(r)<10: continue
        c=r[0].strip()
        try: o=float(r[4]);h=float(r[5]);l=float(r[6]);cl=float(r[7]);pc=float(r[9])
        except: continue
        bars.setdefault(c,[]).append((o,h,l,cl,pc))
def streak(bl):
    newest_red = bl[-1][3] >= bl[-1][0]
    redN=grnN=0
    for o,h,l,cl,pc in reversed(bl):
        if (cl>=o)==newest_red:
            if cl>=o: redN+=1
            else: grnN+=1
        else: break
    return redN, grnN
def limits(o,h,l,cl,pc):
    tku=f_tick(pc*1.1); lu=math.floor(pc*1.1/tku+1e-9)*tku
    tkd=f_tick(pc*0.9); ld=math.ceil(pc*0.9/tkd-1e-9)*tkd
    zt = abs(cl-lu)<tku*0.5
    ztk= (abs(h-lu)<tku*0.5) and not zt
    dt = abs(cl-ld)<tkd*0.5
    dtk= (abs(l-ld)<tkd*0.5) and not dt
    return zt,ztk,dt,dtk

# 3) 集保大戶:各級距 近6週 & 本週 增減(百分點)
per={}; dates=set()
if os.path.exists(CBF):
    with io.open(CBF,encoding='utf-8-sig',newline='') as f:
        rd=csv.reader(f); next(rd,None)
        for r in rd:
            try: c=r[0].strip();d=r[1].strip();lv=int(r[2]);pc=float(r[4])
            except: continue
            if not c or len(d)<10 or lv<1 or lv>15: continue
            per.setdefault(c,{}).setdefault(d,{})[lv]=pc; dates.add(d)
weeks=sorted(dates)[-6:]
LOTS={'400':12,'600':13,'800':14,'1000':15}
def cum(dd,w,minlv):
    lv=dd.get(w)
    return None if lv is None else round(sum(v for l,v in lv.items() if l>=minlv),3)
BIG={}
for c,dd in per.items():
    h6={}; w1={}
    for lot,ml in LOTS.items():
        curv  = cum(dd,weeks[-1],ml) if weeks else None
        firstv= cum(dd,weeks[0],ml) if len(weeks)>=2 else None
        prevv = cum(dd,weeks[-2],ml) if len(weeks)>=2 else None
        h6[lot]= round(curv-firstv,2) if (curv is not None and firstv is not None) else None
        w1[lot]= round(curv-prevv,2)  if (curv is not None and prevv  is not None) else None
    BIG[c]={'h6':h6,'w1':w1}
print('集保大戶 %d 檔,週=%s' % (len(BIG), weeks[-3:] if weeks else []))

# 4) 集中度(可選)
CONC={}; hasConc=False
if os.path.exists(CONCF):
    with io.open(CONCF,encoding='utf-8-sig',newline='') as f:
        rd=csv.reader(f); next(rd,None)
        for r in rd:
            if len(r)<4: continue
            try: CONC[r[0].strip()]={'c5':float(r[1]),'c10':float(r[2]),'c20':float(r[3])}
            except: pass
    hasConc=len(CONC)>0
print('集中度 CSV:', '有 %d 檔' % len(CONC) if hasConc else '無(欄位顯示—)')

# 5) 合併
DATA=[]
for c,g in G.items():
    px=g.get('px'); bu=g.get('bu'); mid=g.get('mid')
    if px is None: continue
    if g.get('mk')=='興櫃': continue   # 鐵律:所有網頁排除興櫃
    pos=''
    if bu is not None and mid is not None:
        lower=2*mid-bu
        pos='上軌' if px>=bu else '中上軌' if px>=mid else '中下軌' if px>=lower else '下軌'
    bbOver=round((px-bu)/bu*100,2) if bu else None
    bbNear=round((bu-px)/bu*100,2) if bu else None
    bl=bars.get(c); redN=grnN=0; zt=ztk=dt=dtk=False
    if bl:
        redN,grnN=streak(bl); zt,ztk,dt,dtk=limits(*bl[-1])
    b=BIG.get(c,{'h6':{},'w1':{}}); cc=CONC.get(c)
    DATA.append({'c':c,'nm':g.get('nm',''),'mk':g.get('mk',''),
      'op':g.get('op'),'px':px,'chg':g.get('chg'),'vol':g.get('vol'),
      'pos':pos,'bo':bbOver,'bn':bbNear,
      'zt':zt,'ztk':ztk,'dt':dt,'dtk':dtk,'rn':redN,'gn':grnN,
      'disp':bool(g.get('disp')),'emg':(g.get('mk','')=='興櫃'),'gap':g.get('gap'),
      'h6':b['h6'],'w1':b['w1'],
      'c5':(cc['c5'] if cc else None),'c10':(cc['c10'] if cc else None),'c20':(cc['c20'] if cc else None)})
print('輸出 %d 檔' % len(DATA))

DATE = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
meta = {'date':DATE,'hasConc':hasConc,'weeks':weeks}
tpl = io.open(os.path.join(HERE,'_綜合選股_模板.html'), encoding='utf-8').read()
html = tpl.replace('/*__META__*/','var META='+json.dumps(meta,ensure_ascii=False)+';') \
          .replace('/*__DATA__*/','var DATA='+json.dumps(DATA,ensure_ascii=False)+';')
io.open(OUT,'w',encoding='utf-8').write(html)
print('完成 ->', os.path.basename(OUT), '(%.0f KB)' % (len(html)/1024))
