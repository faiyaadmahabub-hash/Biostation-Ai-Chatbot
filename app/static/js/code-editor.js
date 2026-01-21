// BioStation AI - Code Editor and Visualization Module

// Code Editor State
let currentCode = '';

// Initialize code editor functionality
document.addEventListener('DOMContentLoaded', () => {
    setupCodeEditor();
    setupVizModal();
});

function setupCodeEditor() {
    const modal = document.getElementById('code-editor-modal');
    const closeBtn = document.getElementById('close-code-modal');
    const copyBtn = document.getElementById('copy-code-btn');
    const downloadBtn = document.getElementById('download-code-btn');
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
