// MilestoneProof Interactive Dashboard Application

document.addEventListener("DOMContentLoaded", () => {
    // Elements
    const modelStatusEl = document.getElementById("modelStatus");
    const modelStatusTextEl = document.getElementById("modelStatusText");
    const loadSampleBtn = document.getElementById("loadSampleBtn");
    const sowInput = document.getElementById("sowInput");
    const deliverablePathInput = document.getElementById("deliverablePathInput");
    const runAuditBtn = document.getElementById("runAuditBtn");
    const auditLoading = document.getElementById("auditLoading");
    const resultsSection = document.getElementById("resultsSection");

    // Metrics
    const metricMilestoneAmount = document.getElementById("metricMilestoneAmount");
    const metricReleaseAmount = document.getElementById("metricReleaseAmount");
    const metricVerifiedPercent = document.getElementById("metricVerifiedPercent");
    const metricRetainedAmount = document.getElementById("metricRetainedAmount");
    const metricProjectName = document.getElementById("metricProjectName");
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

    // 1. Check System Health & Model Status
    async function checkHealth() {
        try {
            const res = await fetch("/api/health");
            const data = await res.json();
            if (data.ollama_connected) {
                modelStatusTextEl.textContent = `Ollama: ${data.active_model} (Active)`;
                modelStatusEl.classList.add("status-connected");
            } else {
                modelStatusTextEl.textContent = "Deterministic Semantic Fallback (Active)";
            }
        } catch (e) {
            modelStatusTextEl.textContent = "Offline Fallback Engine Ready";
        }
    }

    // 2. Load Sample Demo SOW
    async function loadSample() {
        try {
            const res = await fetch("/api/sample");
            const data = await res.json();
            sowInput.value = data.sow_content || "";
            deliverablePathInput.value = data.deliverable_path || "";
        } catch (e) {
            console.error("Failed to load sample:", e);
        }
    }

    // 3. Tab Switching Logic
    tabBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            tabBtns.forEach(b => b.classList.remove("active"));
            tabPanes.forEach(p => p.classList.remove("active"));

            btn.classList.add("active");
            const target = btn.getAttribute("data-tab");
            document.getElementById(target).classList.add("active");
        });
    });

    // 4. Run Deliverable Audit
    async function executeAudit() {
        const sowText = sowInput.value.trim();
        const deliverablePath = deliverablePathInput.value.trim();

        if (!sowText) {
            alert("Please paste an SOW specification or click 'Load Demo SOW'.");
            return;
        }
        if (!deliverablePath) {
            alert("Please enter the local deliverable codebase path.");
            return;
        }

        auditLoading.classList.remove("hidden");
        resultsSection.classList.add("hidden");

        try {
            const response = await fetch("/api/audit", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    sow_text: sowText,
                    deliverable_path: deliverablePath
                })
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

    // 5. Render Audit Findings
    function renderResults(report) {
        const s = report.settlement;

        metricMilestoneAmount.textContent = `$${s.milestone_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricReleaseAmount.textContent = `$${s.recommended_release_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricVerifiedPercent.textContent = `${s.verified_percentage.toFixed(1)}% Verified`;
        metricRetainedAmount.textContent = `$${s.retained_escrow_amount.toLocaleString(undefined, {minimumFractionDigits: 2})}`;
        metricProjectName.textContent = report.project_name || "Milestone Deliverable";

        pillVerified.textContent = `${report.verified_count} Verified`;
        pillPartial.textContent = `${report.partial_count} Partial`;
        pillMissing.textContent = `${report.missing_count} Missing`;

        // Render Criteria Traceability Accordion
        criteriaList.innerHTML = "";
        report.results.forEach((item, index) => {
            const statusClass = item.status === "VERIFIED" ? "status-verified" : (item.status === "PARTIAL" ? "status-partial" : "status-missing");
            const statusBadgeClass = item.status === "VERIFIED" ? "pill-success" : (item.status === "PARTIAL" ? "pill-warning" : "pill-danger");

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
                citationsHtml = `<div class="citation-card"><span class="text-danger">❌ No matching symbols, routes, or tests found in deliverable repository.</span></div>`;
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

        // Render Settlement Details
        let deductionsHtml = "";
        if (s.deductions && s.deductions.length > 0) {
            deductionsHtml = `
                <table style="width:100%; border-collapse:collapse; margin-top:1rem; font-size:0.85rem;">
                    <thead>
                        <tr style="border-bottom:1px solid var(--border-color); text-align:left; color:var(--text-muted);">
                            <th style="padding:0.6rem;">Requirement</th>
                            <th style="padding:0.6rem;">Status</th>
                            <th style="padding:0.6rem;">Escrow Withheld</th>
                            <th style="padding:0.6rem;">Contractual Justification</th>
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
            deductionsHtml = `<div style="padding:1rem; background:var(--success-bg); border:1px solid var(--success-border); border-radius:8px; color:var(--success);">✓ 100% of acceptance criteria verified. No deductions applied. Full payout approved.</div>`;
        }

        settlementDetails.innerHTML = `
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:1.5rem; margin-bottom:1.5rem;">
                <div style="background:rgba(255,255,255,0.02); padding:1.25rem; border-radius:8px; border:1px solid var(--border-color);">
                    <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Immediate Release Payout</div>
                    <div style="font-size:2rem; font-weight:700; color:var(--success); margin:0.3rem 0;">$${s.recommended_release_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${s.currency}</div>
                    <p style="font-size:0.82rem; color:var(--text-secondary);">Calculated from ${s.verified_percentage}% weighted criteria completion. Safe to disburse without project risk.</p>
                </div>
                <div style="background:rgba(255,255,255,0.02); padding:1.25rem; border-radius:8px; border:1px solid var(--border-color);">
                    <div style="font-size:0.8rem; color:var(--text-muted); text-transform:uppercase;">Retained Escrow Protection</div>
                    <div style="font-size:2rem; font-weight:700; color:var(--warning); margin:0.3rem 0;">$${s.retained_escrow_amount.toLocaleString(undefined, {minimumFractionDigits: 2})} ${s.currency}</div>
                    <p style="font-size:0.82rem; color:var(--text-secondary);">Withheld pending resolution of incomplete acceptance criteria.</p>
                </div>
            </div>
            <h4 style="margin-top:1.5rem; font-size:1rem; color:var(--text-primary);">Itemized Escrow Deductions</h4>
            ${deductionsHtml}
        `;

        // Render Letter & Markdown
        letterText.textContent = report.contractor_letter || "";
        markdownExportText.textContent = report.markdown_export || "";
    }

    // Helper: Escape HTML
    function escapeHtml(str) {
        if (!str) return "";
        return str
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // 6. Copy Actions
    copyLetterBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(letterText.textContent);
        const orig = copyLetterBtn.textContent;
        copyLetterBtn.textContent = "✓ Copied!";
        setTimeout(() => copyLetterBtn.textContent = orig, 2000);
    });

    copyMarkdownBtn.addEventListener("click", () => {
        navigator.clipboard.writeText(markdownExportText.textContent);
        const orig = copyMarkdownBtn.textContent;
        copyMarkdownBtn.textContent = "✓ Copied!";
        setTimeout(() => copyMarkdownBtn.textContent = orig, 2000);
    });

    // Event Listeners
    loadSampleBtn.addEventListener("click", loadSample);
    runAuditBtn.addEventListener("click", executeAudit);

    // Initial load
    checkHealth();
    loadSample();
});
