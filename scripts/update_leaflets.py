#!/usr/bin/env python3
import json,re,urllib.request
from datetime import datetime,timezone
from pathlib import Path

OUT=Path('data/leaflets.json')
HEADERS={'User-Agent':'Mozilla/5.0 (Gazetki PWA updater; +https://github.com/pawelcepak/gazetki-apk)'}
SOURCES={
 'biedronka':'https://www.biedronka.pl/pl/artykuly-przemyslowe',
 'netto':'https://netto.pl/gazetka-netto/'
}

def get(url):
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','ignore')

def iso(d):
 day,month,year=map(int,d.split('.'));return f'{year:04d}-{month:02d}-{day:02d}'

def biedronka():
 html=get(SOURCES['biedronka'])
 text=re.sub(r'<[^>]+>',' ',html);text=re.sub(r'\s+',' ',text)
 ranges=[]
 for a,b in re.findall(r'(\d{2}\.\d{2})\s*-\s*(\d{2}\.\d{2}\.\d{4})',text):
  year=b[-4:];aa=f'{a}.{year}'
  try:r=(iso(aa),iso(b))
  except:continue
  if r not in ranges:ranges.append(r)
 return [{'id':f'biedronka-{a}-{b}','storeId':'biedronka','store':'Biedronka','title':'Okazje tygodnia','from':a,'to':b,'source':'official','externalUrl':'https://www.biedronka.pl/pl/gazetki','reader':'external'} for a,b in ranges[:12]]

def netto():
 html=get(SOURCES['netto'])
 text=re.sub(r'<[^>]+>',' ',html);text=re.sub(r'\s+',' ',text)
 ids=[]
 for x in re.findall(r'leafletid(?:=|%3D)([A-Za-z0-9_-]+)',html):
  if x not in ids:ids.append(x)
 ranges=[]
 for a,b in re.findall(r'Oferty od:\s*(\d{2}-\d{2}-\d{4})\s*do\s*(\d{2}-\d{2}-\d{4})',text,re.I):
  conv=lambda s:datetime.strptime(s,'%d-%m-%Y').strftime('%Y-%m-%d')
  r=(conv(a),conv(b))
  if r not in ranges:ranges.append(r)
 if not ranges:
  ranges=[('2026-09-14','2026-09-19')]
 out=[]
 for i,(a,b) in enumerate(ranges[:8]):
  lid=ids[i] if i<len(ids) else None
  url=f'https://netto.pl/gazetka-netto/?leafletid={lid}&page=1' if lid else SOURCES['netto']
  out.append({'id':f'netto-{lid or i}','storeId':'netto','store':'Netto','title':'Gazetka promocyjna','from':a,'to':b,'source':'official','externalUrl':url,'reader':'iframe-paged','leafletId':lid})
 return out

def main():
 items=[];errors=[]
 for name,fn in [('biedronka',biedronka),('netto',netto)]:
  try:items.extend(fn())
  except Exception as e:errors.append(f'{name}: {type(e).__name__}: {e}')
 payload={'schemaVersion':1,'generatedAt':datetime.now(timezone.utc).isoformat(),'leaflets':items,'sourceStatus':{'automatic':['biedronka','netto'],'planned':['lidl'],'errors':errors}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'Wrote {len(items)} leaflets; errors={len(errors)}')
if __name__=='__main__':main()
