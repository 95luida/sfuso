/* Calcolatore del piano anti jet lag (home e pagine delle mete) */
(()=>{
'use strict';
const SF=window.SF,$=id=>document.getElementById(id);
if(!$('f'))return;
const {fh,fdur,esc,H,DAY,t}=SF;
const POP=window.SF_POP||[];
const ROOT=document.querySelector('[data-calc]');
const PRE={da:ROOT.dataset.da,a:ROOT.dataset.a};
const cap=s=>s.charAt(0).toUpperCase()+s.slice(1);

/* ---------- quadrante delle 24 ore ---------- */
function arcD(a,b,R){
  const p=h=>{const k=(h/24)*2*Math.PI-Math.PI/2;return [60+R*Math.cos(k),60+R*Math.sin(k)];};
  if(b-a>=23.99)return `M 60 ${60-R} A ${R} ${R} 0 1 1 59.99 ${60-R}`;
  const [x1,y1]=p(a),[x2,y2]=p(b);
  return `M ${x1.toFixed(2)} ${y1.toFixed(2)} A ${R} ${R} 0 ${b-a>12?1:0} 1 ${x2.toFixed(2)} ${y2.toFixed(2)}`;
}
let ringId=0;
function ring(day,label){
  const m=day.m,R=39,id='h'+(ringId++);
  let s=`<svg class="ring" viewBox="0 0 120 120" aria-hidden="true"><defs><pattern id="${id}" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="5" height="5" fill="#eef0f5"/><rect width="2" height="5" fill="#6b7190"/></pattern></defs>`;
  s+=`<circle cx="60" cy="60" r="${R}" fill="none" stroke="#eceae3" stroke-width="14"/>`;
  const draw=(list,col)=>list.forEach(x=>{s+=`<path d="${arcD(x[0],x[1],R)}" fill="none" stroke="${col}" stroke-width="14" stroke-linecap="butt"/>`;});
  draw(m.travel,'#c9ccd9');draw(m.sleep,'#141c3d');draw(m.avoid,`url(#${id})`);draw(m.seek,'#ffc857');
  const tick=(h,col)=>{const k=(h/24)*2*Math.PI-Math.PI/2;s+=`<line x1="${(60+29*Math.cos(k)).toFixed(1)}" y1="${(60+29*Math.sin(k)).toFixed(1)}" x2="${(60+48*Math.cos(k)).toFixed(1)}" y2="${(60+48*Math.sin(k)).toFixed(1)}" stroke="${col}" stroke-width="3" stroke-linecap="round"/>`;};
  if(day.coffee!=null)tick(day.coffee,'#9a6b3f');
  if(day.mel!=null)tick(day.mel,'#2fbf8f');
  [['0',60,10],['6',113,64],['12',60,118],['18',8,64]].forEach(x=>{s+=`<text x="${x[1]}" y="${x[2]}" text-anchor="middle">${x[0]}</text>`;});
  return s+`<text class="c1" x="60" y="68" text-anchor="middle">${esc(label)}</text></svg>`;
}
function itemsHtml(day){
  const sk=SF.ranges(day.m.seek),av=SF.ranges(day.m.avoid);
  let L='<ul class="items">';
  L+=`<li><i class="dot d-sleep"></i>${t('it_sleep',{t:fh(day.bed)+'–'+fh(day.wake)})}</li>`;
  L+=`<li><i class="dot d-sun"></i>${sk.length?t('it_seek',{t:sk.join(', ')}):t('it_noseek')}</li>`;
  if(av.length)L+=`<li><i class="dot d-avoid"></i>${t('it_avoid',{t:av.join(', ')})}</li>`;
  L+=`<li><i class="dot d-coffee"></i>${t('it_coffee',{t:fh(day.coffee)})}</li>`;
  if(day.mel!=null)L+=`<li><i class="dot d-mel"></i>${t('it_mel',{t:fh(day.mel)})}</li>`;
  return L+'</ul>';
}
const todayIn=tz=>SF.localStr(Date.now(),tz).slice(0,10);
function dayCard(day,label){
  return `<article class="day card">${todayIn(day.tz)===day.date?`<span class="tag">${t('today')}</span>`:''}${ring(day,label)}<div><h3>${esc(day.title)}</h3><span class="when">${esc(t('when',{d:SF.fday(day.ms,day.tz),c:day.place}))}</span>${itemsHtml(day)}</div><p class="tip">${esc(day.tip)}</p></article>`;
}
function flightCard(plan){
  const {o}=plan,f=plan.flight;
  const dLoc=ms=>fh(SF.localH(ms,o.destTz)),hLoc=ms=>fh(SF.localH(ms,o.homeTz));
  let L=`<ul class="items"><li>${t('takeoff',{t:hLoc(o.dep),c:esc(o.home.name)})}</li><li>${t('landing',{t:dLoc(o.arr),c:esc(o.dest.name)})}</li>`;
  if(f.onboard.length)f.onboard.forEach(x=>{const a=Math.max(x[0],o.dep),b=Math.min(x[1],o.arr);L+=`<li><i class="dot d-sleep" style="background:#fff"></i>${t('onboard',{t:dLoc(a)+'–'+dLoc(b),w:(a-o.dep)<9e5?t('right_after'):t('after_h',{h:fdur((a-o.dep)/H)})})}</li>`;});
  else if(f.rawNight.length)L+=`<li><i class="dot d-sun"></i>${t('awake_west')}</li>`;
  else L+=`<li><i class="dot d-sun"></i>${t('awake_day',{c:esc(o.dest.name)})}</li>`;
  return `<article class="day flight full card" style="grid-template-columns:1fr"><div><h3>${t('flight_title')}</h3><span class="when">${esc(SF.fday(o.dep,o.homeTz))}</span>${L}</ul></div><p class="tip">${esc(t('flight_tip',{c:o.dest.name}))}</p></article>`;
}
const actions=()=>`<div class="acts"><button type="button" class="btn main" id="ics"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2"/></svg><span>${t('btn_ics')}</span></button><button type="button" class="btn" id="share">${t('btn_share')}</button><button type="button" class="btn" id="print">${t('btn_print')}</button></div>`;

const state={plan:null,showFull:false};
function render(plan){
  ringId=0;
  const {o,r}=plan,D=r.raw,ahead=Math.abs(D),out=[];
  const dirTxt=r.dir==='none'?t('same_tz'):t(D>0?'ahead':'behind',{b:esc(o.dest.name),a:esc(o.home.name),h:fdur(ahead)});
  const how=r.dir==='advance'?t('how_adv'):r.dir==='delay'&&(r.why==='east-long'||D>0)?t('how_east_long',{T:fdur(r.T),D:fdur(ahead)}):r.dir==='delay'?t('how_del'):'';
  let meter='';for(let i=1;i<=10;i++)meter+=`<i class="${i<=r.score?'on':''}"></i>`;
  out.push(`<h2 class="plan-h">${esc(t('plan_title',{a:o.home.name,b:o.dest.name}))}</h2>`);
  out.push(`<div class="verdict"><div class="map-w">${SF.mapSvg({fit:true,route:[o.home,o.dest],label:t('route_label',{a:o.home.name,b:o.dest.name})})}</div><div class="txt"><div class="big">${D>0?'+':D<0?'−':''}${SF.fnum(ahead)}<small>${t('hours_word')}</small></div>
    <div class="sev">${esc(t('sev',{level:r.dir==='none'?(SF.T._none||''):r.level,s:r.score}))}</div><div class="meter" role="img" aria-label="${esc(t('meter_aria',{s:r.score}))}">${meter}</div><p>${dirTxt}</p><p>${how}</p></div></div>`);
  out.push(`<div class="stats"><div class="stat card"><b>${r.dir==='none'?0:r.after}</b><span>${t('stat_after')}</span></div><div class="stat card"><b>${r.dir==='none'?0:r.noPlan}</b><span>${t('stat_noplan')}</span></div><div class="stat card"><b>${fdur(r.flightH)}</b><span>${t('stat_flight')}</span></div><div class="stat card"><b>${r.pre?fdur(r.pre):'—'}</b><span>${t('stat_pre')}</span></div></div>`);
  if(r.dir==='none'){$('risultato').innerHTML=out.join('');dock(plan);return;}
  if(o.stay===3&&Math.abs(r.d)>=3&&!state.showFull){
    out.push(`<div class="note good"><h3>${esc(t('short_t',{a:o.home.name}))}</h3><p>${t('short_p',{b:esc(o.dest.name),w1:fh(o.wake+r.d)+'–'+fh(o.bed+r.d),w2:fh(o.wake+2+r.d)+'–'+fh(o.wake+10+r.d),s:fh(o.bed+r.d)+'–'+fh(o.wake+r.d)})}</p><button type="button" class="lnk" id="full">${t('short_btn')}</button></div>`);
    out.push(actions());
    $('risultato').innerHTML=out.join('');bind(plan);dock(plan);return;
  }
  const an=SF.arrivalNote(plan);
  out.push(`<div class="note ${an.cls}"><h3>${esc(an.t)}</h3><p>${esc(an.p)}</p></div>`);
  if(Math.abs(r.d)<=2)out.push(`<div class="note"><h3>${t('light_t')}</h3><p>${esc(t('light_p',{h:fdur(ahead)}))}</p></div>`);
  out.push(actions());
  out.push(`<div class="legend" aria-hidden="true"><span><i class="dot d-sleep"></i>${t('lg_sleep')}</span><span><i class="dot d-sun"></i>${t('lg_seek')}</span><span><i class="dot d-avoid"></i>${t('lg_avoid')}</span><span><i class="dot d-coffee"></i>${t('lg_coffee')}</span>${o.mel&&r.dir==='advance'?`<span><i class="dot d-mel"></i>${t('lg_mel')}</span>`:''}</div><div class="days">`);
  let preN=plan.days.filter(x=>x.kind==='pre').length,di=0;
  plan.days.forEach(day=>{
    if(day.kind==='pre'){out.push(dayCard(day,'−'+(preN--)));return;}
    if(di===0)out.push(flightCard(plan));
    di++;out.push(dayCard(day,t('day_short')+di));
  });
  out.push(`<article class="day done full card"><div><h3>${t('done_t',{n:plan.adaptedDay})}</h3><p style="margin:4px 0 0">${t('done_p',{b:fh(o.bed),w:fh(o.wake)})}</p></div></article></div>`);
  if(o.mel&&r.dir!=='advance')out.push(`<p class="small-print">${t('mel_west')}</p>`);
  out.push(`<p class="small-print">${t('disclaimer')}</p>`);
  $('risultato').innerHTML=out.join('');bind(plan);dock(plan);
}
function bind(plan){
  const f=$('full');if(f)f.onclick=()=>{state.showFull=true;render(plan);};
  const ics=$('ics');if(ics)ics.onclick=()=>{
    SF.download(t('ics_file')+'-'+SF.fold(plan.o.dest.name).replace(/[^a-z0-9]+/g,'-')+'.ics',SF.ics(plan),'text/calendar;charset=utf-8');
    ics.querySelector('span').textContent=t('ics_done');
  };
  const sh=$('share');if(sh)sh.onclick=async()=>{
    writeUrl(true);const u=location.href;
    try{if(navigator.share){await navigator.share({title:t('share_title'),text:t('share_text',{a:plan.o.home.name,b:plan.o.dest.name}),url:u});return;}
      await navigator.clipboard.writeText(u);sh.textContent=t('copied');}catch(e){if(!e||e.name!=='AbortError')prompt(t('copy_prompt'),u);}
  };
  const pr=$('print');if(pr)pr.onclick=()=>window.print();
}
function dock(plan){
  const r=plan.r,s=$('dock-s');if(!s)return;
  s.innerHTML=r.dir==='none'?t('dock_same'):t('dock',{d:(r.raw>0?'+':'−')+SF.fnum(Math.abs(r.raw)),level:esc(cap(r.level)),n:r.after});
}

/* ---------- campi città ---------- */
function combo(id){
  const inp=$(id),list=$('sug-'+id);let items=[],act=-1;
  const close=()=>{list.hidden=true;inp.setAttribute('aria-expanded','false');inp.removeAttribute('aria-activedescendant');act=-1;};
  const open=()=>{
    const v=SF.fold(inp.value);
    items=(v?SF.ALL.filter(c=>SF.fold(c.name).includes(v)).sort((x,y)=>(SF.fold(y.name).startsWith(v)-SF.fold(x.name).startsWith(v))||((y.lat!=null)-(x.lat!=null))):POP.concat([PRE.da]).map(SF.find).filter(Boolean)).slice(0,8);
    if(!items.length){close();return;}
    list.innerHTML=items.map((c,i)=>`<li role="option" id="${id}-o${i}" aria-selected="${i===act}" data-i="${i}">${esc(c.name)}<span>${esc(c.code)} · ${SF.tzLabel(c.tz,Date.now())}</span></li>`).join('');
    list.hidden=false;inp.setAttribute('aria-expanded','true');
  };
  const pick=i=>{const c=items[i];if(!c)return;inp.value=c.name;close();touched=true;userTimes=false;run();inp.blur();};
  inp.addEventListener('focus',()=>{inp.select();open();});
  inp.addEventListener('input',()=>{act=-1;open();});
  inp.addEventListener('keydown',e=>{
    if(e.key==='ArrowDown'||e.key==='ArrowUp'){e.preventDefault();if(list.hidden)open();if(!items.length)return;act=(act+(e.key==='ArrowDown'?1:-1)+items.length)%items.length;open();inp.setAttribute('aria-activedescendant',id+'-o'+act);}
    else if(e.key==='Enter'){e.preventDefault();pick(act>=0?act:0);}
    else if(e.key==='Escape')close();
  });
  list.addEventListener('pointerdown',e=>{const li=e.target.closest('li');if(li){e.preventDefault();pick(+li.dataset.i);}});
  inp.addEventListener('blur',()=>setTimeout(()=>{close();const c=SF.find(inp.value);if(c&&inp.value!==c.name)inp.value=c.name;run();},150));
}

/* ---------- stato e URL ---------- */
const segVal=id=>{const b=document.querySelector('#'+id+' [aria-pressed="true"]');return b?b.dataset.v:null;};
const setSeg=(id,v)=>document.querySelectorAll('#'+id+' button').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.v===v)));
function sleepTimes(){
  const v=segVal('sonno');
  if(v&&v!=='custom'){const [b,w]=v.split('-');return {bed:SF.hm(b),wake:SF.hm(w),l:b,s:w};}
  return {bed:SF.hm($('l').value),wake:SF.hm($('s').value),l:$('l').value,s:$('s').value};
}
function defaults(){
  const home=SF.find($('da').value)||SF.find(PRE.da),dest=SF.find($('a').value)||SF.find(PRE.a);
  $('p').value=SF.localStr(Date.now()+14*DAY,home.tz).slice(0,10)+'T10:30';
  const dep=SF.toUtc($('p').value,home.tz);
  $('r').value=SF.localStr(dep+SF.guessHours(home,dest,dep)*H,dest.tz);
}
/* i parametri utm_* dei link condivisi non contano come piano già compilato e restano nell'indirizzo */
const QS=new URLSearchParams(location.search);
let touched=['da','a','p','r'].some(k=>QS.has(k)),userTimes=false,lastKey='';
function readUrl(){
  const q=new URLSearchParams(location.search);
  $('da').value=q.get('da')||PRE.da;$('a').value=q.get('a')||PRE.a;
  const l=q.get('l'),s=q.get('s');
  if(l&&s){const v=l+'-'+s;if(document.querySelector(`#sonno [data-v="${v}"]`))setSeg('sonno',v);else if(/^\d{2}:\d{2}$/.test(l)&&/^\d{2}:\d{2}$/.test(s)){setSeg('sonno','custom');$('l').value=l;$('s').value=s;$('custom').hidden=false;}}
  if(/^[0-3]$/.test(q.get('g')||''))setSeg('prep',q.get('g'));
  if(/^(3|7|8)$/.test(q.get('t')||''))setSeg('stay',q.get('t'));
  if(q.get('m')==='1')$('m').checked=true;
  if(q.get('p')&&q.get('r')){$('p').value=q.get('p');$('r').value=q.get('r');userTimes=true;}else defaults();
}
function writeUrl(force){
  if(!touched&&!force)return;
  const q=new URLSearchParams(),st=sleepTimes();
  QS.forEach((v,k)=>{if(/^utm_/.test(k))q.set(k,v);});
  q.set('da',$('da').value.trim());q.set('a',$('a').value.trim());q.set('p',$('p').value);q.set('r',$('r').value);
  q.set('l',st.l);q.set('s',st.s);q.set('g',segVal('prep'));q.set('t',segVal('stay'));
  if($('m').checked)q.set('m','1');
  try{history.replaceState(null,'',location.pathname+'?'+q.toString()+'#calcola');}catch(e){}
}
function setCity(which,c){
  $('code-'+which).textContent=c?c.code:'···';
  $(which+'-tz').textContent=c?SF.tzLabel(c.tz,Date.now())+' · '+t('now_at',{t:SF.nowIn(c.tz)}):'';
}
function chips(){
  const dest=SF.find($('a').value),box=$('mete');if(!box)return;
  box.innerHTML=POP.map(n=>{const c=SF.find(n);return c?`<button type="button" class="chip" data-c="${esc(c.name)}" aria-pressed="${!!dest&&dest.name===c.name}">${esc(c.name)}<b>${c.code}</b></button>`:'';}).join('');
}
function run(){
  const err=$('err');err.textContent='';
  const home=SF.find($('da').value),dest=SF.find($('a').value);
  setCity('da',home);setCity('a',dest);chips();
  if(!home||!dest){err.textContent=t('city_not_found',{which:t(!home?'which_from':'which_to')});$('fline').textContent='';return;}
  const key=home.name+'|'+dest.name;
  if(lastKey&&key!==lastKey&&!userTimes)defaults();
  lastKey=key;
  const dep=SF.toUtc($('p').value,home.tz),arr=SF.toUtc($('r').value,dest.tz),st=sleepTimes();
  $('cust-l').textContent=segVal('sonno')==='custom'&&!isNaN(st.bed)&&!isNaN(st.wake)?fh(st.bed)+'–'+fh(st.wake):t('custom_set');
  if(isNaN(dep)||isNaN(arr)){err.textContent=t('need_dates');return;}
  const hours=(arr-dep)/H;
  $('fline').innerHTML=hours>0?`<span>${esc(home.code)}</span><i></i><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M21 15.5 13 11V5.5a1.5 1.5 0 0 0-3 0V11l-8 4.5V17l8-2.5V19l-2 1.5V22l3.5-1 3.5 1v-1.5L13 19v-4.5l8 2.5z" fill="#0e1430"/></svg><i></i><span>${esc(dest.code)}</span><span>· ${fdur(hours)}</span>`:'';
  if(hours<=0){err.textContent=t('arr_before_dep',{c:dest.name});return;}
  if(hours>40){err.textContent=t('too_long');return;}
  if(isNaN(st.bed)||isNaN(st.wake)){err.textContent=t('need_sleep');return;}
  const sl=SF.sleepLen(st.bed,st.wake);
  if(sl<4||sl>12){err.textContent=t('sleep_range',{h:fdur(sl)});return;}
  writeUrl();
  const plan=SF.buildPlan({home,dest,homeTz:home.tz,destTz:dest.tz,dep,arr,wake:st.wake,bed:st.bed,prep:+segVal('prep'),stay:+segVal('stay'),mel:$('m').checked});
  state.plan=plan;render(plan);
}

combo('da');combo('a');
['p','r'].forEach(id=>$(id).addEventListener('input',()=>{userTimes=true;touched=true;run();}));
['l','s','m'].forEach(id=>$(id).addEventListener('change',()=>{touched=true;run();}));
['sonno','prep','stay'].forEach(id=>$(id).addEventListener('click',e=>{
  const b=e.target.closest('button');if(!b)return;
  setSeg(id,b.dataset.v);touched=true;
  if(id==='sonno')$('custom').hidden=b.dataset.v!=='custom';
  if(id==='stay')state.showFull=false;
  run();
}));
if($('mete'))$('mete').addEventListener('click',e=>{const b=e.target.closest('.chip');if(!b)return;$('a').value=b.dataset.c;touched=true;userTimes=false;run();});
$('f').addEventListener('submit',e=>{e.preventDefault();run();});
$('swap').addEventListener('click',()=>{
  touched=true;
  const a=$('da').value;$('da').value=$('a').value;$('a').value=a;
  const home=SF.find($('da').value),dest=SF.find($('a').value);
  if(home&&dest){
    /* ritorno: una settimana dopo l'arrivo, a mezzogiorno */
    const arrOld=SF.toUtc($('r').value,home.tz),start=isNaN(arrOld)?Date.now()+21*DAY:arrOld+7*DAY;
    $('p').value=SF.localStr(start,home.tz).slice(0,10)+'T12:00';
    const dep=SF.toUtc($('p').value,home.tz);
    $('r').value=SF.localStr(dep+SF.guessHours(home,dest,dep)*H,dest.tz);
    userTimes=true;
  }
  lastKey=(home?home.name:'')+'|'+(dest?dest.name:'');
  run();
});
/* barra in basso su telefono: si vede mentre compili, sparisce quando il piano è sullo schermo */
const dk=$('dock');
if(dk&&'IntersectionObserver' in window){
  let formIn=false,planIn=false;
  const upd=()=>dk.classList.toggle('on',touched&&formIn&&!planIn&&!!state.plan);
  new IntersectionObserver(es=>{formIn=es[0].isIntersecting;upd();},{threshold:0}).observe($('f'));
  new IntersectionObserver(es=>{planIn=es[0].isIntersecting;upd();},{rootMargin:'0px 0px -35% 0px'}).observe($('risultato'));
}
readUrl();
lastKey=((SF.find($('da').value)||{}).name||'')+'|'+((SF.find($('a').value)||{}).name||'');
run();
})();
