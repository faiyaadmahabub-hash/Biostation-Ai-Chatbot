// BioStation AI - Code Editor and Visualization Module

// Code Editor State
let currentCode = '';
let currentExplanationCode = '';

// Initialize code editor functionality
document.addEventListener('DOMContentLoaded', () => {
    setupCodeEditor();
    setupVizModal();
    setupExplainModal();
});

function setupCodeEditor() {
    const modal = document.getElementById('code-editor-modal');
    const closeBtn = document.getElementById('close-code-modal');
    const copyBtn = document.getElementById('copy-code-btn');
    const downloadBtn = document.getElementById('download-code-btn');
    const explainBtn = document.getElementById('explain-code-btn');
    const runBtn = document.getElementById('run-code-btn');
    const editor = document.getElementById('code-editor');

    if (!modal) return;

    // Close modal
    closeBtn?.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    // Click outside to close
    modal?.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    // Copy code
    copyBtn?.addEventListener('click', () => {
        const code = editor.value;
        navigator.clipboard.writeText(code).then(() => {
            copyBtn.innerHTML = '<span class="material-icons-round">check</span> Copied!';
            setTimeout(() => {
                copyBtn.innerHTML = '<span class="material-icons-round">content_copy</span> Copy';
            }, 2000);
        });
    });

    // Download code
    downloadBtn?.addEventListener('click', () => {
        const code = editor.value;
        const blob = new Blob([code], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'analysis.R';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });

    // Explain code
    explainBtn?.addEventListener('click', () => {
        const code = editor.value;
        if (code.trim()) {
            explainCode(code);
        }
    });

    // Run code
    runBtn?.addEventListener('click', async () => {
        const code = editor.value;
        await runRCode(code);
    });

    // Tab key support in editor
    editor?.addEventListener('keydown', (e) => {
        if (e.key === 'Tab') {
            e.preventDefault();
            const start = editor.selectionStart;
            const end = editor.selectionEnd;
            editor.value = editor.value.substring(0, start) + '  ' + editor.value.substring(end);
            editor.selectionStart = editor.selectionEnd = start + 2;
        }
    });
}

function setupVizModal() {
    const modal = document.getElementById('viz-modal');
    const closeBtn = document.getElementById('close-viz-modal');

    closeBtn?.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    modal?.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Open code editor with code
window.openCodeEditor = function (code) {
    const modal = document.getElementById('code-editor-modal');
    const editor = document.getElementById('code-editor');
    const output = document.getElementById('code-output');

    editor.value = code;
    currentCode = code;
    output.style.display = 'none';
    modal.style.display = 'flex';

    // Focus editor
    setTimeout(() => editor.focus(), 100);
};

// Run R code (API call)
async function runRCode(code) {
    const outputContainer = document.getElementById('code-output');
    const outputContent = document.getElementById('code-output-content');
    const runBtn = document.getElementById('run-code-btn');

    // Show loading state
    runBtn.disabled = true;
    runBtn.innerHTML = '<span class="material-icons-round rotating">sync</span> Running...';
    outputContainer.style.display = 'block';
    outputContent.textContent = 'Executing R code...';

    try {
        const response = await fetch('/api/run-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });

        const data = await response.json();
        console.log('[Code Editor] Response data:', data);

        if (data.success) {
            let output = '';
            if (data.output) {
                output += data.output + '\n';
            }
            if (data.warnings) {
                output += '\n⚠️ Warnings:\n' + data.warnings + '\n';
            }
            if (data.plots && data.plots.length > 0) {
                output += '\n📊 ' + data.plots.length + ' plot(s) generated\n';
            }

            const finalOutput = output || '(No output)';
            console.log('[Code Editor] Setting output:', finalOutput);
            console.log('[Code Editor] Output element:', outputContent);
            outputContent.textContent = finalOutput;

            // If there are plots, show them
            if (data.plots && data.plots.length > 0) {
                showPlots(data.plots);
            }
        } else {
            const errorMsg = '❌ Error:\n' + (data.errors || data.error || 'Unknown error');
            console.log('[Code Editor] Error:', errorMsg);
            outputContent.textContent = errorMsg;

            // Show smart error explanation if analysis is available
            if (data.analysis) {
                showErrorExplanation(data.errors || data.error, data.analysis, code);
            } else {
                // Try to analyze client-side
                analyzeAndShowError(data.errors || data.error, code);
            }
        }
    } catch (error) {
        const networkMsg = '❌ Network error: ' + error.message;
        console.log('[Code Editor] Network error:', networkMsg);
        outputContent.textContent = networkMsg;
    } finally {
        runBtn.disabled = false;
        runBtn.innerHTML = '<span class="material-icons-round">play_arrow</span> Run';
    }
}

function clearOutput() {
    document.getElementById('code-output').style.display = 'none';
    document.getElementById('code-output-content').textContent = '';
}

// Show plots in visualization modal
function showPlots(plotPaths) {
    const modal = document.getElementById('viz-modal');
    const container = document.getElementById('viz-container');

    container.innerHTML = '';

    plotPaths.forEach((path, index) => {
        const img = document.createElement('img');
        img.src = '/api/plot/' + encodeURIComponent(path);
        img.alt = `Plot ${index + 1}`;
        img.className = 'result-plot';
        container.appendChild(img);
    });

    modal.style.display = 'flex';
}

// Show results visualization
window.showVisualization = function (content, type = 'html') {
    const modal = document.getElementById('viz-modal');
    const container = document.getElementById('viz-container');

    if (type === 'html') {
        container.innerHTML = content;
    } else if (type === 'image') {
        container.innerHTML = `<img src="${content}" alt="Result visualization" class="result-plot">`;
    } else if (type === 'table') {
        container.innerHTML = formatAsTable(content);
    }

    modal.style.display = 'flex';
};

// Format data as HTML table
function formatAsTable(data) {
    if (!data || !data.length) return '<p>No data to display</p>';

    const headers = Object.keys(data[0]);
    let html = '<table class="result-table"><thead><tr>';

    headers.forEach(h => {
        html += `<th>${escapeHtml(h)}</th>`;
    });

    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        headers.forEach(h => {
            html += `<td>${escapeHtml(String(row[h] ?? ''))}</td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Setup Explain Modal
function setupExplainModal() {
    const modal = document.getElementById('explain-modal');
    const closeBtn = document.getElementById('close-explain-modal');

    closeBtn?.addEventListener('click', () => {
        modal.style.display = 'none';
    });

    modal?.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Explain Code Function
async function explainCode(code) {
    const modal = document.getElementById('explain-modal');
    const summary = document.getElementById('explain-summary');
    const content = document.getElementById('explain-content');

    // Store current code
    currentExplanationCode = code;

    // Show modal with loading state
    modal.style.display = 'flex';
    summary.style.display = 'none';
    content.innerHTML = `
        <div class="explain-loading">
            <div class="thinking-spinner-large"></div>
            <p class="thinking-text-large">Thinking...</p>
        </div>
    `;

    try {
        const response = await fetch('/api/explain-code/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ code: code })
        });

        if (!response.ok) {
            throw new Error('Failed to get explanation');
        }

        // Clear loading state
        content.innerHTML = '';

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let explanationText = '';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n');
            buffer = lines.pop();

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.type === 'summary') {
                            renderExplainSummary(data.content);
                        } else if (data.type === 'content') {
                            explanationText += data.content;
                            content.innerHTML = formatExplanation(explanationText);
                        } else if (data.type === 'error') {
                            content.innerHTML = `<p style="color: #ef4444;">Error: ${data.content}</p>`;
                        }
                    } catch (e) {
                        console.error('Error parsing SSE:', e);
                    }
                }
            }
        }

    } catch (error) {
        console.error('Error explaining code:', error);
        content.innerHTML = `
            <div class="explain-loading">
                <span class="material-icons-round" style="color: #ef4444;">error</span>
                <p>Failed to generate explanation. Please try again.</p>
            </div>
        `;
    }
}

function renderExplainSummary(summaryData) {
    const summary = document.getElementById('explain-summary');

    let html = '';

    if (summaryData.detected_test) {
        html += `
            <div class="explain-summary-item">
                <span class="material-icons-round">science</span>
                <span class="explain-summary-label">Test Type:</span>
                <span class="explain-summary-value">${summaryData.detected_test}</span>
            </div>
        `;
    }

    html += `
        <div class="explain-summary-item">
            <span class="material-icons-round">code</span>
            <span class="explain-summary-label">Lines:</span>
            <span class="explain-summary-value">${summaryData.total_lines}</span>
        </div>
    `;

    if (summaryData.packages_used && summaryData.packages_used.length > 0) {
        html += `
            <div class="explain-summary-item">
                <span class="material-icons-round">inventory_2</span>
                <span class="explain-summary-label">Packages:</span>
                <span class="explain-summary-value">${summaryData.packages_used.join(', ')}</span>
            </div>
        `;
    }

    if (summaryData.has_visualization) {
        html += `
            <div class="explain-summary-item">
                <span class="material-icons-round">bar_chart</span>
                <span class="explain-summary-value">Includes Visualization</span>
            </div>
        `;
    }

    summary.innerHTML = html;
    summary.style.display = 'flex';
}

function formatExplanation(text) {
    // Convert markdown to HTML
    let html = text;

    // Headers
    html = html.replace(/^### (.*?)$/gm, '<h4>$1</h4>');
    html = html.replace(/^## (.*?)$/gm, '<h3>$1</h3>');
    html = html.replace(/^# (.*?)$/gm, '<h2>$1</h2>');

    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    // Inline code
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Lists
    html = html.replace(/^\* (.*?)$/gm, '<li>$1</li>');
    html = html.replace(/^- (.*?)$/gm, '<li>$1</li>');
    html = html.replace(/^(\d+)\. (.*?)$/gm, '<li>$2</li>');

    // Wrap consecutive li elements in ul
    html = html.replace(/(<li>.*?<\/li>\n?)+/g, '<ul>$&</ul>');

    // Paragraphs (double newlines)
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up empty paragraphs
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(\s*<[hul])/g, '$1');
    html = html.replace(/(<\/[hul][^>]*>)\s*<\/p>/g, '$1');

    return html;
}

// Global function to explain code from anywhere
window.explainCode = explainCode;

window.explainCodeBlock = function(btn) {
    const code = btn.closest('.code-block-wrapper').querySelector('code').textContent;
    explainCode(code);
};

// Add "Open in Editor" button to code blocks in chat
window.enhanceCodeBlocks = function () {
    const codeBlocks = document.querySelectorAll('.bot-text pre code');

    codeBlocks.forEach(block => {
        // Skip if already enhanced
        if (block.parentElement.classList.contains('enhanced') || block.parentElement.parentElement.classList.contains('code-block-wrapper')) return;

        block.parentElement.classList.add('enhanced');

        const pre = block.parentElement;
        const wrapper = document.createElement('div');
        wrapper.className = 'code-block-wrapper';

        const toolbar = document.createElement('div');
        toolbar.className = 'code-block-toolbar';
        toolbar.innerHTML = `
            <span class="code-lang">R</span>
            <div class="code-actions">
                <button class="code-action-btn" onclick="copyCodeBlock(this)" title="Copy">
                    <span class="material-icons-round">content_copy</span>
                </button>
                <button class="code-action-btn explain-btn" onclick="explainCodeBlock(this)" title="Explain Code">
                    <span class="material-icons-round">psychology</span>
                </button>
                <button class="code-action-btn" onclick="openCodeBlock(this)" title="Open in Editor">
                    <span class="material-icons-round">edit</span>
                </button>
            </div>
        `;

        pre.parentNode.insertBefore(wrapper, pre);
        wrapper.appendChild(toolbar);
        wrapper.appendChild(pre);
    });
};

window.copyCodeBlock = function (btn) {
    const code = btn.closest('.code-block-wrapper').querySelector('code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        btn.innerHTML = '<span class="material-icons-round">check</span>';
        setTimeout(() => {
            btn.innerHTML = '<span class="material-icons-round">content_copy</span>';
        }, 1500);
    });
};

window.openCodeBlock = function (btn) {
    const code = btn.closest('.code-block-wrapper').querySelector('code').textContent;
    openCodeEditor(code);
};

// Call enhance after each message
const originalAppendBotMessage = window.appendBotMessage || function () { };
window.appendBotMessage = function (text) {
    originalAppendBotMessage(text);
    setTimeout(enhanceCodeBlocks, 100);
};

// ============ SMART ERROR HANDLING ============

// Store current error data for fix operations
let currentErrorData = null;

// Client-side error patterns for quick analysis
const ERROR_PATTERNS = {
    column_not_found: {
        patterns: [
            /Column [`'](\w+)[`'] is not found/i,
            /object [`'](\w+)[`'] not found/i,
            /undefined columns selected/i,
        ],
        explanation: "Your code references a column that doesn't exist in your dataset.",
        suggestion: "Check your column names and use the correct placeholder or column name."
    },
    curly_brace: {
        patterns: [
            /unexpected [`']\{[`']/i,
            /unexpected [`']\}[`']/i,
        ],
        explanation: "R's curly braces are conflicting with template placeholders.",
        suggestion: "Use DOUBLE braces {{ }} for R code blocks (if/else, loops, functions)."
    },
    package_missing: {
        patterns: [
            /there is no package called [`'](\w+)[`']/i,
            /could not find function [`'](\w+)[`']/i,
        ],
        explanation: "A required R package is not installed or loaded.",
        suggestion: "Add ensure_package(\"package_name\") at the top of your code."
    },
    data_not_found: {
        patterns: [
            /object [`']data[`'] not found/i,
        ],
        explanation: "The data frame was not loaded. The {data_loading} placeholder may be missing.",
        suggestion: "Make sure {data_loading} is at the top of your template after {package_helper}."
    },
    grouping_levels: {
        patterns: [
            /grouping factor must have exactly 2 levels/i,
        ],
        explanation: "T-test requires exactly 2 groups, but your data has a different number.",
        suggestion: "Either filter to 2 groups, or use ANOVA/Kruskal-Wallis for 3+ groups."
    },
    wide_format: {
        patterns: [
            /not all arguments have the same length/i,
            /arguments imply differing number of rows/i,
        ],
        explanation: "Your data may be in WIDE format but the test expects LONG format.",
        suggestion: "Add data reshaping code using pivot_longer() before the analysis."
    }
};

// Analyze error client-side and show explanation
function analyzeAndShowError(errorMessage, code) {
    const analysis = analyzeErrorClientSide(errorMessage);
    if (analysis) {
        showErrorExplanation(errorMessage, analysis, code);
    }
}

// Client-side error analysis
function analyzeErrorClientSide(errorMessage) {
    for (const [errorType, pattern] of Object.entries(ERROR_PATTERNS)) {
        for (const regex of pattern.patterns) {
            if (regex.test(errorMessage)) {
                return {
                    error_type: errorType,
                    explanation: pattern.explanation,
                    suggestion: pattern.suggestion,
                    fix_available: false,
                    dataset_columns: []
                };
            }
        }
    }
    return null;
}

// Show error explanation modal
function showErrorExplanation(errorMessage, analysis, code) {
    const modal = document.getElementById('error-explain-modal');
    if (!modal) return;

    // Store for fix operations
    currentErrorData = {
        error: errorMessage,
        analysis: analysis,
        code: code
    };

    // Populate modal fields
    document.getElementById('error-message-display').textContent = errorMessage.substring(0, 300);
    document.getElementById('error-why-text').textContent = analysis.explanation || 'An error occurred while running your R code.';
    document.getElementById('error-suggestion-text').textContent = analysis.suggestion || 'Check your code for syntax errors.';

    // Show dataset columns if available
    const columnsSection = document.getElementById('error-columns-section');
    if (analysis.dataset_columns && analysis.dataset_columns.length > 0) {
        document.getElementById('error-columns-list').textContent = analysis.dataset_columns.join(', ');
        columnsSection.style.display = 'block';
    } else {
        columnsSection.style.display = 'none';
    }

    // Show code snippet if available
    const snippetSection = document.getElementById('error-code-snippet-section');
    if (analysis.code_snippet) {
        document.getElementById('error-code-snippet').textContent = analysis.code_snippet;
        snippetSection.style.display = 'block';
    } else {
        snippetSection.style.display = 'none';
    }

    // Show alternatives if available
    const alternativesSection = document.getElementById('error-alternatives-section');
    if (analysis.alternatives && analysis.alternatives.length > 0) {
        const listEl = document.getElementById('error-alternatives-list');
        listEl.innerHTML = analysis.alternatives.map(alt => `
            <div style="padding: 8px; background: var(--bg-secondary); border-radius: 4px; cursor: pointer;"
                 onclick="selectAlternative('${alt.test || ''}', '${escapeHtml(alt.code || '')}')">
                <strong>${escapeHtml(alt.name)}</strong>
                <p style="font-size: 11px; color: var(--text-secondary); margin: 4px 0 0;">${escapeHtml(alt.description || '')}</p>
            </div>
        `).join('');
        alternativesSection.style.display = 'block';
    } else {
        alternativesSection.style.display = 'none';
    }

    // Show/hide fix buttons based on availability
    const applyFixBtn = document.getElementById('apply-fix-btn');
    const copyFixBtn = document.getElementById('copy-fix-btn');

    if (analysis.fix_available && analysis.fix_code) {
        applyFixBtn.style.display = 'flex';
        copyFixBtn.style.display = 'flex';
    } else {
        applyFixBtn.style.display = 'none';
        copyFixBtn.style.display = 'none';
    }

    // Show modal
    modal.style.display = 'flex';
}

// Close error explanation modal
window.closeErrorExplainModal = function() {
    const modal = document.getElementById('error-explain-modal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentErrorData = null;
};

// Apply the suggested fix
window.applyErrorFix = function() {
    if (!currentErrorData || !currentErrorData.analysis.fix_code) return;

    const editor = document.getElementById('code-editor');
    if (editor) {
        editor.value = currentErrorData.analysis.fix_code;
        closeErrorExplainModal();

        // Optionally re-run the code
        if (confirm('Fix applied! Do you want to run the code again?')) {
            runRCode(editor.value);
        }
    }
};

// Copy the fix code
window.copyErrorFix = function() {
    if (!currentErrorData || !currentErrorData.analysis.fix_code) return;

    navigator.clipboard.writeText(currentErrorData.analysis.fix_code).then(() => {
        const btn = document.getElementById('copy-fix-btn');
        if (btn) {
            btn.innerHTML = '<span class="material-icons-round">check</span> Copied!';
            setTimeout(() => {
                btn.innerHTML = '<span class="material-icons-round">content_copy</span> Copy Fix';
            }, 2000);
        }
    });
};

// Ask AI for help with the error
window.askAIForHelp = async function() {
    if (!currentErrorData) return;

    const modal = document.getElementById('error-explain-modal');
    const whyText = document.getElementById('error-why-text');
    const suggestionText = document.getElementById('error-suggestion-text');
    const snippetSection = document.getElementById('error-code-snippet-section');
    const snippetCode = document.getElementById('error-code-snippet');

    // Show loading state
    whyText.innerHTML = '<span class="material-icons-round rotating">sync</span> Analyzing error...';
    suggestionText.textContent = 'Please wait...';

    try {
        const response = await fetch('/api/debug-code', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                error: currentErrorData.error,
                code: currentErrorData.code,
                columns: currentErrorData.analysis?.dataset_columns || []
            })
        });

        const data = await response.json();

        if (data.success) {
            whyText.textContent = data.explanation || 'An error occurred in your R code.';
            suggestionText.textContent = data.suggestion || 'Check your code for syntax errors.';

            // Show fixed code if available
            if (data.fixed_code) {
                currentErrorData.analysis.fix_available = true;
                currentErrorData.analysis.fix_code = data.fixed_code;

                document.getElementById('apply-fix-btn').style.display = 'flex';
                document.getElementById('copy-fix-btn').style.display = 'flex';

                snippetCode.textContent = data.fixed_code;
                snippetSection.style.display = 'block';
            }
            // Show code snippet example if available (no direct fix)
            else if (data.code_snippet) {
                snippetCode.textContent = data.code_snippet;
                snippetSection.style.display = 'block';
            }

            // Show dataset columns if available
            if (data.dataset_columns && data.dataset_columns.length > 0) {
                document.getElementById('error-columns-list').textContent = data.dataset_columns.join(', ');
                document.getElementById('error-columns-section').style.display = 'block';
            }

            // Show alternatives if available
            if (data.alternatives && data.alternatives.length > 0) {
                const altSection = document.getElementById('error-alternatives-section');
                const altList = document.getElementById('error-alternatives-list');
                altList.innerHTML = data.alternatives.map(alt => `
                    <div style="padding: 8px; background: var(--bg-secondary); border-radius: 4px; cursor: pointer; margin-bottom: 6px;"
                         onclick="selectAlternative('${alt.test || ''}', '${escapeHtml(alt.code || '')}')">
                        <strong>${escapeHtml(alt.name)}</strong>
                        <p style="font-size: 11px; color: var(--text-secondary); margin: 4px 0 0;">${escapeHtml(alt.description || '')}</p>
                    </div>
                `).join('');
                altSection.style.display = 'block';
            }
        } else {
            whyText.textContent = data.error || 'Could not analyze this error. Please check your code manually.';
            suggestionText.textContent = 'Try checking the BioStation documentation or asking in the community.';
        }
    } catch (error) {
        console.error('Error asking AI for help:', error);
        whyText.textContent = 'Network error: Could not reach the analysis service.';
        suggestionText.textContent = 'Please check your connection and try again.';
    }
};

// Select an alternative solution
window.selectAlternative = function(testId, code) {
    if (testId) {
        // Switch to a different test
        alert(`To use ${testId} instead, ask: "Run ${testId.replace('_', ' ')} on my data"`);
        closeErrorExplainModal();
    } else if (code) {
        // Apply the alternative code
        const editor = document.getElementById('code-editor');
        if (editor) {
            // Insert the code at cursor or append
            const cursorPos = editor.selectionStart;
            const before = editor.value.substring(0, cursorPos);
            const after = editor.value.substring(cursorPos);
            editor.value = before + '\n' + code + '\n' + after;
            closeErrorExplainModal();
        }
    }
};

// ============ HELP TAB SWITCHING (for Teach Modal) ============

window.switchHelpTab = function(tabName) {
    // Update tab buttons
    document.querySelectorAll('.help-tab').forEach(tab => {
        if (tab.dataset.helpTab === tabName) {
            tab.classList.add('active');
            tab.style.color = 'var(--text-primary)';
            tab.style.borderBottom = '2px solid var(--primary-color)';
        } else {
            tab.classList.remove('active');
            tab.style.color = 'var(--text-secondary)';
            tab.style.borderBottom = '2px solid transparent';
        }
    });

    // Update tab content
    document.querySelectorAll('.help-tab-content').forEach(content => {
        content.style.display = 'none';
    });

    const activeContent = document.getElementById(`help-${tabName}`);
    if (activeContent) {
        activeContent.style.display = 'block';
    }
};
