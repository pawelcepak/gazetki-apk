const DEFAULT_STORES = [
  { id:'biedronka', name:'Biedronka', enabled:true, priority:1 },
  { id:'lidl', name:'Lidl', enabled:true, priority:2 },
  { id:'kaufland', name:'Kaufland', enabled:true, priority:3 },
  { id:'action', name:'Action', enabled:true, priority:4 },
  { id:'aldi', name:'Aldi', enabled:false, priority:5 },
  { id:'carrefour', name:'Carrefour', enabled:false, priority:6 },
  { id:'rossmann', name:'Rossmann', enabled:false, priority:7 },
  { id:'pepco', name:'Pepco', enabled:false, priority:8 }
];

// v0.2: oficjalne punkty wejścia. GitHub Pages nie może niezawodnie scrapować
// obcych serwisów z przeglądarki (CORS), dlatego dane są oddzielone od UI.
const STORE_SOURCES = {
  biedronka:'https://www.biedronka.pl/pl/gazetki',
  lidl:'https://www.lidl.pl/c/gazetki-online/s10008614',
  kaufland:'https://sklep.kaufland.pl/gazetka.html',
  action:'https://www.action.com/pl-pl/gazetka-action/',
  aldi:'https://www.aldi.pl/informacje-dla-klienta/nasze-gazetki.html',
  carrefour:'https://www.carrefour.pl/gazetka-promocyjna',
  rossmann:'https://www.rossmann.pl/gazetka',
  pepco:'https://pepco.pl/gazetka-promocyjna/'
};

const LEAFLETS = [
  {id:'b1',storeId:'biedronka',store:'Biedronka',title:'Okazje tygodnia',from:'2026-09-10',to:'2026-09-23',source:'official'},
  {id:'b2',storeId:'biedronka',store:'Biedronka',title:'Nadchodzące okazje tygodnia',from:'2026-09-17',to:'2026-09-30',source:'official'},
  {id:'k1',storeId:'kaufland',store:'Kaufland',title:'Gazetka reklamowa',from:'2026-09-10',to:'2026-09-16',source:'official'},
  {id:'a1',storeId:'action',store:'Action',title:'Promocja Tygodnia',from:'2026-09-09',to:'2026-09-15',source:'official'},
  {id:'l1',storeId:'lidl',store:'Lidl',title:'Gazetki online',from:'2026-09-14',to:'2026-09-20',source:'official'},
  {id:'aldi1',storeId:'aldi',store:'Aldi',title:'Najnowsze gazetki',from:'2026-09-14',to:'2026-09-20',source:'official'},
  {id:'c1',storeId:'carrefour',store:'Carrefour',title:'Gazetka promocyjna',from:'2026-09-14',to:'2026-09-20',source:'official'},
  {id:'r1',storeId:'rossmann',store:'Rossmann',title:'Aktualna oferta i gazetka',from:'2026-09-14',to:'2026-09-20',source:'official'},
  {id:'p1',storeId:'pepco',store:'Pepco',title:'Gazetka promocyjna',from:'2026-09-14',to:'2026-09-20',source:'official'}
];

const state={stores:loadStores(),notify:localStorage.getItem('gazetki.notify')==='true',selectedStores:new Set()};
function loadStores(){try{const saved=JSON.parse(localStorage.getItem('gazetki.stores'));if(Array.isArray(saved)&&saved.length){const map=new Map(saved.map(x=>[x.id,x]));return DEFAULT_STORES.map(x=>({...x,...map.get(x.id)}));}}catch(_){}return structuredClone(DEFAULT_STORES)}
function saveState(){localStorage.setItem('gazetki.stores',JSON.stringify(state.stores));localStorage.setItem('gazetki.notify',String(state.notify))}
function initSelectedStores(){state.selectedStores=new Set(state.stores.filter(s=>s.enabled).map(s=>s.id))}
function todayISO(){return new Date().toLocaleDateString('sv-SE')}
function leafletStatus(item){const t=todayISO();if(item.from>t)return'upcoming';if(item.to>=t)return'current';return'expired'}
function renderStoreChips(){const root=document.querySelector('#storesFilter');root.innerHTML='';[...state.stores].sort((a,b)=>a.priority-b.priority).forEach(store=>{const label=document.createElement('label');label.className=`chip ${state.selectedStores.has(store.id)?'active':''}`;label.innerHTML=`<input type="checkbox" ${state.selectedStores.has(store.id)?'checked':''}> <span>${store.name}</span>`;const cb=label.querySelector('input');cb.addEventListener('change',()=>{cb.checked?state.selectedStores.add(store.id):state.selectedStores.delete(store.id);renderStoreChips();renderLeaflets()});root.appendChild(label)})}
function renderSettings(){const root=document.querySelector('#settingsStores');root.innerHTML='';[...state.stores].sort((a,b)=>a.priority-b.priority).forEach(store=>{const row=document.createElement('div');row.className='store-setting';row.innerHTML=`<input type="checkbox" data-role="enabled" ${store.enabled?'checked':''}><strong>${store.name}</strong><select data-role="priority">${state.stores.map((_,i)=>`<option value="${i+1}" ${store.priority===i+1?'selected':''}>Pozycja ${i+1}</option>`).join('')}</select>`;row.querySelector('[data-role=enabled]').addEventListener('change',e=>store.enabled=e.target.checked);row.querySelector('[data-role=priority]').addEventListener('change',e=>store.priority=Number(e.target.value));root.appendChild(row)});document.querySelector('#notifyToggle').checked=state.notify}
function normalizePriorities(){[...state.stores].sort((a,b)=>a.priority-b.priority||a.name.localeCompare(b.name)).forEach((s,i)=>s.priority=i+1)}
function formatDate(iso){return new Intl.DateTimeFormat('pl-PL',{day:'2-digit',month:'2-digit',year:'numeric'}).format(new Date(`${iso}T12:00:00`))}
function renderLeaflets(){const search=document.querySelector('#searchInput').value.trim().toLowerCase();const status=document.querySelector('#statusFilter').value;const sort=document.querySelector('#sortSelect').value;const priority=Object.fromEntries(state.stores.map(s=>[s.id,s.priority]));let items=LEAFLETS.map(x=>({...x,status:leafletStatus(x)})).filter(x=>x.status!=='expired'&&state.selectedStores.has(x.storeId)&&(status==='all'||x.status===status)&&(!search||`${x.store} ${x.title}`.toLowerCase().includes(search)));items.sort((a,b)=>sort==='dateAsc'?a.from.localeCompare(b.from):sort==='dateDesc'?b.from.localeCompare(a.from):sort==='name'?a.store.localeCompare(b.store,'pl'):(priority[a.storeId]??999)-(priority[b.storeId]??999));document.querySelector('#resultInfo').textContent=`${items.length} aktywnych/nadchodzących gazetek • dane v0.2`;const root=document.querySelector('#leaflets');root.innerHTML='';if(!items.length){root.innerHTML='<div class="empty">Brak gazetek spełniających wybrane kryteria.</div>';return}items.forEach(item=>{const card=document.createElement('article');card.className='card';card.innerHTML=`<div class="card-header"><div><div class="store">${item.store}</div><div class="muted">${item.title}</div></div><span class="badge ${item.status}">${item.status==='current'?'AKTUALNA':'NADCHODZĄCA'}</span></div><div class="meta"><span><strong>Od:</strong> ${formatDate(item.from)}</span><span><strong>Do:</strong> ${formatDate(item.to)}</span><span><strong>Źródło:</strong> oficjalna strona ${item.store}</span></div><a class="button-link" href="${STORE_SOURCES[item.storeId]}" target="_blank" rel="noopener noreferrer">Otwórz gazetkę ↗</a>`;root.appendChild(card)})}
function bindEvents(){['searchInput','statusFilter','sortSelect','sourceSelect'].forEach(id=>document.querySelector(`#${id}`).addEventListener(id==='searchInput'?'input':'change',renderLeaflets));document.querySelector('#refreshBtn').addEventListener('click',renderLeaflets);document.querySelector('#settingsBtn').addEventListener('click',()=>{renderSettings();document.querySelector('#settingsDialog').showModal()});document.querySelector('#saveSettingsBtn').addEventListener('click',e=>{e.preventDefault();state.notify=document.querySelector('#notifyToggle').checked;normalizePriorities();saveState();initSelectedStores();renderStoreChips();renderLeaflets();document.querySelector('#settingsDialog').close()})}
initSelectedStores();bindEvents();renderStoreChips();renderLeaflets();if('serviceWorker'in navigator)window.addEventListener('load',()=>navigator.serviceWorker.register('./sw.js').catch(()=>{}));