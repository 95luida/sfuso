"""Mappa del mondo a punti (proiezione equirettangolare) da world-atlas land-110m → src/assets/map.svg"""
import json, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, LATMAX, LATMIN = 1000, 84, -58
H = round(W * (LATMAX - LATMIN) / 360, 1)
STEP = 6.6

topo = json.load(open(os.path.join(ROOT, 'vendor/land-110m.json')))
sx, sy = topo['transform']['scale']; tx, ty = topo['transform']['translate']
arcs = []
for arc in topo['arcs']:
    x = y = 0; pts = []
    for dx, dy in arc:
        x += dx; y += dy
        pts.append((x * sx + tx, y * sy + ty))
    arcs.append(pts)

def ring(idx):
    pts = []
    for i in idx:
        a = arcs[i] if i >= 0 else arcs[~i][::-1]
        pts.extend(a if not pts else a[1:])
    return pts

polys = []
for g in topo['objects']['land']['geometries']:
    rings = g['arcs'] if g['type'] == 'Polygon' else [r for p in g['arcs'] for r in p]
    if g['type'] == 'Polygon': polys.append([ring(r) for r in rings])
    else:
        for p in g['arcs']: polys.append([ring(r) for r in p])

# bounding box per poligono, per andare veloci
polys = [p for p in polys if max(q[1] for q in p[0]) > -59]  # niente Antartide
# i poligoni che attraversano l'antimeridiano (Siberia, Fiji): longitudini dell'estremo est spostate oltre 180
def unwrap(p):
    if max(q[0] for q in p[0]) - min(q[0] for q in p[0]) < 300: return p
    return [[(x + 360 if x < -100 else x, y) for x, y in r] for r in p]
polys = [unwrap(p) for p in polys]
boxes = []
for p in polys:
    xs = [q[0] for q in p[0]]; ys = [q[1] for q in p[0]]
    boxes.append((min(xs), max(xs), min(ys), max(ys)))

def inside(lon, lat):
    for p, (x0, x1, y0, y1) in zip(polys, boxes):
        if not (x0 <= lon <= x1 and y0 <= lat <= y1): continue
        c = False
        for r in p:
            j = len(r) - 1
            for i in range(len(r)):
                xi, yi = r[i]; xj, yj = r[j]
                if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi: c = not c
                j = i
        if c: return True
    return False

d = []
y = STEP / 2; row = 0
while y < H:
    lat = LATMAX - y / H * (LATMAX - LATMIN)
    x = STEP / 2 + (STEP / 2 if row % 2 else 0)
    while x < W:
        lon = x / W * 360 - 180
        if inside(lon + 1e-6, lat + 1.3e-6) or (lon < -100 and inside(lon + 360 + 1e-6, lat + 1.3e-6)): d.append(f'M{x:.1f} {y:.1f}h0')
        x += STEP
    y += STEP * 0.87; row += 1

svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}">'
       f'<path d="{"".join(d)}" stroke="#9fb6d9" stroke-width="3.4" stroke-linecap="round" fill="none"/></svg>')
open(os.path.join(ROOT, 'src/assets/map.svg'), 'w').write(svg)
print(len(d), 'punti', len(svg)//1024, 'KB', 'H', H)
