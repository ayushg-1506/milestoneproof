// MilestoneProof Modern SaaS Application Logic

document.addEventListener("DOMContentLoaded", () => {
    // Header & Status Elements
    const modelStatusDot = document.getElementById("modelStatusDot");
    const modelStatusText = document.getElementById("modelStatusText");
    const loadSampleBtn = document.getElementById("loadSampleBtn");

    // SOW Input Elements
    const sowInput = document.getElementById("sowInput");
    const uploadSowBtn = document.getElementById("uploadSowBtn");
    const sowFileInput = document.getElementById("sowFileInput");
    const criteriaCountIndicator = document.getElementById("criteriaCountIndicator");

    // Codebase Deliverable Upload Elements
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

    // Executive Metrics
    const metricMilestoneAmount = document.getElementById("metricMilestoneAmount");
    const metricReleaseAmount = document.getElementById("metricReleaseAmount");
    const metricVerifiedPercent = document.getElementById("metricVerifiedPercent");
    const metricRetainedAmount = document.getElementById("metricRetainedAmount");
    const metricProjectName = document.getElementById("metricProjectName");
    const metricAuditMode = document.getElementById("metricAuditMode");
    const pillVerified = document.getElementById("pillVerified");
    const pillPartial = document.getElementById("pillPartial");
    const pillMissing = document.getElementById("pillMissing");

    // Result Containers
    const criteriaList = document.getElementById("criteriaList");
    const settlementDetails = document.getElementById("settlementDetails");
    const letterText = document.getElementById("letterText");
    const markdownExportText = document.getElementById("markdownExportText");
    const copyLetterBtn = document.getElementById("copyLetterBtn");
    const copyMarkdownBtn = document.getElementById("copyMarkdownBtn");
    const downloadMarkdownBtn = document.getElementById("downloadMarkdownBtn");

    // Tab Navigation
    const tabBtns = document.querySelectorAll(".tab-btn, .tab-pill");
    const tabPanes = document.querySelectorAll(".tab-pane");

    let currentSelectedFile = null;

    // 1. Health & Model Runtime Status Check
    async function checkHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            if (data.model_configured && data.active_model) {
                modelStatusText.textContent = `AI: ${data.active_model} (${data.provider})`;
                modelStatusDot.classList.add("active");
            } else {
                modelStatusText.textContent = "Engine: Deterministic AST (Demo Mode)";
                modelStatusDot.classList.remove("active");
            }
        } catch (e) {
            modelStatusText.textContent = "Engine: Offline Deterministic";
            modelStatusDot.classList.remove("active");
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
            updateCriteriaCount();
        } catch (e) {
            console.error("Failed to load sample SOW:", e);
        }
    }

    // Live SOW Criteria Counter Helper
    function updateCriteriaCount() {
        const text = sowInput.value.trim();
        if (!text) {
            criteriaCountIndicator.textContent = "Paste SOW to begin analysis";
            return;
        }
        // Match table rows or headings with AC-
        const matches = text.match(/AC-\d+/g) || [];
        const uniqueCriteria = Array.from(new Set(matches));
        if (uniqueCriteria.length > 0) {
            criteriaCountIndicator.textContent = `${uniqueCriteria.length} acceptance criteria detected (${uniqueCriteria.join(", ")})`;
        } else {
            criteriaCountIndicator.textContent = "SOW specification ready";
        }
    }

    sowInput.addEventListener("input", updateCriteriaCount);

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
            updateCriteriaCount();
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
        selectedFileSize.textContent = file.size > 1024 * 1024 ? `(${sizeMb} MB)` : `(${sizeKb} KB)`;

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

        // Prevent repeated clicks during execution
        runAuditBtn.disabled = true;
        runAuditBtn.textContent = "Auditing Codebase...";
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
            runAuditBtn.disabled = false;
            runAuditBtn.textContent = "Run Deliverable Audit";

            if (!result.success) {
                alert("Audit Error: " + (result.error || "Unknown error occurred"));
                return;
            }

            renderResults(result.report);
            resultsSection.classList.remove("hidden");
            resultsSection.scrollIntoView({ behavior: "smooth" });

        } catch (error) {
            auditLoading.classList.add("hidden");
            runAuditBtn.disabled = false;
            runAuditBtn.textContent = "Run Deliverable Audit";
            alert("Audit execution failed: " + error.message);
        }
    }

    // 6. Render Audit Findings
    function renderResults(report) {
        const s = report.settlement;

        metricMilestoneAmount.textContent = `$${s.milestone_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricReleaseAmount.textContent = `$${s.recommended_release_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricVerifiedPercent.textContent = `${s.verified_percentage.toFixed(1)}% Verified (Proportional Scope Score)`;
        metricRetainedAmount.textContent = `$${s.retained_escrow_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricProjectName.textContent = report.project_name || "Milestone Deliverable";

        const modeDisplay = report.model_name
            ? `Mode: ${report.audit_mode} (${report.model_name})`
            : `Mode: ${report.audit_mode}`;
        metricAuditMode.textContent = modeDisplay;

        pillVerified.textContent = `${report.verified_count} Verified`;
        pillPartial.textContent = `${report.partial_count} Partial`;
        pillMissing.textContent = `${report.missing_count} Missing`;

        // Render Criteria Traceability Accordion
        criteriaList.innerHTML = "";
        report.results.forEach((item, index) => {
            const statusClass = item.status === "VERIFIED" ? "pill-success" : (item.status === "PARTIAL" ? "pill-warning" : "pill-danger");

            let evaluatorTagClass = "evaluator-det";
            let evaluatorLabel = "Deterministic Engine";
            if (item.evaluator === "AI_MODEL") {
                evaluatorTagClass = "evaluator-ai";
                evaluatorLabel = `AI Model: ${item.evaluator_details || "Active Model"}`;
            } else if (item.evaluator === "DETERMINISTIC_FALLBACK") {
                evaluatorTagClass = "evaluator-fallback";
                evaluatorLabel = `Fallback to Deterministic (${item.evaluator_details || ""})`;
            }

            const row = document.createElement("div");
            row.className = "criteria-row";

            let citationsHtml = "";
            if (item.citations && item.citations.length > 0) {
                citationsHtml = `
                    <div class="citations-wrapper">
                        <div class="citations-label">Empirical Code Evidence (${item.citations.length} cited):</div>
                        ${item.citations.map(c => `
                            <div class="citation-card">
                                <div class="citation-header">📄 ${escapeHtml(c.file_path)} : Lines ${c.line_start}-${c.line_end} ${c.symbol_name ? `(${escapeHtml(c.symbol_type)}: ${escapeHtml(c.symbol_name)})` : ""}</div>
                                <div class="citation-code">${escapeHtml(c.snippet)}</div>
                            </div>
                        `).join("")}
                    </div>
                `;
            } else {
                citationsHtml = `
                    <div class="citations-wrapper">
                        <div class="citation-card">
                            <div class="citation-header" style="color:var(--danger);">❌ No matching symbols, routes, or tests found in deliverable repository.</div>
                        </div>
                    </div>
                `;
            }

            let gapsHtml = "";
            if (item.gap_description) {
                gapsHtml = `
                    <div class="gap-callout">
                        <strong>Identified Gap:</strong> ${escapeHtml(item.gap_description)}
                    </div>
                `;
            }
            if (item.remediation_steps) {
                gapsHtml += `
                    <div class="remediation-callout">
                        <strong>Remediation Checklist:</strong> ${escapeHtml(item.remediation_steps)}
                    </div>
                `;
            }

            row.innerHTML = `
                <div class="criteria-summary" tabindex="0" role="button">
                    <div class="criteria-title-area">
                        <span class="criterion-id-tag">${escapeHtml(item.criterion_id)}</span>
                        <span class="criterion-title-text">${escapeHtml(item.title)}</span>
                        <span class="pill ${item.priority === 'MUST' ? 'pill-danger' : 'pill-warning'}">${item.priority}</span>
                    </div>
                    <div class="criteria-meta-area">
                        <span class="evaluator-tag ${evaluatorTagClass}">${escapeHtml(evaluatorLabel)}</span>
                        <span class="pill ${statusClass}">${item.status} (${Math.round(item.confidence * 100)}%)</span>
                        <span style="font-size:0.75rem; color:var(--text-tertiary);">▾</span>
                    </div>
                </div>
                <div class="criteria-body ${index === 0 ? '' : 'hidden'}">
                    <div class="finding-statement">${escapeHtml(item.reasoning)}</div>
                    ${citationsHtml}
                    ${gapsHtml}
                </div>
            `;

            // Click & Keyboard listener on summary
            const summaryEl = row.querySelector(".criteria-summary");
            const bodyEl = row.querySelector(".criteria-body");
            const toggle = () => bodyEl.classList.toggle("hidden");
            summaryEl.addEventListener("click", toggle);
            summaryEl.addEventListener("keydown", (e) => {
                if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    toggle();
                }
            });

            criteriaList.appendChild(row);
        });

        // Render Scope Valuation Reference
        let deductionsHtml = "";
        if (s.deductions && s.deductions.length > 0) {
            deductionsHtml = `
                <table class="data-table" style="margin-top:1rem;">
                    <thead>
                        <tr>
                            <th>Requirement</th>
                            <th>Status</th>
                            <th>Proportional Scope Value</th>
                            <th>Audit Finding / Identified Gap</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${s.deductions.map(d => `
                            <tr>
                                <td><strong>${escapeHtml(d.criterion_id)}</strong>: ${escapeHtml(d.title)}</td>
                                <td><span class="pill ${d.status === 'PARTIAL' ? 'pill-warning' : 'pill-danger'}">${d.status}</span></td>
                                <td class="text-mono" style="color:var(--warning);">$${d.withheld_amount.toFixed(2)}</td>
                                <td>${escapeHtml(d.reason)}</td>
                            </tr>
                        `).join("")}
                    </tbody>
                </table>
            `;
        } else {
            deductionsHtml = `<div style="padding:0.85rem; background:var(--success-subtle); border:1px solid var(--success-border); border-radius:var(--radius-sm); color:var(--success); font-size:0.82rem;">✓ All acceptance criteria verified with empirical code proof.</div>`;
        }

        settlementDetails.innerHTML = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1rem; margin-bottom:1.25rem;">
                <div style="background:var(--bg-surface-elevated); padding:1.15rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
                    <div class="metric-label">Verified Scope Value (Reference Only)</div>
                    <div style="font-size:1.75rem; font-weight:600; color:var(--success); font-family:var(--font-mono); margin:0.25rem 0;">$${s.recommended_release_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${s.currency}</div>
                    <p style="font-size:0.78rem; color:var(--text-secondary); line-height:1.45;">Proportional mathematical reference derived from verified criteria weights (${s.verified_percentage}% score).</p>
                </div>
                <div style="background:var(--bg-surface-elevated); padding:1.15rem; border-radius:var(--radius-sm); border:1px solid var(--border-subtle);">
                    <div class="metric-label">Unverified Scope Value</div>
                    <div style="font-size:1.75rem; font-weight:600; color:var(--warning); font-family:var(--font-mono); margin:0.25rem 0;">$${s.retained_escrow_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${s.currency}</div>
                    <p style="font-size:0.78rem; color:var(--text-secondary); line-height:1.45;">Remaining milestone value associated with unverified, incomplete, or missing acceptance criteria.</p>
                </div>
            </div>
            <h4 style="font-size:0.88rem; font-weight:600; color:var(--text-primary); margin-top:1.25rem;">Itemized Criteria Gap Breakdown</h4>
            ${deductionsHtml}
            <div style="margin-top:1rem; font-size:0.75rem; color:var(--text-tertiary); line-height:1.45;">
                * Notice: Scope valuations are mathematical references proportional to criteria weights. All formal acceptance, contract amendments, and payment releases remain at the sole discretion and authority of the human reviewer.
            </div>
        `;

        // Render Letter & Markdown Preview
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

    // Copy Feedback Letter
    copyLetterBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(letterText.textContent).then(() => {
            copyLetterBtn.textContent = "✓ Copied to Clipboard";
            setTimeout(() => { copyLetterBtn.textContent = "Copy Letter to Clipboard"; }, 2000);
        });
    });

    // Copy Markdown Dossier
    copyMarkdownBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(markdownExportText.textContent).then(() => {
            copyMarkdownBtn.textContent = "✓ Copied to Clipboard";
            setTimeout(() => { copyMarkdownBtn.textContent = "Copy Markdown"; }, 2000);
        });
    });

    // Download Markdown Dossier as .md file
    downloadMarkdownBtn.addEventListener("click", () => {
        const text = markdownExportText.textContent;
        if (!text) return;
        const blob = new Blob([text], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "milestone_audit_report.md";
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Button Bindings
    runAuditBtn.addEventListener("click", executeAudit);
    loadSampleBtn.addEventListener("click", loadSample);

    // Initial Health Check
    checkHealth();
});
