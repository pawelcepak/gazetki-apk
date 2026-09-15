#!/usr/bin/env python3
import html as htmlmod,json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path
OUT=Path('data/leaflets.json')
HEADERS={'User-Agent':'Mozilla/5.0 (Gazetki PWA updater; +https://github.com/pawelcepak/gazetki-apk)'}
BIEDRONKA='https://www.biedronka.pl/pl/artykuly-przemyslowe'; NETTO='https://netto.pl/gazetka-netto/'
def get(url):
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=25) as r:return r.read().decode('utf-8','ignore')
def iso(d):
 day,month,year=map(int,d.split('.'));return f'{year:04d}-{month:02d}-{day:02d}'
def biedronka():
 raw=get(BIEDRONKA); text=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',raw)); ranges=[]
 for a,b in re.findall(r'(\d{2}\.\d{2})\s*-\s*(\d{2}\.\d{2}\.\d{4})',text):
  try:r=(iso(a+'.'+b[-4:]),iso(b))
  except:continue
  if r not in ranges:ranges.append(r)
 return [{'id':f'biedronka-{a}-{b}','storeId':'biedronka','store':'Biedronka','title':'Okazje tygodnia','from':a,'to':b,'source':'official','externalUrl':'https://www.biedronka.pl/pl/gazetki','reader':'external'} for a,b in ranges[:12]]
def tjek_page(raw,n):
 raw=htmlmod.unescape(raw).replace('\\u0026','&').replace('\\/','/')
 urls=re.findall(r'https://image-transformer-api\.tjek\.com/[^"\'<> ]+',raw)
 for u in urls:
  if re.search(r'(?:%2F|/)p-'+str(n)+r'\.webp',u,re.I): return u
 return None
def netto_pages(leaflet_id,max_pages=40):
 pages=[]; misses=0
 for n in range(1,max_pages+1):
  try:raw=get(f'{NETTO}?leafletid={leaflet_id}&page={n}')
  except Exception:break
  u=tjek_page(raw,n)
  if u: pages.append(u);misses=0
  else:
   misses+=1
   if n>1 and misses>=2:break
 return pages
def netto():
 raw=get(NETTO); ids=[]
 for x in re.findall(r'leafletid(?:=|%3D)([A-Za-z0-9_-]+)',raw):
  if x not in ids:ids.append(x)
 text=re.sub(r'\s+',' ',re.sub(r'<[^>]+>',' ',raw)); ranges=[]
 for a,b in re.findall(r'Oferty od:\s*(\d{2}-\d{2}-\d{4})\s*do\s*(\d{2}-\d{2}-\d{4})',text,re.I):
  cv=lambda s:datetime.strptime(s,'%d-%m-%Y').strftime('%Y-%m-%d');r=(cv(a),cv(b))
  if r not in ranges:ranges.append(r)
 if not ranges:ranges=[(datetime.now().strftime('%Y-%m-%d'),datetime.now().strftime('%Y-%m-%d'))]
 out=[]
 for i,(a,b) in enumerate(ranges[:4]):
  lid=ids[i] if i<len(ids) else None; url=f'{NETTO}?leafletid={lid}&page=1' if lid else NETTO; pages=netto_pages(lid) if lid else []
  out.append({'id':f'netto-{lid or i}','storeId':'netto','store':'Netto','title':'Gazetka promocyjna','from':a,'to':b,'source':'official','externalUrl':url,'reader':'images' if pages else 'iframe-paged','leafletId':lid,'pages':pages})
 return out
def main():
 items=[];errors=[]
 for name,fn in [('biedronka',biedronka),('netto',netto)]:
  try:items.extend(fn())
  except Exception as e:errors.append(f'{name}: {type(e).__name__}: {e}')
 payload={'schemaVersion':2,'generatedAt':datetime.now(timezone.utc).isoformat(),'leaflets':items,'sourceStatus':{'automatic':['biedronka','netto'],'imageReader':['netto'],'plannedImageReader':['biedronka','lidl'],'errors':errors}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'Wrote {len(items)} leaflets; image pages={sum(len(x.get("pages",[])) for x in items)}; errors={len(errors)}')
if __name__=='__main__':main()
