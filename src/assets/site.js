/* Sfuso: menu, mappe disegnate nelle pagine, comparsa allo scroll */
(()=>{
'use strict';
const SF=window.SF;
/* menu a tutto schermo su telefono */
const mb=document.querySelector('.menu-b'),sh=document.getElementById('sheet');
if(mb&&sh){
  const set=on=>{sh.classList.toggle('on',on);mb.setAttribute('aria-expanded',String(on));document.body.style.overflow=on?'hidden':'';if(on)sh.querySelector('.x').focus();else mb.focus();};
  mb.addEventListener('click',()=>set(true));
  sh.querySelector('.x').addEventListener('click',()=>set(false));
  sh.addEventListener('keydown',e=>{if(e.key==='Escape')set(false);});
}
/* mappe: data-map="Milano|Tokyo" per una rotta, data-map="mondo" per la sola mappa con la notte */
document.querySelectorAll('[data-map]').forEach(el=>{
  const v=el.dataset.map;
  if(v==='mondo'){el.innerHTML=SF.mapSvg({label:SF.t('night_label')});return;}
  const [a,b]=v.split('|').map(SF.find);
  if(a&&b)el.innerHTML=SF.mapSvg({route:[a,b],fit:el.dataset.fit?+el.dataset.fit:false,label:SF.t('route_label',{a:a.name,b:b.name}),night:el.dataset.night!=='no'});
});
/* ore locali vive dove serve: <span data-now="Europe/Rome"> */
const tickNow=()=>document.querySelectorAll('[data-now]').forEach(e=>{e.textContent=SF.nowIn(e.dataset.now);});
tickNow();setInterval(tickNow,30000);
/* comparsa allo scroll */
if('IntersectionObserver' in window){
  const io=new IntersectionObserver(es=>es.forEach(e=>{if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}}),{rootMargin:'0px 0px -8% 0px'});
  document.querySelectorAll('.rv').forEach(e=>io.observe(e));
}else document.querySelectorAll('.rv').forEach(e=>e.classList.add('in'));
})();
