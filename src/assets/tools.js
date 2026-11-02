/* Sfuso: strumenti (fusi orari, riunioni, sonno, ora nel mondo) */
(()=>{
'use strict';
const SF=window.SF,$=id=>document.getElementById(id),{esc,fh,H,t}=SF;
const DEF=window.SF_DEF||{};
const tool=(document.querySelector('[data-tool]')||{}).dataset;
if(!tool)return;
const store={get(k,d){try{const v=localStorage.getItem('sfuso.'+SF.LOC+'.'+k);return v?JSON.parse(v):d;}catch(e){return d;}},set(k,v){try{localStorage.setItem('sfuso.'+SF.LOC+'.'+k,JSON.stringify(v));}catch(e){}}};
const sorted=SF.CITIES.slice().sort((a,b)=>a.name.localeCompare(b.name,SF.LOC));
const options=sel=>sorted.map(c=>`<option value="${esc(c.name)}"${c.name===sel?' selected':''}>${esc(c.name)} · ${SF.tzLabel(c.tz,Date.now())}</option>`).join('');
const dayWord=(ms,a,b)=>{const da=SF.localStr(ms,a.tz).slice(0,10),db=SF.localStr(ms,b.tz).slice(0,10);return t(db>da?'d_tomorrow':db<da?'d_yesterday':'d_today');};
const sign=d=>(d>0?'+':d<0?'−':'±')+SF.fnum(Math.abs(d))+' h';
const listFromUrl=(key,def)=>{const q=new URLSearchParams(location.search).get(key);const l=(q?q.split(','):store.get(key,def)).map(SF.find).filter(Boolean).map(c=>c.name);return l.length?l:def;};
const urlSet=(k,v)=>{try{const q=new URLSearchParams(location.search);q.set(k,v);history.replaceState(null,'',location.pathname+'?'+q);}catch(e){}};

/* ---------- convertitore di fusi orari ---------- */
if(tool.tool==='fusi-orari'){
  let base=SF.find(new URLSearchParams(location.search).get('da')||DEF.home)||SF.find(DEF.home);
  let list=listFromUrl('c',DEF.tz);
  $('base').innerHTML=options(base.name);$('add').innerHTML=`<option value="">${esc(t('add_city'))}</option>`+options('');
  const setNow=()=>{$('when').value=SF.localStr(Date.now(),base.tz);$('scrub').value=0;};
  setNow();
  const draw=()=>{
    const ms=SF.toUtc($('when').value,base.tz)+(+$('scrub').value)*H;
    $('scrub-l').textContent=(+$('scrub').value?sign(+$('scrub').value)+' · ':'')+t('scrub_l',{t:SF.fhm(SF.localH(ms,base.tz)),c:base.name});
    $('out').innerHTML=[base.name].concat(list.filter(n=>n!==base.name)).map((n,i)=>{const c=SF.find(n),h=SF.localH(ms,c.tz),night=h<6||h>=21;
      return `<div class="clock card${i===0?' dark':''}">${i?`<button type="button" class="x" data-rm="${esc(n)}" aria-label="${esc(t('remove',{c:n}))}">✕</button>`:''}<div class="n">${esc(c.name)} ${night?'🌙':'☀️'}</div><div class="t">${SF.fhm(h)}</div><div class="m">${i?sign(SF.diffH(base,c,ms))+' · '+dayWord(ms,base,c):t('ref_city')} · ${SF.tzLabel(c.tz,ms)}</div></div>`;}).join('');
    store.set('c',list);urlSet('c',list.join(','));urlSet('da',base.name);
  };
  $('base').onchange=e=>{base=SF.find(e.target.value);setNow();draw();};
  $('add').onchange=e=>{const v=e.target.value;if(v&&!list.includes(v))list.push(v);e.target.value='';draw();};
  $('when').oninput=draw;$('scrub').oninput=draw;
  $('now').onclick=()=>{setNow();draw();};
  $('out').onclick=e=>{const b=e.target.closest('[data-rm]');if(b){list=list.filter(n=>n!==b.dataset.rm);draw();}};
  draw();
}

/* ---------- pianificatore di riunioni ---------- */
if(tool.tool==='riunioni'){
  let list=listFromUrl('c',DEF.mtg).slice(0,5),sel=null;
  $('add').innerHTML=`<option value="">${esc(t('add_city5'))}</option>`+options('');
  $('day').value=SF.localStr(Date.now(),SF.find(list[0]).tz).slice(0,10);
  const kind=h=>h>=9&&h<18?2:(h>=7&&h<9)||(h>=18&&h<21)?3:(h>=21&&h<23)||(h>=6&&h<7)?1:0;
  const draw=()=>{
    const base=SF.find(list[0]),start=SF.toUtc($('day').value+'T00:00',base.tz);
    const cols=[...Array(24)].map((_,i)=>start+i*H);
    const good=cols.map(ms=>list.every(n=>kind(Math.floor(SF.localH(ms,SF.find(n).tz)))===2));
    let g='';
    list.forEach((n,ri)=>{const c=SF.find(n);
      g+=`<div class="mrow" role="row"><div class="nm" role="rowheader">${esc(c.name)}<small>${ri?sign(SF.diffH(base,c,start)):t('ref')}${ri?` · <button type="button" data-rm="${esc(n)}" style="border:0;background:none;padding:4px 2px;min-height:28px;min-width:32px;cursor:pointer;color:inherit;text-decoration:underline">${t('remove_word')}</button>`:''}</small></div>`;
      cols.forEach((ms,i)=>{const h=SF.localH(ms,c.tz),k=kind(Math.floor(h));g+=`<button type="button" class="h n${k}${good[i]?' ok':''}${sel===i?' sel':''}" data-i="${i}" aria-label="${esc(t('cell_aria',{c:c.name,t:fh(h)}))}">${fh(h).slice(0,2)}${h%1?'½':''}</button>`;});
      g+='</div>';});
    $('grid').innerHTML=g;
    const slots=good.map((v,i)=>v?i:-1).filter(i=>i>=0);
    $('best').innerHTML=slots.length?t('mt_best',{list:slots.map(i=>fh(SF.localH(cols[i],base.tz))).join(', '),c:esc(base.name)}):t('mt_none');
    if(sel!=null){$('pick').innerHTML=t('mt_pick',{t:fh(SF.localH(cols[sel],base.tz)),c:esc(base.name)})+list.slice(1).map(n=>{const c=SF.find(n);return `${esc(c.name)} ${fh(SF.localH(cols[sel],c.tz))} (${dayWord(cols[sel],base,c)})`;}).join(' · ');}
    else $('pick').textContent=t('mt_hint');
    store.set('c',list);urlSet('c',list.join(','));
  };
  $('add').onchange=e=>{const v=e.target.value;if(v&&!list.includes(v)&&list.length<5)list.push(v);e.target.value='';draw();};
  $('day').oninput=draw;
  $('grid').onclick=e=>{const r=e.target.closest('[data-rm]');if(r){list=list.filter(n=>n!==r.dataset.rm);sel=null;draw();return;}const b=e.target.closest('[data-i]');if(b){sel=+b.dataset.i;draw();}};
  draw();
}

/* ---------- calcolatore del sonno ---------- */
if(tool.tool==='sonno'){
  const seg=document.querySelectorAll('#mode button');
  let mode='wake';
  const draw=()=>{
    const tm=SF.hm($('time').value),out=[];const fh=SF.fhm;
    const now=new Date(),nowH=now.getHours()+now.getMinutes()/60;
    $('time-w').hidden=mode==='now';
    $('time-l').textContent=t(mode==='wake'?'sl_wake':'sl_bed');
    if(mode==='wake'){
      [6,5,4,3].forEach(n=>out.push({h:tm-n*1.5-0.25,n,best:n>=5}));
      $('lead').innerHTML=t('sl_lead_wake',{t:fh(tm)});
    }else{
      const b=mode==='now'?nowH:tm;
      [3,4,5,6].forEach(n=>out.push({h:b+0.25+n*1.5,n,best:n>=5}));
      $('lead').innerHTML=t('sl_lead_bed',{t:fh(b)});
    }
    $('out').innerHTML=out.map(o=>`<div class="o${o.best?' best':''}"><b>${fh(o.h)}</b><span>${t('sl_cycles',{n:o.n,h:SF.fnum(o.n*1.5)})}</span></div>`).join('');
  };
  seg.forEach(b=>b.onclick=()=>{mode=b.dataset.v;seg.forEach(x=>x.setAttribute('aria-pressed',String(x===b)));draw();});
  $('time').oninput=draw;
  draw();
}

/* ---------- ora nel mondo ---------- */
if(tool.tool==='ora-nel-mondo'){
  const names=DEF.world;
  const draw=()=>{
    const ms=Date.now(),base=SF.find(DEF.home);
    $('map').innerHTML=SF.mapSvg({label:t('night_label'),pins:names.map(SF.find)});
    $('out').innerHTML=names.map(n=>{const c=SF.find(n),h=SF.localH(ms,c.tz),night=h<6||h>=20;
      return `<div class="clock card${night?' dark':''}"><div class="n">${esc(c.name)} ${night?'🌙':'☀️'}</div><div class="t">${SF.nowIn(c.tz,ms)}</div><div class="m">${c.name===base.name?esc(t('wc_home')):esc(t('wc_from',{d:sign(SF.diffH(base,c,ms)),day:dayWord(ms,base,c)}))}</div></div>`;}).join('');
    $('utc').textContent='UTC '+new Date(ms).toISOString().slice(11,16);
  };
  draw();setInterval(draw,20000);
}
})();
