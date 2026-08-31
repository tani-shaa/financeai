/* ═══════════════════════════════════════════════════════════════════════════
   Nexora Trading — charts.js (High-Tech Visualizations)
   Expects global: chartData, CURRENCY
═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Nexora Color Palette ──────────────────────────────────────────────── */
  const PALETTE = [
    '#38bdf8', '#818cf8', '#34d399', '#f59e0b',
    '#f43f5e', '#a78bfa', '#2dd4bf', '#fb923c', '#60a5fa',
  ];

  const isDark = () => document.documentElement.dataset.theme !== 'light';
  const gridColor   = () => isDark() ? 'rgba(147, 197, 253, 0.08)' : 'rgba(56, 189, 248, 0.1)';
  const tickColor   = () => isDark() ? '#64748b' : '#475569';
  const legendColor = () => isDark() ? '#f1f5f9' : '#0f172a';

  /* Global Chart.js defaults */
  Chart.defaults.font.family = "'Plus Jakarta Sans', 'Inter', system-ui, sans-serif";
  Chart.defaults.color = tickColor();

  /* ─────────────────────────────────────────────────────────────────────
     1. CIRCULAR DONUT GAUGE — Category / Asset Split
  ───────────────────────────────────────────────────────────────────── */
  const pieCtx = document.getElementById('categoryPieChart');
  if (pieCtx && chartData.categoryLabels && chartData.categoryLabels.length > 0) {
    new Chart(pieCtx, {
      type: 'doughnut',
      data: {
        labels: chartData.categoryLabels,
        datasets: [{
          data: chartData.categoryValues,
          backgroundColor: PALETTE,
          borderColor: isDark() ? '#0d1a38' : '#ffffff',
          borderWidth: 3,
          hoverBorderWidth: 4,
          hoverOffset: 6,
          borderRadius: 8,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        cutout: '76%',
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(10, 20, 44, 0.92)',
            borderColor: 'rgba(56, 189, 248, 0.3)',
            borderWidth: 1,
            titleColor: '#ffffff',
            bodyColor: '#38bdf8',
            padding: 10,
            cornerRadius: 10,
            callbacks: {
              label: ctx => ` ${CURRENCY}${Number(ctx.parsed).toLocaleString()} — ${ctx.label}`,
            },
          },
        },
        animation: { animateRotate: true, duration: 1000 },
      },
    });
  }

  /* ─────────────────────────────────────────────────────────────────────
     2. BAR CHART — Monthly Volume / Flow
  ───────────────────────────────────────────────────────────────────── */
  const barCtx = document.getElementById('monthlyBarChart');
  if (barCtx && chartData.monthlyExpLabels && chartData.monthlyExpLabels.length > 0) {
    new Chart(barCtx, {
      type: 'bar',
      data: {
        labels: chartData.monthlyExpLabels.map(l => l.toUpperCase()),
        datasets: [{
          label: 'Volume',
          data: chartData.monthlyExpValues,
          backgroundColor: ctx => {
            const chart = ctx.chart;
            const { ctx: c, chartArea } = chart;
            if (!chartArea) return '#38bdf8';
            const g = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
            g.addColorStop(0, 'rgba(56, 189, 248, 0.9)');
            g.addColorStop(1, 'rgba(37, 99, 235, 0.25)');
            return g;
          },
          borderColor: '#38bdf8',
          borderWidth: { top: 2, right: 0, bottom: 0, left: 0 },
          borderRadius: 8,
          borderSkipped: false,
          maxBarThickness: 32,
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            backgroundColor: 'rgba(10, 20, 44, 0.92)',
            borderColor: 'rgba(56, 189, 248, 0.3)',
            borderWidth: 1,
            titleColor: '#ffffff',
            bodyColor: '#38bdf8',
            padding: 10,
            cornerRadius: 10,
            callbacks: {
              label: ctx => ` ${CURRENCY}${Number(ctx.parsed.y).toLocaleString()}`,
            },
          },
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: tickColor(), font: { weight: '600', size: 11 } },
            border: { display: false },
          },
          y: {
            grid: { color: gridColor(), drawTicks: false },
            ticks: {
              color: tickColor(),
              font: { size: 11 },
              callback: v => v >= 1000 ? `${CURRENCY}${(v/1000).toFixed(1)}k` : `${CURRENCY}${v}`,
            },
            border: { dash: [4, 4], display: false },
          },
        },
        animation: { duration: 1000 },
      },
    });
  }

  /* ─────────────────────────────────────────────────────────────────────
     3. LINE / AREA — Historical Spending vs Prediction
  ───────────────────────────────────────────────────────────────────── */
  const predCtx = document.getElementById('predictionChart');
  if (predCtx && typeof monthlyData !== 'undefined' && monthlyData.length > 0) {
    new Chart(predCtx, {
      type: 'line',
      data: {
        labels: monthLabels,
        datasets: [
          {
            label: 'Actual Volume',
            data: monthlyData,
            borderColor: '#38bdf8',
            backgroundColor: ctx => {
              const c = ctx.chart.ctx;
              const g = c.createLinearGradient(0, 0, 0, 280);
              g.addColorStop(0, 'rgba(56, 189, 248, 0.28)');
              g.addColorStop(1, 'rgba(56, 189, 248, 0.00)');
              return g;
            },
            fill: true,
            tension: 0.4,
            pointBackgroundColor: '#38bdf8',
            pointBorderColor: '#ffffff',
            pointBorderWidth: 2,
            pointRadius: 5,
            pointHoverRadius: 7,
          },
          {
            label: 'Predicted Flow',
            data: [...monthlyData.slice(0, -1).map(() => null), monthlyData[monthlyData.length - 1], predictedAmount],
            borderColor: '#34d399',
            borderDash: [6, 4],
            backgroundColor: 'transparent',
            pointBackgroundColor: '#34d399',
            pointRadius: 6,
          }
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { labels: { color: legendColor(), boxWidth: 12, font: { weight: '600' } } },
          tooltip: {
            backgroundColor: 'rgba(10, 20, 44, 0.92)',
            borderColor: 'rgba(56, 189, 248, 0.3)',
            borderWidth: 1,
            cornerRadius: 10,
            callbacks: { label: ctx => ` ${CURRENCY}${Number(ctx.parsed.y).toFixed(2)}` },
          },
        },
        scales: {
          x: { grid: { color: gridColor() }, ticks: { color: tickColor() } },
          y: {
            grid: { color: gridColor() },
            ticks: { color: tickColor(), callback: v => `${CURRENCY}${v}` },
          },
        },
      },
    });
  }

  /* ── Re-render charts on theme change ───────────────────────────── */
  document.getElementById('themeToggle')?.addEventListener('click', () => {
    setTimeout(() => {
      if (Chart.instances) {
        Object.values(Chart.instances).forEach(c => {
          c.options.scales?.x && (c.options.scales.x.grid.color = gridColor());
          c.options.scales?.y && (c.options.scales.y.grid.color = gridColor());
          c.update();
        });
      }
    }, 100);
  });

});
