// loading.js - Exibe overlay de loading em submits e AJAX globais

// Cria overlay se não existir
if (!document.getElementById('global-loading-overlay')) {
  const overlay = document.createElement('div');
  overlay.id = 'global-loading-overlay';
  overlay.innerHTML = '<div id="global-loading-spinner"></div>';
  document.body.appendChild(overlay);
}

function showLoading() {
  document.getElementById('global-loading-overlay').classList.add('active');
}
function hideLoading() {
  document.getElementById('global-loading-overlay').classList.remove('active');
}

// Ativa loading em todos os formulários
window.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('form').forEach(function(form) {
    form.addEventListener('submit', function() {
      showLoading();
    });
  });
});

// Ativa loading em todos os links e botões com data-loading
window.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('[data-loading]').forEach(function(el) {
    el.addEventListener('click', function() {
      showLoading();
    });
  });
});

// Intercepta AJAX (fetch)
(function() {
  const origFetch = window.fetch;
  window.fetch = function() {
    showLoading();
    return origFetch.apply(this, arguments)
      .finally(hideLoading);
  };
})();

// Intercepta AJAX (XMLHttpRequest)
(function() {
  const origOpen = XMLHttpRequest.prototype.open;
  XMLHttpRequest.prototype.open = function() {
    this.addEventListener('loadend', hideLoading);
    showLoading();
    return origOpen.apply(this, arguments);
  };
})();
