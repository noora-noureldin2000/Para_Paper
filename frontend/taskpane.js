// API Base URL (auto-detect from current page origin)
const API_BASE_URL = window.location.origin;

// Detect if opened directly from filesystem (not through server)
if (window.location.protocol === 'file:') {
  document.addEventListener("DOMContentLoaded", () => {
    showInfoBanner("Opened directly from file system. Run the backend server first: cd backend && python main.py then open http://localhost:8765", true);
  });
}

// State Tracker
let activeSelection = "";

// Initialize on DOM ready
document.addEventListener("DOMContentLoaded", () => {
  initApp();
});

function initApp() {
  setupTabs();
  setupEventListeners();
}

// Read text from textarea
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

// Copy text to clipboard
async function copyToClipboard(text) {
  try {
    await navigator.clipboard.writeText(text);
    updateStatus("green", "Copied to clipboard");
    showInfoBanner("Text copied to clipboard!", false);
  } catch (err) {
    // Fallback for older browsers or non-secure contexts
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

// Tab Switching Mechanism
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

// Event Listeners for Buttons
function setupEventListeners() {
  // Clear button
  document.getElementById("btnClearInput").addEventListener("click", () => {
    document.getElementById("inputText").value = "";
    activeSelection = "";
    updateStatus("green", "Cleared");
  });

  // 1. Paraphrase trigger
  document.getElementById("btnRunParaphrase").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;

    updateStatus("orange", "Paraphrasing...");
    hideInfoBanner();
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/paraphrase`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text })
      });
      
      if (!response.ok) {
        const errData = await response.json();
        throw new Error(errData.detail || "Server error");
      }
      
      const data = await response.json();
      
      const options = data.options;
      const academic = options.find(o => o.type === "Academic")?.text || "";
      const concise = options.find(o => o.type === "Concise")?.text || "";
      const impact = options.find(o => o.type === "High-Impact")?.text || "";
      
      document.getElementById("para-academic-text").textContent = academic;
      document.getElementById("para-concise-text").textContent = concise;
      document.getElementById("para-impact-text").textContent = impact;
      
      document.getElementById("paraphraseResults").classList.remove("hidden");
      updateStatus("green", "Paraphrase complete");
    } catch (error) {
      console.error(error);
      updateStatus("red", "Paraphrase failed");
      showInfoBanner("Cannot reach server. Make sure it's running (cd backend && python main.py) and access via http://localhost:8765 (not file://)", true);
    }
  });

  // Copy buttons for paraphrase cards
  document.querySelectorAll("#paraphraseResults .btn-insert").forEach(btn => {
    btn.addEventListener("click", () => {
      const resultId = btn.getAttribute("data-result-id");
      const text = document.getElementById(resultId).textContent;
      if (text) copyToClipboard(text);
    });
  });

  // 2. Humanize trigger
  document.getElementById("btnRunHumanize").addEventListener("click", async () => {
    const text = getInputText();
    if (!text) return;

    const selectedMode = document.querySelector('input[name="humanizeMode"]:checked').value;
    updateStatus("orange", "Humanizing...");
    hideInfoBanner();

    try {
      const response = await fetch(`${API_BASE_URL}/api/humanize`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, mode: selectedMode })
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

  // Copy button for Humanize result
  document.getElementById("btnCopyHumanize").addEventListener("click", () => {
    const text = document.getElementById("humanizedText").textContent;
    if (text) copyToClipboard(text);
  });

  // 3. Proofread triggers (Phase 1: Detection)
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
          item.innerHTML = `
            <input type="checkbox" class="issue-checkbox" data-id="${issue.id}" checked>
            <div class="issue-details">
              <div class="issue-meta">
                <span class="issue-id">[Issue #${issue.id}]</span>
                <span class="severity-badge ${issue.severity.toLowerCase()}">${issue.severity}</span>
                <span class="issue-location">${issue.location}</span>
              </div>
              <div class="issue-diagnosis">${issue.diagnosis}</div>
              <div class="issue-why"><strong>Consequence:</strong> ${issue.why_matters}</div>
              <div class="issue-fix"><strong>Actionable Fix:</strong> ${issue.actionable_fix}</div>
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

  // Proofread Apply Approved Fixes (Phase 2: Fix)
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
        body: JSON.stringify({ 
          text, 
          phase: "fix",
          approved_ids: approvedIds 
        })
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

  // Copy proofread output
  document.getElementById("btnCopyProofreadFix").addEventListener("click", () => {
    const text = document.getElementById("proofreadFixedText").textContent;
    if (text) copyToClipboard(text);
  });

  // Back button in Proofread tab
  document.getElementById("btnBackToIssues").addEventListener("click", () => {
    document.getElementById("proofreadFixedContainer").classList.add("hidden");
    document.getElementById("proofreadResults").classList.remove("hidden");
  });
}

// Status bar controller
function updateStatus(dotColor, text) {
  const dot = document.querySelector(".status-dot");
  const label = document.getElementById("statusText");
  
  dot.className = "status-dot";
  dot.classList.add(dotColor);
  
  label.textContent = text;
}

// Banner controls
function showInfoBanner(message, isError = true) {
  const banner = document.getElementById("infoBanner");
  const msgEl = document.getElementById("infoBannerMessage");
  
  msgEl.textContent = message;
  banner.classList.remove("hidden");
  
  if (isError) {
    banner.style.borderColor = "var(--danger)";
    banner.querySelector(".info-icon").style.color = "var(--danger)";
  } else {
    banner.style.borderColor = "var(--concise)";
    banner.querySelector(".info-icon").style.color = "var(--concise)";
    setTimeout(() => {
      hideInfoBanner();
    }, 4000);
  }
}

function hideInfoBanner() {
  const banner = document.getElementById("infoBanner");
  banner.classList.add("hidden");
}
