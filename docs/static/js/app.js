const form = document.getElementById('analyze-form');
const resultsEl = document.getElementById('results');
const statusEl = document.getElementById('status');
const savedJobsEl = document.getElementById('saved-jobs');
let gapChart;

// 构建 API 基础 URL
// 如果定义了 window.API_BASE_URL（来自 config.js），使用该地址
// 否则使用相对路径（适合同源部署）
const API_BASE_URL = window.API_BASE_URL || '';
const ANALYZE_ENDPOINT = `${API_BASE_URL}/api/analyze`;

function getSavedJobs() {
  return JSON.parse(localStorage.getItem('savedJobs') || '[]');
}

function saveJob(job) {
  const saved = getSavedJobs();
  if (!saved.find((j) => j.id === job.id)) {
    saved.push(job);
    localStorage.setItem('savedJobs', JSON.stringify(saved));
  }
  renderSavedJobs();
}

function removeJob(jobId) {
  const saved = getSavedJobs();
  const filtered = saved.filter((j) => j.id !== jobId);
  localStorage.setItem('savedJobs', JSON.stringify(filtered));
  renderSavedJobs();
}

function renderSavedJobs() {
  const saved = getSavedJobs();
  if (!saved.length) {
    savedJobsEl.innerHTML = '<p>No saved jobs yet.</p>';
    return;
  }
  savedJobsEl.innerHTML = saved.map((job) => `
    <article class="job">
      <h3><a href="${job.redirect_url || '#'}" target="_blank" rel="noreferrer">${job.title}</a></h3>
      <div class="meta">${job.company} · ${job.location}</div>
      <button class="remove-job" data-job-id="${job.id}">Remove</button>
    </article>
  `).join('');

  savedJobsEl.querySelectorAll('.remove-job').forEach((btn) => {
    btn.addEventListener('click', () => removeJob(btn.dataset.jobId));
  });
}

function renderGapChart(gaps) {
  const ctx = document.getElementById('gapChart');
  if (gapChart) gapChart.destroy();
  gapChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: gaps.map((g) => g.skill),
      datasets: [{ label: 'Missing skill frequency', data: gaps.map((g) => g.count), backgroundColor: '#6366f1' }],
    },
    options: { responsive: true, plugins: { legend: { display: false } } },
  });
}

function renderResults(jobs) {
  if (!jobs.length) {
    resultsEl.innerHTML = '<p>No strict title matches found.</p>';
    return;
  }
  resultsEl.innerHTML = jobs.map((entry) => {
    const j = entry.job;
    const salary = j.salary_min || j.salary_max ? `$${(j.salary_min || 0).toLocaleString()} - $${(j.salary_max || 0).toLocaleString()}` : 'Not listed';
    return `<article class="job">
      <h3>${j.title}</h3>
      <div class="meta">${j.company} · ${j.location} · Salary: ${salary}</div>
      <p><strong>Fit score:</strong> ${entry.fit_score}/100 · <strong>Sponsorship:</strong> ${entry.sponsorship_classification}</p>
      <p>${entry.explanation}</p>
      <div class="tags">${entry.matched_strengths.map((s) => `<span class="tag">${s}</span>`).join('')}</div>
      <div class="tags">${entry.missing_skills.map((s) => `<span class="tag miss">Missing: ${s}</span>`).join('')}</div>
      <button data-save='${JSON.stringify(j)}'>Save job</button>
      <a href="${j.redirect_url}" target="_blank" rel="noreferrer">Original posting</a>
    </article>`;
  }).join('');

  resultsEl.querySelectorAll('button[data-save]').forEach((btn) => {
    btn.addEventListener('click', () => saveJob(JSON.parse(btn.dataset.save)));
  });
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = 'Analyzing...';
  resultsEl.innerHTML = '';
  const formData = new FormData(form);
  try {
    const resp = await fetch(ANALYZE_ENDPOINT, { method: 'POST', body: formData });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'Unknown backend error');
    if (data.message) statusEl.textContent = data.message;
    else statusEl.textContent = `Analyzed ${data.jobs.length} jobs.`;
    renderResults(data.jobs);
    renderGapChart(data.skill_gap_summary || []);
  } catch (err) {
    statusEl.textContent = `Error: ${err.message}`;
  }
});

renderSavedJobs();
