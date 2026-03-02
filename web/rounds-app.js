// Rounds Prep — Web Demo

let currentRoundsCase = null;
let roundsTypingTimer = null;
let examApplied = false;

// --- Load a rounds case ---
async function loadRoundsCase(caseName) {
  // Update button states
  document.querySelectorAll('.case-btn').forEach(btn => btn.classList.remove('active'));
  document.querySelector(`[data-case="${caseName}"]`).classList.add('active');

  // Stop any in-progress typing
  if (roundsTypingTimer) clearTimeout(roundsTypingTimer);

  // Fetch case data
  const resp = await fetch(`rounds-cases/${caseName}.json`);
  currentRoundsCase = await resp.json();

  // Reset exam state
  examApplied = false;
  const examInput = document.getElementById('exam-input');
  if (examInput) examInput.value = '';

  // Show demo area
  document.getElementById('demo').style.display = 'block';

  // Render chart
  renderRoundsChart(currentRoundsCase.chart);

  // Reset and start agent output
  resetRoundsStages();
  showRoundsStage('alerts_dayplan');
  typeRoundsStage('alerts_dayplan', currentRoundsCase.stages.alerts_dayplan);

  // Scroll to demo
  document.getElementById('demo').scrollIntoView({ behavior: 'smooth', block: 'start' });
}


// --- Render the EHR chart panel ---
function renderRoundsChart(chart) {
  const el = document.getElementById('chart-content');
  const p = chart.patient;
  const enc = chart.encounter;

  let html = '';

  // Patient header
  html += section('Demographics', `
    ${row('Name', p.name)}
    ${row('MRN', p.mrn)}
    ${row('DOB', p.dob + (p.age ? ' (Age ' + p.age + ')' : ''))}
    ${row('Sex', p.gender)}
    ${row('Location', enc.location)}
    ${enc.service ? row('Service', enc.service + (enc.attending ? ' — ' + enc.attending : '')) : ''}
    ${p.admit_date ? row('Admitted', p.admit_date + (p.hospital_day ? ' (HD' + p.hospital_day + ')' : '')) : ''}
    ${p.code_status ? row('Code Status', p.code_status) : ''}
    ${row('Reason', enc.reason)}
  `);

  // Allergies
  html += section('Allergies', list(chart.allergies));

  // Problem list
  html += section('Problems', list(chart.conditions));

  // Vitals
  html += section('Vitals', list(chart.vitals));

  // Labs
  const labHtml = chart.labs.map(lab => {
    const abnormal = isAbnormal(lab);
    return `<li class="${abnormal ? 'abnormal' : ''}" style="${abnormal ? 'color: #f85149; font-weight: 600;' : ''}">${lab}</li>`;
  }).join('');
  html += section('Labs', `<ul class="chart-list">${labHtml}</ul>`);

  // Home meds
  html += section('Home Medications', list(chart.medications.home));

  // Current orders
  html += section('Current Orders', list(chart.medications.inpatient));

  // Imaging
  if (chart.imaging && chart.imaging.length > 0) {
    chart.imaging.forEach(img => {
      html += section('Imaging', `
        <div style="margin-bottom: 0.25rem; font-weight: 600; color: var(--text);">[${img.status.toUpperCase()}] ${img.study}</div>
        <div class="chart-note">${img.findings}</div>
      `);
    });
  }

  // Notes
  if (chart.notes && chart.notes.length > 0) {
    chart.notes.forEach(note => {
      html += section(note.type, `<div class="chart-note">${note.text}</div>`);
    });
  }

  // Yesterday's plan
  if (chart.yesterday_plan) {
    html += section("Yesterday's Plan", `<div class="chart-note">${chart.yesterday_plan}</div>`);
  }

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
    /WBC:\s*(1[4-9]|[2-9]\d)/,       // WBC > 14
    /Lactate:\s*([2-9]|[1-9]\d)/,     // Lactate > 2
    /Creatinine:\s*(1\.[3-9]|[2-9])/, // Cr > 1.3
    /pH:\s*7\.[0-3][0-3]/,            // pH < 7.34
    /Potassium:\s*(5\.[1-9]|[6-9])/,  // K > 5.0
    /BUN:\s*([3-9]\d|[1-9]\d\d)/,     // BUN > 30
    /CO2:\s*(1[0-9]|[0-9])\s/,        // CO2 < 20
    /HCO3:\s*(1[0-8]|[0-9])\s/,       // HCO3 < 19
    /INR:\s*(1\.[3-9]|[2-9])/,        // INR > 1.3
    /Hemoglobin:\s*([0-9]|1[01])\./,   // Hgb < 12
    /Hemoglobin:\s*9\.\d/,             // Hgb 9.x
    /aPTT:\s*(8[0-9]|9\d|\d{3})/,     // aPTT > 80 (supratherapeutic)
  ];
  return abnormals.some(re => re.test(labString));
}


// --- Agent output tabs & typing ---
function resetRoundsStages() {
  ['alerts_dayplan', 'presentation', 'am_brief'].forEach(stage => {
    document.getElementById(`stage-${stage}`).innerHTML = '';
  });

  document.querySelectorAll('.stage-tab').forEach(tab => {
    tab.classList.remove('completed');
    tab.classList.remove('active');
  });
  document.querySelector('[data-stage="alerts_dayplan"]').classList.add('active');
}

function showRoundsStage(stage) {
  document.querySelectorAll('.stage-content').forEach(el => el.style.display = 'none');
  const target = document.getElementById(`stage-${stage}`);
  target.style.display = 'block';
  target.style.animation = 'none';
  target.offsetHeight;
  target.style.animation = '';

  document.querySelectorAll('.stage-tab').forEach(tab => tab.classList.remove('active'));
  document.querySelector(`[data-stage="${stage}"]`).classList.add('active');
}

function typeRoundsStage(stageName, text) {
  const el = document.getElementById(`stage-${stageName}`);
  const rendered = markdownToHtml(text);
  const chars = rendered;
  let i = 0;
  const speed = 3;

  el.innerHTML = '';
  el.classList.add('typing-cursor');

  function type() {
    if (i < chars.length) {
      el.innerHTML = chars.substring(0, i + 5);
      i += 5;
      roundsTypingTimer = setTimeout(type, speed);
    } else {
      el.innerHTML = chars;
      el.classList.remove('typing-cursor');

      // Wrap h2 sections into collapsible cards
      makeCollapsible(el, stageName);

      // Mark tab as completed and auto-advance
      document.querySelector(`[data-stage="${stageName}"]`).classList.add('completed');

      const stages = ['alerts_dayplan', 'presentation', 'am_brief'];
      const nextIdx = stages.indexOf(stageName) + 1;
      if (nextIdx < stages.length && currentRoundsCase) {
        const nextStage = stages[nextIdx];
        setTimeout(() => {
          showRoundsStage(nextStage);
          typeRoundsStage(nextStage, currentRoundsCase.stages[nextStage]);
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
    header.innerHTML = `<span class="collapsible-chevron">\u25B6</span><span class="collapsible-title">${title}</span>`;
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
  if (t.includes('CRITICAL') || t.includes('ALERT')) return 'red-flag';
  if (t.includes('DAY PLAN') || t.includes('PLAN')) return 'plan-section';
  if (t.includes('OVERNIGHT')) return 'gaps';
  if (t.includes('YESTERDAY')) return 'gaps';
  if (t.includes('KEY CONTEXT')) return 'imaging';
  if (t.includes('CURRENT STATUS')) return 'assessment';
  return '';
}


// --- Update with exam findings ---
function updateWithExam() {
  const examInput = document.getElementById('exam-input');
  const examText = examInput.value.trim();
  if (!examText) return;

  // Replace [PENDING] placeholders in all stage content
  const pendingPatterns = [
    /\[PENDING\s*—\s*bedside exam findings\]/gi,
    /\[PENDING\s*—\s*bedside exam,?\s*check port sites\]/gi,
    /\[PENDING\s*—\s*abdominal exam is the key thing this morning\]/gi,
    /\[PENDING\s*—\s*bedside exam\]/gi,
    /\[PENDING\s*—\s*verify on exam\]/gi,
    /\[PENDING[^\]]*\]/gi,
  ];

  const stageIds = ['stage-alerts_dayplan', 'stage-presentation', 'stage-am_brief'];
  stageIds.forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      let html = el.innerHTML;
      pendingPatterns.forEach(pattern => {
        html = html.replace(pattern, `<span class="exam-inserted">${escapeHtml(examText)}</span>`);
      });
      el.innerHTML = html;
    }
  });

  // Visual feedback
  examApplied = true;
  const btn = document.querySelector('.btn-update-exam');
  btn.textContent = 'Exam Applied \u2713';
  btn.style.background = 'var(--green)';
  btn.style.borderColor = 'var(--green)';
  setTimeout(() => {
    btn.textContent = 'Update with Exam \u2192';
    btn.style.background = '';
    btn.style.borderColor = '';
  }, 2000);
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML;
}


// --- Simple markdown to HTML ---
function markdownToHtml(md) {
  let html = md;

  // Headers
  html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

  // Bold
  html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Italic
  html = html.replace(/(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');

  // Unordered lists
  html = html.replace(/^- \[ \] (.+)$/gm, '<li>\u2610 $1</li>');
  html = html.replace(/^- \[x\] (.+)$/gm, '<li>\u2611 $1</li>');
  html = html.replace(/^- (.+)$/gm, '<li>$1</li>');

  // Wrap consecutive <li> in <ul>
  html = html.replace(/((?:<li>.*<\/li>\n?)+)/g, '<ul>$1</ul>');

  // Numbered lists
  html = html.replace(/^\d+\. (.+)$/gm, '<li>$1</li>');

  // Paragraphs (double newline)
  html = html.replace(/\n\n/g, '</p><p>');
  html = '<p>' + html + '</p>';

  // Clean up empty paragraphs
  html = html.replace(/<p>\s*<\/p>/g, '');
  html = html.replace(/<p>\s*(<[hul])/g, '$1');
  html = html.replace(/(<\/[hul].*?>)\s*<\/p>/g, '$1');

  // Horizontal rules
  html = html.replace(/<p>---<\/p>/g, '<hr>');
  html = html.replace(/^---$/gm, '<hr>');

  return html;
}
