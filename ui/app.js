const $ = s => document.querySelector(s);
const $$ = s => [...document.querySelectorAll(s)];
const api = () => window.pywebview.api;
const state = { root: null, out: null, selections: {} };

function toast(msg, ms = 2600) {
  const t = $("#toast"); t.textContent = msg; t.hidden = false;
  clearTimeout(t._h); t._h = setTimeout(() => t.hidden = true, ms);
}

/* ---------- onglets ---------- */
$$(".tab").forEach(b => b.onclick = () => {
  $$(".tab").forEach(x => x.classList.remove("active"));
  $$(".panel").forEach(x => x.classList.remove("active"));
  b.classList.add("active");
  $("#" + b.dataset.tab).classList.add("active");
});

/* ---------- init ---------- */
window.addEventListener("pywebviewready", init);
async function init() {
  const s = await api().get_settings();
  $("#seuil").value = s.seuil; $("#seuilVal").textContent = (+s.seuil).toFixed(2);
  $("#d_inc").value = s.dossier_inconnus;
  $("#d_sv").value = s.dossier_sans_visage;
  $("#d_err").value = s.dossier_erreurs;
  $("#heic").checked = !!s.heic;
  $("#gpu").checked = !!s.gpu;
  $$('input[name=mode]').forEach(r => r.checked = (r.value === s.mode));
  await refreshPeople();
}

/* ---------- personnes ---------- */
async function refreshPeople() {
  const people = await api().get_people();
  const box = $("#people"); box.innerHTML = "";
  $("#peopleEmpty").style.display = people.length ? "none" : "block";
  for (const p of people) {
    const c = document.createElement("div"); c.className = "pcard";
    const img = p.thumb ? `<img src="${p.thumb}">` : `<div class="ph"></div>`;
    c.innerHTML = `${img}<div class="nm">${esc(p.name)}</div>
      <div class="ct">${p.count} photo(s) de référence</div>
      <button class="del">Supprimer</button>`;
    c.querySelector(".del").onclick = async () => {
      if (confirm(`Supprimer ${p.name} ?`)) { await api().remove_person(p.name); refreshPeople(); }
    };
    box.appendChild(c);
  }
}

$("#addPerson").onclick = () => {
  state.selections = {};
  $("#personName").value = "";
  $("#faces").innerHTML = "";
  $("#modal").hidden = false;
  setTimeout(() => $("#personName").focus(), 50);
};

$("#pickPhotos").onclick = async () => {
  const paths = await api().pick_images();
  if (!paths || !paths.length) return;
  const note = document.createElement("div");
  note.className = "hint"; note.textContent = "Détection des visages…";
  $("#faces").appendChild(note);
  const res = await api().detect_in_files(paths);
  note.remove();
  renderFacePicker(res);
};

function renderFacePicker(res) {
  const box = $("#faces");
  for (const item of res) {
    const g = document.createElement("div"); g.className = "photoGroup";
    g.innerHTML = `<div class="fname">${esc(item.path)}</div>`;
    if (item.error) { g.innerHTML += `<div class="noface">Erreur : ${esc(item.error)}</div>`; box.appendChild(g); continue; }
    if (!item.n) { g.innerHTML += `<div class="noface">Aucun visage détecté.</div>`; box.appendChild(g); continue; }
    const row = document.createElement("div"); row.className = "faceRow";
    item.faces.forEach(f => {
      const im = document.createElement("img");
      im.className = "facePick"; im.src = f.crop;
      const key = item.path + "#" + f.idx;
      if (item.n === 1) { im.classList.add("sel"); state.selections[key] = { path: item.path, idx: f.idx }; }
      im.onclick = () => {
        // un seul visage retenu par photo
        [...row.children].forEach(c => { c.classList.remove("sel"); delete state.selections[item.path + "#" + c.dataset.idx]; });
        im.classList.add("sel"); state.selections[key] = { path: item.path, idx: f.idx };
      };
      im.dataset.idx = f.idx;
      row.appendChild(im);
    });
    g.appendChild(row); box.appendChild(g);
  }
}

function closeModal() { $("#modal").hidden = true; }
$("#modalClose").onclick = closeModal;
$("#modalCancel").onclick = closeModal;
$("#modalSave").onclick = async () => {
  const name = $("#personName").value.trim();
  if (!name) { toast("Indique d'abord un prénom."); $("#personName").focus(); return; }
  const sels = Object.values(state.selections);
  if (!sels.length) { toast("Choisis des photos et sélectionne au moins un visage."); return; }
  const r = await api().enroll(name, sels);
  if (r.error) { toast(r.error); return; }
  closeModal(); toast(`${name} enregistré(e).`); refreshPeople();
};

/* ---------- source & paramètres ---------- */
$("#pickRoot").onclick = async () => {
  const d = await api().pick_folder(); if (!d) return;
  state.root = d; $("#root").value = d;
  if (!$("#out").value) { state.out = d + "/Photos classées"; $("#out").value = state.out; }
  $("#count").textContent = "Comptage…";
  const r = await api().count_images(d);
  $("#count").textContent = r.error ? ("Erreur : " + r.error) : (r.count + " image(s) trouvée(s).");
};
$("#pickOut").onclick = async () => {
  const d = await api().pick_folder(); if (!d) return;
  state.out = d; $("#out").value = d;
};
$("#out").onchange = e => state.out = e.target.value;

$("#seuil").oninput = e => $("#seuilVal").textContent = (+e.target.value).toFixed(2);
function saveSettings() {
  api().set_settings({
    seuil: parseFloat($("#seuil").value),
    mode: ($$('input[name=mode]').find(r => r.checked) || {}).value || "copier",
    dossier_inconnus: $("#d_inc").value.trim() || "Inconnus",
    dossier_sans_visage: $("#d_sv").value.trim() || "Sans visage",
    dossier_erreurs: $("#d_err").value.trim() || "Erreurs",
    heic: $("#heic").checked, gpu: $("#gpu").checked,
  });
}
["#seuil", "#d_inc", "#d_sv", "#d_err", "#heic", "#gpu"].forEach(s => $(s).addEventListener("change", saveSettings));
$$('input[name=mode]').forEach(r => r.addEventListener("change", saveSettings));

/* ---------- aperçu / classement ---------- */
function showProg(txt) { $("#prog").hidden = false; $("#progTxt").textContent = txt; $("#barFill").style.width = "0%"; }
function hideProg() { $("#prog").hidden = true; }
function updateProg(p) {
  const pct = p.total ? Math.round(100 * p.done / p.total) : 0;
  $("#barFill").style.width = pct + "%";
  $("#progTxt").textContent = `${p.done}/${p.total}` + (p.current ? ` — ${p.current}` : "");
}
function poll(onU) {
  return new Promise(res => {
    const id = setInterval(async () => {
      const p = await api().get_progress();
      onU(p);
      if (p.done_flag) { clearInterval(id); res(p); }
    }, 300);
  });
}

$("#cancel").onclick = () => api().cancel_job();

$("#apercu").onclick = async () => {
  if (!state.root) { toast("Choisis d'abord le dossier source (onglet Source)."); return; }
  $("#dist").innerHTML = ""; $("#report").innerHTML = ""; $("#lancer").hidden = true;
  $("#cancel").hidden = false; showProg("Analyse des visages…");
  await api().start_analyze(state.root);
  const p = await poll(updateProg);
  hideProg(); $("#cancel").hidden = true;
  if (p.error) { toast("Erreur : " + p.error); return; }
  renderDist(p.counts || {});
  $("#lancer").hidden = false;
};

$("#lancer").onclick = async () => {
  if (!state.out) { toast("Indique un dossier de sortie."); return; }
  $("#cancel").hidden = false; showProg("Classement en cours…");
  await api().start_execute(state.out);
  const p = await poll(updateProg);
  hideProg(); $("#cancel").hidden = true;
  if (p.error) { toast("Erreur : " + p.error); return; }
  $("#report").innerHTML = `<div class="empty" style="border-style:solid">
    ${p.moved} fichier(s) classé(s) dans <b>${esc(state.out)}</b>.</div>`;
  toast("Classement terminé.");
};

function renderDist(counts) {
  const keys = Object.keys(counts).sort((a, b) => counts[b] - counts[a]);
  if (!keys.length) { $("#dist").innerHTML = `<div class="empty">Aucune image.</div>`; return; }
  let rows = keys.map(k => `<tr><td>${tagFor(k)}</td><td class="num">${counts[k]}</td></tr>`).join("");
  $("#dist").innerHTML = `<h2 style="margin-top:18px">Aperçu de la répartition</h2>
    <table><thead><tr><th>Dossier de destination</th><th class="num">Photos</th></tr></thead>
    <tbody>${rows}</tbody></table>
    <p class="hint">Rien n'a encore été copié. Clique « Lancer le classement » pour valider.</p>`;
}
function tagFor(name) {
  const s = state, set = window._settings || {};
  if (name === $("#d_inc").value) return `<span class="tag inc">${esc(name)}</span>`;
  if (name === $("#d_sv").value) return `<span class="tag sv">${esc(name)}</span>`;
  if (name === $("#d_err").value) return `<span class="tag err">${esc(name)}</span>`;
  if (name.includes("_") || name.startsWith("Groupe_")) return `${esc(name)} <span class="tag">groupe</span>`;
  return esc(name);
}

function esc(s) { return (s ?? "").toString().replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
