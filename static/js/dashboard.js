/**
 * TradeIQ - Main Dashboard Controller
 * Manages animated KPI counters, filter controls, API synchronization, and theme switching.
 */

document.addEventListener('DOMContentLoaded', () => {
  // --------------------------------------------------------------------------
  // 1. Theme Toggle & Persistence
  // --------------------------------------------------------------------------
  const themeToggleBtn = document.getElementById('theme-toggle-btn');
  const themeIcon = document.getElementById('theme-icon');
  
  function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('tradeiq-theme', theme);
    if (themeIcon) {
      themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }
    // Re-render charts with updated theme palette if dashboard is active
    if (window.currentDashboardData) {
      renderAllCharts(window.currentDashboardData);
    }
  }

  const savedTheme = localStorage.getItem('tradeiq-theme') || 'light';
  applyTheme(savedTheme);

  if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', () => {
      const current = document.documentElement.getAttribute('data-theme');
      applyTheme(current === 'dark' ? 'light' : 'dark');
    });
  }

  // --------------------------------------------------------------------------
  // 2. Animated Number Counters
  // --------------------------------------------------------------------------
  function animateValue(elem, start, end, duration = 800, isCurrency = false, isPercent = false) {
    if (!elem) return;
    if (isNaN(end) || end === null || end === undefined) return;
    
    // Check user preference for reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      if (isCurrency) {
        elem.innerText = `$${end.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      } else if (isPercent) {
        elem.innerText = `${end.toFixed(2)}%`;
      } else {
        elem.innerText = end.toLocaleString();
      }
      return;
    }

    // Smoothly transition from current rendered number if available
    let startVal = start;
    if (startVal === 0 && elem.innerText) {
      const currentParsed = parseFloat(elem.innerText.replace(/[^0-9.-]/g, ''));
      if (!isNaN(currentParsed) && currentParsed > 0) {
        startVal = currentParsed;
      }
    }

    let startTimestamp = null;
    const step = (timestamp) => {
      if (!startTimestamp) startTimestamp = timestamp;
      const progress = Math.min((timestamp - startTimestamp) / duration, 1);
      // Ease out cubic
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentVal = startVal + (end - startVal) * easeOut;

      if (isCurrency) {
        elem.innerText = `$${currentVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      } else if (isPercent) {
        elem.innerText = `${currentVal.toFixed(2)}%`;
      } else {
        elem.innerText = Math.floor(currentVal).toLocaleString();
      }

      if (progress < 1) {
        window.requestAnimationFrame(step);
      } else {
        if (isCurrency) {
          elem.innerText = `$${end.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        } else if (isPercent) {
          elem.innerText = `${end.toFixed(2)}%`;
        } else {
          elem.innerText = end.toLocaleString();
        }
      }
    };
    window.requestAnimationFrame(step);
  }

  // --------------------------------------------------------------------------
  // 3. Filter Management & State
  // --------------------------------------------------------------------------
  const filterForm = document.getElementById('filter-form');
  const btnApplyFilter = document.getElementById('btn-apply-filter');
  const btnResetFilter = document.getElementById('btn-reset-filter');
  const selectMonth = document.getElementById('filter-month');
  const inputStartDate = document.getElementById('filter-start-date');
  const inputEndDate = document.getElementById('filter-end-date');
  const selectCategory = document.getElementById('filter-category');
  const selectRegion = document.getElementById('filter-region');
  const selectStatus = document.getElementById('filter-status');
  const presetPills = document.querySelectorAll('.preset-pill, .range-chip');

  let revenueTrendViewMode = 'monthly';

  function getActiveFilterParams() {
    const params = new URLSearchParams();
    const activePreset = document.querySelector('.preset-pill.active, .range-chip.active');
    const isAllPreset = activePreset && activePreset.getAttribute('data-preset') === 'all';

    // If month dropdown is chosen, it takes priority
    if (selectMonth && selectMonth.value && selectMonth.value !== 'All') {
      params.append('month', selectMonth.value);
    } else if (!isAllPreset) {
      if (inputStartDate && inputStartDate.value) params.append('start_date', inputStartDate.value);
      if (inputEndDate && inputEndDate.value) params.append('end_date', inputEndDate.value);
    }
    if (selectCategory && selectCategory.value && selectCategory.value !== 'All') params.append('category', selectCategory.value);
    if (selectRegion && selectRegion.value && selectRegion.value !== 'All') params.append('region', selectRegion.value);
    if (selectStatus && selectStatus.value && selectStatus.value !== 'All') params.append('order_status', selectStatus.value);
    params.append('view_mode', revenueTrendViewMode);
    return params;
  }

  // Preset Date Range Selectors
  presetPills.forEach(pill => {
    pill.addEventListener('click', (e) => {
      presetPills.forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      const preset = pill.getAttribute('data-preset');
      const today = new Date();
      if (selectMonth) selectMonth.value = 'All';

      if (preset === 'all') {
        if (inputStartDate) inputStartDate.value = '';
        if (inputEndDate) inputEndDate.value = '';
      } else if (preset === '30d') {
        const d = new Date();
        d.setDate(d.getDate() - 30);
        if (inputStartDate) inputStartDate.value = d.toISOString().split('T')[0];
        if (inputEndDate) inputEndDate.value = today.toISOString().split('T')[0];
      } else if (preset === '90d') {
        const d = new Date();
        d.setDate(d.getDate() - 90);
        if (inputStartDate) inputStartDate.value = d.toISOString().split('T')[0];
        if (inputEndDate) inputEndDate.value = today.toISOString().split('T')[0];
      } else if (preset === 'ytd') {
        const currentYear = today.getFullYear();
        if (inputStartDate) inputStartDate.value = `${currentYear}-01-01`;
        if (inputEndDate) inputEndDate.value = today.toISOString().split('T')[0];
      }
      fetchDashboardData();
    });
  });

  // Instant Auto-Update on changing Month, Category, Region, Status, or Dates
  if (selectMonth) {
    selectMonth.addEventListener('change', () => {
      const val = selectMonth.value;
      if (val && val !== 'All') {
        const [yearStr, monthStr] = val.split('-');
        const year = parseInt(yearStr, 10);
        const monthNum = parseInt(monthStr, 10);
        const lastDay = new Date(year, monthNum, 0).getDate();
        if (inputStartDate) inputStartDate.value = `${val}-01`;
        if (inputEndDate) inputEndDate.value = `${val}-${String(lastDay).padStart(2, '0')}`;
        presetPills.forEach(p => p.classList.remove('active'));
      } else {
        if (inputStartDate) inputStartDate.value = '';
        if (inputEndDate) inputEndDate.value = '';
        presetPills.forEach(p => p.classList.remove('active'));
        const allPill = document.querySelector('.preset-pill[data-preset="all"], .range-chip[data-preset="all"]');
        if (allPill) allPill.classList.add('active');
      }
      fetchDashboardData();
    });
  }

  if (selectCategory) {
    selectCategory.addEventListener('change', () => {
      fetchDashboardData();
    });
  }

  if (selectRegion) {
    selectRegion.addEventListener('change', () => {
      fetchDashboardData();
    });
  }

  if (selectStatus) {
    selectStatus.addEventListener('change', () => {
      fetchDashboardData();
    });
  }

  if (inputStartDate) {
    inputStartDate.addEventListener('change', () => {
      if (selectMonth) selectMonth.value = 'All';
      presetPills.forEach(p => p.classList.remove('active'));
      fetchDashboardData();
    });
  }

  if (inputEndDate) {
    inputEndDate.addEventListener('change', () => {
      if (selectMonth) selectMonth.value = 'All';
      presetPills.forEach(p => p.classList.remove('active'));
      fetchDashboardData();
    });
  }

  if (btnApplyFilter) {
    btnApplyFilter.addEventListener('click', (e) => {
      e.preventDefault();
      presetPills.forEach(p => p.classList.remove('active'));
      fetchDashboardData();
    });
  }

  if (btnResetFilter) {
    btnResetFilter.addEventListener('click', (e) => {
      e.preventDefault();
      if (selectMonth) selectMonth.value = 'All';
      if (inputStartDate) inputStartDate.value = '';
      if (inputEndDate) inputEndDate.value = '';
      if (selectCategory) selectCategory.value = 'All';
      if (selectRegion) selectRegion.value = 'All';
      if (selectStatus) selectStatus.value = 'All';
      presetPills.forEach(p => p.classList.remove('active'));
      const allPill = document.querySelector('.preset-pill[data-preset="all"], .range-chip[data-preset="all"]');
      if (allPill) allPill.classList.add('active');
      fetchDashboardData();
    });
  }

  // Monthly vs Quarterly Toggle on Revenue Chart
  const btnToggleMonthly = document.getElementById('btn-view-monthly');
  const btnToggleQuarterly = document.getElementById('btn-view-quarterly');
  if (btnToggleMonthly && btnToggleQuarterly) {
    btnToggleMonthly.addEventListener('click', () => {
      btnToggleMonthly.classList.add('active');
      btnToggleQuarterly.classList.remove('active');
      revenueTrendViewMode = 'monthly';
      fetchRevenueTrendOnly();
    });
    btnToggleQuarterly.addEventListener('click', () => {
      btnToggleQuarterly.classList.add('active');
      btnToggleMonthly.classList.remove('active');
      revenueTrendViewMode = 'quarterly';
      fetchRevenueTrendOnly();
    });
  }

  // --------------------------------------------------------------------------
  // 4. Update KPI Cards & Trends
  // --------------------------------------------------------------------------
  function updateKPIs(kpiData) {
    if (!kpiData) return;
    const curr = kpiData.current;
    const chg = kpiData.changes;
    const prev = kpiData.previous;

    // 1. Gross Sales
    animateValue(document.getElementById('kpi-val-gross'), 0, curr.gross_sales, 800, true);
    updateTrendBadge('kpi-trend-gross', chg.gross_sales_pct, prev.gross_sales, true);

    // 2. Net Sales
    animateValue(document.getElementById('kpi-val-net'), 0, curr.net_sales, 800, true);
    updateTrendBadge('kpi-trend-net', chg.net_sales_pct, prev.net_sales, true);

    // 3. Valid Orders
    animateValue(document.getElementById('kpi-val-orders'), 0, curr.valid_orders, 800, false);
    updateTrendBadge('kpi-trend-orders', chg.orders_pct, prev.valid_orders, false);

    // 4. Average Order Value (AOV)
    animateValue(document.getElementById('kpi-val-aov'), 0, curr.aov, 800, true);
    updateTrendBadge('kpi-trend-aov', chg.aov_pct, prev.aov, true);

    // 5. Total Discounts
    animateValue(document.getElementById('kpi-val-discounts'), 0, curr.total_discounts, 800, true);
    updateTrendBadge('kpi-trend-discounts', chg.discounts_pct, prev.total_discounts, true);

    // 6. Total Returns
    animateValue(document.getElementById('kpi-val-returns'), 0, curr.total_returns, 800, true);
    updateTrendBadge('kpi-trend-returns', chg.returns_pct, prev.total_returns, true, true); // true = higher return is warning

    // 7. Revenue Growth Percentage
    const growthElem = document.getElementById('kpi-val-growth');
    const growthSub = document.getElementById('kpi-sub-growth');
    if (curr.revenue_growth_pct !== null && curr.revenue_growth_pct !== undefined) {
      animateValue(growthElem, 0, curr.revenue_growth_pct, 800, false, true);
      updateTrendBadge('kpi-trend-growth', curr.revenue_growth_pct, null, false);
      if (growthSub) growthSub.innerText = `vs prior baseline`;
    } else {
      if (growthElem) growthElem.innerText = 'N/A';
      if (growthSub) growthSub.innerText = 'Baseline Period';
      const badge = document.getElementById('kpi-trend-growth');
      if (badge) {
        badge.className = 'trend-indicator neutral';
        badge.innerHTML = '<i class="fas fa-minus"></i> Baseline';
      }
    }
  }

  function updateTrendBadge(elemId, pctChange, prevVal, isCurrency, invert = false) {
    const badge = document.getElementById(elemId);
    if (!badge) return;

    if (pctChange === null || pctChange === undefined) {
      badge.className = 'trend-indicator neutral';
      badge.innerHTML = '<i class="fas fa-minus"></i> Baseline';
      return;
    }

    const isPositive = invert ? pctChange < 0 : pctChange >= 0;
    const arrow = pctChange > 0 ? 'fa-arrow-up' : (pctChange < 0 ? 'fa-arrow-down' : 'fa-minus');
    const badgeClass = isPositive ? 'up' : 'down';

    badge.className = `trend-indicator ${badgeClass}`;
    badge.innerHTML = `<i class="fas ${arrow}"></i> ${pctChange > 0 ? '+' : ''}${pctChange.toFixed(1)}%`;
  }

  // --------------------------------------------------------------------------
  // 5. Fetch & Render All Dashboard Components
  // --------------------------------------------------------------------------
  async function fetchDashboardData() {
    const params = getActiveFilterParams();
    const queryString = params.toString();

    // Show loading state
    const btn = document.getElementById('btn-apply-filter');
    if (btn) btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';

    const safeFetch = (url) => fetch(url)
      .then(r => r.ok ? r.json() : { success: false, data: {} })
      .catch(err => { console.warn(`Error fetching ${url}:`, err); return { success: false, data: {} }; });

    try {
      const [kpisRes, trendRes, catRes, regRes, gvnRes, statusRes, growthRes, topRes] = await Promise.all([
        safeFetch(`/api/kpis?${queryString}`),
        safeFetch(`/api/revenue-trend?${queryString}`),
        safeFetch(`/api/category-performance?${queryString}`),
        safeFetch(`/api/regional-revenue?${queryString}`),
        safeFetch(`/api/gross-vs-net?${queryString}`),
        safeFetch(`/api/order-status?${queryString}`),
        safeFetch(`/api/period-growth?${queryString}`),
        safeFetch(`/api/top-products?${queryString}`)
      ]);

      if (kpisRes && kpisRes.success) updateKPIs(kpisRes.data);

      window.currentDashboardData = {
        trend: trendRes.data,
        category: catRes.data,
        regional: regRes.data,
        grossVsNet: gvnRes.data,
        orderStatus: statusRes.data,
        periodGrowth: growthRes.data,
        topProducts: topRes.data
      };

      renderAllCharts(window.currentDashboardData);
    } catch (err) {
      console.error('Error fetching dashboard analytics:', err);
    } finally {
      if (btn) btn.innerHTML = '<i class="fas fa-filter"></i> Apply Filters';
    }
  }

  async function fetchRevenueTrendOnly() {
    const params = getActiveFilterParams();
    try {
      const res = await fetch(`/api/revenue-trend?${params.toString()}`).then(r => r.json());
      if (res.success && document.getElementById('chart-revenue-trend')) {
        TradeIQCharts.renderRevenueTrend('chart-revenue-trend', res.data, revenueTrendViewMode);
      }
    } catch (err) {
      console.error('Error fetching revenue trend:', err);
    }
  }

  function renderAllCharts(data) {
    if (!data) return;
    if (typeof Plotly === 'undefined') {
      setTimeout(() => renderAllCharts(data), 120);
      return;
    }
    if (document.getElementById('chart-revenue-trend') && data.trend) {
      TradeIQCharts.renderRevenueTrend('chart-revenue-trend', data.trend, revenueTrendViewMode);
    }
    if (document.getElementById('chart-category-donut') && data.category) {
      TradeIQCharts.renderCategoryDonut('chart-category-donut', data.category);
    }
    if (document.getElementById('chart-regional-revenue') && data.regional) {
      TradeIQCharts.renderRegionalRevenue('chart-regional-revenue', data.regional);
    }
    if (document.getElementById('chart-gross-vs-net') && data.grossVsNet) {
      TradeIQCharts.renderGrossVsNet('chart-gross-vs-net', data.grossVsNet);
    }
    if (document.getElementById('chart-order-status') && data.orderStatus) {
      TradeIQCharts.renderOrderStatus('chart-order-status', data.orderStatus);
    }
    if (document.getElementById('chart-period-growth') && data.periodGrowth) {
      TradeIQCharts.renderPeriodGrowth('chart-period-growth', data.periodGrowth);
    }
    if (document.getElementById('chart-top-products') && data.topProducts) {
      TradeIQCharts.renderTopProducts('chart-top-products', data.topProducts);
    }
  }

  // --------------------------------------------------------------------------
  // 6. Export Action Handlers
  // --------------------------------------------------------------------------
  const btnExportCsv = document.getElementById('btn-export-csv');
  const btnExportPdf = document.getElementById('btn-export-pdf');

  if (btnExportCsv) {
    btnExportCsv.addEventListener('click', () => {
      const params = getActiveFilterParams();
      window.location.href = `/api/export/csv?${params.toString()}`;
    });
  }

  if (btnExportPdf) {
    btnExportPdf.addEventListener('click', () => {
      const params = getActiveFilterParams();
      window.location.href = `/api/export/pdf?${params.toString()}`;
    });
  }

  // --------------------------------------------------------------------------
  // 7. Mobile Sidebar Toggle
  // --------------------------------------------------------------------------
  const mobileToggle = document.getElementById('mobile-sidebar-toggle');
  const sidebar = document.querySelector('.app-sidebar');
  if (mobileToggle && sidebar) {
    mobileToggle.addEventListener('click', () => {
      sidebar.classList.toggle('show-mobile');
    });
  }



  // --------------------------------------------------------------------------
  // 9. Live Client-Side Product Table Search & Filter
  // --------------------------------------------------------------------------
  const tableSearchInput = document.getElementById('table-search-input');
  const tableCategoryFilter = document.getElementById('table-category-filter');
  const productsCatalogTable = document.getElementById('products-catalog-table');

  function filterProductRows() {
    if (!productsCatalogTable) return;
    const q = (tableSearchInput?.value || '').toLowerCase().trim();
    const cat = (tableCategoryFilter?.value || '').toLowerCase().trim();
    const rows = productsCatalogTable.querySelectorAll('tbody tr');
    rows.forEach(row => {
      const text = row.innerText.toLowerCase();
      const rowCat = row.querySelector('td:nth-child(3)')?.innerText.toLowerCase().trim() || '';
      const matchesText = !q || text.includes(q);
      const matchesCat = !cat || rowCat === cat || rowCat.includes(cat);
      row.style.display = (matchesText && matchesCat) ? '' : 'none';
    });
  }

  if (tableSearchInput) tableSearchInput.addEventListener('input', filterProductRows);
  if (tableCategoryFilter) tableCategoryFilter.addEventListener('change', filterProductRows);

  // Check if current page contains any chart containers and trigger data fetch
  const chartContainers = [
    'chart-revenue-trend',
    'chart-category-donut',
    'chart-regional-revenue',
    'chart-gross-vs-net',
    'chart-order-status',
    'chart-period-growth',
    'chart-top-products'
  ];

  const hasAnyChart = chartContainers.some(id => document.getElementById(id) !== null);
  if (hasAnyChart) {
    fetchDashboardData();
  }
});

