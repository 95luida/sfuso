"""Genera il sito Sfuso in site/jet-lag/ in tutte le lingue di src/i18n (da caricare in htdocs/jet-lag su Tophost).
Uso: ~/siti-monitor/.venv/bin/python tools/build.py   (serve Python 3.12)"""
import json, math, os, re, shutil, sys
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape as E

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'src'))
from cities import CITIES, DESTS, DESTS_AM

OUT = os.path.join(ROOT, 'site', 'jet-lag')
SITE = 'https://www.dalpuntoweb.it'
BASE = SITE + '/jet-lag/'
TODAY = '2026-11-02'
VER = '4'
BY = {c[0]: c for c in CITIES}
DEST_BY = {**{d[0]: d for d in DESTS_AM}, **{d[0]: d for d in DESTS}}
ORDER = ['it', 'en', 'es', 'fr', 'de', 'en-us', 'es-mx', 'pt-br', 'fr-ca']
LANGS = [l for l in ORDER if os.path.exists(os.path.join(ROOT, 'src', 'i18n', f'{l}.json'))]
XDEFAULT = 'en' if 'en' in LANGS else 'it'
H12 = False   # orari a 12 ore (inglese USA)
DEFAULT_DEST = {'en-us': 'Londra', 'es-mx': 'Madrid', 'pt-br': 'Lisbona', 'fr-ca': 'Parigi'}
HOME_DESTS_AM = ['Londra', 'Parigi', 'Roma', 'Tokyo', 'Madrid', 'Dubai', 'Bangkok', 'Sydney', 'Lisbona', 'Bali']
POP_AM = ['Londra', 'Parigi', 'Roma', 'Madrid', 'Tokyo', 'Dubai', 'Bangkok', 'Sydney', 'Lisbona', 'Bali', 'Barcellona']
WARN = []

# ---------------------------------------------------------------- calcoli sulle rotte
def off(tz, when): return datetime(*when, tzinfo=ZoneInfo(tz)).utcoffset().total_seconds() / 3600
WINTER, SUMMER = (2026, 1, 15, 12), (2026, 7, 15, 12)
def dist_km(a, b):
    r = math.pi / 180; dl, dn = (b[3] - a[3]) * r, (b[4] - a[4]) * r
    x = math.sin(dl / 2) ** 2 + math.cos(a[3] * r) * math.cos(b[3] * r) * math.sin(dn / 2) ** 2
    return 2 * 6371 * math.asin(math.sqrt(x))
def norm(h): return h % 24
def fh(h):
    h = round(norm(h) * 4) / 4
    if h >= 24: h -= 24
    H, M = int(h), round((h - int(h)) * 60)
    if H12:
        hh = H % 12 or 12; suf = 'AM' if H < 12 else 'PM'
        return f'{hh}:{M:02d} {suf}' if M else f'{hh} {suf}'
    return f'{H:02d}:{M:02d}'
def segs(a, b):
    ln = b - a; a = norm(a)
    if ln <= 0: return []
    if ln >= 24: return [[0, 24]]
    e = a + ln
    return [[a, e]] if e <= 24 else [[a, 24], [0, e - 24]]
def minus(lst, cut):
    out = lst
    for c in cut:
        n = []
        for s in out:
            if c[1] <= s[0] or c[0] >= s[1]: n.append(s); continue
            if c[0] > s[0]: n.append([s[0], c[0]])
            if c[1] < s[1]: n.append([c[1], s[1]])
        out = n
    return [s for s in out if s[1] - s[0] >= .25]
def trim(lst, start, first):
    a = norm(start); q = []
    for i in range(96):
        h = norm(a + i * .25)
        if any(s[0] - 1e-9 <= h < s[1] - 1e-9 for s in lst): q.append(i)
    keep = q[:16] if first else q[-16:]; out = []
    for i in keep:
        h = norm(a + i * .25)
        if out and abs(out[-1][1] - h) < 1e-9 and h < 24: out[-1][1] = h + .25
        else: out.append([h, h + .25])
    return [[s[0], min(s[1], 24)] for s in out]
def ranges(lst):
    if not lst: return []
    lst = sorted(lst)
    if len(lst) > 1 and lst[0][0] == 0 and lst[-1][1] == 24:
        f = lst.pop(0); l = lst.pop(); lst.append([l[0], f[1] + 24])
    return [(fh(s[0]), fh(s[1])) for s in lst]  # nel formato della lingua in corso

def route(dest_name, home, bed=23, wake=7):
    h, d = BY[home], BY[dest_name]
    dw = off(d[1], WINTER) - off(h[1], WINTER); ds = off(d[1], SUMMER) - off(h[1], SUMMER)
    D = dw
    while D > 12: D -= 24
    while D <= -12: D += 24
    if D > 0:
        if (24 - D) / 1.5 < D: dirn, T, why = 'delay', 24 - D, 'east-long'
        else: dirn, T, why = 'advance', D, ''
    else: dirn, T, why = 'delay', -D, ''
    rate = 1 if dirn == 'advance' else 1.5
    km = dist_km(h, d); fl = max(1, round((km / 820 + .6) * 2) / 2)
    score = max(1, min(10, round(T / rate * .85 + (1 if fl > 10 else 0))))
    li = 0 if score <= 2 else 1 if score <= 4 else 2 if score <= 7 else 3
    days0 = math.ceil(T / rate - 1e-9); pre2 = min(2, int(T)); days2 = math.ceil((T - pre2) / rate - 1e-9) if T - pre2 > 0 else 1
    cbt = norm(wake - 2 + D); sleep = segs(bed, bed + norm(wake - bed))
    if dirn == 'advance': seek, avoid, first = [cbt, cbt + 5], [cbt - 4, cbt], True
    else: seek, avoid, first = [cbt - 9, cbt], [cbt, cbt + 4], False
    east = D > 0
    arr_w = (12, 16) if east and why != 'east-long' else (10, 16)
    return dict(name=dest_name, D=D, dw=dw, ds=ds, dir=dirn, east=east, T=T, why=why, km=round(km), fl=fl, score=score, li=li,
                days0=days0, days2=days2, noplan=math.ceil(abs(D)), seek=ranges(trim(minus(segs(*seek), sleep), seek[0], first)),
                avoid=ranges(minus(segs(*avoid), sleep)), arr=arr_w, dep=(norm(arr_w[0] - D - fl), norm(arr_w[1] - D - fl)), tz=d[1])

# ---------------------------------------------------------------- pezzi fissi
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@500&display=swap" rel="stylesheet">'
GTM_HEAD = """<!-- Google Tag Manager (consenso statistiche negato finché il banner cookie non lo concede) -->
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('consent','default',{ad_storage:'denied',ad_user_data:'denied',ad_personalization:'denied',analytics_storage:/(^|;\\s*)dpw_cc=[^;]*analytics/.test(document.cookie)?'granted':'denied'});
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);})(window,document,'script','dataLayer','GTM-MGWWGWX');</script>
<!-- End Google Tag Manager -->"""
GTM_BODY = '<!-- Google Tag Manager (noscript) --><noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-MGWWGWX" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript><!-- End Google Tag Manager (noscript) -->'
LOGO = '<span class="tile" aria-hidden="true"><i>S</i><i>S</i></span><span class="word" aria-hidden="true"><span class="shift"><span class="t">Sfuso</span><span class="b">Sfuso</span></span></span>'
TOOL_KEYS = ['fusi-orari', 'riunioni', 'sonno', 'ora-nel-mondo']
TOOL_ICON = {
    'fusi-orari': '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 7v5l3 2" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round"/>',
    'riunioni': '<rect x="3" y="5" width="18" height="15" rx="3" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 10h18M8 3v4M16 3v4" stroke="currentColor" stroke-width="2"/>',
    'sonno': '<path d="M20 14.5A8 8 0 0 1 9.5 4 8 8 0 1 0 20 14.5z" fill="none" stroke="currentColor" stroke-width="2"/>',
    'ora-nel-mondo': '<circle cx="12" cy="12" r="9" fill="none" stroke="currentColor" stroke-width="2"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18" fill="none" stroke="currentColor" stroke-width="1.6"/>'}
PERSON = {"@type": "Person", "@id": SITE + "/#luigi", "name": "Luigi", "url": SITE + "/", "sameAs": ["https://github.com/95luida"]}
CITATIONS = [{"@type": "ScholarlyArticle", "name": "How To Travel the World Without Jet lag", "author": ["Charmane I. Eastman", "Helen J. Burgess"], "datePublished": "2009", "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC2829880/"},
             {"@type": "ScholarlyArticle", "name": "Melatonin for the prevention and treatment of jet lag", "author": ["Andrew Herxheimer", "Keith J. Petrie"], "datePublished": "2002", "url": "https://pubmed.ncbi.nlm.nih.gov/12076414/"}]
POP_IT = ["New York", "Tokyo", "Dubai", "Bangkok", "Maldive", "Los Angeles", "Miami", "Sydney", "Bali", "Cancún"]
HOME_DESTS = ['New York', 'Tokyo', 'Dubai', 'Bangkok', 'Maldive', 'Los Angeles', 'Bali', 'Sydney']
GUIDE_MAPS = ['Tokyo', 'New York', 'Singapore', 'Bangkok', 'New York', 'Dubai']
ALL_PAGES = {}   # id -> {lang: path}
LINFO = {}       # lang -> (nome, hreflang, sigla)

class Safe(dict):
    def __missing__(self, k):
        WARN.append('segnaposto mancante {' + k + '}'); return '{' + k + '}'

# ---------------------------------------------------------------- una lingua
class Lang:
    def __init__(self, code):
        self.code = code
        self.L = json.load(open(os.path.join(ROOT, 'src', 'i18n', f'{code}.json')))
        gfile = 'guide.json' if code == 'it' else f'guide.{code}.json'
        self.G = json.load(open(os.path.join(ROOT, 'src', gfile)))
        if code == 'it':
            for g in self.G:
                for k in ('title', 'h1'): g[k] = g[k].replace(' a adattarsi', ' ad adattarsi')
        L = self.L; self.P = L['p']; self.S = L['slugs']
        self.cn = lambda it: L['cities'].get(it, it)          # nome città nella lingua
        inv = {v: k for k, v in L['cities'].items()}
        self.home = inv[L['home']['city']]                       # chiave italiana della città di casa
        self.alt = L['home']['alt_city']
        self.pre = '' if code == 'it' else code + '/'
        self.am = '-' in code
        self.h12 = code == 'en-us'
        self.hl = L['locale'] if self.am else code
        if self.am:
            cand = [d for d in DESTS_AM if d[0] != self.home]
            self.dests = [d for d in cand if abs(route(d[0], self.home)['D']) >= 2][:24]
        else: self.dests = list(DESTS)
        self.dnames = [d[0] for d in self.dests]
        self.default_dest = DEFAULT_DEST.get(code, 'New York')
        self.home_dests = [n for n in (HOME_DESTS_AM if self.am else ['New York', 'Tokyo', 'Dubai', 'Bangkok', 'Maldive', 'Los Angeles', 'Bali', 'Sydney']) if n in self.dnames][:8]
        self.pop = [n for n in (POP_AM if self.am else POP_IT) if n != self.home][:10]
        h = L['home']
        self.ctx = {'from': h['from'], 'From': h['from'][:1].upper() + h['from'][1:], 'home_country': h['country'], 'home_in': h['in'], 'home_rel': h['rel'],
                    'home_of': h['of'], 'hc': L['home']['city'], 'alt': h['alt_city']}
        self.dec = L['dec']
        self.grp = {'en': ',', 'en-us': ',', 'es-mx': ',', 'fr': ' ', 'fr-ca': ' '}.get(code, '.')
        self.compute()
    def compute(self):
        global H12
        H12 = self.h12
        self.R = {d[0]: route(d[0], self.home) for d in self.dests}

    # testi
    def f(self, _tpl, **kw): return _tpl.format_map(Safe({**self.ctx, **kw}))
    def p(self, k, **kw): return self.f(self.P[k], **kw)
    def fnum(self, x):
        x = round(x * 2) / 2
        return (f'{x:.1f}'.replace('.', self.dec)) if x % 1 else str(int(x))
    def hr(self, n): return fh(n) if self.h12 else str(n)
    def sgn(self, x): return ('+' if x > 0 else '−' if x < 0 else '±') + self.fnum(abs(x))
    def lvl(self, r): return self.L['levels'][r['li']]
    def km(self, n): return f'{n:,}'.replace(',', self.grp)
    # indirizzi
    def u(self, *parts): return '/jet-lag/' + self.pre + ''.join(parts)
    def path_routes(self): return self.S['rotte'] + '/'
    def path_route(self, slug): return f"{self.S['rotte']}/{slug}/"
    def path_rank(self): return self.S['classifica'] + '/'
    def path_tools(self): return self.S['strumenti'] + '/'
    def path_tool(self, k): return f"{self.S['strumenti']}/{self.S['tools'][k]}/"
    def path_guides(self): return self.S['guide'] + '/'
    def path_guide(self, gi): return f"{self.S['guide']}/{self.G[gi]['slug']}/"

def collect_paths(langs):
    for lg in langs:
        reg = {'home': '', 'routes': lg.path_routes(), 'rank': lg.path_rank(), 'tools': lg.path_tools(), 'guides': lg.path_guides()}
        for d in lg.dests: reg['route:' + d[1]] = lg.path_route(d[1])
        for k in TOOL_KEYS: reg['tool:' + k] = lg.path_tool(k)
        for i in range(len(lg.G)): reg[f'guide:{i}'] = lg.path_guide(i)
        for pid, pth in reg.items(): ALL_PAGES.setdefault(pid, {})[lg.code] = lg.pre + pth

# ---------------------------------------------------------------- pezzi di pagina
def header(lg, cur, pid):
    P = lg.P; AC = ' aria-current="page"'
    nav = [('rotte', lg.u(lg.path_routes()), P['nav_routes']), ('strumenti', lg.u(lg.path_tools()), P['nav_tools']), ('guide', lg.u(lg.path_guides()), P['nav_guides']), ('classifica', lg.u(lg.path_rank()), P['nav_rank'])]
    links = ''.join(f'<a href="{u}"{AC if k == cur else ""}>{E(t)}</a>' for k, u, t in nav)
    sheet = f'<a class="big" href="{lg.u()}">{E(P["nav_calc"])}<span>→</span></a>' + ''.join(f'<a class="big" href="{u}">{E(t)}<span>→</span></a>' for k, u, t in nav)
    alts = ALL_PAGES.get(pid, {})
    items = ''.join(f'<a href="/jet-lag/{alts.get(c, ALL_PAGES["home"][c])}" hreflang="{LINFO[c][1]}" lang="{LINFO[c][1]}"{AC if c == lg.code else ""}><b>{E(LINFO[c][2])}</b>{E(LINFO[c][0])}</a>' for c in LANGS)
    langs = f'<details class="langs"><summary aria-label="{E(P["lang_aria"])}">{E(lg.L["short"])}</summary><div class="ll">{items}</div></details>'
    return f'''<header class="site-h"><div class="wrap"><div class="bar">
<a class="brand" href="{lg.u()}" aria-label="{E(P['home_aria'])}">{LOGO}</a>
<nav aria-label="{E(P['nav_aria'])}">{links}<a class="go" href="{lg.u()}#calcola">{E(P['nav_go'])}</a></nav>
<div class="langs" aria-label="{E(P['lang_aria'])}">{langs}</div>
<button type="button" class="menu-b" aria-label="{E(P['menu_open'])}" aria-expanded="false" aria-controls="sheet"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16M4 12h16M4 17h10" stroke="#fff" stroke-width="2.2" stroke-linecap="round"/></svg></button>
</div></div></header>
<div class="sheet" id="sheet" role="dialog" aria-modal="true" aria-label="{E(P['menu'])}"><div class="top"><span class="brand">{LOGO}</span><button type="button" class="x" aria-label="{E(P['menu_close'])}">✕</button></div>{sheet}<div class="big-l">{items}</div></div>'''

def footer(lg):
    P = lg.P
    mete = ''.join(f'<li><a href="{lg.u(lg.path_route(d[1]))}">{E(lg.p("jl_city", c=lg.cn(d[0])))}</a></li>' for d in lg.dests[:8])
    tl = ''.join(f'<li><a href="{lg.u(lg.path_tool(k))}">{E(P["tools"][k]["name"])}</a></li>' for k in TOOL_KEYS)
    gl = ''.join(f'<li><a href="{lg.u(lg.path_guide(i))}">{E(g["h1"])}</a></li>' for i, g in enumerate(lg.G[:5]))
    credit = lg.p('foot_credit', date=f'<time datetime="{TODAY}">{E(lg.L["date_text"])}</time>')
    return f'''<footer class="site"><div class="wrap"><div class="cols">
<div><a class="brand" href="{lg.u()}">{LOGO}</a><p>{E(P['foot_about'])}</p></div>
<div><h3>{E(P['foot_routes'])}</h3><ul>{mete}<li><a href="{lg.u(lg.path_routes())}">{E(P['foot_all_routes'])}</a></li></ul></div>
<div><h3>{E(P['foot_tools'])}</h3><ul><li><a href="{lg.u()}">{E(P['foot_plan'])}</a></li>{tl}<li><a href="{lg.u(lg.path_rank())}">{E(P['foot_rank'])}</a></li></ul></div>
<div><h3>{E(P['foot_guides'])}</h3><ul>{gl}<li><a href="{lg.u(lg.path_guides())}">{E(P['foot_all_guides'])}</a></li></ul></div>
</div><div class="base"><address>{credit} · <a href="https://github.com/95luida" target="_blank" rel="noopener" aria-label="{E(P['foot_contact_aria'])}">{E(P['foot_contact'])}</a></address>
<span><a href="/cookie/">{E(P['privacy'])}</a> · <button type="button" data-cc="show-preferencesModal">{E(P['cookie_prefs'])}</button></span></div></div></footer>'''

def crumbs(lg, items):
    full = [('Sfuso', lg.u())] + items
    ld = {"@type": "BreadcrumbList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "name": n, "item": SITE + u} for i, (n, u) in enumerate(full)]}
    html = '<ol class="crumbs">' + ''.join(f'<li><a href="{u}">{E(n)}</a></li>' if i < len(full) - 1 else f'<li aria-current="page">{E(n)}</li>' for i, (n, u) in enumerate(full)) + '</ol>'
    return html, ld
def faq_ld(faq): return {"@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
def faq_html(faq, h2): return f'<h2 id="domande-h">{E(h2)}</h2>' + ''.join(f'<div class="qa"><h3>{E(q)}</h3><p>{E(a)}</p></div>' for q, a in faq)
def speak(*sel): return {"@type": "SpeakableSpecification", "cssSelector": list(sel)}

def page(lg, pid, title, desc, body, cur='', ld=None, scripts=('site',), og_title=None):
    path = ALL_PAGES[pid][lg.code]; url = BASE + path
    if len(title) > 62: WARN.append(f'{lg.code} title {len(title)}: {title}')
    if not 110 <= len(desc) <= 162: WARN.append(f'{lg.code} desc {len(desc)}: {path}')
    graph = [PERSON] + (ld or [])
    for n in graph:
        if n.get('@type') in ('WebPage', 'CollectionPage', 'WebApplication', 'Article', 'WebSite'): n.setdefault('inLanguage', lg.L['locale'])
    cities = json.dumps([[lg.cn(c[0])] + list(c[1:]) for c in CITIES], ensure_ascii=False, separators=(',', ':'))
    T = dict(lg.L['ui']); T['_dec'] = lg.dec; T['_levels'] = lg.L['levels']; T['_none'] = lg.L['level_none']; T['_h12'] = lg.h12
    home = lg.home
    tzl = [x for x in ['New York', 'Londra', 'Dubai', 'Tokyo', 'Los Angeles', 'Sydney', 'Milano'] if x != home][:6]
    world = [home] + [x for x in ['Londra', 'New York', 'Los Angeles', 'Città del Messico', 'San Paolo', 'Dubai', 'Mosca', 'Nuova Delhi', 'Bangkok', 'Singapore', 'Hong Kong', 'Tokyo', 'Sydney', 'Auckland', 'Honolulu', 'Milano'] if x != home]
    DEF = {'home': lg.cn(home), 'tz': [lg.cn(x) for x in tzl], 'mtg': [lg.cn(x) for x in [home, 'New York', 'Tokyo']], 'world': [lg.cn(x) for x in world[:16]]}
    alts = ALL_PAGES[pid]
    hl = ''.join(f'<link rel="alternate" hreflang="{LINFO[c][1]}" href="{BASE}{alts[c]}">' for c in LANGS if c in alts)
    hl += f'<link rel="alternate" hreflang="x-default" href="{BASE}{alts.get(XDEFAULT, path)}">'
    ogalt = ''.join(f'<meta property="og:locale:alternate" content="{json.load(open(os.path.join(ROOT, "src", "i18n", c + ".json")))["og_locale"]}">' for c in LANGS if c != lg.code and c in alts)
    js = ''.join(f'<script src="/jet-lag/assets/{s}.js?v={VER}" defer></script>' for s in scripts)
    html = f'''<!doctype html>
<html lang="{lg.hl}">
<head>
<meta charset="utf-8">
{GTM_HEAD}
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}">
{hl}
<meta name="theme-color" content="#0a1024">
<meta property="og:type" content="website"><meta property="og:site_name" content="Sfuso · dal punto web">
<meta property="og:title" content="{E(og_title or title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}og.png"><meta property="og:image:width" content="1200"><meta property="og:image:height" content="630">
<meta property="og:locale" content="{lg.L['og_locale']}">{ogalt}<meta name="twitter:card" content="summary_large_image">
<meta name="apple-mobile-web-app-title" content="Sfuso"><meta name="format-detection" content="telephone=no">
<link rel="icon" href="/jet-lag/favicon.svg" type="image/svg+xml">
{FONTS}
<link rel="stylesheet" href="/jet-lag/assets/style.css?v={VER}">
<script type="application/ld+json">{json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False)}</script>
</head>
<body>
{GTM_BODY}
<a class="skip" href="#contenuto">{E(lg.P['skip'])}</a>
{header(lg, cur, pid)}
<main id="contenuto">
{body}
</main>
{footer(lg)}
<script>window.SF_CITIES={cities};window.SF_T={json.dumps(T, ensure_ascii=False)};window.SF_LOC="{lg.L['locale']}";window.SF_POP={json.dumps([lg.cn(x) for x in lg.pop], ensure_ascii=False)};window.SF_DEF={json.dumps(DEF, ensure_ascii=False)};</script>
<script src="/jet-lag/assets/core.js?v={VER}" defer></script>{js}
<script src="/cookie/consent.js" defer></script>
</body>
</html>
'''
    dst = os.path.join(OUT, path, 'index.html')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'w').write(html)
    SITEMAP.append(path)
SITEMAP = []

def hero(lg, h1, lead, crumbs_html=None, kicker=None, dest='New York', small=True, extra='', lead_id='definizione', cta=None):
    cta = lg.u() + '#calcola' if cta is None else cta
    if dest == lg.home or dest not in BY: dest = lg.default_dest
    return f'''<section class="hero{' small' if small else ''}"><div class="map-w" data-map="{E(lg.cn(lg.home))}|{E(lg.cn(dest))}" aria-hidden="true"></div><div class="wrap in">
{crumbs_html or ''}{f'<span class="kicker"><i></i>{E(kicker)}</span>' if kicker else ''}
<h1>{h1}</h1><p class="lead" id="{lead_id}">{lead}</p>{f'<p style="margin:20px 0 0"><a class="btn main" href="{cta}">{E(lg.P["hero_cta"])}</a></p>' if cta else ''}{extra}</div></section>'''

def calc_html(lg, dest):
    P = lg.P; da, a = lg.cn(lg.home), lg.cn(dest)
    return f'''<section id="calcola" aria-label="{E(P['f_aria'])}" data-calc data-da="{E(da)}" data-a="{E(a)}"><div class="wrap lift">
<form class="glass calc" id="f" novalidate autocomplete="off">
  <div class="route-in">
    <div class="cityf"><label class="lab" for="da">{E(P['f_from'])}</label><div class="code" id="code-da" aria-hidden="true">···</div>
      <input id="da" name="da" value="{E(da)}" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="sug-da" spellcheck="false" enterkeyhint="next">
      <ul class="sug" id="sug-da" role="listbox" aria-label="{E(P['f_list_from'])}" hidden></ul><span class="meta" id="da-tz"></span></div>
    <button type="button" class="swap" id="swap" aria-label="{E(P['f_swap'])}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M4 8h14m0 0-4-4m4 4-4 4M20 16H6m0 0 4-4m-4 4 4 4" fill="none" stroke="#fff" stroke-width="2.2"/></svg></button>
    <div class="cityf r"><label class="lab" for="a">{E(P['f_to'])}</label><div class="code" id="code-a" aria-hidden="true">···</div>
      <input id="a" name="a" value="{E(a)}" role="combobox" aria-autocomplete="list" aria-expanded="false" aria-controls="sug-a" spellcheck="false" enterkeyhint="next">
      <ul class="sug" id="sug-a" role="listbox" aria-label="{E(P['f_list_to'])}" hidden></ul><span class="meta" id="a-tz"></span></div>
  </div>
  <div class="chips" id="mete" role="group" aria-label="{E(P['f_chips'])}"></div>
  <div class="sep"></div>
  <div class="two">
    <div class="field"><label class="lab" for="p">{E(P['f_dep'])}</label><input id="p" name="p" type="datetime-local" required></div>
    <div class="field"><label class="lab" for="r">{E(P['f_arr'])}</label><input id="r" name="r" type="datetime-local" required><span class="hint">{E(P['f_arr_hint'])}</span></div>
  </div>
  <div class="flightline" id="fline"></div>
  <div class="sep"></div>
  <span class="lab" id="l-sonno">{E(P['f_sleep'])}</span>
  <div class="seg" role="group" aria-labelledby="l-sonno" id="sonno">
    <button type="button" data-v="22:00-06:00" aria-pressed="false">{E(P['f_lark'])}<small>{fh(22) if lg.h12 else '22'}–{fh(6) if lg.h12 else '06'}</small></button>
    <button type="button" data-v="23:00-07:00" aria-pressed="true">{E(P['f_classic'])}<small>{fh(23) if lg.h12 else '23'}–{fh(7) if lg.h12 else '07'}</small></button>
    <button type="button" data-v="00:30-08:30" aria-pressed="false">{E(P['f_owl'])}<small>{fh(0.5) if lg.h12 else '0:30'}–{fh(8.5) if lg.h12 else '8:30'}</small></button>
    <button type="button" data-v="custom" aria-pressed="false">{E(P['f_custom'])}<small id="cust-l">{E(lg.L['ui']['custom_set'])}</small></button>
  </div>
  <div class="custom two" id="custom" hidden>
    <div class="field"><label class="lab" for="l">{E(P['f_bed'])}</label><input id="l" name="l" type="time" value="23:00"></div>
    <div class="field"><label class="lab" for="s">{E(P['f_wake'])}</label><input id="s" name="s" type="time" value="07:00"></div>
  </div>
  <div class="row"><span class="lab" id="l-prep">{E(P['f_prep'])}</span>
    <div class="seg" role="group" aria-labelledby="l-prep" id="prep">
      <button type="button" data-v="0" aria-pressed="false">0<small>{E(P['f_prep0'])}</small></button><button type="button" data-v="1" aria-pressed="false">1<small>{E(P['f_day'])}</small></button><button type="button" data-v="2" aria-pressed="true">2<small>{E(P['f_days'])}</small></button><button type="button" data-v="3" aria-pressed="false">3<small>{E(P['f_days'])}</small></button>
    </div></div>
  <div class="row"><span class="lab" id="l-stay">{E(P['f_stay'])}</span>
    <div class="seg" role="group" aria-labelledby="l-stay" id="stay">
      <button type="button" data-v="3" aria-pressed="false">1–3<small>{E(P['f_days'])}</small></button><button type="button" data-v="7" aria-pressed="true">4–7<small>{E(P['f_days'])}</small></button><button type="button" data-v="8" aria-pressed="false">8+<small>{E(P['f_days'])}</small></button>
    </div></div>
  <label class="toggle"><span>{E(P['f_mel'])}<br><small class="muted">{E(P['f_mel_s'])}</small></span><input type="checkbox" id="m" name="m"><span class="sw" aria-hidden="true"></span></label>
  <p class="err" id="err" role="alert"></p>
</form></div></section>
<section id="piano" aria-label="{E(P['plan_aria'])}"><div class="wrap" id="risultato" aria-live="polite"></div></section>
<div class="dock" id="dock" aria-hidden="true"><div class="s" id="dock-s"></div><a href="#piano" tabindex="-1">{E(P['dock_btn'])}</a></div>'''

def dest_card(lg, name):
    d, r = DEST_BY[name], lg.R[name]
    return f'''<a class="dest rv" href="{lg.u(lg.path_route(d[1]))}"><span data-map="{E(lg.cn(lg.home))}|{E(lg.cn(name))}" data-night="no" data-fit="0.62" aria-hidden="true"></span><span class="c">{E(lg.L['countries'].get(d[2], d[2]))}</span><b>{E(lg.cn(name))}</b><span class="d"><span>{E(lg.P['card_east'] if r['east'] else lg.P['card_west'])}<br>{E(lg.p('card_level', level=lg.lvl(r)))}</span><strong>{lg.sgn(r['D'])} h</strong></span></a>'''
def tool_card(lg, k):
    T = lg.P['tools'][k]
    return f'<a class="tool-c card rv" href="{lg.u(lg.path_tool(k))}"><span class="ic"><svg viewBox="0 0 24 24" aria-hidden="true">{TOOL_ICON[k]}</svg></span><b>{E(T["name"])}</b><span>{E(T["card"])}</span><em>{E(lg.P["tool_open"])}</em></a>'
def guide_card(lg, i):
    g = lg.G[i]
    return f'<a class="tool-c card rv" href="{lg.u(lg.path_guide(i))}"><span class="eyebrow" style="margin:0">{E(g["kicker"])}</span><b>{E(g["h1"])}</b><span>{E(g["description"])}</span><em>{E(lg.P["guide_read"])}</em></a>'
def cta_band(lg, text=None, href=None, btn=None):
    P = lg.P
    return f'<div class="cta-band rv"><div><h2>{E(text or P["cta_t"])}</h2><p>{E(P["cta_p"])}</p></div><a class="btn main" href="{href or lg.u() + "#calcola"}">{E(btn or P["cta_btn"])}</a></div>'
def sources(lg):
    P = lg.P; nt = P['new_tab']
    return f'''<h2 id="fonti">{E(P['sources_h'])}</h2><p>{E(P['sources_p'])}</p><ul>
<li>Eastman C.I., Burgess H.J., <a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC2829880/" target="_blank" rel="noopener" aria-label="How To Travel the World Without Jet lag {E(nt)}">How To Travel the World Without Jet lag</a>, Sleep Medicine Clinics, 2009: {E(P['src1_note'])}</li>
<li>Herxheimer A., Petrie K.J., <a href="https://pubmed.ncbi.nlm.nih.gov/12076414/" target="_blank" rel="noopener" aria-label="Melatonin for the prevention and treatment of jet lag {E(nt)}">Melatonin for the prevention and treatment of jet lag</a>, {E(P['src2_kind'])}, 2002: {E(P['src2_note'])}</li></ul>
<p class="warn-box">{E(P['medical'])}</p>'''

# ---------------------------------------------------------------- pagine
def build_home(lg):
    P = lg.P; R = lg.R
    lo = min(R.values(), key=lambda r: (r['noplan'], r['fl'])); hi = max(R.values(), key=lambda r: (r['noplan'], r['fl']))
    facts = f'<div class="facts"><div class="fact"><b>24</b><span>{E(lg.p("home_f1"))}</span></div><div class="fact"><b>4</b><span>{E(P["home_f2"])}</span></div><div class="fact"><b>.ics</b><span>{E(P["home_f3"])}</span></div></div>'
    body = hero(lg, P['home_h1'], E(P['home_lead']), None, P['home_kicker'], 'Tokyo', False, facts, cta='#calcola')
    body += calc_html(lg, lg.default_dest)
    faq = [tuple(x) for x in P['home_faq']]
    body += f'''<section class="section" id="come" aria-labelledby="h-come"><div class="wrap">
<span class="eyebrow">{E(P['m_eyebrow'])}</span><h2 id="h-come">{E(P['m_h'])}</h2><p class="prose muted">{E(P['m_p'])}</p>
<div class="grid3">{''.join(f'<div class="feat card rv"><span class="n">{i}</span><h3>{E(P[f"m{i}_h"])}</h3><p>{E(P[f"m{i}_p"])}</p></div>' for i in (1, 2, 3))}</div></div></section>
<section class="section" aria-labelledby="h-mete"><div class="wrap"><span class="eyebrow">{E(lg.p('hd_eyebrow'))}</span><h2 id="h-mete">{E(P['hd_h'])}</h2>
<p class="prose muted">{E(lg.p('hd_p', min_days=lo['noplan'], min_city=lg.cn(lo['name']), max_days=hi['noplan'], max_city=lg.cn(hi['name'])))}</p>
<div class="grid4">{''.join(dest_card(lg, n) for n in lg.home_dests)}</div><p style="margin-top:16px"><a class="btn dark" href="{lg.u(lg.path_routes())}">{E(P['hd_all'])}</a> <a class="btn" href="{lg.u(lg.path_rank())}">{E(P['hd_rank'])}</a></p></div></section>
<section class="section" aria-labelledby="h-str"><div class="wrap"><span class="eyebrow">{E(P['ht_eyebrow'])}</span><h2 id="h-str">{E(P['ht_h'])}</h2><p class="prose muted">{E(P['ht_p'])}</p>
<div class="grid4">{''.join(tool_card(lg, k) for k in TOOL_KEYS)}</div></div></section>
<section class="section" aria-labelledby="h-gd"><div class="wrap"><span class="eyebrow">{E(P['hg_eyebrow'])}</span><h2 id="h-gd">{E(P['hg_h'])}</h2><p class="prose muted">{E(P['hg_p'])}</p>
<div class="grid3">{''.join(guide_card(lg, i) for i in range(3))}</div></div></section>
<section class="section" id="domande" aria-labelledby="domande-h"><div class="wrap prose">{faq_html(faq, P['home_faq_h'])}<div style="margin-top:40px">{sources(lg)}</div></div></section>'''
    base = BASE + lg.pre
    ld = [{"@type": "WebPage", "@id": base + "#pagina", "url": base, "name": P['home_title'], "datePublished": TODAY, "dateModified": TODAY, "description": P['home_ld_desc'], "author": {"@id": PERSON["@id"]}, "mainEntity": {"@id": base + "#app"}, "citation": CITATIONS, "speakable": speak("#definizione", "#domande h3")},
          {"@type": "WebSite", "@id": base + "#sito", "url": base, "name": "Sfuso", "publisher": {"@id": PERSON["@id"]}},
          {"@type": "WebApplication", "@id": base + "#app", "name": P['app_name'], "url": base, "applicationCategory": "TravelApplication", "operatingSystem": "Web", "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "featureList": P['features']},
          faq_ld(faq)]
    page(lg, 'home', P['home_title'], P['home_desc'], body, 'calcolatore', ld, ('site', 'calc'), P['home_og'])

def build_route(lg, d):
    P = lg.P; name, slug, country, _ = d; r = lg.R[name]; c = lg.cn(name)
    way = P['way_ahead'] if r['D'] > 0 else P['way_behind']
    seas = lg.p('seas_diff', w=lg.fnum(abs(r['dw'])), s=lg.fnum(abs(r['ds'])), way=way) if abs(r['ds']) != abs(r['dw']) else lg.p('seas_same', w=lg.fnum(abs(r['dw'])), way=way)
    if r['why'] == 'east-long': how = lg.p('r_how_long', D=lg.fnum(abs(r['D'])), T=lg.fnum(r['T']))
    elif r['dir'] == 'advance': how = lg.p('r_how_adv', c=c)
    else: how = lg.p('r_how_del', c=c)
    pre = lg.p('r_pre_adv' if r['dir'] == 'advance' else 'r_pre_del', n=r['days2'])
    light = lg.p('r_light_seek', a=r['seek'][0][0], b=r['seek'][0][1]) if r['seek'] else P['r_light_none']
    light += lg.p('r_light_avoid', a=r['avoid'][0][0], b=r['avoid'][0][1]) if r['avoid'] else '.'
    arr = lg.p('r_arr_win', a=lg.hr(r['arr'][0]), b=lg.hr(r['arr'][1]))
    flight = lg.p('r_flight', fl=lg.fnum(r['fl']), km=lg.km(r['km'])) + (lg.p('r_flight_e', c=c) if r['east'] else P['r_flight_w'])
    back = lg.p('r_back_adv', n=math.ceil(abs(r['D']) / 1.5 - 1e-9)) if r['dir'] == 'advance' else lg.p('r_back_del', n=math.ceil(abs(r['D']) - 1e-9))
    dirw = P['dir_east'] if r['east'] else P['dir_west']
    faq = [(lg.p('r_faq1_q', c=c), lg.p('r_faq1_a', c=c, n=r['noplan'], d0=r['days0'], d2=r['days2'])),
           (lg.p('r_faq2_q', c=c), lg.p('r_faq2_a', c=c, seas=seas, tw=fh(12 + r['dw']), ts=fh(12 + r['ds']))),
           (lg.p('r_faq3_q', c=c), lg.p('r_faq3_a', c=c, arr=arr, fl=lg.fnum(r['fl']), d0=fh(r['dep'][0]), d1=fh(r['dep'][1])))]
    title = lg.p('r_title', c=c)
    if len(title) > 60: title = lg.p('r_title_short', c=c)
    desc = lg.p('r_desc', c=c, D=lg.fnum(abs(r['D'])), dir=dirw, days=r['days0'])
    ch, cld = crumbs(lg, [(P['nav_routes'], lg.u(lg.path_routes())), (lg.p('jl_city', c=c), lg.u(lg.path_route(slug)))])
    facts = f'''<div class="facts"><div class="fact"><b>{lg.sgn(r['dw'])} h</b><span>{E(P['r_f_w'])}</span></div><div class="fact"><b>{lg.sgn(r['ds'])} h</b><span>{E(P['r_f_s'])}</span></div><div class="fact"><b>{r['days0']} {E(P['r_f_days_unit'])}</b><span>{E(lg.p('r_f_days', n=r['noplan']))}</span></div><div class="fact"><b>{r['score']}/10</b><span>{E(lg.p('r_f_level', level=lg.lvl(r)))}</span></div><div class="fact"><b>~{lg.fnum(r['fl'])} h</b><span>{E(P['r_f_fl'])}</span></div><div class="fact"><b><span data-now="{r['tz']}">--:--</span></b><span>{E(lg.p('r_f_now', c=c))}</span></div></div>'''
    body = hero(lg, E(lg.p('r_h1', c=c)), E(lg.p('r_lead', c=c, seas=seas, how=how)), ch, lg.p('r_kicker', country=lg.L['countries'].get(country, country), dir=dirw), name, True, facts, cta='#calcola')
    body += calc_html(lg, name)
    others = [x[0] for x in lg.dests if x[0] != name and lg.R[x[0]]['east'] == r['east']][:4]
    link = f'<a href="https://pmc.ncbi.nlm.nih.gov/articles/PMC2829880/" target="_blank" rel="noopener" aria-label="How To Travel the World Without Jet lag {E(P["new_tab"])}">How To Travel the World Without Jet lag</a>'
    body += f'''<section class="section" aria-labelledby="h-quanto"><div class="wrap prose">
<span class="eyebrow">{E(lg.p('r_eyebrow', c=c))}</span>
<h2 id="h-quanto">{E(lg.p('r_h_long', c=c))}</h2><p>{lg.p('r_p_long', n=r['noplan'], d0=r['days0'], s=r['score'], level=E(lg.lvl(r)))}</p>
<h2>{E(P['r_h_pre'])}</h2><p>{E(pre)}</p>
<h2>{E(P['r_h_fl'])}</h2><p>{E(flight)}{E(lg.p('r_fl_tail', c=c))}</p>
<h2>{E(lg.p('r_h_arr', c=c))}</h2><p>{E(lg.p('r_p_arr', arr=arr, light=light))}</p>
<h2>{E(lg.p('r_h_back'))}</h2><p>{E(back)}</p>
{faq_html(faq, P['faq_h'])}
<p class="small-print">{lg.p('r_src', link=link)}</p>
</div></section>
<section class="section" aria-labelledby="h-altre"><div class="wrap"><h2 id="h-altre">{E(lg.p('r_h_more', dir=dirw))}</h2><div class="grid4">{''.join(dest_card(lg, n) for n in others)}</div>
<div style="margin-top:28px">{cta_band(lg, lg.p('r_cta', c=c), '#calcola', P['r_cta_btn'])}</div></div></section>'''
    url = BASE + ALL_PAGES['route:' + slug][lg.code]
    ld = [{"@type": "WebPage", "@id": url + "#pagina", "url": url, "name": title, "dateModified": TODAY, "description": desc, "author": {"@id": PERSON["@id"]}, "isPartOf": {"@id": BASE + lg.pre + "#sito"},
           "about": {"@type": "City", "name": c, "containedInPlace": {"@type": "Country", "name": lg.L['countries'].get(country, country)}}, "speakable": speak("#definizione", "#domande-h ~ .qa h3")}, cld, faq_ld(faq)]
    page(lg, 'route:' + slug, title, desc, body, 'rotte', ld, ('site', 'calc'))

def build_routes_hub(lg):
    P = lg.P; R = lg.R
    ch, cld = crumbs(lg, [(P['nav_routes'], lg.u(lg.path_routes()))])
    west = [d[0] for d in lg.dests if not R[d[0]]['east']]; east = [d[0] for d in lg.dests if R[d[0]]['east']]
    wd = [abs(R[n]['D']) for n in west] or [0]; ed = [R[n]['D'] for n in east if R[n]['why'] != 'east-long'] or [0]
    top = max(R.values(), key=lambda r: (r['score'], r['fl'])); low = sorted(R.values(), key=lambda r: (r['score'], r['fl']))[:2]
    faq = [(lg.p('rh_q1'), lg.p('rh_a1', c=lg.cn(top['name']), D=lg.fnum(abs(top['D'])), fl=lg.fnum(top['fl']), s=top['score'], n=top['noplan'])),
           (lg.p('rh_q2'), lg.p('rh_a2', c1=lg.cn(low[0]['name']), c2=lg.cn(low[1]['name']), D1=lg.fnum(abs(low[0]['D'])), D2=lg.fnum(abs(low[1]['D'])), s1=low[0]['score'], s2=low[1]['score'])),
           (P['rh_q3'], P['rh_a3']), (P['rh_q4'], P['rh_a4'])]
    body = hero(lg, E(lg.p('rh_h1')), E(P['rh_lead']), ch, lg.p('rh_kicker'), 'Bangkok')
    body += f'''<section class="section" style="padding-top:40px" aria-labelledby="h-come-m"><div class="wrap prose"><h2 id="h-come-m">{E(P['rh_h_read'])}</h2><p>{E(lg.p('rh_p_read'))}</p>
<ul><li>{lg.p('rh_li_w', a=lg.fnum(min(wd)), b=lg.fnum(max(wd)))}</li><li>{lg.p('rh_li_e', a=lg.fnum(min(ed)), b=lg.fnum(max(ed)))}</li><li>{P['rh_li_l']}</li></ul></div></section>
<section class="section" style="padding-top:40px" aria-labelledby="h-ovest"><div class="wrap"><h2 id="h-ovest">{E(P['rh_h_w'])}</h2><p class="prose muted">{E(P['rh_p_w'])}</p><div class="grid4">{''.join(dest_card(lg, n) for n in west)}</div></div></section>
<section class="section" aria-labelledby="h-est"><div class="wrap"><h2 id="h-est">{E(P['rh_h_e'])}</h2><p class="prose muted">{E(P['rh_p_e'])}</p><div class="grid4">{''.join(dest_card(lg, n) for n in east)}</div>
<div style="margin-top:28px">{cta_band(lg)}</div></div></section>
<section class="section" id="domande" aria-labelledby="domande-h"><div class="wrap prose">{faq_html(faq, lg.p('rh_faq_h'))}</div></section>'''
    url = BASE + ALL_PAGES['routes'][lg.code]
    ld = [faq_ld(faq), {"@type": "CollectionPage", "url": url, "name": lg.p('rh_h1'), "dateModified": TODAY, "isPartOf": {"@id": BASE + lg.pre + "#sito"}, "speakable": speak("#definizione", "#domande h3"),
           "mainEntity": {"@type": "ItemList", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + ALL_PAGES['route:' + d[1]][lg.code], "name": lg.p('jl_city', c=lg.cn(d[0]))} for i, d in enumerate(lg.dests)]}}, cld]
    page(lg, 'routes', lg.p('rh_title'), lg.p('rh_desc'), body, 'rotte', ld)

def build_rank(lg):
    P = lg.P; R = lg.R
    ch, cld = crumbs(lg, [(P['nav_rank'], lg.u(lg.path_rank()))])
    rows = sorted(R.values(), key=lambda r: (-r['score'], -r['fl']))
    tr = ''
    for i, r in enumerate(rows):
        slug = DEST_BY[r['name']][1]
        bars = ''.join(f'<i class="{"on" if k < r["score"] else ""}"></i>' for k in range(10))
        tr += f'''<tr><td class="mono">{i + 1}</td><td><a href="{lg.u(lg.path_route(slug))}">{E(lg.cn(r['name']))}</a></td><td><span class="pill {'e' if r['east'] else 'w'}">{lg.sgn(r['dw'])} h · {E(P['dir_east'] if r['east'] else P['dir_west'])}</span></td><td class="mono">~{lg.fnum(r['fl'])} h</td><td class="mono">{r['noplan']} / {r['days0']}</td><td><span class="bar10" role="img" aria-label="{E(lg.f(lg.L['ui']['meter_aria'], s=r['score']))}">{bars}</span> <span class="mono">{r['score']}</span></td><td class="mono">{lg.hr(r['arr'][0])}–{lg.hr(r['arr'][1])}</td><td class="mono">{fh(r['dep'][0])}–{fh(r['dep'][1])}</td></tr>'''
    top = rows[0]; tk, bk, sy = R['Tokyo'], R['Bangkok'], R['Sydney']
    faq = [(P['k_q1'], P['k_a1']),
           (P['k_q2'], lg.p('k_a2', c1=lg.cn('Tokyo'), a1=fh(tk['dep'][0]), b1=fh(tk['dep'][1]), c2=lg.cn('Bangkok'), a2=fh(bk['dep'][0]), b2=fh(bk['dep'][1]))),
           (P['k_q3'], lg.p('k_a3', D=lg.fnum(abs(sy['D'])), T=lg.fnum(sy['T'])))]
    th = ''.join(f'<th scope="col">{E(lg.f(h))}</th>' for h in P['k_th'])
    body = hero(lg, E(lg.p('k_h1')), E(lg.p('k_lead', c=lg.cn(top['name']), D=lg.fnum(abs(top['D'])), fl=lg.fnum(top['fl']))), ch, P['k_kicker'], top['name'])
    body += f'''<section class="section" style="padding-top:40px" aria-labelledby="h-tab"><div class="wrap"><h2 id="h-tab">{E(P['k_h_tab'])}</h2>
<div class="table-wrap"><table><thead><tr>{th}</tr></thead><tbody>{tr}</tbody></table></div>
<p class="tcap">{E(lg.p('k_cap'))}</p></div></section>
<section class="section" aria-labelledby="h-met"><div class="wrap prose"><h2 id="h-met">{E(P['k_h_met'])}</h2><p>{E(P['k_p1'])}</p><p>{E(P['k_p2'])}</p><p>{E(P['k_p3'])}</p>
{faq_html(faq, P['faq_h'])}{cta_band(lg, P['k_cta'])}</div></section>'''
    url = BASE + ALL_PAGES['rank'][lg.code]
    ld = [faq_ld(faq), {"@type": "WebPage", "url": url, "name": lg.p('k_h1'), "dateModified": TODAY, "isPartOf": {"@id": BASE + lg.pre + "#sito"}, "speakable": speak("#definizione", "#domande-h ~ .qa h3"),
           "mainEntity": {"@type": "ItemList", "itemListOrder": "https://schema.org/ItemListOrderDescending", "itemListElement": [{"@type": "ListItem", "position": i + 1, "url": BASE + ALL_PAGES['route:' + DEST_BY[r['name']][1]][lg.code], "name": lg.cn(r['name'])} for i, r in enumerate(rows)]}}, cld]
    page(lg, 'rank', lg.p('k_title'), lg.p('k_desc'), body, 'classifica', ld)

def tool_ui(lg, k):
    T = lg.P['tools'][k]
    if k == 'fusi-orari':
        return f'''<div class="glass calc"><div class="two"><div class="field"><label class="lab" for="base">{E(T['l_base'])}</label><select id="base"></select></div><div class="field"><label class="lab" for="when">{E(T['l_when'])}</label><input id="when" type="datetime-local"></div></div>
<label class="lab" for="scrub" style="margin-top:16px">{E(T['l_scrub'])}</label><input class="scrub" id="scrub" type="range" min="-12" max="12" step="0.5" value="0"><span class="hint" id="scrub-l"></span>
<div class="two" style="margin-top:12px"><div class="field"><label class="lab" for="add">{E(T['l_add'])}</label><select id="add"></select></div><div style="display:flex;align-items:end"><button type="button" class="btn" id="now">{E(T['l_now'])}</button></div></div></div>
<div class="clocks" id="out" style="margin-top:16px" aria-live="polite"></div>'''
    if k == 'riunioni':
        return f'''<div class="glass calc"><div class="two"><div class="field"><label class="lab" for="day">{E(T['l_day'])}</label><input id="day" type="date"></div><div class="field"><label class="lab" for="add">{E(T['l_add'])}</label><select id="add"></select></div></div>
<p class="hint" style="margin-top:12px">{E(T['l_legend'])} <span class="pill" style="background:#2fbf8f;color:#04261b">{E(T['lg_ok'])}</span> <span class="pill">{E(T['lg_work'])}</span> <span class="pill" style="background:#ffe2c2">{E(T['lg_edge'])}</span> <span class="pill" style="background:#1b2350;color:#c9d1f2">{E(T['lg_night'])}</span></p></div>
<div class="card" style="margin-top:16px;padding:16px"><div class="mgrid" id="grid" role="grid" aria-label="{E(T['grid_aria'])}"></div><p id="best" style="margin:14px 0 6px"></p><p id="pick" class="muted" style="margin:0" aria-live="polite"></p></div>'''
    if k == 'sonno':
        return f'''<div class="glass calc"><span class="lab" id="l-mode">{E(T['l_mode'])}</span><div class="seg" id="mode" role="group" aria-labelledby="l-mode"><button type="button" data-v="wake" aria-pressed="true">{E(T['m_wake'])}<small>{E(T['m_wake_s'])}</small></button><button type="button" data-v="bed" aria-pressed="false">{E(T['m_bed'])}<small>{E(T['m_bed_s'])}</small></button><button type="button" data-v="now" aria-pressed="false">{E(T['m_now'])}<small>{E(T['m_now_s'])}</small></button></div>
<div class="field row" id="time-w"><label class="lab" for="time" id="time-l">{E(T['l_time'])}</label><input id="time" type="time" value="07:00"></div>
<p id="lead" style="margin:18px 0 0" aria-live="polite"></p><div class="sleep-out" id="out"></div><p class="hint">{E(T['hint'])}</p></div>'''
    return '<div class="big-map" id="map"></div><p class="hint mono" id="utc"></p><div class="clocks" id="out" style="margin-top:12px" aria-live="off"></div>'

def build_tools(lg):
    P = lg.P
    ch, cld = crumbs(lg, [(P['nav_tools'], lg.u(lg.path_tools()))])
    tfaq = [tuple(x) for x in P['t_hub_faq']]
    body = hero(lg, E(P['t_hub_h1']), E(P['t_hub_lead']), ch, P['t_hub_kicker'], 'Singapore')
    body += f'''<section class="section" style="padding-top:40px" aria-labelledby="h-t"><div class="wrap"><h2 id="h-t">{E(P['t_hub_h'])}</h2><div class="grid4">{''.join(tool_card(lg, k) for k in TOOL_KEYS)}</div></div></section>
<section class="section" aria-labelledby="h-cosa"><div class="wrap prose"><h2 id="h-cosa">{E(P['t_hub_h2'])}</h2><ul>{''.join(f'<li>{x}</li>' for x in P['t_hub_li'])}</ul>
{faq_html(tfaq, P['t_hub_faq_h'])}<div style="margin-top:28px">{cta_band(lg, P['t_hub_cta'])}</div></div></section>'''
    url = BASE + ALL_PAGES['tools'][lg.code]
    page(lg, 'tools', P['t_hub_title'], P['t_hub_desc'], body, 'strumenti', [{"@type": "CollectionPage", "url": url, "name": P['t_hub_h1'], "isPartOf": {"@id": BASE + lg.pre + "#sito"}, "speakable": speak("#definizione", "#domande-h ~ .qa h3")}, cld, faq_ld(tfaq)])
    for k in TOOL_KEYS:
        T = P['tools'][k]; faq = [tuple(x) for x in T['faq']]
        ch, cld = crumbs(lg, [(P['nav_tools'], lg.u(lg.path_tools())), (T['h1'], lg.u(lg.path_tool(k)))])
        body = hero(lg, E(T['h1']), E(T['lead']), ch, P['t_kicker'], 'Tokyo' if k == 'ora-nel-mondo' else 'New York')
        body += f'<section class="wrap lift" data-tool="{k}" aria-label="{E(T["h1"])}">{tool_ui(lg, k)}</section>'
        body += f'<section class="section" aria-label="{E(P["t_more_h"])}"><div class="wrap prose">' + ''.join(f'<h2>{E(h)}</h2><p>{E(p)}</p>' for h, p in T['text']) + faq_html(faq, P['faq_h']) + '</div></section>'
        body += f'<section class="section" aria-labelledby="h-alt"><div class="wrap"><h2 id="h-alt">{E(P["t_more"])}</h2><div class="grid3">{"".join(tool_card(lg, x) for x in TOOL_KEYS if x != k)}</div><div style="margin-top:28px">{cta_band(lg)}</div></div></section>'
        url = BASE + ALL_PAGES['tool:' + k][lg.code]
        ld = [{"@type": "WebApplication", "@id": url + "#app", "name": T['h1'], "url": url, "applicationCategory": "UtilitiesApplication", "operatingSystem": "Web", "isAccessibleForFree": True, "offers": {"@type": "Offer", "price": "0", "priceCurrency": "EUR"}, "author": {"@id": PERSON["@id"]}},
              {"@type": "WebPage", "url": url, "name": T['title'], "dateModified": TODAY, "isPartOf": {"@id": BASE + lg.pre + "#sito"}, "speakable": speak("#definizione")}, cld, faq_ld(faq)]
        page(lg, 'tool:' + k, T['title'], T['desc'], body, 'strumenti', ld, ('site', 'tools'))

def build_guides(lg):
    P = lg.P
    ch, cld = crumbs(lg, [(P['nav_guides'], lg.u(lg.path_guides()))])
    gfaq = [tuple(x) for x in P['g_hub_faq']]
    body = hero(lg, E(P['g_hub_h1']), E(P['g_hub_lead']), ch, P['g_hub_kicker'], 'Hong Kong')
    body += f'''<section class="section" style="padding-top:40px" aria-labelledby="h-g"><div class="wrap"><h2 id="h-g">{E(P['g_hub_h'])}</h2><div class="grid3">{''.join(guide_card(lg, i) for i in range(len(lg.G)))}</div></div></section>
<section class="section" id="domande" aria-labelledby="domande-h"><div class="wrap prose">{faq_html(gfaq, P['g_hub_faq_h'])}</div></section>'''
    url = BASE + ALL_PAGES['guides'][lg.code]
    page(lg, 'guides', P['g_hub_title'], P['g_hub_desc'], body, 'guide', [{"@type": "CollectionPage", "url": url, "name": P['g_hub_h1'], "isPartOf": {"@id": BASE + lg.pre + "#sito"}, "speakable": speak("#definizione", "#domande h3")}, cld, faq_ld(gfaq)])
    for i, g in enumerate(lg.G):
        ch, cld = crumbs(lg, [(P['nav_guides'], lg.u(lg.path_guides())), (g['h1'], lg.u(lg.path_guide(i)))])
        body = hero(lg, E(g['h1']), E(g['intro']), ch, g['kicker'], GUIDE_MAPS[i % len(GUIDE_MAPS)])
        secs = ''
        for s in g['sections']:
            secs += f"<h2>{E(s['h2'])}</h2>" + ''.join(f'<p>{E(p)}</p>' for p in s['paragraphs'])
            if s.get('list'): secs += '<ul>' + ''.join(f'<li>{E(x)}</li>' for x in s['list']) + '</ul>'
        faq = [(f['q'], f['a']) for f in g['faq']]
        body += f'''<section class="section" style="padding-top:48px" aria-label="{E(g['kicker'])}"><div class="wrap prose">{secs}<div style="margin:36px 0">{cta_band(lg)}</div>{faq_html(faq, P['faq_h'])}</div></section>
<section class="section" aria-labelledby="h-og"><div class="wrap"><h2 id="h-og">{E(P['g_more'])}</h2><div class="grid3">{''.join(guide_card(lg, j) for j in [x for x in range(len(lg.G)) if x != i][:3])}</div></div></section>'''
        url = BASE + ALL_PAGES[f'guide:{i}'][lg.code]
        ld = [{"@type": "Article", "@id": url + "#articolo", "headline": g['h1'], "description": g['description'], "datePublished": TODAY, "dateModified": TODAY, "author": {"@id": PERSON["@id"]}, "publisher": {"@id": PERSON["@id"]}, "image": BASE + "og.png", "mainEntityOfPage": url, "isPartOf": {"@id": BASE + lg.pre + "#sito"}}, cld, faq_ld(faq)]
        page(lg, f'guide:{i}', g['title'], g['description'], body, 'guide', ld)

# ---------------------------------------------------------------- avvio
if __name__ == '__main__':
    if os.path.isdir(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT)
    shutil.copytree(os.path.join(ROOT, 'src', 'assets'), os.path.join(OUT, 'assets'))
    for f in ('favicon.svg', 'og.png'): shutil.copy(os.path.join(ROOT, f), os.path.join(OUT, f))
    langs = [Lang(c) for c in LANGS]
    for lg in langs: LINFO[lg.code] = (lg.L['label'], lg.hl, lg.L['short'])
    collect_paths(langs)
    for lg in langs:
        lg.compute()
        build_home(lg)
        for d in lg.dests: build_route(lg, d)
        build_routes_hub(lg); build_rank(lg); build_tools(lg); build_guides(lg)
    sm = ''.join(f'  <url><loc>{BASE}{p}</loc><lastmod>{TODAY}</lastmod></url>\n' for p in SITEMAP)
    open(os.path.join(ROOT, 'site', 'sitemap-jet-lag.txt'), 'w').write(sm)
    for w in sorted(set(WARN)): print('ATTENZIONE', w)
    print(len(SITEMAP), 'pagine in', OUT, 'lingue', LANGS)
