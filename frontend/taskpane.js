const API_BASE_URL = window.location.origin;

let activeSelection = "";

// Robust initialization — works whether DOM is ready or still loading
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initApp);
} else {
  initApp();
}

function initApp() {
  try {
    setupTabs();
    setupEventListeners();
    const statusEl = document.getElementById("statusText");
    if (statusEl) {
      statusEl.textContent = "JS Ready";
    }
    console.log("[AI Writer] Initialized successfully");
  } catch (err) {
    console.error("[AI Writer] Init error:", err);
    const statusEl = document.getElementById("statusText");
    if (statusEl) {
      statusEl.textContent = "JS Error: " + err.message;
    }
  }
}

function getInputText() {
  const textarea = document.getElementById("inputText");
  const text = textarea.value.trim();
  if (!text) {
    showInfoBanner("Please enter or paste some text first.", true);
    return null;
  }
  activeSelection = text;
  return text;
}

async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    updateStatus("green", "Copied to clipboard");
    showInfoBanner("Text copied to clipboard!", false);
  } catch (err) {
    const textarea = document.createElement("textarea");
    textarea.value = text;
    textarea.style.position = "fixed";
    textarea.style.opacity = "0";
    document.body.appendChild(textarea);
    textarea.select();
    document.execCommand("copy");
    document.body.removeChild(textarea);
    updateStatus("green", "Copied to clipboard");
    showInfoBanner("Text copied to clipboard!", false);
  }
}

function buildStatCard(value, label) {
  const div = document.createElement("div");
  div.className = "stat-card";
  div.innerHTML = `<span class="stat-value">${value}</span><span class="stat-label">${label}</span>`;
  return div;
}

function setupTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabContents = document.querySelectorAll(".tab-content");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      tabButtons.forEach(b => b.classList.remove("active"));
      tabContents.forEach(c => c.classList.add("hidden"));
      btn.classList.add("active");
      const tabId = "tab-" + btn.getAttribute("data-tab");
      document.getElementById(tabId).classList.remove("hidden");
    });
  });
}

const STRENGTH_LABELS = {
  1: "1 - Light",
  2: "2 - Light-Moderate",
  3: "3 - Moderate",
  4: "4 - Strong",
  5: "5 - Maximum"
};

function setupEventListeners() {
  document.getElementById("btnClearInput").addEventListener("click", () => {
    document.getElementById("inputText").value = "";
    activeSelection = "";
    updateStatus("green", "Cleared");
  });

  const strengthSlider = document.getElementById("paraphraseStrength");
  const strengthValue = document.getElementById("paraphraseStrengthValue");
  if (strengthSlider) {
    strengthSlider.addEventListener("input", () => {
      strengthValue.textContent = STRENGTH_LABELS[strengthSlider.value] || `${strengthSlider.value} - Moderate`;
    });
  }

  const humanizeStrengthSlider = document.getElementById("humanizeStrength");
  const humanizeStrengthValue = document.getElementById("humanizeStrengthValue");
  if (humanizeStrengthSlider) {
    humanizeStrengthSlider.addEventListener("input", () => {
      humanizeStrengthValue.textContent = STRENGTH_LABELS[humanizeStrengthSlider.value] || `${humanizeStrengthSlider.value} - Moderate`;
    });
  }

  // ---- API Key Sync ----
  document.getElementById("btnSyncApiKey").addEventListener("click", async () => {
    const apiKey = document.getElementById("apiKeyInput").value.trim();
    if (!apiKey) {
      showInfoBanner("Please enter a Gemini API key first.", true);
      return;
    }
    updateStatus("orange", "Linking API key...");
    try {
      const response = await fetch(`${API_BASE_URL}/api/configure`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ provider: "gemini", api_key: apiKey })
      });
      if (!response.ok) throw new Error("Sync failed");
      const btn = document.getElementById("btnSyncApiKey");
      btn.textContent = "Synced";
      btn.classList.add("linked");
      updateStatus("green", "API key linked");
      showInfoBanner("Gemini API key linked successfully!", false);
    } catch (error) {
      updateStatus("red", "Link failed");
      showInfoBanner("Failed to link API key. Make sure the server is running.", true);
    }
  });

  // ---- 1. Paraphrase ----
  document.getElementById("btnRunParaphrase").addEventListener("click", async () => {
    console.log("[AI Writer] Paraphrase clicked");
    const text = getInputText();
    if (!text) return;
    const strength = parseInt(document.getElementById("paraphraseStrength").value, 10);
    const selectedMode = document.querySelector('input[name="paraphraseMode"]:checked').value;
    const apiEndpoint = selectedMode === "medical" ? `${API_BASE_URL}/api/paraphrase/medical` : `${API_BASE_URL}/api/paraphrase`;
    updateStatus("orange", "Paraphrasing...");
    hideInfoBanner();
    try {
      console.log("[AI Writer] Fetching:", apiEndpoint);
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, strength })
      });
      console.log("[AI Writer] Response status:", response.status);
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      console.log("[AI Writer] Data received:", data);
      const options = data.options;
      if (!options) throw new Error("No options in response");
      const acadEl = document.getElementById("para-academic-text");
      const concEl = document.getElementById("para-concise-text");
      const impEl = document.getElementById("para-impact-text");
      const resEl = document.getElementById("paraphraseResults");
      if (!acadEl || !concEl || !impEl || !resEl) throw new Error("DOM elements not found");
      acadEl.textContent = options.find(o => o.type === "Academic")?.text || "";
      concEl.textContent = options.find(o => o.type === "Concise")?.text || "";
      impEl.textContent = options.find(o => o.type === "High-Impact")?.text || "";
      resEl.classList.remove("hidden");
      console.log("[AI Writer] Results displayed");
      updateStatus("green", "Paraphrase complete");
    } catch (error) {
      console.error("[AI Writer] Paraphrase error:", error);
      updateStatus("red", "Paraphrase failed");
      showInfoBanner("Paraphrase failed: " + error.message, true);
    }
  });

  document.querySelectorAll("#paraphraseResults .btn-insert").forEach(btn => {
    btn.addEventListener("click", () => {
      const resultId = btn.getAttribute("data-result-id");
      const text = document.getElementById(resultId).textContent;
      if (text) copyToClipboard(text);
    });
  });

  // ---- 2. Humanize ----
  document.getElementById("btnRunHumanize").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;
    const selectedMode = document.querySelector('input[name="humanizeMode"]:checked').value;
    const strength = parseInt(document.getElementById("humanizeStrength").value) || 3;
    updateStatus("orange", "Humanizing...");
    hideInfoBanner();
    try {
      const response = await fetch(`${API_BASE_URL}/api/humanize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, mode: selectedMode, strength })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      document.getElementById("humanizedText").textContent = data.text;
      document.getElementById("humanizeResults").classList.remove("hidden");
      updateStatus("green", "Humanize complete");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Humanize failed");
      showInfoBanner("Cannot reach server. Make sure it's running (cd backend && python main.py) and access via http://localhost:8765 (not file://)", true);
    }
  });

  document.getElementById("btnCopyHumanize").addEventListener("click", () => {
    const text = document.getElementById("humanizedText").textContent;
    if (text) copyToClipboard(text);
  });

  // ---- 3. Proofread ----
  document.getElementById("btnRunProofread").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;
    updateStatus("orange", "Auditing document...");
    hideInfoBanner();
    document.getElementById("proofreadFixedContainer").classList.add("hidden");
    try {
      const response = await fetch(`${API_BASE_URL}/api/proofread`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, phase: "detection" })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      const issues = data.issues;
      const issuesList = document.getElementById("issuesList");
      issuesList.innerHTML = "";
      if (!issues || issues.length === 0) {
        issuesList.innerHTML = "<p class='placeholder-text'>No proofreading issues detected! Your manuscript meets high peer-review standards.</p>";
        document.getElementById("proofreadFooter").classList.add("hidden");
      } else {
        issues.forEach(issue => {
          const item = document.createElement("div");
          item.className = "issue-item";
          const category = issue.category || "General";
          const catLower = category.toLowerCase();
          item.innerHTML = `
            <input type="checkbox" class="issue-checkbox" data-id="${issue.id}" checked>
            <div class="issue-details">
              <div class="issue-meta">
                <span class="issue-id">[Issue #${issue.id}]</span>
                <span class="severity-badge ${(issue.severity || 'minor').toLowerCase()}">${issue.severity || 'MINOR'}</span>
                <span class="category-badge ${catLower}">${category}</span>
                <span class="issue-location">${issue.location || ''}</span>
              </div>
              <div class="issue-diagnosis">${issue.diagnosis || ''}</div>
              <div class="issue-why"><strong>Consequence:</strong> ${issue.why_matters || ''}</div>
              <div class="issue-fix"><strong>Actionable Fix:</strong> ${issue.actionable_fix || ''}</div>
            </div>
          `;
          issuesList.appendChild(item);
        });
        document.getElementById("proofreadFooter").classList.remove("hidden");
      }
      document.getElementById("proofreadResults").classList.remove("hidden");
      updateStatus("green", "Audit complete");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Audit failed");
      showInfoBanner("Cannot reach server. Make sure it's running (cd backend && python main.py) and access via http://localhost:8765 (not file://)", true);
    }
  });

  document.getElementById("btnApplyFixes").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;
    const checkedCheckboxes = document.querySelectorAll(".issue-checkbox:checked");
    const approvedIds = Array.from(checkedCheckboxes).map(cb => parseInt(cb.getAttribute("data-id")));
    if (approvedIds.length === 0) {
      showInfoBanner("Please select at least one issue fix to apply.", true);
      return;
    }
    updateStatus("orange", "Applying approved fixes...");
    hideInfoBanner();
    try {
      const response = await fetch(`${API_BASE_URL}/api/proofread`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, phase: "fix", approved_ids: approvedIds })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      document.getElementById("proofreadFixedText").textContent = data.text;
      document.getElementById("proofreadResults").classList.add("hidden");
      document.getElementById("proofreadFixedContainer").classList.remove("hidden");
      updateStatus("green", "Fixes generated");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Fix application failed");
      showInfoBanner("Cannot reach server. Make sure it's running (cd backend && python main.py) and access via http://localhost:8765 (not file://)", true);
    }
  });

  document.getElementById("btnCopyProofreadFix").addEventListener("click", () => {
    const text = document.getElementById("proofreadFixedText").textContent;
    if (text) copyToClipboard(text);
  });

  document.getElementById("btnBackToIssues").addEventListener("click", () => {
    document.getElementById("proofreadFixedContainer").classList.add("hidden");
    document.getElementById("proofreadResults").classList.remove("hidden");
  });

  // ---- 4. Manuscript Review ----
  document.getElementById("btnRunReview").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;
    updateStatus("orange", "Reviewing manuscript...");
    hideInfoBanner();
    try {
      const response = await fetch(`${API_BASE_URL}/api/manuscript-review`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, strength: 3 })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      document.getElementById("reviewAcademicScore").textContent = data.academic_score || "0.00";

      const statsContainer = document.getElementById("reviewStats");
      statsContainer.innerHTML = "";
      if (data.stats) {
        statsContainer.appendChild(buildStatCard(data.stats.word_count, "Words"));
        statsContainer.appendChild(buildStatCard(data.stats.sentence_count, "Sentences"));
        statsContainer.appendChild(buildStatCard(data.stats.avg_sentence_length, "Avg Sent. Length"));
        statsContainer.appendChild(buildStatCard(data.stats.char_count, "Characters"));
      }

      let scoreDesc = "Low academic vocabulary density.";
      const score = data.academic_score || 0;
      if (score >= 0.5) scoreDesc = "Moderate academic vocabulary density.";
      if (score >= 0.7) scoreDesc = "High academic vocabulary density — strong scholarly writing.";
      document.getElementById("reviewScoreDetail").textContent = scoreDesc;

      const issuesList = document.getElementById("reviewIssuesList");
      issuesList.innerHTML = "";
      if (data.issues && data.issues.length > 0) {
        issuesList.innerHTML = "<div class='result-title' style='margin-bottom: 6px;'>Detected Issues</div>";
        data.issues.slice(0, 5).forEach(issue => {
          const item = document.createElement("div");
          item.className = "issue-item";
          item.innerHTML = `<div class="issue-details">
            <div class="issue-meta">
              <span class="severity-badge ${(issue.severity || 'minor').toLowerCase()}">${issue.severity || 'MINOR'}</span>
              <span class="issue-diagnosis">${issue.diagnosis || ''}</span>
            </div>
          </div>`;
          issuesList.appendChild(item);
        });
      }

      document.getElementById("reviewResults").classList.remove("hidden");
      updateStatus("green", "Review complete");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Review failed");
      showInfoBanner("Review failed. Is the server running?", true);
    }
  });

  // ---- 5. Write Paper ----
  document.getElementById("btnRunWrite").addEventListener("click", async () => {
    const topic = document.getElementById("paperTopic").value.trim();
    if (!topic) {
      showInfoBanner("Please enter a paper topic.", true);
      return;
    }
    const outlineText = document.getElementById("paperOutline").value.trim();
    const sections = outlineText ? outlineText.split("\n").filter(s => s.trim()).map(s => s.trim()) : null;
    updateStatus("orange", "Generating paper...");
    hideInfoBanner();
    try {
      const response = await fetch(`${API_BASE_URL}/api/write-paper`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic, sections, style: "academic" })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      const options = data.options;
      const texts = options ? options.map(o => o.text).filter(t => t) : [];
      document.getElementById("writeResultText").textContent = texts.join("\n\n---\n\n") || data.text || "No content generated.";
      document.getElementById("writeResults").classList.remove("hidden");
      updateStatus("green", "Paper generated");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Generation failed");
      showInfoBanner("Paper generation failed. Is the server running?", true);
    }
  });

  document.getElementById("btnCopyWriteResult").addEventListener("click", () => {
    const text = document.getElementById("writeResultText").textContent;
    if (text) copyToClipboard(text);
  });

  // ---- 6. Vocab Analysis ----
  document.getElementById("btnRunVocab").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;
    updateStatus("orange", "Analyzing vocabulary...");
    hideInfoBanner();
    try {
      const response = await fetch(`${API_BASE_URL}/api/vocab-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, strength: 3 })
      });
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      const data = await response.json();
      document.getElementById("vocabAcademicScore").textContent = data.academic_score || "0.00";

      const statsContainer = document.getElementById("vocabStats");
      statsContainer.innerHTML = "";
      if (data.stats) {
        statsContainer.appendChild(buildStatCard(data.stats.word_count, "Total Words"));
        statsContainer.appendChild(buildStatCard(data.stats.unique_words, "Unique Words"));
        statsContainer.appendChild(buildStatCard(data.stats.lexical_diversity + "%", "Lexical Diversity"));
        statsContainer.appendChild(buildStatCard(data.stats.avg_word_length, "Avg Word Length"));
        statsContainer.appendChild(buildStatCard(data.stats.long_words, "Long Words (>6)"));
        statsContainer.appendChild(buildStatCard(data.stats.sentence_count, "Sentences"));
      }

      let scoreDesc = "Low academic vocabulary density.";
      const score = data.academic_score || 0;
      if (score >= 0.5) scoreDesc = "Moderate academic vocabulary density — some scholarly terms detected.";
      if (score >= 0.7) scoreDesc = "High academic vocabulary density — strong scholarly writing.";
      if (score >= 0.9) scoreDesc = "Very high academic vocabulary density — excellent scholarly register.";
      document.getElementById("vocabScoreDetail").textContent = scoreDesc;

      document.getElementById("vocabResults").classList.remove("hidden");
      updateStatus("green", "Analysis complete");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Analysis failed");
      showInfoBanner("Analysis failed. Is the server running?", true);
    }
  });

  // ---- File Upload ----
  const uploadZone = document.getElementById('uploadZone');
  const fileInput = document.getElementById('fileInput');
  const uploadPlaceholder = document.getElementById('uploadPlaceholder');
  const uploadBadge = document.getElementById('uploadBadge');
  const uploadFilename = document.getElementById('uploadFilename');
  const btnRemoveFile = document.getElementById('btnRemoveFile');

  uploadZone.addEventListener('click', (e) => {
    if (e.target === btnRemoveFile || e.target.closest('.badge-remove')) return;
    fileInput.click();
  });

  uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
  });
  uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
  });
  uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  btnRemoveFile.addEventListener('click', (e) => {
    e.stopPropagation();
    uploadPlaceholder.classList.remove('hidden');
    uploadBadge.classList.add('hidden');
    fileInput.value = '';
  });
}

function updateStatus(dotColor, text) {
  const dot = document.querySelector(".status-dot");
  const label = document.getElementById("statusText");
  dot.className = "status-dot";
  dot.classList.add(dotColor);
  label.textContent = text;
}

function showInfoBanner(message, isError = true) {
  try {
    const banner = document.getElementById("infoBanner");
    const msgEl = document.getElementById("infoBannerMessage");
    if (!banner || !msgEl) return;
    msgEl.textContent = message;
    banner.classList.remove("hidden");
    if (isError) {
      banner.style.borderColor = "var(--danger)";
      const icon = banner.querySelector(".info-icon");
      if (icon) icon.style.color = "var(--danger)";
    } else {
      banner.style.borderColor = "var(--concise)";
      const icon = banner.querySelector(".info-icon");
      if (icon) icon.style.color = "var(--concise)";
      setTimeout(() => hideInfoBanner(), 4000);
    }
  } catch (e) {
    console.error("Banner error:", e);
  }
}

function hideInfoBanner() {
  try {
    const banner = document.getElementById("infoBanner");
    if (banner) banner.classList.add("hidden");
  } catch (e) {
    console.error("Banner hide error:", e);
  }
}

async function handleFileUpload(file) {
  const allowedExts = ['.docx', '.pdf', '.txt'];
  const ext = '.' + file.name.split('.').pop().toLowerCase();
  if (!allowedExts.includes(ext)) {
    showInfoBanner('Unsupported file type. Please upload .docx, .pdf, or .txt files.', true);
    return;
  }
  const uploadPlaceholder = document.getElementById('uploadPlaceholder');
  const uploadBadge = document.getElementById('uploadBadge');
  const uploadFilename = document.getElementById('uploadFilename');
  updateStatus('orange', 'Extracting text...');
  if (ext === '.txt') {
    try {
      const text = await file.text();
      document.getElementById('inputText').value = text;
      uploadPlaceholder.classList.add('hidden');
      uploadBadge.classList.remove('hidden');
      uploadFilename.textContent = file.name;
      updateStatus('green', 'File loaded');
    } catch (err) {
      showInfoBanner('Failed to read text file.', true);
      updateStatus('red', 'Upload failed');
    }
    return;
  }
  const formData = new FormData();
  formData.append('file', file);
  try {
    const response = await fetch(`${API_BASE_URL}/api/upload`, {
      method: 'POST',
      body: formData
    });
    if (!response.ok) {
      const errData = await response.json();
      throw new Error(errData.detail || 'Upload failed');
    }
    const data = await response.json();
    document.getElementById('inputText').value = data.text;
    uploadPlaceholder.classList.add('hidden');
    uploadBadge.classList.remove('hidden');
    uploadFilename.textContent = file.name;
    updateStatus('green', 'File loaded');
  } catch (error) {
    console.error(error);
    showInfoBanner('Failed to extract text from file. ' + error.message, true);
    updateStatus('red', 'Upload failed');
  }
}