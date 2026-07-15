let repos = window.__INITIAL_REPOS__ || [];
let activeFilter = 'all';

const esc = value => String(value ?? '').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'",'&#039;');

function toast(message, error=false){const el=document.getElementById('toast');el.textContent=message;el.classList.remove('hidden');el.classList.toggle('error',error);setTimeout(()=>el.classList.add('hidden'),3400)}
async function api(url, options={}){const r=await fetch(url,{headers:{'Content-Type':'application/json'},...options});const d=await r.json().catch(()=>({}));if(!r.ok)throw new Error(d.detail||'Actie mislukt');return d}
function modal(title, content){document.getElementById('modalTitle').textContent=title;document.getElementById('modalContent').textContent=typeof content==='string'?content:JSON.stringify(content,null,2);document.getElementById('modal').showModal()}
function closeModal(){document.getElementById('modal').close()}
function formatDate(value){if(!value)return 'Nog onbekend';const date=new Date(value);return Number.isNaN(date.getTime())?value:date.toLocaleString('nl-NL',{dateStyle:'medium',timeStyle:'short'})}

function pills(repo){const list=[];
  if(repo.is_new) list.push('<span class="pill pill-new"><i>✦</i>NIEUW</span>');
  if(repo.has_update) list.push(`<span class="pill pill-update"><i>↻</i>NIEUWE UPDATE · ${repo.behind}</span>`);
  if(repo.is_running) list.push('<span class="pill pill-running"><i>●</i>DRAAIT</span>');
  if(repo.is_live) list.push('<span class="pill pill-live"><i>◆</i>LIVE</span>');
  if(repo.is_private) list.push('<span class="pill pill-private"><i>⌁</i>PRIVÉ</span>');
  if(repo.git_status==='local-changes') list.push('<span class="pill pill-warning"><i>!</i>LOKALE CHANGES</span>');
  if(repo.deploy_ready&&!repo.is_live) list.push('<span class="pill pill-ready"><i>✓</i>PUBLICATIE KLAAR</span>');
  return list.join('');
}
function matches(repo){if(activeFilter==='new')return repo.is_new;if(activeFilter==='update')return repo.has_update;if(activeFilter==='running')return repo.is_running;if(activeFilter==='live')return repo.is_live;return true}
function updateStats(){document.getElementById('statProjects').textContent=repos.length;document.getElementById('statNew').textContent=repos.filter(r=>r.is_new).length;document.getElementById('statUpdates').textContent=repos.filter(r=>r.has_update).length;document.getElementById('statLive').textContent=repos.filter(r=>r.is_live).length}

function renderRepos(){const grid=document.getElementById('repoGrid');const visible=repos.filter(matches);if(!visible.length){grid.innerHTML='<article class="panel empty">Geen projecten binnen dit filter.</article>';updateStats();return}
 grid.innerHTML=visible.map(repo=>`<article class="panel repo-card ${repo.is_new?'highlight':''}">
  <div class="repo-top"><div class="icon-tile">${esc((repo.name||'?').slice(0,2).toUpperCase())}</div><div class="repo-title"><div class="pill-row">${pills(repo)}</div><h3>${esc(repo.name)}</h3><p>${esc(repo.description||'Nog geen beschrijving. Zodra code en manifest zijn toegevoegd verschijnt hier automatisch de projectsamenvatting.')}</p></div></div>
  <div class="preview">${repo.preview_url?`<img src="${esc(repo.preview_url)}" alt="Preview ${esc(repo.name)}">`:`<div class="preview-placeholder"><svg viewBox="0 0 120 80" aria-hidden="true"><rect x="8" y="10" width="104" height="60" rx="10"/><path d="M24 55l18-17 14 12 16-21 24 26"/><circle cx="38" cy="29" r="6"/></svg><span>${repo.is_new?'Nieuwe repo — nog niet lokaal':'Geen preview in turbo-project.json'}</span></div>`}</div>
  <div class="info-grid"><div><span>Versie</span><strong>${esc(repo.version||'-')}</strong></div><div><span>Bijgewerkt</span><strong>${esc(formatDate(repo.updated_at))}</strong></div><div><span>Data</span><strong>${esc(repo.data_mode||'none')}</strong></div><div><span>Hosting</span><strong>${esc(repo.deployment_provider||'niet gekozen')}</strong></div></div>
  ${repo.changelog_summary?`<div class="change-note"><span>Laatste wijziging</span>${esc(repo.changelog_summary)}</div>`:''}
  <div class="tag-row">${(repo.tags||[]).map(t=>`<span>${esc(t)}</span>`).join('')}${repo.integrations?.home_assistant?'<span>Home Assistant</span>':''}${repo.integrations?.mqtt?'<span>MQTT</span>':''}</div>
  <div class="actions"><button class="btn primary small" onclick="syncRepo('${esc(repo.slug)}')">${repo.is_new?'Clone':'Update'}</button><button class="btn secondary small" onclick="startRepo('${esc(repo.slug)}')">Start</button><button class="btn secondary small" onclick="openApp('${esc(repo.health_url)}')">Open</button><button class="btn ghost small" onclick="testRepo('${esc(repo.slug)}')">Tests</button><button class="btn ghost small" onclick="openVSCode('${esc(repo.slug)}')">VS Code</button><button class="btn publish small" onclick="publishPlan('${esc(repo.slug)}')">Publiceer</button></div>
  <div class="card-foot"><a href="${esc(repo.repo_url)}" target="_blank" rel="noopener">GitHub</a><button onclick="openFolder('${esc(repo.slug)}')">Map openen</button><span>${esc(repo.git_status)}</span></div>
 </article>`).join('');updateStats()}

async function refreshRepos(){const d=await api('/api/repos');repos=d.repos;document.getElementById('repoRoot').value=d.repo_root;renderRepos()}
async function loadGitHub(auto=true){const s=await api('/api/github/status');document.getElementById('installGhButton').classList.toggle('hidden',s.cli_installed);document.getElementById('loginGhButton').classList.toggle('hidden',s.authenticated||!s.cli_installed);document.getElementById('importGhButton').classList.toggle('hidden',!s.authenticated);document.getElementById('githubTitle').textContent=s.authenticated?`Ingelogd als ${s.username}`:s.cli_installed?'GitHub koppelen':'GitHub CLI installeren';document.getElementById('githubMessage').textContent=s.authenticated?'Alle openbare en privé-repo’s worden automatisch bijgehouden.':'Login veilig via de officiële GitHub CLI.';if(s.authenticated&&auto)await importGitHubRepos(true)}
async function importGitHubRepos(silent=false){try{const d=await api('/api/github/import',{method:'POST'});repos=d.repos;renderRepos();if(!silent)toast(`${d.found} repo’s gevonden · ${d.imported} nieuw`)}catch(e){if(!silent)toast(e.message,true)}}
async function installGitHubCli(){await api('/api/github/install',{method:'POST'});toast('Installatievenster geopend. Start de launcher daarna opnieuw.')}
async function loginGitHub(){await api('/api/github/login',{method:'POST'});toast('Rond de browserlogin af en klik daarna op Alles verversen.')}
async function refreshEverything(){try{await loadGitHub(true);await refreshRepos();toast('Dashboard volledig ververst')}catch(e){toast(e.message,true)}}
async function addRepo(){const input=document.getElementById('repoUrl');if(!input.value.trim())return toast('Vul een GitHub URL in',true);try{await api('/api/repos',{method:'POST',body:JSON.stringify({repo_url:input.value.trim()})});input.value='';await refreshRepos();toast('Nieuwe repo toegevoegd')}catch(e){toast(e.message,true)}}
async function saveRepoRoot(){try{await api('/api/settings/repo-root',{method:'POST',body:JSON.stringify({repo_root:document.getElementById('repoRoot').value.trim()})});await refreshRepos();toast('Projectmap opgeslagen')}catch(e){toast(e.message,true)}}
async function action(slug,name,message){try{await api(`/api/repos/${slug}/${name}`,{method:'POST'});await refreshRepos();toast(message)}catch(e){toast(e.message,true)}}
const syncRepo=slug=>action(slug,'sync','Repo bijgewerkt');const startRepo=slug=>action(slug,'start','Project gestart');const openFolder=slug=>action(slug,'open-folder','Map geopend');const openVSCode=slug=>action(slug,'open-vscode','VS Code geopend');
async function testRepo(slug){try{const d=await api(`/api/repos/${slug}/test`,{method:'POST'});modal(d.ok?'Tests geslaagd ✅':'Tests mislukt ❌',d.output||'Geen uitvoer');await refreshRepos()}catch(e){toast(e.message,true)}}
async function publishPlan(slug){try{const d=await api(`/api/repos/${slug}/publish-plan`);modal(d.ready?'Publicatiecheck geslaagd 🚀':'Nog niet publiceerbaar',d)}catch(e){toast(e.message,true)}}
function openApp(url){if(!url)return toast('Geen lokale URL ingesteld',true);window.open(url.replace(/\/health\/?$/,''),'_blank','noopener')}

document.querySelectorAll('.filter').forEach(btn=>btn.addEventListener('click',()=>{document.querySelectorAll('.filter').forEach(b=>b.classList.remove('active'));btn.classList.add('active');activeFilter=btn.dataset.filter;renderRepos()}));
renderRepos();loadGitHub(true).catch(e=>toast(e.message,true));
