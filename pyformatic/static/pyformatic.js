function pyformaticValidateField(ev) {
  const el = ev.target;
  const form = el.closest('form');
  if (!form) {
    return;
  }
  const payload = { field: el.name, value: el.value };
  if (el.dataset.include) {
    payload.fields = {};
    el.dataset.include.split(',').forEach(name => {
      const other = form.querySelector(`[name="${name}"]`);
      if (other) {
        if (other.type === 'checkbox' || other.type === 'radio') {
          payload.fields[name] = other.checked ? other.value : '';
        } else {
          payload.fields[name] = other.value;
        }
      }
    });
  }
  fetch(form.action, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  }).then(r => r.json()).then(resp => {
    el.value = resp.value;
    const outer = el.closest('div');
    if (outer) {
      outer.classList.remove('info', 'warning', 'error', 'ok');
      if (resp.level) {
        outer.classList.add(resp.level);
      }
      const msg = outer.querySelector('.validation-msg');
      if (msg) {
        msg.textContent = resp.message || '';
        msg.className = 'validation-msg ' + (resp.level || '');
      }
    }
  });
}

function pyformaticInit() {
  document.querySelectorAll('form.pyformatic input').forEach(el => {
    if (el.type !== 'submit') {
      el.addEventListener('blur', pyformaticValidateField);
    }
  });
}

if (document.readyState !== 'loading') {
  pyformaticInit();
} else {
  document.addEventListener('DOMContentLoaded', pyformaticInit);
}
