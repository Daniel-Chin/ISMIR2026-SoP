// Runsheet controls. State lives in the URL: ?mode=highlight&roles=zoom-volunteer,room-volunteer
(() => {
  const MODES = ['totality', 'highlight', 'filter'];
  const controls = document.getElementById('controls');
  const modeSelect = document.getElementById('mode');
  const picker = document.getElementById('role-picker');
  const boxes = [...picker.querySelectorAll('input[type=checkbox]')];
  const rows = [...document.querySelectorAll('tr.job')];
  const chips = [...document.querySelectorAll('.role-chip')];
  const roleDescs = [...document.querySelectorAll('.role-desc')];
  const status = document.getElementById('status');
  const expandAll = document.getElementById('expand-all');

  const params = new URLSearchParams(location.search);
  const urlMode = params.get('mode');
  const urlRoles = new Set((params.get('roles') || '').split(',').filter(Boolean));
  modeSelect.value = MODES.includes(urlMode) ? urlMode : 'totality';
  boxes.forEach((b) => { b.checked = urlRoles.has(b.value); });

  function apply() {
    const mode = modeSelect.value;
    const selected = new Set(boxes.filter((b) => b.checked).map((b) => b.value));
    document.body.dataset.mode = mode;
    picker.hidden = mode === 'totality';

    let shown = 0;
    let hits = 0;
    rows.forEach((row) => {
      const hit = row.dataset.roles.split(' ').some((r) => selected.has(r));
      row.classList.toggle('hit', mode !== 'totality' && hit);
      row.hidden = mode === 'filter' && !hit;
      if (hit) hits++;
      if (!row.hidden) shown++;
    });
    chips.forEach((c) => c.classList.toggle('selected', mode !== 'totality' && selected.has(c.dataset.role)));
    // Exactly one role ticked: show its job description above the table.
    const only = mode !== 'totality' && selected.size === 1 ? [...selected][0] : null;
    roleDescs.forEach((d) => { d.hidden = d.dataset.role !== only; });

    if (mode !== 'totality' && selected.size === 0) {
      status.textContent = 'Tick at least one role.';
    } else if (mode === 'filter') {
      status.textContent = `Showing ${shown} of ${rows.length} jobs.`;
    } else if (mode === 'highlight') {
      status.textContent = `${hits} of ${rows.length} jobs highlighted.`;
    } else {
      status.textContent = '';
    }

    // Slugs are URL-safe, so build the query by hand to keep the commas readable.
    let query = '';
    if (mode !== 'totality' || selected.size) {
      query = `?mode=${mode}`;
      if (selected.size) query += `&roles=${[...selected].join(',')}`;
    }
    history.replaceState(null, '', location.pathname + query + location.hash);
  }

  const details = [...document.querySelectorAll('tr.job details')];
  function syncExpandLabel() {
    expandAll.textContent = details.length && details.every((d) => d.open) ? 'Collapse all' : 'Expand all';
  }
  expandAll.hidden = details.length === 0;
  expandAll.addEventListener('click', () => {
    const open = !details.every((d) => d.open);
    details.forEach((d) => { d.open = open; });
    syncExpandLabel();
  });
  details.forEach((d) => d.addEventListener('toggle', syncExpandLabel));

  modeSelect.addEventListener('change', apply);
  boxes.forEach((b) => b.addEventListener('change', apply));
  controls.hidden = false;
  apply();
})();
