// MilestoneProof Interactive Dashboard Application

document.addEventListener("DOMContentLoaded", () => {
    // Header & Status Elements
    const modelStatusEl = document.getElementById("modelStatus");
    const modelStatusTextEl = document.getElementById("modelStatusText");
    const brandTechBadge = document.getElementById("brandTechBadge");
    const loadSampleBtn = document.getElementById("loadSampleBtn");

    // SOW Inputs
    const sowInput = document.getElementById("sowInput");
    const uploadSowBtn = document.getElementById("uploadSowBtn");
    const sowFileInput = document.getElementById("sowFileInput");

    // Deliverable Upload Inputs
    const dropZone = document.getElementById("dropZone");
    const zipFileInput = document.getElementById("zipFileInput");
    const selectedFileContainer = document.getElementById("selectedFileContainer");
    const selectedFileName = document.getElementById("selectedFileName");
    const selectedFileSize = document.getElementById("selectedFileSize");
    const removeFileBtn = document.getElementById("removeFileBtn");
    const useDemoDeliverable = document.getElementById("useDemoDeliverable");

    // Audit Trigger & Loading
    const runAuditBtn = document.getElementById("runAuditBtn");
    const auditLoading = document.getElementById("auditLoading");
    const resultsSection = document.getElementById("resultsSection");

    // Metrics
    const metricMilestoneAmount = document.getElementById("metricMilestoneAmount");
    const metricReleaseAmount = document.getElementById("metricReleaseAmount");
    const metricVerifiedPercent = document.getElementById("metricVerifiedPercent");
    const metricRetainedAmount = document.getElementById("metricRetainedAmount");
    const metricProjectName = document.getElementById("metricProjectName");
    const metricAuditMode = document.getElementById("metricAuditMode");
    const pillVerified = document.getElementById("pillVerified");
    const pillPartial = document.getElementById("pillPartial");
    const pillMissing = document.getElementById("pillMissing");

    // Content Containers
    const criteriaList = document.getElementById("criteriaList");
    const settlementDetails = document.getElementById("settlementDetails");
    const letterText = document.getElementById("letterText");
    const markdownExportText = document.getElementById("markdownExportText");
    const copyLetterBtn = document.getElementById("copyLetterBtn");
    const copyMarkdownBtn = document.getElementById("copyMarkdownBtn");

    // Tabs
    const tabBtns = document.querySelectorAll(".tab-btn");
    const tabPanes = document.querySelectorAll(".tab-pane");

    let currentSelectedFile = null;

    // 1. Check System Health & Model Configuration
    async function checkHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            if (data.model_configured && data.active_model) {
                modelStatusTextEl.textContent = `AI: ${data.active_model} (${data.provider})`;
                modelStatusEl.classList.add("status-connected");
                brandTechBadge.textContent = `${data.provider} AI`;
            } else {
                modelStatusTextEl.textContent = "Deterministic Demo Mode (No API Key)";
                modelStatusEl.classList.remove("status-connected");
                brandTechBadge.textContent = "Deterministic AST";
            }
        } catch (e) {
            modelStatusTextEl.textContent = "Deterministic Offline Engine Ready";
            modelStatusEl.classList.remove("status-connected");
        }
    }

    // 2. Load Sample Demo SOW
    async function loadSample() {
        try {
            const res = await fetch("/api/sample");
            const data = await res.json();
            sowInput.value = data.sow_content || "";
            useDemoDeliverable.checked = true;
            clearSelectedZip();
        } catch (e) {
            console.error("Failed to load sample:", e);
        }
    }

    // SOW File Upload Handler
    uploadSowBtn.addEventListener("click", () => {
        sowFileInput.click();
    });

    sowFileInput.addEventListener("change", (e) => {
        const file = e.target.files[0];
        if (!file) return;
        const reader = new FileReader();
        reader.onload = (event) => {
            sowInput.value = event.target.result;
        };
        reader.readAsText(file);
    });

    // 3. ZIP File Drag & Drop Handlers
    dropZone.addEventListener("click", () => {
        zipFileInput.click();
    });

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleZipFileSelection(e.dataTransfer.files[0]);
        }
    });

    zipFileInput.addEventListener("change", (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleZipFileSelection(e.target.files[0]);
        }
    });

    function handleZipFileSelection(file) {
        if (!file.name.toLowerCase().endsWith(".zip")) {
            alert("Please select a valid .zip archive of the deliverable codebase.");
            return;
        }

        currentSelectedFile = file;
        selectedFileName.textContent = file.name;
        const sizeKb = (file.size / 1024).toFixed(1);
        const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
        selectedFileSize.textContent = file.size > 1024 * 1024 ? `${sizeMb} MB` : `${sizeKb} KB`;

        selectedFileContainer.classList.remove("hidden");
        useDemoDeliverable.checked = false;
    }

    function clearSelectedZip() {
        currentSelectedFile = null;
        zipFileInput.value = "";
        selectedFileContainer.classList.add("hidden");
    }

    removeFileBtn.addEventListener("click", (e) => {
        e.stopPropagation();
        clearSelectedZip();
    });

    useDemoDeliverable.addEventListener("change", () => {
        if (useDemoDeliverable.checked) {
            clearSelectedZip();
        }
    });

    // 4. Tab Switching Logic
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.getAttribute("data-tab");
            const targetPane = document.getElementById(target);
            if (targetPane) targetPane.classList.add("active");
        });
    });

    // 5. Run Deliverable Audit
    async function executeAudit() {
        const sowText = sowInput.value.trim();

        if (!sowText) {
            alert("Please paste Statement of Work markdown or click 'Load Demo SOW'.");
            return;
        }

        if (!currentSelectedFile && !useDemoDeliverable.checked) {
            alert("Please upload a .zip archive of the codebase or select 'Use bundled demo deliverable'.");
            return;
        }

        auditLoading.classList.remove("hidden");
        resultsSection.classList.add("hidden");

        const formData = new FormData();
        formData.append("sow_text", sowText);

        if (currentSelectedFile) {
            formData.append("deliverable_zip", currentSelectedFile);
        } else if (useDemoDeliverable.checked) {
            formData.append("use_sample_deliverable", "true");
        }

        try {
            const response = await fetch("/api/audit", {
                method: "POST",
                body: formData
            });

            const result = await response.json();
            auditLoading.classList.add("hidden");

            if (!result.success) {
                alert("Audit Error: " + (result.error || "Unknown error occurred"));
                return;
            }

            renderResults(result.report);
            resultsSection.classList.remove("hidden");
            resultsSection.scrollIntoView({ behavior: "smooth" });

        } catch (error) {
            auditLoading.classList.add("hidden");
            alert("Audit execution failed: " + error.message);
        }
    }

    // 6. Render Audit Findings
    function renderResults(report) {
        const s = report.settlement;

        metricMilestoneAmount.textContent = `$${s.milestone_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricReleaseAmount.textContent = `$${s.recommended_release_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricVerifiedPercent.textContent = `${s.verified_percentage.toFixed(1)}% Verified (Reference)`;
        metricRetainedAmount.textContent = `$${s.retained_escrow_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricProjectName.textContent = report.project_name || "Milestone Deliverable";

        const auditModeLabel = report.model_name
            ? `Mode: ${report.audit_mode} (${report.model_name})`
            : `Mode: ${report.audit_mode}`;
        metricAuditMode.textContent = auditModeLabel;

        pillVerified.textContent = `${report.verified_count} Verified`;
        pillPartial.textContent = `${report.partial_count} Partial`;
        pillMissing.textContent = `${report.missing_count} Missing`;

        // Render Criteria Traceability Accordion
        criteriaList.innerHTML = "";
        report.results.forEach((item, index) => {
            const statusClass = item.status === "VERIFIED" ? "status-verified" : (item.status === "PARTIAL" ? "status-partial" : "status-missing");
            const statusBadgeClass = item.status === "VERIFIED" ? "pill-success" : (item.status === "PARTIAL" ? "pill-warning" : "pill-danger");

            let evaluatorTagClass = "evaluator-det";
            let evaluatorLabel = "Deterministic Engine";
            if (item.evaluator === "AI_MODEL") {
                evaluatorTagClass = "evaluator-ai";
                evaluatorLabel = `AI Model: ${item.evaluator_details || "Active Model"}`;
            } else if (item.evaluator === "DETERMINISTIC_FALLBACK") {
                evaluatorTagClass = "evaluator-fallback";
                evaluatorLabel = `Fallback to Deterministic (${item.evaluator_details || ""})`;
            }

            const card = document.createElement("div");
            card.className = `criteria-item ${statusClass}`;

            let citationsHtml = "";
            if (item.citations && item.citations.length > 0) {
                citationsHtml = `
                    <div class="citations-section">
                        <strong style="font-size:0.8rem; color:var(--text-secondary);">Empirical Evidence Found on Disk (${item.citations.length}):</strong>
                        ${item.citations.map(c => `
                            <div class="citation-card">
                                <div class="citation-header">📄 ${c.file_path} : Lines ${c.line_start}-${c.line_end} ${c.symbol_name ? `(${c.symbol_type}: ${c.symbol_name})` : ""}</div>
                                <div class="citation-code">${escapeHtml(c.snippet)}</div>
                            </div>
                        `).join("")}
                    </div>
                `;
            } else {
                citationsHtml = `<div class="citation-card"><span class="text-danger">❌ No matching symbols, routes, or tests detected in deliverable archive.</span></div>`;
            }

            let gapsHtml = "";
            if (item.gap_description) {
                gapsHtml = `
                    <div style="background:var(--warning-bg); border:1px solid var(--warning-border); padding:0.6rem 0.8rem; border-radius:6px; margin-top:0.4rem;">
                        <strong class="text-warning">Identified Gap:</strong> ${escapeHtml(item.gap_description)}
                    </div>
                `;
            }
            if (item.remediation_steps) {
                gapsHtml += `
                    <div style="background:rgba(255,255,255,0.03); border:1px solid var(--border-color); padding:0.6rem 0.8rem; border-radius:6px; margin-top:0.4rem;">
                        <strong style="color:var(--primary);">Remediation Checklist:</strong> ${escapeHtml(item.remediation_steps)}
                    </div>
                `;
            }

            card.innerHTML = `
                <div class="criteria-summary" onclick="this.nextElementSibling.classList.toggle('hidden')">
                    <div class="criteria-title-group">
                        <span class="criteria-id">${item.criterion_id}</span>
                        <strong>${escapeHtml(item.title)}</strong>
                        <span class="pill ${item.priority === 'MUST' ? 'pill-danger' : 'pill-warning'}" style="font-size:0.68rem;">${item.priority}</span>
                        <span class="evaluator-tag ${evaluatorTagClass}">${escapeHtml(evaluatorLabel)}</span>
                    </div>
                    <div style="display:flex; align-items:center; gap:0.75rem;">
                        <span class="pill ${statusBadgeClass}">${item.status} (${Math.round(item.confidence * 100)}%)</span>
                        <span style="font-size:0.8rem; color:var(--text-muted);">▼</span>
                    </div>
                </div>
                <div class="criteria-body ${index === 0 ? '' : 'hidden'}">
                    <p style="color:var(--text-secondary); margin-bottom:0.4rem;">${escapeHtml(item.reasoning)}</p>
                    ${citationsHtml}
                    ${gapsHtml}
                </div>
            `;
            criteriaList.appendChild(card);
        });

        // Render Settlement / Valuation Details
        let deductionsHtml = "";
        if (s.deductions && s.deductions.length > 0) {
            deductionsHtml = `
                <table style="width:100%; border-collapse:collapse; margin-top:1rem; font-size:0.85rem;">
                    <thead>
                        <tr style="border-bottom:1px solid var(--border-color); text-align:left; color:var(--text-muted);">
                            <th style="padding:0.6rem;">Requirement</th>
                            <th style="padding:0.6rem;">Status</th>
                            <th style="padding:0.6rem;">Proportional Scope Value</th>
                            <th style="padding:0.6rem;">Finding / Gap Detail</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${s.deductions.map(d => `
                            <tr style="border-bottom:1px solid rgba(255,255,255,0.04);">
                                <td style="padding:0.75rem 0.6rem;"><strong>${d.criterion_id}</strong>: ${escapeHtml(d.title)}</td>
                                <td style="padding:0.75rem 0.6rem;"><span class="pill ${d.status === 'PARTIAL' ? 'pill-warning' : 'pill-danger'}">${d.status}</span></td>
                                <td style="padding:0.75rem 0.6rem; font-family:var(--font-mono); color:var(--warning);">$${d.withheld_amount.toFixed(2)}</td>
                                <td style="padding:0.75rem 0.6rem; color:var(--text-secondary);">${escapeHtml(d.reason)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } else {
            deductionsHtml = `<div style="padding:1rem; background:var(--success-bg); border:1px solid var(--success-border); border-radius:8px; color:var(--success);">✓ 100% of acceptance criteria verified with empirical code proof.</div>`;
        }

        settlementDetails.innerHTML = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
                <div style="background:rgba(255,255,255,0.02); padding:1.25rem; border-radius:8px; border:1px solid var(--border-color);">
                    <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Verified Scope Value (Reference)</div>
                    <div style="font-size:2rem; font-weight:700; color:var(--success); margin:0.3rem 0;">$${s.recommended_release_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${s.currency}</div>
                    <p style="font-size:0.82rem; color:var(--text-secondary);">Proportional value of verified criteria (${s.verified_percentage}% weighted score). Provided for reviewer reference.</p>
                </div>
                <div style="background:rgba(255,255,255,0.02); padding:1.25rem; border-radius:8px; border:1px solid var(--border-color);">
                    <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Unverified Scope Value</div>
                    <div style="font-size:2rem; font-weight:700; color:var(--warning); margin:0.3rem 0;">$${s.retained_escrow_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${s.currency}</div>
                    <p style="font-size:0.82rem; color:var(--text-secondary);">Milestone value corresponding to unverified or partially implemented criteria.</p>
                </div>
            </div>
            <h4 style="margin-top:1.5rem; font-size:1rem; color:var(--text-primary);">Itemized Criteria Gap Breakdown</h4>
            ${deductionsHtml}
            <div style="margin-top:1.25rem; font-size:0.8rem; color:var(--text-muted); font-style:italic;">
                * Note: Monies and percentages are mathematical references derived from agreed criteria weights. All formal acceptance, contract amendments, and payment releases remain at the sole discretion of the human reviewer.
            </div>
        `;

        // Render Letter & Markdown
        letterText.textContent = report.contractor_letter || "";
        markdownExportText.textContent = report.markdown_export || "";
    }

    // Helper: Escape HTML
    function escapeHtml(text) {
        if (!text) return "";
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Copy Buttons
    copyLetterBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(letterText.textContent).then(() => {
            copyLetterBtn.textContent = "✓ Copied!";
            setTimeout(() => { copyLetterBtn.textContent = "📋 Copy Letter"; }, 2000);
        });
    });

    copyMarkdownBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(markdownExportText.textContent).then(() => {
            copyMarkdownBtn.textContent = "✓ Copied!";
            setTimeout(() => { copyMarkdownBtn.textContent = "📋 Copy Markdown"; }, 2000);
        });
    });

    // Run Audit Button
    runAuditBtn.addEventListener("click", executeAudit);
    loadSampleBtn.addEventListener("click", loadSample);

    // Initial Health Check
    checkHealth();
});
