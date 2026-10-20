/**
 * TradeIQ - Interactive Plotly.js Chart Controller
 * Royal Blue & White Cream Luxury Executive Visualization Engine
 * Handles 7 interactive business intelligence visualizations with theme responsiveness.
 */

const TradeIQCharts = (function () {
  // Royal Blue & White Cream Executive Palette
  const PALETTE = {
    royalBlue: '#1E40AF',
    royalBlueDark: '#0F204E',
    royalBlueDeep: '#070F24',
    royalBlueLight: '#2563EB',
    royalBlueVivid: '#3B82F6',
    royalBlueSoft: '#60A5FA',
    whiteCream: '#FAF8F5',
    creamBg: '#F5F1E9',
    creamSoft: '#EFE9DE',
    creamBorder: '#DCD4C4',
    creamGold: '#D99B26',
    emerald: '#15803D',
    coral: '#DC2626',
    amber: '#D97706',
    white: '#FFFFFF',
    slate: '#53627C',
    donut: ['#1E40AF', '#2563EB', '#3B82F6', '#60A5FA', '#D99B26', '#15803D', '#0F204E']
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
        color: dark ? '#FAF8F5' : '#0F172A',
        size: 11
      },
      margin: { l: 50, r: 25, t: 25, b: 40 },
      hoverlabel: {
        bgcolor: dark ? '#0E172F' : '#FFFFFF',
        bordercolor: dark ? '#3B82F6' : '#1E40AF',
        font: { color: dark ? '#FAF8F5' : '#0F172A', size: 12 }
      },
      legend: {
        orientation: 'h',
        yanchor: 'bottom',
        y: 1.02,
        xanchor: 'right',
        x: 1,
        font: { size: 10, color: dark ? '#CBD5E1' : '#53627C' }
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
      line: { color: '#1E40AF', width: 3.2, shape: 'spline' },
      marker: { color: '#0F204E', size: 7, symbol: 'circle' },
      fill: 'tozeroy',
      fillcolor: dark ? 'rgba(30, 64, 175, 0.30)' : 'rgba(30, 64, 175, 0.12)',
      hovertemplate: '<b>%{x}</b><br>Net Sales: $%{y:,.2f}<extra></extra>'
    };

    const traceGross = {
      x: data.labels,
      y: data.gross_sales,
      name: 'Gross Sales ($)',
      type: 'scatter',
      mode: 'lines',
      line: { color: '#3B82F6', width: 2, dash: 'dot', shape: 'spline' },
      hovertemplate: 'Gross Sales: $%{y:,.2f}<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      xaxis: {
        gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE',
        zerolinecolor: dark ? 'rgba(59, 130, 246, 0.35)' : '#DCD4C4'
      },
      yaxis: {
        tickprefix: '$',
        gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE',
        zerolinecolor: dark ? 'rgba(59, 130, 246, 0.35)' : '#DCD4C4'
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
        color: ['#1E40AF', '#2563EB', '#3B82F6', '#60A5FA', '#93C5FD'],
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
        gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE'
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
      marker: { color: '#2563EB' },
      hovertemplate: 'Gross: $%{y:,.2f}<extra></extra>'
    };

    const traceNet = {
      x: data.periods,
      y: data.net,
      name: 'Net Sales',
      type: 'bar',
      marker: { color: '#1E40AF' },
      hovertemplate: 'Net: $%{y:,.2f}<extra></extra>'
    };

    const traceDiscounts = {
      x: data.periods,
      y: data.discounts,
      name: 'Discounts',
      type: 'bar',
      marker: { color: '#D99B26' },
      hovertemplate: 'Discounts: $%{y:,.2f}<extra></extra>'
    };

    const traceReturns = {
      x: data.periods,
      y: data.returns,
      name: 'Returns',
      type: 'bar',
      marker: { color: '#DC2626' },
      hovertemplate: 'Returns: $%{y:,.2f}<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      barmode: 'group',
      xaxis: { gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE' },
      yaxis: { tickprefix: '$', gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE' }
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
      'Delivered': '#1E40AF',
      'Returned': '#D99B26',
      'Cancelled': '#DC2626',
      'Processing': '#2563EB'
    };

    const colors = data.statuses.map(s => statusColors[s] || '#60A5FA');

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
        color: data.growth_rates.map(g => g >= 0 ? '#1E40AF' : '#DC2626'),
        line: { width: 0 }
      },
      text: data.growth_rates.map(g => `${g > 0 ? '+' : ''}${g}%`),
      textposition: 'outside',
      hovertemplate: '<b>%{x}</b><br>MoM Growth: %{y:.2f}%<extra></extra>'
    };

    const layout = {
      ...getBaseLayout(),
      xaxis: { gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE' },
      yaxis: {
        ticksuffix: '%',
        gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE',
        zeroline: true,
        zerolinecolor: dark ? '#3B82F6' : '#1E40AF',
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
        color: '#1E40AF',
        opacity: 0.92
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
        gridcolor: dark ? 'rgba(59, 130, 246, 0.18)' : '#EFE9DE'
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
