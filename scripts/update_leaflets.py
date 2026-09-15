#!/usr/bin/env python3
import html as htmlmod,json,re,urllib.request
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.parse import urljoin
OUT=Path('data/leaflets.json')
HEADERS={'User-Agent':'Mozilla/5.0 (Gazetki PWA updater; +https://github.com/pawelcepak/gazetki-apk)'}
MG='https://mojagazetka.com/'
KNOWN={
 'netto':'https://mojagazetka.com/gazetki-promocyjne/netto/netto-14-09-26-19-09-26-owkbc/1',
 'aldi':'https://mojagazetka.com/gazetki-promocyjne/aldi/aldi-14-09-26-19-09-26-hjajv/1',
 'lidl':'https://mojagazetka.com/gazetki-promocyjne/lidl/lidl-14-09-26-16-09-26-dsqqg/1'
}
NAMES={'netto':'Netto','aldi':'ALDI','lidl':'Lidl'}
TITLES={'netto':'Gazetka spożywcza','aldi':'Wybieram ALDI','lidl':'Od poniedziałku'}
OFFICIAL={'netto':'https://netto.pl/gazetka-netto/','aldi':'https://www.aldi.pl/informacje-dla-klienta/nasze-gazetki.html','lidl':'https://www.lidl.pl/c/gazetki-online/s10008614'}
def get(url):
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=30) as r:return r.read().decode('utf-8','ignore')
def clean(raw):return htmlmod.unescape(raw).replace('\\/','/').replace('\\u0026','&')
def dates_from_slug(url):
 m=re.search(r'-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-',url)
 if not m:return None
 d1,m1,y1,d2,m2,y2=map(int,m.groups());return f'20{y1:02d}-{m1:02d}-{d1:02d}',f'20{y2:02d}-{m2:02d}-{d2:02d}'
def discover(store):
 try:raw=clean(get(MG))
 except:return KNOWN[store]
 urls=[]
 for h in re.findall(r'href=["\']([^"\']+)["\']',raw,re.I):
  if f'/gazetki-promocyjne/{store}/' not in h.lower():continue
  u=urljoin(MG,h);dr=dates_from_slug(u)
  if not dr:continue
  a,b=dr
  if a<=date.today().isoformat()<=b:urls.append((a,b,u))
 if not urls:return KNOWN[store]
 # Prefer the broadest currently valid main weekly leaflet; detailed validation below.
 urls.sort(key=lambda x:(x[1],x[0]),reverse=True)
 best=None
 for a,b,u in urls[:8]:
  try:
   raw=clean(get(u));pages=extract_pages(raw)
   score=len(pages)
   if best is None or score>best[0]:best=(score,u)
  except:pass
 return best[1] if best and best[0]>=4 else KNOWN[store]
def extract_pages(raw):
 urls=re.findall(r'https://app\.moja-e-gazetka\.pl/[^"\'<> ]+/image\d+\.webp',raw,re.I)
 seen=[]
 for u in urls:
  u=u.replace('&amp;','&')
  if u not in seen:seen.append(u)
 def num(u):
  m=re.search(r'image(\d+)\.webp',u,re.I);return int(m.group(1)) if m else 9999
 return sorted(seen,key=num)
def adapter(store):
 source=discover(store);raw=clean(get(source));pages=extract_pages(raw);dr=dates_from_slug(source)
 if not dr:raise RuntimeError('brak dat w adresie gazetki')
 if len(pages)<2:raise RuntimeError(f'znaleziono tylko {len(pages)} stron')
 a,b=dr
 return {'id':f'{store}-{a}-{b}','storeId':store,'store':NAMES[store],'title':TITLES[store],'from':a,'to':b,'source':'mojagazetka','sourcePage':source,'externalUrl':OFFICIAL[store],'reader':'images','pageCount':len(pages),'pages':pages}
def main():
 items=[];errors=[]
 for store in ('netto','aldi','lidl'):
  try:items.append(adapter(store))
  except Exception as e:errors.append(f'{store}: {type(e).__name__}: {e}')
 payload={'schemaVersion':3,'generatedAt':datetime.now(timezone.utc).isoformat(),'leaflets':items,'sourceStatus':{'automatic':['netto','aldi','lidl'],'imageReader':['netto','aldi','lidl'],'errors':errors}}
 OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(f'Wrote {len(items)} leaflets; pages={sum(len(x.get("pages",[])) for x in items)}; errors={len(errors)}')
if __name__=='__main__':main()
