// Surgical Consult Agent — Web Demo

let currentCase = null;
let typingTimer = null;
let currentNoteView = 'summary';
let fullNoteHtml = '';

// --- Load a demo case ---
async function loadCase(caseName) {
  // Update button states
  document.querySelectorAll('.case-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelector(`[data-case="${caseName}"]`).classList.add('active');

  // Stop any in-progress typing
  if (typingTimer) clearTimeout(typingTimer);

  try {
    const resp = await fetch(`cases/${caseName}.json`);
    if (!resp.ok) throw new Error('Failed to load case');
    currentCase = await resp.json();

    // Show consult banner
    const banner = document.getElementById('consult-banner');
    banner.style.display = 'flex';
    document.getElementById('consult-message').textContent = currentCase.consult_message;

    // Show demo area
    document.getElementById('demo').style.display = 'block';

    // Render chart
    renderChart(currentCase.chart, currentCase.chart_text);
    renderKeyFindings(currentCase.key_findings);

    // Show resident input — populate textarea if it exists, otherwise fall back to static text
    const resSection = document.getElementById('resident-section');
    resSection.style.display = 'block';
    const inputField = document.getElementById('resident-input-field');
    const inputText = document.getElementById('resident-text');
    if (inputField) {
      inputField.value = currentCase.resident_input || '';
    } else if (inputText) {
      inputText.textContent = currentCase.resident_input;
    }

    // Reset and start agent output
    resetStages();
    showStage('triage');
    typeStage('triage', currentCase.stages.triage);

    // Scroll to demo
    banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    console.error('Error loading case:', error);
    alert('Error loading case. Please try again.');
  }
}


// --- Key Findings Banner ---
function renderKeyFindings(kf) {
  const el = document.getElementById('key-findings-banner');
  if (!kf) {
    el.style.display = 'none';
    return;
  }
  el.style.display = 'flex';
  el.innerHTML = `
    <span class="kf-acuity ${kf.acuity_color}">${kf.acuity}</span>
    <span class="kf-divider"></span>
    <span class="kf-vitals">${kf.vitals_summary}</span>
    <span class="kf-divider"></span>
    <span class="kf-impression">${kf.impression}</span>
  `;
}


// --- Render the EHR chart panel ---
function renderChart(chart, chartText) {
  const el = document.getElementById('chart-content');
  const p = chart.patient;
  const enc = chart.encounter;

  let html = '';

  html += section('Patient', `
    ${row('Name', p.name)}
    ${row('MRN', p.mrn)}
    ${row('DOB', p.dob)}
    ${row('Sex', p.gender)}
    ${row('Location', enc.location)}
  `);

  html += section('Allergies', list(chart.allergies));
  html += section('Problem List', list(chart.conditions));
  html += section('Vitals', list(chart.vitals));

  const labHtml = chart.labs.map(lab => {
    const abnormal = isAbnormal(lab);
    return `<li class="${abnormal ? 'abnormal' : ''}" style="${abnormal ? 'color: #f85149; font-weight: 600;' : ''}">${lab}</li>`;
  }).join('');
  html += section('Labs', `<ul class="chart-list">${labHtml}</ul>`);

  html += section('Home Medications', list(chart.medications.home));
  html += section('Current Orders', list(chart.medications.inpatient));

  chart.imaging.forEach(img => {
    html += section('Imaging', `
      <div style="margin-bottom: 0.25rem; font-weight: 600; color: var(--text);">[${img.status.toUpperCase()}] ${img.study}</div>
      <div class="chart-note">${img.findings}</div>
    `);
  });

  chart.notes.forEach(note => {
    html += section(note.type, `<div class="chart-note">${note.text}</div>`);
  });

  el.innerHTML = html;
}

function section(title, content) {
  return `<div class="chart-section">
    <div class="chart-section-header">${title}</div>
    ${content}
  </div>`;
}

function row(label, value) {
  return `<div class="chart-row">
    <span class="chart-label">${label}</span>
    <span class="chart-value">${value}</span>
  </div>`;
}

function list(items) {
  if (!items || items.length === 0) return '<span style="color: var(--text-dim)">None</span>';
  return `<ul class="chart-list">${items.map(i => `<li>${i}</li>`).join('')}</ul>`;
}

function isAbnormal(labString) {
  const abnormals = [
    /WBC:\s*(1[5-9]|[2-9]\d)/,
    /Lactate:\s*([3-9]|[1-9]\d)/,
    /Creatinine:\s*(1\.[5-9]|[2-9])/,
    /pH:\s*7\.[012]/,
    /Potassium:\s*(5\.[2-9]|[6-9])/,
    /BUN:\s*([3-9]\d|[1-9]\d\d)/,
    /CO2:\s*(1[0-8]|[0-9])\s/,
    /HCO3:\s*(1[0-8]|[0-9])\s/,
    /INR:\s*(1\.[4-9]|[2-9])/,
    /Hemoglobin:\s*([0-9]|1[01])\./
  ];
  return abnormals.some(re => re.test(labString));
}


// --- Agent output tabs & typing ---
function resetStages() {
  ['triage', 'context', 'plan'].forEach(stage => {
    document.getElementById(`stage-${stage}`).innerHTML = '';
  });
  const noteContent = document.getElementById('note-content');
  if (noteContent) noteContent.innerHTML = '';
  const noteToggle = document.getElementById('note-view-toggle');
  if (noteToggle) noteToggle.style.display = 'none';

  currentNoteView = 'summary';
  fullNoteHtml = '';
  document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.dataset.view === 'summary') btn.classList.add('active');
  });

  document.querySelectorAll('.stage-tab').forEach(tab => {
    tab.classList.remove('completed');
    tab.classList.remove('active');
  });
  document.querySelector('[data-stage="triage"]').classList.add('active');
}

function showStage(stage) {
  document.querySelectorAll('.stage-content').forEach(el => el.style.display = 'none');
  const target = document.getElementById(`stage-${stage}`);
  target.style.display = 'block';
  target.style.animation = 'none';
  target.offsetHeight; // force reflow
  target.style.animation = '';

  document.querySelectorAll('.stage-tab').forEach(tab => tab.classList.remove('active'));
  document.querySelector(`[data-stage="${stage}"]`).classList.add('active');
}

function typeStage(stageName, text) {
  const isNote = stageName === 'note';
  const el = isNote ? document.getElementById('note-content') : document.getElementById(`stage-${stageName}`);
  const rendered = markdownToHtml(text, stageName);
  const chars = rendered;
  let i = 0;
  const speed = 3; // ms per character

  el.innerHTML = '';
  el.classList.add('typing-cursor');

  function type() {
    if (i < chars.length) {
      el.innerHTML = chars.substring(0, i + 5);
      i += 5;
      typingTimer = setTimeout(type, speed);
    } else {
      el.innerHTML = chars;
      el.classList.remove('typing-cursor');

      if (!isNote) {
        makeCollapsible(el, stageName);
      }

      if (isNote) {
        fullNoteHtml = chars;
        const noteToggle = document.getElementById('note-view-toggle');
        noteToggle.style.display = 'flex';
        currentNoteView = 'summary';
        document.querySelectorAll('.toggle-btn').forEach(btn => {
          btn.classList.remove('active');
          if (btn.dataset.view === 'summary') btn.classList.add('active');
        });
        applyNoteView();
      }

      // Mark tab as completed and auto-advance
      document.querySelector(`[data-stage="${stageName}"]`).classList.add('completed');

      const stages = ['triage', 'context', 'plan', 'note'];
      const nextIdx = stages.indexOf(stageName) + 1;
      if (nextIdx < stages.length && currentCase) {
        const nextStage = stages[nextIdx];
        setTimeout(() => {
          showStage(nextStage);
          typeStage(nextStage, currentCase.stages[nextStage]);
        }, 800);
      }
    }
  }

  type();
}


// --- Collapsible sections ---
function makeCollapsible(container, stageName) {
  const h2s = container.querySelectorAll('h2');
  if (h2s.length === 0) return;

  const sections = [];
  h2s.forEach((h2, idx) => {
    const title = h2.textContent;
    const contentNodes = [];
    let sibling = h2.nextElementSibling;
    while (sibling && sibling.tagName !== 'H2') {
      contentNodes.push(sibling);
      sibling = sibling.nextElementSibling;
    }

    const colorClass = getSectionColorClass(title);
    const isFirst = idx === 0;

    const wrapper = document.createElement('div');
    wrapper.className = `collapsible-section${isFirst ? ' open' : ''}`;

    const header = document.createElement('div');
    header.className = `collapsible-header ${colorClass}`;
    header.innerHTML = `<span class="collapsible-chevron">▶</span><span class="collapsible-title">${title}</span>`;
    header.addEventListener('click', () => {
      wrapper.classList.toggle('open');
    });

    const body = document.createElement('div');
    body.className = 'collapsible-body';
    contentNodes.forEach(node => body.appendChild(node));

    wrapper.appendChild(header);
    wrapper.appendChild(body);
    sections.push({ h2, wrapper });
  });

  container.innerHTML = '';
  sections.forEach(s => container.appendChild(s.wrapper));
}

function getSectionColorClass(title) {
  const t = title.toUpperCase();
  if (t.includes('RED FLAG')) return 'red-flag';
  if (t.includes('TRIAGE')) return 'assessment';
  if (t.includes('ASSESSMENT')) return 'assessment';
  if (t.includes('IMAGING') || t.includes('KEY IMAGING')) return 'imaging';
  if (t.includes('GAP') || t.includes('MISSING') || t.includes('CURRENT MANAGEMENT')) return 'gaps';
  if (t.includes('PLAN') || t.includes('RECOMMEND') || t.includes('WORKUP') || t.includes('GUIDELINE') || t.includes('ADDITIONAL')) return 'plan-section';
  return '';
}


// --- Note view toggle ---
function toggleNoteView(view) {
  currentNoteView = view;
  document.querySelectorAll('.toggle-btn').forEach(btn => {
    btn.classList.toggle('active', btn.dataset.view === view);
  });
  applyNoteView();
}

function applyNoteView() {
  const el = document.getElementById('note-content');
  if (currentNoteView === 'summary') {
    el.innerHTML = extractNoteSummary(fullNoteHtml);
  } else {
    el.innerHTML = fullNoteHtml;
  }
}

function extractNoteSummary(html) {
  const container = document.createElement('div');
  container.innerHTML = html;

  const allElements = Array.from(container.children);
  let summaryHtml = '';
  let capturing = false;

  for (const el of allElements) {
    const text = el.textContent.toUpperCase();

    if (el.tagName === 'H2' && (text.includes('ASSESSMENT') || text.includes('STAFFING'))) {
      capturing = true;
      summaryHtml += el.outerHTML;
      continue;
    }

    if (el.tagName === 'H2' && capturing) {
      if (!text.includes('ASSESSMENT') && !text.includes('STAFFING') && !text.includes('PLAN')) {
        capturing = false;
        summaryHtml += '<hr>';
        continue;
      }
      summaryHtml += el.outerHTML;
      continue;
    }

    if (el.tagName === 'HR' && capturing) {
      summaryHtml += el.outerHTML;
      continue;
    }

    if (capturing) {
      summaryHtml += el.outerHTML;
    }
  }

  return summaryHtml || fullNoteHtml;
}


// --- Simple markdown to HTML ---
function markdownToHtml(md, stageName) {
  let html = md;

  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

  html = html.replace(/^- \[ \] (.+)$/gm, '<li>☐ $1</li>');
  html = html.replace(/^- \[x\] (.+)$/gm, '<li>☑ $1</li>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');

  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';

  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p>\s*(<[hul])/g, '$1');
  html = html.replace(/(<\/[hul].*?>)\s*<\/p>/g, '$1');

  html = html.replace(/<p>---<\/p>/g, '<hr>');
  html = html.replace(/^---$/gm, '<hr>');

  // Emoji acuity colors
  html = html.replace(/\uD83D\uDD34/g, '<span style="color: #f85149;">\uD83D\uDD34</span>');
  html = html.replace(/\uD83D\uDFE1/g, '<span style="color: #d29922;">\uD83D\uDFE1</span>');
  html = html.replace(/\uD83D\uDFE2/g, '<span style="color: #3fb950;">\uD83D\uDFE2</span>');

  return html;
}
