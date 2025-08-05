// loading.js - Exibe overlay de loading em submits e AJAX globais


// Cria overlay quando DOM estiver pronto
window.addEventListener('DOMContentLoaded', function() {
  if (!document.getElementById('global-loading-overlay')) {
    const overlay = document.createElement('div');
    overlay.id = 'global-loading-overlay';
    overlay.innerHTML = '<div id="global-loading-spinner"></div>';
    document.body.appendChild(overlay);
  }
});

function showLoading() {
  var overlay = document.getElementById('global-loading-overlay');
  if (overlay) overlay.classList.add('active');
}
function hideLoading() {
  var overlay = document.getElementById('global-loading-overlay');
  if (overlay) overlay.classList.remove('active');
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
  // Elementos com data-loading
  document.querySelectorAll('[data-loading]').forEach(function(el) {
    el.addEventListener('click', function() {
      showLoading();
    });
  });

  // Links <a> que redirecionam (exceto download e #)
  document.querySelectorAll('a[href]:not([href^="#"]):not([download])').forEach(function(link) {
    link.addEventListener('click', function(e) {
      // Só mostra se for link normal (não abrir em nova aba)
      if (!link.target || link.target === '_self') {
        showLoading();
      }
    });
  });

  // Botões que usam window.location.href no onclick
  document.querySelectorAll('button[onclick]').forEach(function(btn) {
    var onclick = btn.getAttribute('onclick');
    if (onclick && onclick.includes('window.location.href')) {
      btn.addEventListener('click', function() {
        showLoading();
      });
    }
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
