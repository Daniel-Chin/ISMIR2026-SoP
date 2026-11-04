// Session page controls. State lives in the URL: ?mode=highlight&roles=zoom-volunteer,room-volunteer
// The Mode/Roles panel drives both the Staffing list and the Runsheet.
(() => {
  const MODES = ['mastermind', 'highlight', 'filter'];
  const controls = document.getElementById('controls');
  const runsheetControls = document.getElementById('runsheet-controls');
  const modeSelect = document.getElementById('mode');
  const picker = document.getElementById('role-picker');
  const boxes = [...picker.querySelectorAll('input[type=checkbox]')];
  const rows = [...document.querySelectorAll('tr.job')];
  const chips = [...document.querySelectorAll('.role-chip')];
  const staff = [...document.querySelectorAll('.staff')];
  const status = document.getElementById('status');
  const staffingStatus = document.getElementById('staffing-status');
  const staffingTitle = document.getElementById('staffing-title');
  const ideas = [...document.querySelectorAll('article[data-idea]')];
  const ideaSources = [...document.querySelectorAll('[data-idea-source]')];
  const ideaTitle = document.getElementById('idea-title');
  const videos = [...document.querySelectorAll('[data-video]')];
  const staffingHeading = document.getElementById('staffing');

  function load(search) {
    const params = new URLSearchParams(search);
    const urlMode = params.get('mode');
    const urlRoles = new Set((params.get('roles') || '').split(',').filter(Boolean));
    modeSelect.value = MODES.includes(urlMode) ? urlMode : 'mastermind';
    boxes.forEach((b) => { b.checked = modeSelect.value === 'mastermind' || urlRoles.has(b.value); });
  }

  // Mastermind means every box ticked: keep the dropdown and the boxes consistent.
  function syncModeToBoxes() {
    if (boxes.every((b) => b.checked)) modeSelect.value = 'mastermind';
    else if (modeSelect.value === 'mastermind') modeSelect.value = 'filter';
  }

  let prevMode = null; // the mode the page last showed
  function apply() {
    const mode = modeSelect.value;
    prevMode = mode;
    const selected = new Set(boxes.filter((b) => b.checked).map((b) => b.value));
    document.body.dataset.mode = mode;

    let shown = 0;
    let hits = 0;
    rows.forEach((row) => {
      const hit = row.dataset.roles.split(' ').some((r) => selected.has(r));
      row.classList.toggle('hit', mode !== 'mastermind' && hit);
      row.hidden = mode === 'filter' && !hit;
      if (hit) hits++;
      if (!row.hidden) shown++;
    });
    chips.forEach((c) => c.classList.toggle('selected', mode !== 'mastermind' && selected.has(c.dataset.role)));
    // Staffing lists every role in mastermind, otherwise only the ticked ones.
    staff.forEach((s) => { s.hidden = mode !== 'mastermind' && !selected.has(s.dataset.role); });
    // The Idea: the AI-generated view for the one ticked role, if there is one; otherwise the full version.
    const only = mode !== 'mastermind' && selected.size === 1 ? [...selected][0] : '';
    const view = ideas.some((a) => a.dataset.idea === only) ? only : '';
    ideas.forEach((a) => { a.hidden = a.dataset.idea !== view; });
    videos.forEach((v) => { v.hidden = v.dataset.video !== only; });
    ideaSources.forEach((a) => { a.hidden = a.dataset.ideaSource !== view; });
    // A role's view already merges The Idea with its job description: retitle it, and drop Staffing.
    ideaTitle.textContent = view ? `For the ${boxes.find((b) => b.value === view).parentElement.textContent.trim()}` : 'The Idea';
    staffingHeading.hidden = !!view;
    if (view) staff.forEach((s) => { s.hidden = true; });

    const none = mode !== 'mastermind' && selected.size === 0;
    staffingStatus.textContent = none ? 'Tick at least one role.' : '';
    staffingStatus.hidden = !none;
    staffingTitle.textContent = mode === 'mastermind' ? 'Staffing' : 'Selected Roles';
    if (none) {
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
    if (mode !== 'mastermind') {
      query = `?mode=${mode}`;
      if (selected.size) query += `&roles=${[...selected].join(',')}`;
    }
    history.replaceState(null, '', location.pathname + query + location.hash);
  }

  // Opening on a role's anchor in Staffing: make sure that role is shown.
  function revealTarget() {
    const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (target && target.classList.contains('staff') && target.hidden) {
      const box = boxes.find((b) => b.value === target.dataset.role);
      if (box) box.checked = true;
      syncModeToBoxes();
      apply();
    }
    target?.scrollIntoView();
  }

  // Links to this same page with a view (role chips, mentions, Staffing headings) switch the view in place.
  document.addEventListener('click', (e) => {
    const a = e.target.closest('a[href]');
    if (!a || e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const url = new URL(a.href, location.href);
    if (url.origin !== location.origin || url.pathname !== location.pathname || !url.search) return;
    e.preventDefault();
    load(url.search);
    history.replaceState(null, '', location.pathname + location.search + url.hash);
    apply();
    revealTarget();
  });

  // Entering mastermind ticks every box; leaving it via the dropdown starts from none.
  modeSelect.addEventListener('change', () => {
    if (modeSelect.value === 'mastermind') boxes.forEach((b) => { b.checked = true; });
    else if (prevMode === 'mastermind') boxes.forEach((b) => { b.checked = false; });
    apply();
  });
  boxes.forEach((b) => b.addEventListener('change', () => { syncModeToBoxes(); apply(); }));
  load(location.search);
  controls.hidden = false;
  runsheetControls.hidden = false;
  apply();
  // Showing the controls and filtering rows shifts the layout after the browser's own jump to the hash.
  revealTarget();
})();
