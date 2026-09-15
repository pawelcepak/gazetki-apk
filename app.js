const DEFAULT_STORES = [
  { id: 'biedronka', name: 'Biedronka', enabled: true, priority: 1 },
  { id: 'lidl', name: 'Lidl', enabled: true, priority: 2 },
  { id: 'kaufland', name: 'Kaufland', enabled: true, priority: 3 },
  { id: 'action', name: 'Action', enabled: true, priority: 4 },
  { id: 'aldi', name: 'Aldi', enabled: false, priority: 5 },
  { id: 'carrefour', name: 'Carrefour', enabled: false, priority: 6 },
  { id: 'rossmann', name: 'Rossmann', enabled: false, priority: 7 },
  { id: 'pepco', name: 'Pepco', enabled: false, priority: 8 }
];

const DEMO_LEAFLETS = [
  { id: 1, storeId: 'biedronka', store: 'Biedronka', title: 'Gazetka tygodniowa', status: 'current', from: '2026-09-14', to: '2026-09-20', source: 'demo', products: ['kawa', 'masło', 'nabiał', 'napoje'] },
  { id: 2, storeId: 'lidl', store: 'Lidl', title: 'Oferta od poniedziałku', status: 'current', from: '2026-09-14', to: '2026-09-20', source: 'demo', products: ['pieczywo', 'owoce', 'kawa', 'chemia'] },
  { id: 3, storeId: 'kaufland', store: 'Kaufland', title: 'Gazetka promocyjna', status: 'current', from: '2026-09-10', to: '2026-09-16', source: 'demo', products: ['mięso', 'masło', 'warzywa'] },
  { id: 4, storeId: 'action', store: 'Action', title: 'Nowości i promocje', status: 'upcoming', from: '2026-09-16', to: '2026-09-22', source: 'demo', products: ['dom', 'dekoracje', 'chemia'] },
  { id: 5, storeId: 'aldi', store: 'Aldi', title: 'Oferta od środy', status: 'upcoming', from: '2026-09-16', to: '2026-09-20', source: 'demo', products: ['nabiał', 'kawa', 'warzywa'] }
];

const state = {
  stores: loadStores(),
  notify: localStorage.getItem('gazetki.notify') === 'true',
  selectedStores: new Set()
};

function loadStores() {
  try {
    const saved = JSON.parse(localStorage.getItem('gazetki.stores'));
    if (Array.isArray(saved) && saved.length) return saved;
  } catch (_) {}
  return structuredClone(DEFAULT_STORES);
}

function saveState() {
  localStorage.setItem('gazetki.stores', JSON.stringify(state.stores));
  localStorage.setItem('gazetki.notify', String(state.notify));
}

function initSelectedStores() {
  state.selectedStores = new Set(state.stores.filter(s => s.enabled).map(s => s.id));
}

function renderStoreChips() {
  const root = document.querySelector('#storesFilter');
  root.innerHTML = '';
  [...state.stores].sort((a,b)=>a.priority-b.priority).forEach(store => {
    const label = document.createElement('label');
    label.className = `chip ${state.selectedStores.has(store.id) ? 'active' : ''}`;
    label.innerHTML = `<input type="checkbox" ${state.selectedStores.has(store.id) ? 'checked' : ''}> <span>${store.name}</span>`;
    const checkbox = label.querySelector('input');
    checkbox.addEventListener('change', () => {
      checkbox.checked ? state.selectedStores.add(store.id) : state.selectedStores.delete(store.id);
      renderStoreChips();
      renderLeaflets();
    });
    root.appendChild(label);
  });
}

function renderSettings() {
  const root = document.querySelector('#settingsStores');
  root.innerHTML = '';
  [...state.stores].sort((a,b)=>a.priority-b.priority).forEach(store => {
    const row = document.createElement('div');
    row.className = 'store-setting';
    row.innerHTML = `
      <input type="checkbox" data-role="enabled" ${store.enabled ? 'checked' : ''}>
      <strong>${store.name}</strong>
      <select data-role="priority">
        ${state.stores.map((_,i)=>`<option value="${i+1}" ${store.priority===i+1?'selected':''}>Pozycja ${i+1}</option>`).join('')}
      </select>
    `;
    row.querySelector('[data-role=enabled]').addEventListener('change', e => store.enabled = e.target.checked);
    row.querySelector('[data-role=priority]').addEventListener('change', e => store.priority = Number(e.target.value));
    root.appendChild(row);
  });
  document.querySelector('#notifyToggle').checked = state.notify;
}

function normalizePriorities() {
  const ordered = [...state.stores].sort((a,b)=>a.priority-b.priority || a.name.localeCompare(b.name));
  ordered.forEach((store, index) => store.priority = index + 1);
}

function formatDate(iso) {
  return new Intl.DateTimeFormat('pl-PL', { day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date(`${iso}T12:00:00`));
}

function renderLeaflets() {
  const search = document.querySelector('#searchInput').value.trim().toLowerCase();
  const status = document.querySelector('#statusFilter').value;
  const sort = document.querySelector('#sortSelect').value;
  const source = document.querySelector('#sourceSelect').value;
  const priorityMap = Object.fromEntries(state.stores.map(s => [s.id, s.priority]));

  let items = DEMO_LEAFLETS.filter(item => {
    if (!state.selectedStores.has(item.storeId)) return false;
    if (status !== 'all' && item.status !== status) return false;
    if (source !== 'all' && item.source !== source) return false;
    if (search) {
      const haystack = `${item.store} ${item.title} ${item.products.join(' ')}`.toLowerCase();
      if (!haystack.includes(search)) return false;
    }
    return true;
  });

  items.sort((a,b) => {
    if (sort === 'dateAsc') return a.from.localeCompare(b.from);
    if (sort === 'dateDesc') return b.from.localeCompare(a.from);
    if (sort === 'name') return a.store.localeCompare(b.store, 'pl');
    return (priorityMap[a.storeId] ?? 999) - (priorityMap[b.storeId] ?? 999);
  });

  const root = document.querySelector('#leaflets');
  const info = document.querySelector('#resultInfo');
  info.textContent = `${items.length} wynik${items.length === 1 ? '' : items.length < 5 ? 'i' : 'ów'}`;
  root.innerHTML = '';

  if (!items.length) {
    root.innerHTML = '<div class="empty">Brak gazetek spełniających wybrane kryteria.</div>';
    return;
  }

  items.forEach(item => {
    const card = document.createElement('article');
    card.className = 'card';
    card.innerHTML = `
      <div class="card-header">
        <div>
          <div class="store">${item.store}</div>
          <div class="muted">${item.title}</div>
        </div>
        <span class="badge ${item.status}">${item.status === 'current' ? 'AKTUALNA' : 'NADCHODZĄCA'}</span>
      </div>
      <div class="meta">
        <span><strong>Od:</strong> ${formatDate(item.from)}</span>
        <span><strong>Do:</strong> ${formatDate(item.to)}</span>
        <span><strong>Przykładowe kategorie:</strong> ${item.products.join(', ')}</span>
      </div>
      <button type="button" disabled title="Po podłączeniu prawdziwego źródła danych">Otwórz gazetkę — źródło w v0.2</button>
    `;
    root.appendChild(card);
  });
}

function bindEvents() {
  ['searchInput','statusFilter','sortSelect','sourceSelect'].forEach(id => {
    document.querySelector(`#${id}`).addEventListener(id === 'searchInput' ? 'input' : 'change', renderLeaflets);
  });

  document.querySelector('#refreshBtn').addEventListener('click', renderLeaflets);
  document.querySelector('#settingsBtn').addEventListener('click', () => {
    renderSettings();
    document.querySelector('#settingsDialog').showModal();
  });
  document.querySelector('#saveSettingsBtn').addEventListener('click', event => {
    event.preventDefault();
    state.notify = document.querySelector('#notifyToggle').checked;
    normalizePriorities();
    saveState();
    initSelectedStores();
    renderStoreChips();
    renderLeaflets();
    document.querySelector('#settingsDialog').close();
  });
}

initSelectedStores();
bindEvents();
renderStoreChips();
renderLeaflets();

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('./sw.js').catch(()=>{}));
}
