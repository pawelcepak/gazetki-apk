let PAGE_INDEX=[];
const searchNorm=s=>(s||'').toLocaleLowerCase('pl').normalize('NFD').replace(/[\u0300-\u036f]/g,'').replace(/ł/g,'l');
async function loadPageIndex(){
 try{const r=await fetch('./data/page-index.json',{cache:'no-store'});if(!r.ok)throw Error(r.status);const d=await r.json();PAGE_INDEX=Array.isArray(d.pages)?d.pages:[]}
 catch{PAGE_INDEX=[]}
 enhancedRenderProducts();
}
function pageSnippet(text,q){
 const plain=(text||'').replace(/\s+/g,' ').trim(),n=searchNorm(plain),needle=searchNorm(q),i=n.indexOf(needle);
 if(i<0)return plain.slice(0,180);const a=Math.max(0,i-70),b=Math.min(plain.length,i+needle.length+110);return `${a?'…':''}${plain.slice(a,b)}${b<plain.length?'…':''}`;
}
function enhancedRenderProducts(){
 const input=document.querySelector('#productSearch');if(!input)return;
 const q=input.value.trim(),nq=searchNorm(q),sort=document.querySelector('#productSort')?.value||'priceAsc';
 let a=PRODUCTS.filter(x=>!nq||searchNorm(`${x.name} ${x.category||''} ${x.store||''} ${x.conditions||''}`).includes(nq));
 a.sort((x,y)=>sort==='priceDesc'?y.price-x.price:sort==='unitAsc'?(x.unitPrice??999)-(y.unitPrice??999):sort==='store'?x.store.localeCompare(y.store,'pl'):x.price-y.price);
 let hits=[];
 if(nq.length>=2){
  const productLeafletPages=new Set(a.map(x=>`${x.leafletId}:${x.page||1}`));
  hits=PAGE_INDEX.filter(x=>searchNorm(x.text).includes(nq)&&!productLeafletPages.has(`${x.leafletId}:${x.page}`)).slice(0,40);
 }
 const info=document.querySelector('#productInfo'),root=document.querySelector('#products');
 info.textContent=nq?`${a.length} ofert produktowych • ${hits.length} dodatkowych stron gazetki zawiera „${q}”`:`${a.length} prawdziwych ofert • pełne strony gazetek są dodatkowo indeksowane do wyszukiwania`;
 root.innerHTML='';
 a.forEach(x=>{const d=document.createElement('article');d.className='product-card';d.innerHTML=`<div class="product-store">${x.store}</div><h3>${x.name}</h3><div class="product-price">${money(x.price)}</div>${x.regularPrice?`<div class="old-price">${money(x.regularPrice)}</div>`:''}<div class="muted">${x.package||x.category||'Oferta z gazetki'}</div><div class="promo-line">${x.promotion?'PROMOCJA • ':''}do ${fmt(x.validTo)}</div>${x.conditions?`<div class="muted">${x.conditions.slice(0,160)}</div>`:''}<div class="product-actions"><button data-add>Dodaj do listy</button><button data-page class="secondary">Pokaż w gazetce</button></div>`;d.querySelector('[data-add]').onclick=()=>addToCart(x.id);d.querySelector('[data-page]').onclick=()=>showProductLeaflet(x);root.appendChild(d)});
 hits.forEach(h=>{const leaf=LEAFLETS.find(x=>x.id===h.leafletId)||LEAFLETS.find(x=>x.storeId===h.storeId);if(!leaf)return;const d=document.createElement('article');d.className='product-card';d.innerHTML=`<div class="product-store">${h.store}</div><h3>Znaleziono w gazetce — strona ${h.page}</h3><div class="muted">${pageSnippet(h.text,q)}</div><div class="promo-line">PEŁNY INDEKS STRONY • OCR</div><div class="product-actions"><button data-page>Pokaż stronę ${h.page}</button></div>`;d.querySelector('[data-page]').onclick=()=>openViewer(leaf,h.page);root.appendChild(d)});
 if(nq&&!a.length&&!hits.length)root.innerHTML='<div class="empty">Nie znaleziono tego tekstu ani w katalogu produktów, ani na zindeksowanych stronach aktualnych gazetek.</div>';
}
const productSearch=document.querySelector('#productSearch'),productSort=document.querySelector('#productSort');
if(productSearch)productSearch.oninput=enhancedRenderProducts;if(productSort)productSort.onchange=enhancedRenderProducts;
loadPageIndex();
