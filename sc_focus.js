/* sc_focus.js(2026-10-09 v2,使用者:「連結打開預設就是那個個股的資訊」)
   網址帶 ?code=2330:① 頁面最上面放一塊「這檔」的摘要(資料 sc_flow.js:權證多空/外資投信自營/主動ETF 5、10、20 日 + 小圖)
   ② 權證日報:只留這檔的卡片;權證分點:篩選框直接填代碼;其他頁:把這檔的列標黃並捲過去。按「顯示全部」恢復。 */
(function(){var Q=new URLSearchParams(location.search),c=Q.get('code');if(!c)return;
var pg=(location.pathname.split('/').pop()||'').toLowerCase();
function el(t,css,h){var e=document.createElement(t);if(css)e.style.cssText=css;if(h!=null)e.innerHTML=h;return e}
function sg(x){if(x==null)return '—';x=Math.round(x);return '<b style="color:'+(x>0?'#e5484d':(x<0?'#2fa36b':'inherit'))+'">'+(x>0?'+':'')+x.toLocaleString()+'</b>'}
function sum(a,n){var t=0,k=0;(a||[]).slice(-n).forEach(function(x){if(x!=null){t+=x;k++}});return k?t:null}
function bars(a,n){a=(a||[]).slice(-n);var W=n*8,H=24,mx=0;a.forEach(function(x){if(x!=null&&Math.abs(x)>mx)mx=Math.abs(x)});if(!mx)return '—';
 var o='<svg width="'+W+'" height="'+H+'"><line x1="0" x2="'+W+'" y1="12" y2="12" stroke="rgba(128,128,128,.4)"/>';
 a.forEach(function(x,i){if(!x)return;var h=Math.max(1,Math.abs(x)*12/mx);o+='<rect x="'+(i*8+1)+'" y="'+(x>0?12-h:12)+'" width="6" height="'+h+'" fill="'+(x>0?'#e5484d':'#2fa36b')+'"/>'});return o+'</svg>'}
var box=el('div','position:relative;z-index:9998;background:#fff8db;color:#222;border:2px solid #f2c94c;border-radius:8px;padding:8px 12px;margin:6px;font:14px/1.7 "Microsoft JhengHei",sans-serif',
 '<b style="font-size:16px">📌 '+c+'</b> <span id="scfN"></span> <button id="scfAll" style="margin-left:10px">顯示全部</button> <button id="scfX">關閉</button><div id="scfB">載入中…</div>');
function put(){document.body.insertBefore(box,document.body.firstChild);
 document.getElementById('scfX').onclick=function(){box.remove()};
 document.getElementById('scfAll').onclick=function(){[].forEach.call(document.querySelectorAll('[data-scf-hide]'),function(e){e.style.display='';e.removeAttribute('data-scf-hide')});
   var q=document.getElementById('q');if(q&&typeof flt==='function'){q.value='';flt('')}};}
function fill(){var F=window.SCF;if(!F||!F.s){document.getElementById('scfB').textContent='(沒有 sc_flow.js 資料)';return}
 var r=F.s[c],K={};if(!r){document.getElementById('scfB').textContent='近 20 日沒有這檔的資料';return}(F.k||[]).forEach(function(k,i){K[k]=r[i]});
 var add=function(a,b,d){return a.map(function(x,i){var t=null;[x,b[i],d[i]].forEach(function(v){if(v!=null)t=(t||0)+v});return t})};
 var row=function(n,a){return '<tr><td>'+n+'</td><td>'+sg(sum(a,5))+'</td><td>'+sg(sum(a,10))+'</td><td>'+sg(sum(a,20))+'</td><td style="padding-left:10px">'+bars(a,20)+'</td></tr>'};
 var W=(F.wd||{})[c],rows='';
 if(/warrant/.test(pg))rows=row('認購 投資人淨買萬',K.wcn)+row('認售 投資人淨買萬',K.wpn)+row('認購 買進萬',K.wc)+row('認售 買進萬',K.wp);
 else if(/etf/.test(pg))rows=row('主動ETF 淨買張',K.e)+row('外資',K.f)+row('投信',K.t);
 else rows=row('外資',K.f)+row('投信',K.t)+row('自營',K.d)+row('<b>法人合計</b>',add(K.f,K.t,K.d))+row('主動ETF',K.e);
 document.getElementById('scfB').innerHTML=(W?'<b>權證多空</b> <b style="padding:0 8px;border-radius:5px;color:#fff;background:'+(/多/.test(W[0])?'#e5484d':(/空/.test(W[0])?'#2fa36b':'#868e96'))+'">'+W[0]+'</b> <span style="opacity:.7">('+(W[1]==='HiStock'?'HiStock':'自算5日')+(W[2]?'；'+W[2]:'')+')</span> · ':'')
  +'<span style="opacity:.7">資料到 '+String((F.d||[]).slice(-1)[0]||'').slice(5)+',張(權證萬元)</span><table style="border-collapse:collapse;text-align:right"><tr style="opacity:.6"><td></td><td>5日</td><td>10日</td><td>20日</td><td style="text-align:left;padding-left:10px">近20日(紅買綠賣)</td></tr>'+rows+'</table>'}
function focus(n){var re=new RegExp('(^|[^0-9])'+c+'([^0-9]|$)'),hit=[];
 if(/warrantdaily/.test(pg)){[].forEach.call(document.querySelectorAll('.card'),function(k){var h=k.querySelector('.h');if(!h)return;if(h.textContent.trim().indexOf(c)===0)hit.push(k);else{k.style.display='none';k.setAttribute('data-scf-hide',1)}})}
 if(/warrantflow/.test(pg)){var q=document.getElementById('q');if(q&&typeof flt==='function'){q.value=c;flt(c);hit.push(q)}}
 [].forEach.call(document.querySelectorAll('tr'),function(r){if(!r.querySelector('tr')&&re.test(r.textContent||'')){r.style.outline='3px solid #f2c94c';r.style.background='rgba(255,212,59,.25)';hit.push(r)}});
 if(!hit.length&&n<20){setTimeout(function(){focus(n+1)},300);return}
 var t=hit.filter(function(x){return x.tagName!=='INPUT'})[0];if(t)t.scrollIntoView({block:'center'});
 if(!hit.length)document.getElementById('scfN').innerHTML='<span style="color:#c92a2a">這頁今天沒有 '+c+' 的列,看上面摘要</span>';}
function go(){put();var nm=document.getElementById('scfN');
 var s=document.createElement('script');s.src='sc_flow.js?v='+new Date().toISOString().slice(0,10);s.onload=fill;s.onerror=fill;document.head.appendChild(s);setTimeout(function(){focus(0)},400)}
if(document.readyState==='complete')go();else window.addEventListener('load',go);})();
