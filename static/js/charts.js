/**
 * TradeIQ - Interactive Plotly.js Chart Controller
 * Wine Red & Light Sand Luxury Executive Visualization Engine
 * Handles 7 interactive business intelligence visualizations with theme responsiveness.
 */

const TradeIQCharts = (function () {
  // Wine Red & Light Sand Luxury Palette
  const PALETTE = {
    wineRed: '#722F37',
    wineRedDark: '#4A0E17',
    wineRedDeep: '#380C14',
    wineRedLight: '#8B1E3F',
    wineRedVivid: '#9B2C3B',
    lightSand: '#F7F4EE',
    sandCream: '#FAF8F5',
    sandSoft: '#EFEADF',
    sandBorder: '#DFD5C4',
    sandGold: '#C8A26A',
    sandDark: '#A67C52',
    emerald: '#15803D',
    coral: '#C0392B',
    amber: '#D97706',
    white: '#FFFFFF',
    slate: '#6B5E59',
    donut: ['#722F37', '#C8A26A', '#8B1E3F', '#15803D', '#A67C52', '#9B2C3B', '#D97706']
  };

  function isDarkMode() {
    return document.documentElement.getAttribute('data-theme') === 'dark';
  }

  function getBaseLayout() {
    const dark = isDarkMode();
    return {
      paper_bgcolor: 'transparent',
      plot_bgcolor: 'transparent',
      autosize: true,
      font: {
        family: 'Inter, system-ui, -apple-system, sans-serif',
        color: dark ? '#F7F4EE' : '#2A1810',
        size: 11
      },
      margin: { l: 50, r: 25, t: 25, b: 40 },
      hoverlabel: {
        bgcolor: dark ? '#260E14' : '#FFFFFF',
        bordercolor: dark ? '#C8A26A' : '#722F37',
        font: { color: dark ? '#FAF8F5' : '#2A1810', size: 12 }
      },
      legend: {
        orientation: 'h',
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'right',
        x: 1,
        font: { size: 10, color: dark ? '#C8B9B0' : '#6B5E59' }
      }
    };
  }

  // 1. Chart A: Monthly Revenue Trend
  function renderRevenueTrend(containerId, data, viewMode = 'monthly') {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.labels || data.labels.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No revenue records found for this period.</div>';
      return;
    }

    const dark = isDarkMode();
    const traceNet = {
      x: data.labels,
      y: data.net_sales,
      name: 'Net Sales ($)',
      type: 'scatter',
      mode: 'lines+markers',
      line: { color: '#722F37', width: 3, shape: 'spline' },
      marker: { color: '#4A0E17', size: 7, symbol: 'circle' },
      fill: 'tozeroy',
      fillcolor: dark ? 'rgba(114, 47, 55, 0.28)' : 'rgba(114, 47, 55, 0.12)',
      hovertemplate: '<b>%{x}</b><br>Net Sales: $%{y:,.2f}<extra></extra>'
    };

    const traceGross = {
      x: data.labels,
      y: data.gross_sales,
      name: 'Gross Sales ($)',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#C8A26A', width: 2, dash: 'dot', shape: 'spline' },
      hovertemplate: 'Gross Sales: $%{y:,.2f}<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      xaxis: {
        gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF',
        zerolinecolor: dark ? 'rgba(200, 162, 106, 0.4)' : '#DFD5C4'
      },
      yaxis: {
        tickprefix: '$',
        gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF',
        zerolinecolor: dark ? 'rgba(200, 162, 106, 0.4)' : '#DFD5C4'
      }
    };

    const config = { responsive: true, displayModeBar: false };
    Plotly.react(containerId, [traceGross, traceNet], layout, config);
  }

  // 2. Chart B: Category Performance Donut
  function renderCategoryDonut(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.labels || data.labels.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No category data available.</div>';
      return;
    }

    const dark = isDarkMode();
    const trace = {
      labels: data.labels,
      values: data.values,
      type: 'pie',
      hole: 0.58,
      marker: { colors: PALETTE.donut },
      textinfo: 'percent',
      hoverinfo: 'label+value+percent',
      hovertemplate: '<b>%{label}</b><br>Net Sales: $%{value:,.2f}<br>Share: %{percent}<extra></extra>',
      textfont: { color: '#ffffff', size: 11 }
    };

    const layout = {
      ...getBaseLayout(),
      margin: { l: 20, r: 20, t: 10, b: 10 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 0,
        y: -0.1,
        font: { size: 10 }
      }
    };

    Plotly.react(containerId, [trace], layout, { responsive: true, displayModeBar: false });
  }

  // 3. Chart C: Regional Revenue Comparison Horizontal Bar
  function renderRegionalRevenue(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.regions || data.regions.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No regional data available.</div>';
      return;
    }

    const dark = isDarkMode();
    const trace = {
      x: data.net_sales,
      y: data.regions,
      type: 'bar',
      orientation: 'h',
      marker: {
        color: ['#722F37', '#8B1E3F', '#C8A26A', '#A67C52', '#4A0E17'],
        opacity: 0.95,
        line: { width: 0 }
      },
      text: data.net_sales.map(v => `$${v.toLocaleString()}`),
      textposition: 'auto',
      hovertemplate: '<b>%{y}</b><br>Net Revenue: $%{x:,.2f}<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      margin: { l: 95, r: 25, t: 15, b: 25 },
      xaxis: {
        tickprefix: '$',
        gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF'
      },
      yaxis: {
        automargin: true
      }
    };

    Plotly.react(containerId, [trace], layout, { responsive: true, displayModeBar: false });
  }

  // 4. Chart D: Gross Sales vs Net Sales Grouped Bar
  function renderGrossVsNet(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.periods || data.periods.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No breakdown data available.</div>';
      return;
    }

    const dark = isDarkMode();
    const traceGross = {
      x: data.periods,
      y: data.gross,
      name: 'Gross Sales',
      type: 'bar',
      marker: { color: '#722F37' },
      hovertemplate: 'Gross: $%{y:,.2f}<extra></extra>'
    };

    const traceNet = {
      x: data.periods,
      y: data.net,
      name: 'Net Sales',
      type: 'bar',
      marker: { color: '#C8A26A' },
      hovertemplate: 'Net: $%{y:,.2f}<extra></extra>'
    };

    const traceDiscounts = {
      x: data.periods,
      y: data.discounts,
      name: 'Discounts',
      type: 'bar',
      marker: { color: '#A67C52' },
      hovertemplate: 'Discounts: $%{y:,.2f}<extra></extra>'
    };

    const traceReturns = {
      x: data.periods,
      y: data.returns,
      name: 'Returns',
      type: 'bar',
      marker: { color: '#C0392B' },
      hovertemplate: 'Returns: $%{y:,.2f}<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      barmode: 'group',
      xaxis: { gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF' },
      yaxis: { tickprefix: '$', gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF' }
    };

    Plotly.react(containerId, [traceGross, traceNet, traceDiscounts, traceReturns], layout, { responsive: true, displayModeBar: false });
  }

  // 5. Chart E: Order Status Distribution Donut
  function renderOrderStatus(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.statuses || data.statuses.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No order status records found.</div>';
      return;
    }

    const statusColors = {
      'Completed': '#15803D',
      'Delivered': '#722F37',
      'Returned': '#C8A26A',
      'Cancelled': '#C0392B',
      'Processing': '#8B1E3F'
    };

    const colors = data.statuses.map(s => statusColors[s] || '#A67C52');

    const trace = {
      labels: data.statuses,
      values: data.counts,
      type: 'pie',
      hole: 0.55,
      marker: { colors: colors },
      textinfo: 'percent',
      hovertemplate: '<b>%{label}</b><br>Orders: %{value}<br>Share: %{percent}<extra></extra>',
      textfont: { color: '#ffffff', size: 10 }
    };

    const layout = {
      ...getBaseLayout(),
      margin: { l: 15, r: 15, t: 10, b: 10 },
      showlegend: true,
      legend: {
        orientation: 'h',
        x: 0,
        y: -0.15,
        font: { size: 10 }
      }
    };

    Plotly.react(containerId, [trace], layout, { responsive: true, displayModeBar: false });
  }

  // 6. Chart F: Period-over-Period Growth Bar Chart
  function renderPeriodGrowth(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.periods || data.periods.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No period comparison data.</div>';
      return;
    }

    const dark = isDarkMode();
    const trace = {
      x: data.periods,
      y: data.growth_rates,
      type: 'bar',
      marker: {
        color: data.growth_rates.map(g => g >= 0 ? '#722F37' : '#C0392B'),
        line: { width: 0 }
      },
      text: data.growth_rates.map(g => `${g > 0 ? '+' : ''}${g}%`),
      textposition: 'outside',
      hovertemplate: '<b>%{x}</b><br>MoM Growth: %{y:.2f}%<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      xaxis: { gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF' },
      yaxis: {
        ticksuffix: '%',
        gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF',
        zeroline: true,
        zerolinecolor: dark ? '#C8A26A' : '#722F37',
        zerolinewidth: 1.5
      }
    };

    Plotly.react(containerId, [trace], layout, { responsive: true, displayModeBar: false });
  }

  // 7. Chart G: Top Performing Products Horizontal Bar
  function renderTopProducts(containerId, data) {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.products || data.products.length === 0) {
      if (el) el.innerHTML = '<div class="text-center p-4 text-muted">No product performance data.</div>';
      return;
    }

    const dark = isDarkMode();
    const trace = {
      x: data.net_sales,
      y: data.products,
      type: 'bar',
      orientation: 'h',
      marker: {
        color: '#722F37',
        opacity: 0.9
      },
      text: data.net_sales.map(v => `$${v.toLocaleString()}`),
      textposition: 'inside',
      hovertemplate: '<b>%{y}</b><br>Category: %{customdata}<br>Net Sales: $%{x:,.2f}<extra></extra>',
      customdata: data.categories
    };

    const layout = {
      ...getBaseLayout(),
      margin: { l: 150, r: 25, t: 15, b: 25 },
      xaxis: {
        tickprefix: '$',
        gridcolor: dark ? 'rgba(114, 47, 55, 0.25)' : '#EFEADF'
      },
      yaxis: {
        automargin: true
      }
    };

    Plotly.react(containerId, [trace], layout, { responsive: true, displayModeBar: false });
  }

  // Global window resize listener
  window.addEventListener('resize', () => {
    const chartIds = [
      'chart-revenue-trend',
      'chart-category-donut',
      'chart-regional-revenue',
      'chart-gross-vs-net',
      'chart-order-status',
      'chart-period-growth',
      'chart-top-products'
    ];
    chartIds.forEach(id => {
      const el = document.getElementById(id);
      if (el && el.data) {
        Plotly.Plots.resize(el);
      }
    });
  });

  return {
    renderRevenueTrend,
    renderCategoryDonut,
    renderRegionalRevenue,
    renderGrossVsNet,
    renderOrderStatus,
    renderPeriodGrowth,
    renderTopProducts
  };
})();
