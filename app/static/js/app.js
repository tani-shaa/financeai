/* ═══════════════════════════════════════════════════════════════════════════
   FinanceAI — app.js  (global interactions)
═══════════════════════════════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ── Theme Toggle ──────────────────────────────────────────────────── */
  const html      = document.documentElement;
  const themeBtn  = document.getElementById('themeToggle');
  const themeIcon = document.getElementById('themeIcon');

  // v2 key — old 'financeai-theme' key is ignored, fresh default is dark
  const THEME_KEY = 'financeai-theme-v2';
  const savedTheme = localStorage.getItem(THEME_KEY) || 'dark';
  applyTheme(savedTheme);

  if (themeBtn) {
    themeBtn.addEventListener('click', () => {
      const next = html.dataset.theme === 'dark' ? 'light' : 'dark';
      applyTheme(next);
      localStorage.setItem(THEME_KEY, next);
    });
  }

  function applyTheme(theme) {
    html.dataset.theme = theme;
    if (themeIcon) {
      themeIcon.textContent = theme === 'dark' ? 'light_mode' : 'dark_mode';
    }
  }

  /* ── Sidebar Toggle (mobile) ───────────────────────────────────────── */
  const sidebar     = document.getElementById('sidebar');
  const toggleBtn   = document.getElementById('sidebarToggle');
  let   overlay     = document.querySelector('.sidebar-overlay');

  if (!overlay) {
    overlay = document.createElement('div');
    overlay.className = 'sidebar-overlay';
    document.body.appendChild(overlay);
  }

  function openSidebar() {
    sidebar?.classList.add('open');
    overlay.classList.add('show');
    document.body.style.overflow = 'hidden';
  }

  function closeSidebar() {
    sidebar?.classList.remove('open');
    overlay.classList.remove('show');
    document.body.style.overflow = '';
  }

  toggleBtn?.addEventListener('click', () => {
    if (sidebar?.classList.contains('open')) closeSidebar();
    else openSidebar();
  });

  overlay.addEventListener('click', closeSidebar);

  /* ── Auto-dismiss flash alerts ─────────────────────────────────────── */
  document.querySelectorAll('.alert:not(.alert-permanent)').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s ease, max-height 0.5s ease';
      el.style.opacity = '0';
      el.style.maxHeight = '0';
      setTimeout(() => el.remove(), 500);
    }, 4000);
  });

  /* ── Animate stat cards on scroll ─────────────────────────────────── */
  const observer = new IntersectionObserver(
    entries => entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.animation = 'slideUp 0.4s ease both';
        observer.unobserve(e.target);
      }
    }),
    { threshold: 0.1 }
  );

  document.querySelectorAll('.stat-card, .card-glass, .insight-card').forEach(el => {
    observer.observe(el);
  });

  /* ── Active nav highlight (fallback) ──────────────────────────────── */
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-item').forEach(link => {
    if (link.getAttribute('href') === currentPath) {
      link.classList.add('active');
    }
  });

});

/* ── Password toggle (accessible globally) ──────────────────────────── */
function togglePassword(fieldId) {
  const field = document.getElementById(fieldId);
  if (!field) return;
  const btn  = field.closest('.input-icon-wrap')?.querySelector('.toggle-pw .material-icons');
  if (field.type === 'password') {
    field.type = 'text';
    if (btn) btn.textContent = 'visibility_off';
  } else {
    field.type = 'password';
    if (btn) btn.textContent = 'visibility';
  }
}

/* ── Format currency ─────────────────────────────────────────────────── */
function formatCurrency(amount, symbol = '$') {
  return `${symbol}${parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
}
