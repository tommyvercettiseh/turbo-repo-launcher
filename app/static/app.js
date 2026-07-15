let repos = window.__INITIAL_REPOS__ || [];

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;');
}

function showToast(message, error = false) {
  const toast = document.getElementById('toast');
  toast.textContent = message;
  toast.style.borderColor = error ? 'rgba(255,105,130,.45)' : 'rgba(111,157,255,.4)';
  toast.classList.remove('hidden');
  window.setTimeout(() => toast.classList.add('hidden'), 3400);
}

async function api(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail || 'Actie mislukt');
  return data;
}

function statusClass(status) {
  return `chip ${String(status || 'unknown').replaceAll(' ', '-').toLowerCase()}`;
}

function updateStats() {
  document.getElementById('statProjects').textContent = repos.length;
  document.getElementById('statRunning').textContent = repos.filter(repo => repo.is_running).length;
  document.getElementById('statChanges').textContent = repos.filter(repo => repo.git_status === 'local-changes').length;
}

function renderRepos() {
  const grid = document.getElementById('repoGrid');
  if (!repos.length) {
    grid.innerHTML = '<article class="panel repo-card"><div class="preview-empty">Nog geen projecten toegevoegd. Plak hierboven je eerste GitHub URL 🚀</div></article>';
    updateStats();
    return;
  }

  grid.innerHTML = repos.map(repo => `
    <article class="panel repo-card">
      <div class="repo-head">
        <div>
          <h3 class="repo-name">${escapeHtml(repo.name)}</h3>
          <p class="repo-desc">${escapeHtml(repo.description || 'Nog geen projectbeschrijving beschikbaar.')}</p>
        </div>
        <div>
          <span class="${statusClass(repo.git_status)}">${escapeHtml(repo.git_status)}</span>
          ${repo.is_running ? '<span class="chip running">draait</span>' : ''}
        </div>
      </div>
      <div class="preview">
        ${repo.preview_url ? `<img src="${escapeHtml(repo.preview_url)}" alt="Preview ${escapeHtml(repo.name)}">` : '<div class="preview-empty">Synchroniseer de repo om de preview te laden</div>'}
      </div>
      <div class="meta">
        <div class="meta-box"><strong>Versie</strong><span>${escapeHtml(repo.version || '-')}</span></div>
        <div class="meta-box"><strong>Poort</strong><span>${escapeHtml(repo.default_port || '-')}</span></div>
        <div class="meta-box"><strong>Startscript</strong><span>${escapeHtml(repo.start_command || '-')}</span></div>
        <div class="meta-box"><strong>Lokaal pad</strong><span>${escapeHtml(repo.local_path)}</span></div>
      </div>
      <a class="repo-url" href="${escapeHtml(repo.repo_url)}" target="_blank" rel="noopener">${escapeHtml(repo.repo_url)}</a>
      <div class="actions">
        <button class="btn primary small" onclick="syncRepo('${escapeHtml(repo.slug)}')">Sync</button>
        <button class="btn secondary small" onclick="startRepo('${escapeHtml(repo.slug)}')">Start</button>
        <button class="btn secondary small" onclick="stopRepo('${escapeHtml(repo.slug)}')">Stop</button>
        <button class="btn ghost small" onclick="openFolder('${escapeHtml(repo.slug)}')">Map</button>
        <button class="btn ghost small" onclick="openVSCode('${escapeHtml(repo.slug)}')">VS Code</button>
        <button class="btn ghost small" onclick="openApp('${escapeHtml(repo.health_url)}')">Open app</button>
      </div>
    </article>
  `).join('');
  updateStats();
}

async function refreshRepos() {
  try {
    const data = await api('/api/repos');
    repos = data.repos;
    document.getElementById('repoRoot').value = data.repo_root;
    document.getElementById('statRoot').textContent = data.repo_root;
    renderRepos();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function addRepo() {
  const input = document.getElementById('repoUrl');
  const repoUrl = input.value.trim();
  if (!repoUrl) return showToast('Vul eerst een GitHub URL in', true);
  try {
    await api('/api/repos', { method: 'POST', body: JSON.stringify({ repo_url: repoUrl }) });
    input.value = '';
    showToast('Repo toegevoegd');
    await refreshRepos();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function saveRepoRoot() {
  const repoRoot = document.getElementById('repoRoot').value.trim();
  try {
    await api('/api/settings/repo-root', { method: 'POST', body: JSON.stringify({ repo_root: repoRoot }) });
    showToast('Projectmap opgeslagen');
    await refreshRepos();
  } catch (error) {
    showToast(error.message, true);
  }
}

async function action(slug, name, success) {
  try {
    await api(`/api/repos/${slug}/${name}`, { method: 'POST' });
    showToast(success);
    await refreshRepos();
  } catch (error) {
    showToast(error.message, true);
  }
}

function syncRepo(slug) { showToast('Repo synchroniseren...'); return action(slug, 'sync', 'Repo gesynchroniseerd'); }
function startRepo(slug) { return action(slug, 'start', 'Project gestart'); }
function stopRepo(slug) { return action(slug, 'stop', 'Project gestopt'); }
function openFolder(slug) { return action(slug, 'open-folder', 'Projectmap geopend'); }
function openVSCode(slug) { return action(slug, 'open-vscode', 'Visual Studio Code geopend'); }

function openApp(healthUrl) {
  if (!healthUrl) return showToast('Dit project heeft nog geen health URL', true);
  const url = healthUrl.replace(/\/health\/?$/, '');
  window.open(url, '_blank', 'noopener');
}

renderRepos();
