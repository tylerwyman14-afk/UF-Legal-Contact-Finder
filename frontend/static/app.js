const ORG_TYPE_LABELS = {
  law_firm: "Law Firm Leadership",
  in_house: "In-House Counsel",
  judiciary_government: "Judiciary / Government",
};

const searchInput = document.getElementById("search");
const orgTypeSelect = document.getElementById("filter-org-type");
const practiceAreaSelect = document.getElementById("filter-practice-area");
const stateSelect = document.getElementById("filter-state");
const resultsEl = document.getElementById("results");
const resultsCountEl = document.getElementById("results-count");
const exportBtn = document.getElementById("export-btn");

let debounceTimer = null;

function currentFilters() {
  const params = new URLSearchParams();
  if (searchInput.value.trim()) params.set("q", searchInput.value.trim());
  if (orgTypeSelect.value) params.set("org_type", orgTypeSelect.value);
  if (practiceAreaSelect.value) params.set("practice_area", practiceAreaSelect.value);
  if (stateSelect.value) params.set("state", stateSelect.value);
  return params;
}

async function loadFilters() {
  const res = await fetch("/api/meta/filters");
  const data = await res.json();

  for (const val of data.org_type) {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = ORG_TYPE_LABELS[val] || val;
    orgTypeSelect.appendChild(opt);
  }
  for (const val of data.practice_area) {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = val;
    practiceAreaSelect.appendChild(opt);
  }
  for (const val of data.state) {
    const opt = document.createElement("option");
    opt.value = val;
    opt.textContent = val;
    stateSelect.appendChild(opt);
  }
}

function copyToClipboard(text, btn) {
  navigator.clipboard.writeText(text).then(() => {
    const original = btn.textContent;
    btn.textContent = "Copied!";
    setTimeout(() => (btn.textContent = original), 1200);
  });
}

function renderCard(p) {
  const card = document.createElement("div");
  card.className = "card";

  const contactRow = document.createElement("div");
  contactRow.className = "contact-row";

  if (p.email) {
    const a = document.createElement("a");
    a.href = `mailto:${p.email}`;
    a.textContent = "Email";
    contactRow.appendChild(a);

    const copyBtn = document.createElement("button");
    copyBtn.textContent = "Copy email";
    copyBtn.onclick = () => copyToClipboard(p.email, copyBtn);
    contactRow.appendChild(copyBtn);
  }
  if (p.phone) {
    const a = document.createElement("a");
    a.href = `tel:${p.phone}`;
    a.textContent = p.phone;
    contactRow.appendChild(a);
  }
  if (p.contact_form_url) {
    const a = document.createElement("a");
    a.href = p.contact_form_url;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "Contact form";
    contactRow.appendChild(a);
  }
  if (p.linkedin_url) {
    const a = document.createElement("a");
    a.href = p.linkedin_url;
    a.target = "_blank";
    a.rel = "noopener";
    a.textContent = "LinkedIn";
    contactRow.appendChild(a);
  }

  const locationBits = [p.city, p.state].filter(Boolean).join(", ");
  const ufBits = [p.uf_degree, p.uf_grad_year].filter(Boolean).join(" • ");

  card.innerHTML = `
    <span class="tag">${ORG_TYPE_LABELS[p.org_type] || p.org_type}</span>
    ${p.practice_area ? `<span class="tag">${p.practice_area}</span>` : ""}
    <h3>${p.full_name}</h3>
    <div class="title">${p.title}</div>
    <div class="org">${p.organization}</div>
    <div class="meta">
      ${locationBits ? locationBits + "<br/>" : ""}
      ${ufBits ? "UF: " + ufBits : ""}
    </div>
  `;
  card.appendChild(contactRow);

  const source = document.createElement("div");
  source.className = "source";
  source.innerHTML = `Source: <a href="${p.source_url}" target="_blank" rel="noopener">${p.source_note || "verify"}</a> &mdash; verified ${p.date_verified}`;
  card.appendChild(source);

  return card;
}

async function search() {
  const params = currentFilters();
  const res = await fetch(`/api/people?${params.toString()}`);
  const people = await res.json();

  resultsEl.innerHTML = "";
  if (people.length === 0) {
    resultsEl.innerHTML = '<div class="empty-state">No matches yet. Try adjusting filters, or the database may not be seeded yet.</div>';
    resultsCountEl.textContent = "";
    return;
  }
  resultsCountEl.textContent = `${people.length} result${people.length === 1 ? "" : "s"}`;
  for (const p of people) {
    resultsEl.appendChild(renderCard(p));
  }
}

function debouncedSearch() {
  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(search, 250);
}

searchInput.addEventListener("input", debouncedSearch);
orgTypeSelect.addEventListener("change", search);
practiceAreaSelect.addEventListener("change", search);
stateSelect.addEventListener("change", search);

exportBtn.addEventListener("click", () => {
  const params = currentFilters();
  window.location.href = `/api/people/export.csv?${params.toString()}`;
});

loadFilters().then(search);
