/* Sfuso: fusi orari, modello del piano anti jet lag e mappa. Le città arrivano da build.py in window.SF_CITIES. */
(()=>{
'use strict';
const SF=window.SF={};
SF.T=window.SF_T||{};SF.LOC=window.SF_LOC||'it-IT';SF.DEC=SF.T._dec||',';
/* testi tradotti: SF.t('chiave',{segnaposto}) */
SF.t=(k,v)=>String(SF.T[k]!=null?SF.T[k]:k).replace(/\{(\w+)\}/g,(m,x)=>v&&v[x]!=null?v[x]:m);
const t=SF.t;
const CITIES=SF.CITIES=(window.SF_CITIES||[]).map(c=>({name:c[0],tz:c[1],code:c[2],lat:c[3],lon:c[4]}));
const fold=SF.fold=t=>String(t||'').normalize('NFD').replace(/[̀-ͯ]/g,'').toLowerCase().trim();
/* altre città dai fusi del browser, per chi non trova la sua (senza coordinate: niente punto sulla mappa) */
const EXTRA=[];
try{const known=new Set(CITIES.map(c=>c.tz));(Intl.supportedValuesOf?Intl.supportedValuesOf('timeZone'):[]).forEach(z=>{const n=z.split('/').pop().replace(/_/g,' ');if(!known.has(z)&&/^(Europe|America|Asia|Africa|Australia|Pacific|Atlantic|Indian)\//.test(z))EXTRA.push({name:n,tz:z,code:n.slice(0,3).toUpperCase()});});}catch(e){}
SF.ALL=CITIES.concat(EXTRA);
SF.find=v=>{v=fold(v);if(!v)return null;return SF.ALL.find(c=>fold(c.name)===v)||SF.ALL.find(c=>fold(c.name).startsWith(v))||null;};
const DAY=SF.DAY=864e5,H=SF.H=36e5;

/* ---------- fusi orari ---------- */
const fmts={};
const offMin=SF.offMin=(tz,ms)=>{
  const f=fmts[tz]||(fmts[tz]=new Intl.DateTimeFormat('en-US',{timeZone:tz,hourCycle:'h23',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',second:'2-digit'}));
  const p={};f.formatToParts(new Date(ms)).forEach(x=>p[x.type]=x.value);
  return Math.round((Date.UTC(+p.year,+p.month-1,+p.day,+p.hour%24,+p.minute,+p.second)-ms)/6e4);
};
SF.toUtc=(local,tz)=>{
  const m=/^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(local||'');if(!m)return NaN;
  const g=Date.UTC(+m[1],m[2]-1,+m[3],+m[4],+m[5]);
  const ms=g-offMin(tz,g)*6e4;return g-offMin(tz,ms)*6e4;
};
const pad=SF.pad=n=>(n<10?'0':'')+n;
SF.localStr=(ms,tz)=>{const x=new Date(ms+offMin(tz,ms)*6e4);return x.getUTCFullYear()+'-'+pad(x.getUTCMonth()+1)+'-'+pad(x.getUTCDate())+'T'+pad(x.getUTCHours())+':'+pad(x.getUTCMinutes());};
SF.localH=(ms,tz)=>{const h=((ms+offMin(tz,ms)*6e4)/H)%24;return h<0?h+24:h;};
SF.hm=v=>{const m=/^(\d{1,2}):(\d{2})/.exec(v||'');return m?(+m[1])+(+m[2])/60:NaN;};
const norm=SF.norm=h=>{h%=24;return h<0?h+24:h;};
/* ore nel formato della lingua: 24 ore, oppure 12 ore con AM/PM (inglese USA) */
const hfmt=(a,b)=>{if(!SF.T._h12)return pad(a)+':'+pad(b);const x=a%12||12,su=a<12?'AM':'PM';return b?x+':'+pad(b)+' '+su:x+' '+su;};
const fh=SF.fh=h=>{h=Math.round(norm(h)*4)/4;if(h>=24)h-=24;const a=Math.floor(h),b=Math.round((h-a)*60);return hfmt(a,b);};
SF.fhm=h=>{let m=Math.round(norm(h)*60)%1440;return hfmt(Math.floor(m/60),m%60);};
const fdur=SF.fdur=x=>{x=Math.round(x*2)/2;return (x%1?String(x).replace('.',SF.DEC):x)+' h';};
SF.fnum=x=>String(Math.round(x*2)/2).replace('.',SF.DEC);
SF.fday=(ms,tz)=>new Intl.DateTimeFormat(SF.LOC,{weekday:'long',day:'numeric',month:'long',timeZone:tz}).format(new Date(ms));
SF.tzLabel=(tz,ms)=>{let o=offMin(tz,ms)/60;const s=o>=0?'+':'−';o=Math.abs(o);return 'UTC'+s+(o%1?String(o).replace('.',SF.DEC):o);};
SF.nowIn=(tz,ms)=>new Intl.DateTimeFormat(SF.LOC,SF.T._h12?{hour:'numeric',minute:'2-digit',hour12:true,timeZone:tz}:{hour:'2-digit',minute:'2-digit',hourCycle:'h23',timeZone:tz}).format(new Date(ms||Date.now()));
SF.diffH=(a,b,ms)=>{let d=(offMin(b.tz,ms)-offMin(a.tz,ms))/60;while(d>12)d-=24;while(d<=-12)d+=24;return d;};
SF.esc=t=>String(t).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));

/* ---------- intervalli su 24 h ---------- */
const segs=SF.segs=(a,b)=>{const len=b-a;a=norm(a);if(len<=0)return[];if(len>=24)return[[0,24]];const e=a+len;return e<=24?[[a,e]]:[[a,24],[0,e-24]];};
const minus=(list,cut)=>{let out=list;cut.forEach(c=>{const n=[];out.forEach(s=>{if(c[1]<=s[0]||c[0]>=s[1]){n.push(s);return;}if(c[0]>s[0])n.push([s[0],c[0]]);if(c[1]<s[1])n.push([c[1],s[1]]);});out=n;});return out.filter(s=>s[1]-s[0]>=0.25);};
/* tiene al massimo 4 h di luce: le prime dall'inizio della finestra (anticipo) o le ultime (ritardo) */
const trim=(list,start,first)=>{
  const q=[],a=norm(start);
  for(let i=0;i<96;i++){const h=norm(a+i*0.25);if(list.some(s=>h>=s[0]-1e-9&&h<s[1]-1e-9))q.push(i);}
  const keep=first?q.slice(0,16):q.slice(-16),out=[];
  keep.forEach(i=>{const h=norm(a+i*0.25),l=out[out.length-1];if(l&&Math.abs(l[1]-h)<1e-9&&h<24)l[1]=h+0.25;else out.push([h,h+0.25]);});
  out.forEach(s=>{if(s[1]>24)s[1]=24;});
  return out;
};
SF.ranges=list=>{
  if(!list.length)return[];list=list.slice().sort((x,y)=>x[0]-y[0]);
  if(list.length>1&&list[0][0]===0&&list[list.length-1][1]===24){const f=list.shift(),l=list.pop();list.push([l[0],f[1]+24]);}
  return list.map(s=>fh(s[0])+'–'+fh(s[1]));
};
const sleepLen=SF.sleepLen=(b,w)=>norm(w-b)||24;
const inWin=(h,b,w)=>{h=norm(h);b=norm(b);w=norm(w);return w>b?(h>=b&&h<w):(h>=b||h<w);};

/* ---------- modello ---------- */
SF.compute=o=>{
  const off=(offMin(o.destTz,o.arr)-offMin(o.homeTz,o.arr))/60;
  let d=off;while(d>12)d-=24;while(d<=-12)d+=24;
  let dir,T,why='';
  if(Math.abs(d)<0.01){dir='none';T=0;}
  else if(d>0){if((24-d)/1.5<d){dir='delay';T=24-d;why='east-long';}else{dir='advance';T=d;}}
  else{dir='delay';T=-d;}
  const rate=dir==='advance'?1:1.5,sign=dir==='advance'?-1:1;
  const pre=Math.min(o.prep,Math.floor(T));
  const after=T-pre>0?Math.ceil((T-pre)/rate-1e-9):0;
  const noPlan=Math.ceil(Math.abs(d));
  /* gravità 1-10: giorni che il corpo impiegherebbe da solo, più la fatica dei voli lunghi */
  const flightH=(o.arr-o.dep)/H;
  const score=dir==='none'?0:Math.max(1,Math.min(10,Math.round(T/(dir==='advance'?1:1.5)*0.85+(flightH>10?1:0))));
  const LV=SF.T._levels||['lieve','moderato','forte','molto forte'];
  const level=LV[score<=2?0:score<=4?1:score<=7?2:3];
  return {d,dir,T,why,rate,sign,pre,after,noPlan,score,level,flightH};
};
const lightFor=(cbt,dir)=>dir==='advance'?{seek:[cbt,cbt+5],avoid:[cbt-4,cbt]}:{seek:[cbt-9,cbt],avoid:[cbt,cbt+4]};
const dayModel=(bed,wake,cbt,dir,travelUntil)=>{
  const sleep=segs(bed,bed+sleepLen(bed,wake));
  const L=lightFor(cbt,dir);
  const travel=travelUntil!=null?segs(0,travelUntil):[];
  const block=sleep.concat(travel);
  return {sleep,travel,seek:trim(minus(segs(L.seek[0],L.seek[1]),block),L.seek[0],dir==='advance'),avoid:minus(segs(L.avoid[0],L.avoid[1]),block)};
};
SF.buildPlan=o=>{
  const r=SF.compute(o),D=r.d,W=o.wake,B=o.bed,CBT0=W-2;
  const plan={o,r,days:[],flight:null};
  if(r.dir==='none')return plan;
  for(let k=r.pre;k>=1;k--){
    const s=r.pre-k+1,bed=B+r.sign*s,wake=W+r.sign*s,cbt=CBT0+r.sign*s;
    plan.days.push({kind:'pre',tz:o.homeTz,date:SF.localStr(o.dep-k*DAY,o.homeTz).slice(0,10),ms:o.dep-k*DAY,
      title:k===1?t('pre1'):t('preN',{n:k}),place:o.home.name,
      m:dayModel(norm(bed),norm(wake),norm(cbt),r.dir,null),bed:norm(bed),wake:norm(wake),coffee:norm(bed-6),mel:o.mel&&r.dir==='advance'?norm(bed-0.5):null,
      tip:t(r.dir==='advance'?'tip_pre_adv':'tip_pre_del',{h:fdur(s)})});
  }
  /* a bordo si dorme quando a destinazione è notte; verso ovest solo se anche il corpo è nella sua notte */
  const collect=body=>{
    const res=[];let cur=null;
    for(let t=o.dep;t<o.arr;t+=9e5){
      const ok=inWin(SF.localH(t,o.destTz),B,W)&&(!body||inWin(SF.localH(t,o.homeTz),B+r.sign*r.pre,W+r.sign*r.pre));
      if(ok){if(!cur)cur=[t,t];cur[1]=Math.min(t+9e5,o.arr);}else if(cur){res.push(cur);cur=null;}
    }
    if(cur)res.push(cur);
    return res.filter(x=>x[1]-x[0]>=H);
  };
  const rawNight=collect(false);
  let onboard=r.dir==='delay'?collect(true):rawNight;
  if(!onboard.length&&rawNight.length&&r.why==='east-long')onboard=rawNight;
  const arrH=SF.localH(o.arr,o.destTz);
  plan.flight={onboard,rawNight,arrH};
  const n=Math.max(1,r.after);
  for(let i=0;i<n;i++){
    const sNow=Math.min(r.T,r.pre+r.rate*i),sEnd=Math.min(r.T,r.pre+r.rate*(i+1));
    const cbtL=norm(CBT0+r.sign*sNow+D);
    const left=r.T-sEnd,bodyBed=norm(B+r.sign*sNow+D);
    let tip=left>0.01?t('tip_left',{h:fdur(left)}):t('tip_tomorrow',{c:o.dest.name});
    if(r.dir==='advance'&&norm(bodyBed-B)>1.5&&norm(bodyBed-B)<12)tip+=t('tip_body',{t:fh(bodyBed),w:fh(W)});
    if(r.dir==='delay'&&i<2)tip+=t('tip_early');
    if(i===0)tip+=t('tip_nap');
    plan.days.push({kind:'dest',tz:o.destTz,date:SF.localStr(o.arr+i*DAY,o.destTz).slice(0,10),ms:o.arr+i*DAY,
      title:i===0?t('d1'):t('dN',{n:i+1}),place:o.dest.name,
      m:dayModel(norm(B),norm(W),cbtL,r.dir,i===0?arrH:null),bed:norm(B),wake:norm(W),coffee:norm(B-6),mel:o.mel&&r.dir==='advance'&&i<4?norm(B-0.5):null,tip});
  }
  plan.adaptedDay=n+1;
  return plan;
};
SF.arrivalNote=plan=>{
  const {r,o}=plan,a=plan.flight.arrH,d0=plan.days.find(x=>x.kind==='dest');
  const av=SF.ranges(d0.m.avoid);
  if(r.dir==='advance'){
    if(a>=12&&a<16)return {cls:'good',t:t('arr_ideal_t'),p:t('arr_ideal_p',{t:fh(a)})};
    if(a>=4&&a<12)return {cls:'warn',t:t('arr_morning_t'),p:t('arr_morning_p',{t:fh(a),av:av.length?t('avoid_paren',{r:av.join(', ')}):''})};
    return {cls:'warn',t:t('arr_night_t'),p:t('arr_night_p',{t:fh(a)})};
  }
  if(a>=10&&a<17)return {cls:'good',t:t('w_good_t'),p:t('w_good_p',{t:fh(a),b:fh(o.bed)})};
  if(a>=17||a<4)return {cls:'good',t:t('w_eve_t'),p:t('w_eve_p',{t:fh(a)})};
  return {cls:'warn',t:t('w_dawn_t'),p:t('w_dawn_p',{t:fh(a)})};
};
/* durata stimata del volo (solo per precompilare): distanza ortodromica a 820 km/h più decollo e atterraggio */
SF.distKm=(a,b)=>{if(a.lat==null||b.lat==null)return null;const R=6371,r=Math.PI/180,dl=(b.lat-a.lat)*r,dn=(b.lon-a.lon)*r;const x=Math.sin(dl/2)**2+Math.cos(a.lat*r)*Math.cos(b.lat*r)*Math.sin(dn/2)**2;return 2*R*Math.asin(Math.sqrt(x));};
SF.guessHours=(a,b,ms)=>{const k=SF.distKm(a,b);if(k!=null)return Math.max(1,Math.round((k/820+0.6)*2)/2);const d0=Math.abs(SF.diffH(a,b,ms));return d0<1?2:Math.round(2+d0*1.15);};

/* ---------- calendario .ics ---------- */
SF.ics=plan=>{
  const {o}=plan,ev=[];
  const at=(date,h,tz)=>SF.toUtc(date+'T'+fh(h),tz);
  const z=ms=>new Date(ms).toISOString().replace(/[-:]/g,'').replace(/\.\d{3}/,'');
  const add=(a,b,sum,desc)=>{if(b>a)ev.push([a,b,sum,desc]);};
  plan.days.forEach(day=>{
    const s0=at(day.date,day.bed,day.tz);
    add(s0,s0+sleepLen(day.bed,day.wake)*H,t('ics_sleep'),t('ics_sleep_d'));
    const seg=(list,sum,desc)=>list.forEach(x=>{let a=at(day.date,x[0],day.tz);if(x[0]<day.wake-0.01)a+=DAY;add(a,a+(x[1]-x[0])*H,sum,desc);});
    seg(day.m.seek,t('ics_seek'),t('ics_seek_d'));
    seg(day.m.avoid,t('ics_avoid'),t('ics_avoid_d'));
    const c=at(day.date,day.coffee,day.tz);add(c,c+9e5,t('ics_coffee'),t('ics_coffee_d'));
    if(day.mel!=null){const m=at(day.date,day.mel,day.tz);add(m,m+9e5,t('ics_mel'),t('ics_mel_d'));}
  });
  (plan.flight?plan.flight.onboard:[]).forEach(x=>add(Math.max(x[0],o.dep),Math.min(x[1],o.arr),t('ics_onboard'),t('ics_onboard_d')));
  const stamp=z(Date.now());
  const lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//dal punto web//Sfuso//IT','CALSCALE:GREGORIAN','METHOD:PUBLISH','X-WR-CALNAME:Sfuso · '+o.home.name+' → '+o.dest.name];
  ev.forEach((e,i)=>lines.push('BEGIN:VEVENT','UID:sfuso-'+stamp+'-'+i+'@dalpuntoweb.it','DTSTAMP:'+stamp,'DTSTART:'+z(e[0]),'DTEND:'+z(e[1]),'SUMMARY:'+e[2],'DESCRIPTION:'+e[3].replace(/[,;]/g,'\\$&'),'TRANSP:TRANSPARENT','END:VEVENT'));
  lines.push('END:VCALENDAR');
  return lines.join('\r\n');
};
SF.download=(name,text,type)=>{
  const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type}));a.download=name;
  document.body.appendChild(a);a.click();setTimeout(()=>{URL.revokeObjectURL(a.href);a.remove();},800);
};

/* ---------- mappa: proiezione equirettangolare come assets/map.svg ---------- */
const MW=1000,LATMAX=84,LATMIN=-58,MH=394.4;
SF.MAP={W:MW,H:MH};
SF.proj=(lat,lon)=>[(lon+180)/360*MW,(LATMAX-lat)/(LATMAX-LATMIN)*MH];
/* arco di volo: curva verso il polo, più alta per le tratte lunghe; se conviene passa dall'altro lato del mondo */
SF.arc=(a,b)=>{
  let [x1,y1]=SF.proj(a.lat,a.lon),[x2,y2]=SF.proj(b.lat,b.lon);
  if(Math.abs(x2-x1)>MW/2){if(x2>x1)x2-=MW;else x2+=MW;}
  const mx=(x1+x2)/2,my=(y1+y2)/2,len=Math.hypot(x2-x1,y2-y1);
  const lift=Math.min(130,len*0.32),north=(a.lat+b.lat)/2>=-10?-1:1;
  return {d:`M${x1.toFixed(1)} ${y1.toFixed(1)} Q${mx.toFixed(1)} ${(my+north*lift).toFixed(1)} ${x2.toFixed(1)} ${y2.toFixed(1)}`,x1,y1,x2,y2,cx:mx,cy:my+north*lift};
};
/* parte della Terra al buio adesso (terminatore), come poligono sulla mappa */
SF.night=ms=>{
  const d=new Date(ms),start=Date.UTC(d.getUTCFullYear(),0,0),doy=(ms-start)/DAY;
  const decl=-23.44*Math.cos(2*Math.PI/365*(doy+10))*Math.PI/180;
  const utcH=d.getUTCHours()+d.getUTCMinutes()/60;
  const subLon=(12-utcH)*15;
  const pts=[];
  for(let lon=-180;lon<=180;lon+=4){
    const lat=Math.atan(-Math.cos((lon-subLon)*Math.PI/180)/Math.tan(decl))*180/Math.PI;
    pts.push(SF.proj(Math.max(LATMIN,Math.min(LATMAX,lat)),lon));
  }
  const darkSouth=decl>0;
  const edge=darkSouth?MH+300:-300;
  return 'M'+pts.map(p=>p[0].toFixed(1)+' '+p[1].toFixed(1)).join(' L')+` L${MW} ${edge} L0 ${edge} Z`;
};
SF.mapSvg=(opts)=>{
  /* opts: {route:[a,b], pins:[city], night:true, id} */
  const id=opts.id||'m'+Math.random().toString(36).slice(2,7);
  /* fit: inquadra solo la rotta, così su telefono non resta tagliata */
  let vb=`0 0 ${MW} ${MH}`;
  if(opts.fit&&opts.route&&opts.route[0].lat!=null&&opts.route[1].lat!=null){
    const A=SF.arc(opts.route[0],opts.route[1]);
    const x0=Math.min(A.x1,A.x2,A.cx),x1=Math.max(A.x1,A.x2,A.cx),y0=Math.min(A.y1,A.y2,A.cy),y1=Math.max(A.y1,A.y2,A.cy);
    const w=Math.max(x1-x0+170,380),h=Math.max(y1-y0+120,w*(opts.fit===true?0.62:opts.fit));
    vb=`${((x0+x1)/2-w/2).toFixed(0)} ${((y0+y1)/2-h/2).toFixed(0)} ${w.toFixed(0)} ${h.toFixed(0)}`;
  }
  let s=`<svg class="map" viewBox="${vb}" role="img" aria-label="${SF.esc(opts.label||t('map_label'))}" preserveAspectRatio="xMidYMid slice"><defs><linearGradient id="${id}g" x1="0" x2="1"><stop offset="0" stop-color="#7cc4ff"/><stop offset="1" stop-color="#ff6a3d"/></linearGradient></defs>`;
  s+=`<rect class="day" x="${-MW}" y="-400" width="${MW*3}" height="${MH+800}"/>`;
  const img=opts.base||'/jet-lag/assets/map.svg';
  [-MW,0,MW].forEach(dx=>{s+=`<image href="${img}" x="${dx}" width="${MW}" height="${MH}" opacity=".55"/>`;});
  if(opts.night!==false){const n=SF.night(Date.now());[-MW,0,MW].forEach(dx=>{s+=`<path class="night" transform="translate(${dx} 0)" d="${n}"/>`;});}
  if(opts.route){
    const [a,b]=opts.route;if(a.lat!=null&&b.lat!=null){
      const A=SF.arc(a,b);
      s+=`<path class="route-shadow" d="${A.d}"/><path class="route" pathLength="1" d="${A.d}" stroke="url(#${id}g)"/>`;
      const still=matchMedia('(prefers-reduced-motion: reduce)').matches;
      s+=`<g class="plane"><path d="M-9 -2 L4 -2 L9 0 L4 2 L-9 2 L-11 6 L-13 6 L-11 0 L-13 -6 L-11 -6 Z M-2 -2 L-6 -9 L-3 -9 L3 -2 M-2 2 L-6 9 L-3 9 L3 2" fill="#fff"/><animateMotion dur="${still?'0.01s':'3.2s'}" begin="0.3s" fill="freeze" rotate="auto" calcMode="spline" keyTimes="0;1" keySplines=".45 0 .25 1" path="${A.d}"/></g>`;
      [[a,A.x1,A.y1],[b,A.x2,A.y2]].forEach(([c,x,y],i)=>{s+=`<g class="pin ${i?'to':'from'}" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})"><circle r="14" class="halo"/><circle r="5.5"/><text y="-20" text-anchor="middle">${SF.esc(c.code)} ${SF.nowIn(c.tz)}</text></g>`;});
    }
  }
  (opts.pins||[]).forEach(c=>{if(c.lat==null)return;const [x,y]=SF.proj(c.lat,c.lon);s+=`<g class="pin dot" transform="translate(${x.toFixed(1)} ${y.toFixed(1)})"><circle r="4"/></g>`;});
  return s+'</svg>';
};
})();
