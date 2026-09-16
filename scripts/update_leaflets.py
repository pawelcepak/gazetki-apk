#!/usr/bin/env python3
import html as htmlmod,json,re,urllib.request,subprocess,tempfile,os,shutil
from datetime import datetime,date,timezone
from pathlib import Path
from urllib.parse import urljoin
LEAFLETS_OUT=Path('data/leaflets.json'); PRODUCTS_OUT=Path('data/products.json'); PAGE_INDEX_OUT=Path('data/page-index.json'); OCR_VERSION=2
HEADERS={'User-Agent':'Mozilla/5.0 (Gazetki PWA updater; +https://github.com/pawelcepak/gazetki-apk)'}
MG='https://mojagazetka.com/'
KNOWN={'netto':'https://mojagazetka.com/gazetki-promocyjne/netto/netto-14-09-26-19-09-26-owkbc/1','aldi':'https://mojagazetka.com/gazetki-promocyjne/aldi/aldi-14-09-26-19-09-26-hjajv/1','lidl':'https://mojagazetka.com/gazetki-promocyjne/lidl/lidl-14-09-26-16-09-26-dsqqg/1'}
NAMES={'netto':'Netto','aldi':'ALDI','lidl':'Lidl'};TITLES={'netto':'Gazetka spożywcza','aldi':'Wybieram ALDI','lidl':'Od poniedziałku'}
OFFICIAL={'netto':'https://netto.pl/gazetka-netto/','aldi':'https://www.aldi.pl/informacje-dla-klienta/nasze-gazetki.html','lidl':'https://www.lidl.pl/c/gazetki-online/s10008614'}
def get(url,binary=False):
 req=urllib.request.Request(url,headers=HEADERS)
 with urllib.request.urlopen(req,timeout=30) as r:
  data=r.read();return data if binary else data.decode('utf-8','ignore')
def clean(raw):return htmlmod.unescape(raw).replace('\\/','/').replace('\\u0026','&')
def dates_from_slug(url):
 m=re.search(r'-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-(\d{2})-',url)
 if not m:return None
 d1,m1,y1,d2,m2,y2=map(int,m.groups());return f'20{y1:02d}-{m1:02d}-{d1:02d}',f'20{y2:02d}-{m2:02d}-{d2:02d}'
def leaflet_code(url):
 path=url.split('?')[0].rstrip('/');slug=path.split('/')[-2] if path.split('/')[-1].isdigit() else path.split('/')[-1]
 m=re.search(r'-([a-z]{5})$',slug,re.I);return m.group(1).lower() if m else None
def extract_pages(raw,store,source):
 code=leaflet_code(source);urls=re.findall(r'https://app\.moja-e-gazetka\.pl/[^"\'<> ]+/image\d+\.webp',raw,re.I);seen=[]
 for u in urls:
  u=u.replace('&amp;','&');folder=u.split('/')[-2].lower()
  if code and not folder.endswith(f'_{store}_{code}'):continue
  if u not in seen:seen.append(u)
 def num(u):
  m=re.search(r'image(\d+)\.webp',u,re.I);return int(m.group(1)) if m else 9999
 return [u for u in sorted(seen,key=num) if not re.search(r'/image00\.webp$',u,re.I)]
def discover(store):
 try:raw=clean(get(MG))
 except:return KNOWN[store]
 urls=[]
 for h in re.findall(r'href=["\']([^"\']+)["\']',raw,re.I):
  if f'/gazetki-promocyjne/{store}/' not in h.lower():continue
  u=urljoin(MG,h);dr=dates_from_slug(u)
  if dr and dr[0]<=date.today().isoformat()<=dr[1] and u not in [x[2] for x in urls]:urls.append((dr[0],dr[1],u))
 if not urls:return KNOWN[store]
 best=None
 for a,b,u in urls[:12]:
  try:
   rr=clean(get(u));score=len(extract_pages(rr,store,u))
   if best is None or score>best[0]:best=(score,u)
  except:pass
 return best[1] if best and best[0]>=4 else KNOWN[store]
def text(raw):
 s=re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>',' ',raw,flags=re.I);s=re.sub(r'<[^>]+>','\n',s);return re.sub(r'[ \t]+',' ',htmlmod.unescape(s)).replace('\r','')
def products_from_leaflet(raw,leaflet):
 t=text(raw);anchor='Wybrane promocje w gazetce';end='Kategorie produktów';block=t.split(anchor,1)[1] if anchor in t else ''
 if end in block:block=block.split(end,1)[0]
 lines=[x.strip(' *\t') for x in block.split('\n') if x.strip()];skip=('Wybraliśmy produkty','Pokaż','Image:','chevron');detail_re=re.compile(r'^(?:Cena(?::|\s)|Opakowanie:|Cena promocyjna:|\d{1,4}[,.]\d{2}\s*zł$|\d+%|Aktywuj|Przy zakupie|Cena za|Najniższa cena|Cena regularna|Taniej|SUPERCENA|\d+\+\d+)',re.I);chunks=[];cur=[]
 for line in lines:
  if any(line.startswith(x) for x in skip):continue
  if not cur:cur=[line];continue
  if detail_re.match(line):cur.append(line)
  else:chunks.append(cur);cur=[line]
 if cur:chunks.append(cur)
 out=[]
 for i,c in enumerate(chunks):
  name=c[0].strip();detail=' '.join(c[1:])
  if re.fullmatch(r'\d{1,4}[,.]\d{2}\s*zł',name,re.I):continue
  prices=[float(x.replace(',','.')) for x in re.findall(r'(\d{1,4}[,.]\d{2})\s*zł',detail,re.I)]
  if not prices:continue
  promo_match=re.search(r'Cena promocyjna:\s*(\d{1,4}[,.]\d{2})\s*zł',detail,re.I);promo=float(promo_match.group(1).replace(',','.')) if promo_match else None;final=promo if promo is not None else prices[-1]
  regular_match=re.search(r'(?:Cena regularna[^:]*:|Cena:)\s*(\d{1,4}[,.]\d{2})\s*zł',detail,re.I);regular=float(regular_match.group(1).replace(',','.')) if regular_match and float(regular_match.group(1).replace(',','.'))>final else None
  pack=re.search(r'Opakowanie:\s*(.+?)(?=\s+(?:Cena|\d+%|Przy zakupie|SUPERCENA)|$)',detail,re.I);package=pack.group(1).strip() if pack else ''
  out.append({'id':f"{leaflet['storeId']}-{leaflet['from']}-{i}",'name':name,'category':'Promocje z gazetki','storeId':leaflet['storeId'],'store':leaflet['store'],'price':final,'regularPrice':regular,'package':package,'unit':package or 'szt.','promotion':bool(promo is not None or re.search(r'TANIEJ|GRATIS|kupon|przy zakupie|SUPERCENA',detail,re.I)),'conditions':detail[:500],'validFrom':leaflet['from'],'validTo':leaflet['to'],'leafletId':leaflet['id'],'page':1,'source':'mojagazetka','sourcePage':leaflet['sourcePage']})
 return out
def adapter(store):
 source=discover(store);raw=clean(get(source));pages=extract_pages(raw,store,source);dr=dates_from_slug(source)
 if not dr:raise RuntimeError('brak dat w adresie gazetki')
 if len(pages)<2:raise RuntimeError(f'znaleziono tylko {len(pages)} stron')
 a,b=dr;leaf={'id':f'{store}-{a}-{b}','storeId':store,'store':NAMES[store],'title':TITLES[store],'from':a,'to':b,'source':'mojagazetka','sourcePage':source,'externalUrl':OFFICIAL[store],'reader':'images','pageCount':len(pages),'pages':pages};return leaf,products_from_leaflet(raw,leaf)
def load_old_index():
 try:return json.loads(PAGE_INDEX_OUT.read_text(encoding='utf-8')).get('pages',[])
 except:return []
def ocr_page(url):
 data=get(url,binary=True)
 with tempfile.NamedTemporaryFile(suffix='.webp',delete=False) as f:f.write(data);path=f.name
 try:
  texts=[]
  for psm in ('11','6'):
   p=subprocess.run(['tesseract',path,'stdout','-l','pol','--psm',psm],capture_output=True,text=True,timeout=45)
   if not p.returncode and p.stdout.strip():texts.append(p.stdout)
  return re.sub(r'\s+',' ',' '.join(texts)).strip()[:24000]
 finally:
  try:os.unlink(path)
  except:pass
def build_page_index(leaflets):
 old=load_old_index();old_by={(x.get('leafletId'),x.get('page')):x for x in old};out=[];can_ocr=bool(shutil.which('tesseract'))
 for leaf in leaflets:
  for n,url in enumerate(leaf['pages'],1):
   prev=old_by.get((leaf['id'],n))
   if prev and prev.get('imageUrl')==url and prev.get('text') and prev.get('ocrVersion')==OCR_VERSION:out.append(prev);continue
   txt=''
   if can_ocr:
    try:txt=ocr_page(url)
    except Exception as e:print(f'OCR warning {leaf["storeId"]} p{n}: {e}')
   out.append({'leafletId':leaf['id'],'storeId':leaf['storeId'],'store':leaf['store'],'page':n,'imageUrl':url,'ocrVersion':OCR_VERSION,'text':txt})
 return out
def main():
 items=[];products=[];errors=[]
 for store in ('netto','aldi','lidl'):
  try:leaf,prods=adapter(store);items.append(leaf);products.extend(prods)
  except Exception as e:errors.append(f'{store}: {type(e).__name__}: {e}')
 bad=[p for p in products if re.fullmatch(r'\d{1,4}[,.]\d{2}\s*zł',p['name'],re.I)]
 if bad:raise RuntimeError(f'niepoprawne nazwy produktów: {len(bad)}')
 page_index=build_page_index(items);now=datetime.now(timezone.utc).isoformat();payload={'schemaVersion':5,'generatedAt':now,'leaflets':items,'sourceStatus':{'automatic':['netto','aldi','lidl'],'imageReader':[x['storeId'] for x in items],'productCatalog':[x for x in ('netto','aldi','lidl') if any(p['storeId']==x for p in products)],'pageSearch':'ocr-v2' if any(x.get('text') for x in page_index) else 'unavailable','errors':errors}}
 LEAFLETS_OUT.parent.mkdir(parents=True,exist_ok=True);LEAFLETS_OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');PRODUCTS_OUT.write_text(json.dumps({'schemaVersion':4,'generatedAt':now,'demo':False,'products':products},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');PAGE_INDEX_OUT.write_text(json.dumps({'schemaVersion':2,'ocrVersion':OCR_VERSION,'generatedAt':now,'pages':page_index},ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(f'Wrote {len(items)} leaflets; pages={sum(len(x.get("pages",[])) for x in items)}; products={len(products)}; indexedPages={sum(bool(x.get("text")) for x in page_index)}; errors={len(errors)}')
if __name__=='__main__':main()
