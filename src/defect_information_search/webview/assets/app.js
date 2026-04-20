const state = {
  bootstrap: null,
  products: [],
  currentPart: null,
  currentSearchResult: null,
  currentMachine: '全て',
  tableQuery: '',
  detailColumns: [],
};

const DETAIL_NUMERIC_COLUMNS = new Set([
  '時間',
  '数量',
  '総不具合数',
  '外観キズ',
  '圧痕',
  '切粉',
  '毟れ',
  '穴大',
  '穴小',
  '穴キズ',
  'バリ',
  '短寸',
  '面粗',
  'サビ',
  'ボケ',
  '挽目',
  '汚れ',
  'メッキ',
  '落下',
  'フクレ',
  'ツブレ',
  'ボッチ',
  '段差',
  'バレル石',
  '径プラス',
  '径マイナス',
  'ゲージ',
  '異物混入',
  '形状不良',
  'こすれ',
  '変色シミ',
  '材料キズ',
  'ゴミ',
  'その他',
]);

const elements = {};
let domReady = false;
let backendReady = false;
let started = false;

function $(id) {
  return document.getElementById(id);
}

function bindElements() {
  [
    'app-title',
    'close-btn',
    'keyword',
    'part-name',
    'customer',
    'search-from',
    'search-to',
    'search-btn',
    'product-count',
    'product-body',
    'export-from',
    'export-to',
    'export-all-btn',
    'export-aggregate-btn',
    'export-disposal-btn',
    'quantity-value',
    'defect-count-value',
    'defect-rate-value',
    'machine-select',
    'defect-grid',
    'detail-count',
    'filter-state',
    'table-search',
    'clear-search-btn',
    'export-current-btn',
    'detail-colgroup',
    'detail-head',
    'detail-body',
    'overlay',
    'overlay-title',
    'overlay-message',
    'dialog',
    'dialog-title',
    'dialog-message',
    'dialog-actions',
    'toast',
  ].forEach((id) => {
    elements[id] = $(id);
  });
}

function showOverlay(title, message) {
  elements['overlay-title'].textContent = title;
  elements['overlay-message'].textContent = message;
  elements['overlay'].classList.remove('hidden');
}

function hideOverlay() {
  elements['overlay'].classList.add('hidden');
}

function hideDialog() {
  elements['dialog'].classList.add('hidden');
  elements['dialog-actions'].replaceChildren();
}

function showDialog(title, message, actions) {
  elements['dialog-title'].textContent = title;
  elements['dialog-message'].textContent = message;
  elements['dialog-actions'].replaceChildren();
  actions.forEach((action) => {
    const button = document.createElement('button');
    button.className = `button ${action.className || 'button-secondary'}`;
    button.type = 'button';
    button.textContent = action.label;
    button.addEventListener('click', async () => {
      hideDialog();
      await action.onClick?.();
    });
    elements['dialog-actions'].appendChild(button);
  });
  elements['dialog'].classList.remove('hidden');
}

function confirmDialog(title, message) {
  return new Promise((resolve) => {
    showDialog(title, message, [
      { label: 'キャンセル', className: 'button-secondary', onClick: () => resolve(false) },
      { label: '実行', className: 'button-primary', onClick: () => resolve(true) },
    ]);
  });
}

function infoDialog(title, message) {
  return new Promise((resolve) => {
    showDialog(title, message, [
      { label: 'OK', className: 'button-primary', onClick: () => resolve(true) },
    ]);
  });
}

function errorDialog(message) {
  return infoDialog('エラー', message);
}

function toast(message) {
  elements['toast'].textContent = message;
  elements['toast'].classList.remove('hidden');
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => {
    elements['toast'].classList.add('hidden');
  }, 2600);
}

function nextPaint() {
  return new Promise((resolve) => requestAnimationFrame(() => resolve()));
}

function setBusy(isBusy, title = '処理中', message = 'しばらくお待ちください。') {
  if (isBusy) {
    showOverlay(title, message);
  } else {
    hideOverlay();
  }
}

async function callApi(name, ...args) {
  const fn = window.pywebview?.api?.[name];
  if (!fn) {
    throw new Error('Backend API is not ready.');
  }
  return await fn(...args);
}

function escapeText(value) {
  return value == null ? '' : String(value);
}

function renderProducts(products) {
  state.products = products;
  elements['product-count'].textContent = `${products.length}件`;
  const body = elements['product-body'];
  body.replaceChildren();

  products.forEach((product) => {
    const row = document.createElement('tr');
    row.dataset.partNumber = escapeText(product['品番'] ?? product['part_number']);
    row.innerHTML = `
      <td>${escapeText(product['品番'] ?? product['part_number'])}</td>
      <td>${escapeText(product['品名'] ?? product['part_name'])}</td>
      <td>${escapeText(product['客先'] ?? product['customer'])}</td>
    `;
    row.addEventListener('click', (event) => handleProductRowClick(event, row, product));
    body.appendChild(row);
  });
}

async function handleProductRowClick(event, row, product) {
  const partNumber = escapeText(product['品番'] ?? product['part_number']);

  await selectProductFromRow(row, product, false);

  if (event.detail >= 2) {
    await loadProductDetails(partNumber, true);
    return;
  }
}

async function selectProductFromRow(row, product, loadDetails = true) {
  [...elements['product-body'].querySelectorAll('tr')].forEach((el) => el.classList.remove('selected'));
  row.classList.add('selected');
  const partNumber = escapeText(product['品番'] ?? product['part_number']);
  const partName = escapeText(product['品名'] ?? product['part_name']);
  const customer = escapeText(product['客先'] ?? product['customer']);
  elements['keyword'].value = partNumber;
  elements['part-name'].value = partName;
  elements['customer'].value = customer;
  if (loadDetails) {
    await loadProductDetails(partNumber, false);
  }
}

function renderBootstrap(bootstrap) {
  state.bootstrap = bootstrap;
  state.detailColumns = bootstrap.detail_columns || [];
  elements['app-title'].textContent = bootstrap.app_name || '不具合情報検索';
  elements['search-from'].value = bootstrap.default_search_from;
  elements['search-to'].value = bootstrap.default_search_to;
  elements['export-from'].value = bootstrap.default_search_from;
  elements['export-to'].value = bootstrap.default_search_to;
  renderDefectGrid(bootstrap.defect_fields || []);
  renderDetailHead(state.detailColumns);
}

function renderDefectGrid(labels) {
  const grid = elements['defect-grid'];
  grid.replaceChildren();
  labels.forEach((label) => {
    const chip = document.createElement('div');
    chip.className = 'defect-chip';
    chip.dataset.label = label;
    chip.innerHTML = `<label>${label}</label><strong>0</strong>`;
    grid.appendChild(chip);
  });
}

function renderDetailHead(columns) {
  const head = elements['detail-head'];
  head.replaceChildren();
  columns.forEach((column) => {
    const th = document.createElement('th');
    th.textContent = column;
    head.appendChild(th);
  });
}

function normalizeCell(value) {
  if (value === null || value === undefined) {
    return '';
  }
  return String(value);
}

function getCurrentRows() {
  const result = state.currentSearchResult;
  if (!result) {
    return [];
  }
  const query = state.tableQuery.trim().toLowerCase();
  const rows = result.details?.rows || [];
  if (!query) {
    return rows;
  }
  return rows.filter((row) => Object.values(row).some((value) => normalizeCell(value).toLowerCase().includes(query)));
}

function renderSummary(summary) {
  elements['quantity-value'].textContent = formatInteger(summary?.quantity ?? 0);
  elements['defect-count-value'].textContent = formatInteger(summary?.defect_count ?? 0);
  elements['defect-rate-value'].textContent = formatPercent(summary?.defect_rate);

  document.querySelectorAll('.defect-chip').forEach((chip) => {
    const label = chip.dataset.label;
    const value = summary?.[label] ?? 0;
    chip.querySelector('strong').textContent = formatInteger(value);
  });
}

function renderMachines(machines, selected = '全て') {
  const select = elements['machine-select'];
  select.replaceChildren();
  machines.forEach((machine) => {
    const option = document.createElement('option');
    option.value = machine;
    option.textContent = machine;
    select.appendChild(option);
  });
  const desired = machines.includes(selected) ? selected : '全て';
  select.value = desired;
  state.currentMachine = desired;
}

function renderDetails(detailsPayload) {
  const body = elements['detail-body'];
  body.replaceChildren();
  const rows = detailsPayload?.rows || [];
  elements['detail-count'].textContent = `${rows.length}件`;
  rows.forEach((row) => {
    const tr = document.createElement('tr');
    tr.innerHTML = (detailsPayload.columns || state.detailColumns)
      .map((column) => `<td class="${getDetailCellClass(column)}">${formatDetailCell(column, row[column])}</td>`)
      .join('');
    body.appendChild(tr);
  });
}

function renderDetailColgroup(columns) {
  const colgroup = elements['detail-colgroup'];
  if (!colgroup) {
    return;
  }
  colgroup.replaceChildren();
  const widths = {
    '生産ロットID': 112,
    '品番': 100,
    '指示日': 92,
    '号機': 86,
    '検査者1': 92,
    '検査者2': 92,
    '検査者3': 92,
    '検査者4': 92,
    '検査者5': 92,
    '時間': 72,
    '数量': 72,
    '総不具合数': 88,
    '不良率': 68,
    'その他内容': 160,
    '数値検査員': 132,
  };
  columns.forEach((column) => {
    const col = document.createElement('col');
    col.style.width = `${widths[column] || 72}px`;
    colgroup.appendChild(col);
  });
}

function renderSearchResult(result, selectedMachine = '全て') {
  state.currentSearchResult = result;
  state.detailColumns = result.details?.columns || state.detailColumns;
  renderDetailColgroup(state.detailColumns);
  renderDetailHead(state.detailColumns);
  renderMachines(result.machines || ['全て'], selectedMachine);
  renderSummary(result.summary || {});
  renderDetails(result.details || { columns: [], rows: [] });
  updateFilterState(selectedMachine);
}

function updateFilterState(selectedMachine = state.currentMachine) {
  const keywordLabel = state.currentPart ? `検索条件: ${state.currentPart}` : '検索条件: なし';
  const machineLabel = selectedMachine && selectedMachine !== '全て' ? ` / 号機: ${selectedMachine}` : '';
  elements['filter-state'].textContent = `${keywordLabel}${machineLabel}`;
}

function formatInteger(value) {
  if (value === null || value === undefined || value === '') {
    return '';
  }
  const num = Number(value);
  return Number.isFinite(num) ? num.toLocaleString('ja-JP') : escapeText(value);
}

function formatPercent(value) {
  if (value === null || value === undefined || value === '') {
    return '0.00%';
  }
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return '0.00%';
  }
  return `${(num * 100).toFixed(2)}%`;
}

function formatDetailCell(column, value) {
  if (column === '不良率') {
    return formatDetailPercent(value);
  }
  if (DETAIL_NUMERIC_COLUMNS.has(column)) {
    return formatInteger(value);
  }
  return escapeText(value);
}

function formatDetailPercent(value) {
  if (value === null || value === undefined || value === '') {
    return '0.0%';
  }
  const num = Number(value);
  if (!Number.isFinite(num)) {
    return escapeText(value);
  }
  return `${(num * 100).toFixed(1)}%`;
}

function getDetailCellClass(column) {
  if (column === '不良率') {
    return 'cell-number cell-rate';
  }
  if (DETAIL_NUMERIC_COLUMNS.has(column)) {
    return 'cell-number';
  }
  return 'cell-text';
}

async function searchProducts() {
  const keyword = elements['keyword'].value.trim();
  if (!keyword) {
    await errorDialog(state.bootstrap?.messages?.empty_keyword || '品番を入力してください。');
    return;
  }

  setBusy(true, '検索中', '品番候補を検索しています。');
  try {
    await nextPaint();
    const response = await callApi('search_products', keyword);
    if (!response.ok) {
      await errorDialog(response.error || '検索に失敗しました。');
      return;
    }

    const products = response.products?.rows || [];
    if (products.length === 0) {
      renderProducts([]);
      state.currentPart = null;
      elements['part-name'].value = '';
      elements['customer'].value = '';
      state.currentSearchResult = null;
      renderSummary({});
      renderDetails({ columns: state.detailColumns, rows: [] });
      elements['detail-count'].textContent = '0件';
      await infoDialog('検索結果', state.bootstrap?.messages?.no_products || '該当する品番はありません。');
      return;
    }

    renderProducts(products);
    if (products.length === 1) {
      const row = elements['product-body'].querySelector('tr');
      await selectProductFromRow(row, products[0]);
    } else {
      state.currentPart = null;
      elements['part-name'].value = '';
      elements['customer'].value = '';
      state.currentSearchResult = null;
      renderSummary({});
      renderDetails({ columns: state.detailColumns, rows: [] });
      elements['detail-count'].textContent = '0件';
      updateFilterState();
      toast('候補一覧から品番を選択してください。');
    }
  } catch (error) {
    await errorDialog(error?.message || String(error));
  } finally {
    setBusy(false);
  }
}

async function loadProductDetails(partNumber, showBusy = true) {
  const from = elements['search-from'].value;
  const to = elements['search-to'].value;
  if (!from || !to) {
    await errorDialog('日付を指定してください。');
    return;
  }
  if (showBusy) {
    setBusy(true, '読み込み中', '不具合情報を取得しています。');
  }
  try {
    if (showBusy) {
      await nextPaint();
    }
    const response = await callApi('load_product', partNumber, from, to);
    if (!response.ok) {
      await errorDialog(response.error || 'データ取得に失敗しました。');
      return;
    }

    const result = response.result;
    elements['table-search'].value = '';
    state.tableQuery = '';
    state.currentPart = partNumber;
    if (!result.summary || Object.keys(result.summary).length === 0) {
      state.currentSearchResult = result;
      renderDetailHead(result.details?.columns || state.detailColumns);
      renderMachines(result.machines || ['全て']);
      renderSummary({});
      renderDetails({ columns: result.details?.columns || state.detailColumns, rows: [] });
      elements['detail-count'].textContent = '0件';
      await infoDialog('検索結果', '対象データはありません。');
      return;
    }
    renderSearchResult(result);
  } catch (error) {
    await errorDialog(error?.message || String(error));
  } finally {
    if (showBusy) {
      setBusy(false);
    }
  }
}

async function applyMachineFilter() {
  const machine = elements['machine-select'].value;
  if (!state.currentSearchResult) {
    return;
  }
  setBusy(true, '絞り込み中', '号機で表示を更新しています。');
  try {
    await nextPaint();
    const response = await callApi('filter_by_machine', state.currentSearchResult.all_details, machine);
    if (!response.ok) {
      await errorDialog(response.error || '絞り込みに失敗しました。');
      return;
    }
    state.currentMachine = machine;
    renderSearchResult(response.result, machine);
    updateFilterState(machine);
    if (state.tableQuery) {
      renderDetails(visibleDetailsPayload());
      elements['detail-count'].textContent = `${getCurrentRows().length}件`;
    }
  } catch (error) {
    await errorDialog(error?.message || String(error));
  } finally {
    setBusy(false);
  }
}

function visibleDetailsPayload() {
  return {
    columns: state.currentSearchResult?.details?.columns || state.detailColumns,
    rows: getCurrentRows(),
  };
}

async function exportCurrent() {
  const result = state.currentSearchResult;
  const payload = visibleDetailsPayload();
  if (!result || !payload.rows.length) {
    await errorDialog('出力できるデータがありません。');
    return;
  }
  const confirmed = await confirmDialog('不具合結果エクスポート', '表示中の明細を Excel に出力しますか。');
  if (!confirmed) {
    return;
  }

  setBusy(true, '保存中', 'Excel ファイルを作成しています。');
  try {
    const defaultName = buildCurrentExportName();
    const response = await callApi('export_current', payload, defaultName, null);
    if (!response.ok) {
      if (response.error) {
        await errorDialog(response.error);
      }
      return;
    }
    if (!response.canceled) {
      await infoDialog('完了', `Excel ファイルを保存しました。\n${response.path}`);
    }
  } finally {
    setBusy(false);
  }
}

async function exportByDate(actionName, title) {
  const confirmed = await confirmDialog(title, 'Excel に出力しますか。');
  if (!confirmed) {
    return;
  }
  const from = elements['export-from'].value;
  const to = elements['export-to'].value;
  setBusy(true, title, 'Excel ファイルを作成しています。');
  try {
    const response = await callApi(actionName, from, to);
    if (!response.ok) {
      if (response.error) {
        await errorDialog(response.error);
      }
      return;
    }
    if (!response.canceled) {
      await infoDialog('完了', `Excel ファイルを保存しました。\n${response.path}`);
    }
  } finally {
    setBusy(false);
  }
}

function buildCurrentExportName() {
  const part = (state.currentPart || elements['keyword'].value || '').trim();
  const safe = part.replace(/[<>:"/\\|?*]/g, '').trim();
  return safe ? `${safe}_不具合情報.xlsx` : '不具合情報.xlsx';
}

function wireEvents() {
  elements['close-btn'].addEventListener('click', async () => {
    await callApi('close_app');
  });
  elements['search-btn'].addEventListener('click', searchProducts);
  elements['keyword'].addEventListener('keydown', (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      searchProducts();
    }
  });
  elements['machine-select'].addEventListener('change', applyMachineFilter);
  elements['table-search'].addEventListener('input', (event) => {
    state.tableQuery = event.target.value;
    renderDetails(visibleDetailsPayload());
    elements['detail-count'].textContent = `${getCurrentRows().length}件`;
    updateFilterState();
  });
  elements['clear-search-btn'].addEventListener('click', () => {
    elements['table-search'].value = '';
    state.tableQuery = '';
    renderDetails(state.currentSearchResult?.details || { columns: state.detailColumns, rows: [] });
    elements['detail-count'].textContent = `${state.currentSearchResult?.details?.row_count || 0}件`;
    updateFilterState();
  });
  elements['export-current-btn'].addEventListener('click', exportCurrent);
  elements['export-all-btn'].addEventListener('click', () => exportByDate('export_all_defects', '不具合情報エクスポート'));
  elements['export-aggregate-btn'].addEventListener('click', () => exportByDate('export_aggregate', '集計データ'));
  elements['export-disposal-btn'].addEventListener('click', () => exportByDate('export_disposal', '廃棄データエクスポート'));
}

async function start() {
  if (started) {
    return;
  }
  started = true;
  bindElements();
  wireEvents();

  const bootstrap = await callApi('bootstrap');
  if (!bootstrap.ok) {
    await errorDialog(bootstrap.error || '初期化に失敗しました。');
    return;
  }
  renderBootstrap(bootstrap);
}

function maybeStart() {
  if (!domReady || !backendReady || started) {
    return;
  }
  start().catch(async (error) => {
    await errorDialog(error?.message || String(error));
  });
}

document.addEventListener('DOMContentLoaded', () => {
  domReady = true;
  maybeStart();
});

window.addEventListener('pywebviewready', () => {
  backendReady = true;
  maybeStart();
});

if (window.pywebview?.api) {
  backendReady = true;
  maybeStart();
}
