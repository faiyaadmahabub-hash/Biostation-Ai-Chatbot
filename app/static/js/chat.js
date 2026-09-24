// BioStation AI - Chat Interface with History Management

let currentConversationId = null;
let isProcessing = false;
let abortController = null; // New: controller for stopping requests
let currentPreviewData = null; // Store current preview data

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const stopBtn = document.getElementById('stop-btn'); // New
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-input');
const filePreviewArea = document.getElementById('file-preview-area'); // New
const emptyState = document.getElementById('empty-state');
const previewModal = document.getElementById('preview-modal');

let pendingAttachment = null; // New state
const historyList = document.getElementById('history-list');
const newChatBtn = document.getElementById('new-chat-btn');
const contextMenu = document.getElementById('context-menu');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');

// ============ INITIALIZATION ============

document.addEventListener('DOMContentLoaded', () => {
    loadConversations();
    userInput.focus();
    setupEventListeners();
    setupCodeBlockObserver(); // Watch for new code blocks
});

function setupEventListeners() {
    // Input handling
    userInput.addEventListener('input', handleInputChange);
    userInput.addEventListener('keydown', handleKeyDown);
    userInput.addEventListener('keydown', handleKeyDown);
    sendBtn.addEventListener('click', sendMessage);
    // Stop button listener
    if (stopBtn) {
        stopBtn.addEventListener('click', stopGeneration);
    }

    // File upload
    uploadBtn.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', handleFileUpload);

    // New chat
    newChatBtn.addEventListener('click', startNewChat);

    // Sidebar toggle
    sidebarToggle.addEventListener('click', toggleSidebar);

    // Close context menu on outside click
    document.addEventListener('click', (e) => {
        if (!contextMenu.contains(e.target)) {
            contextMenu.style.display = 'none';
        }
    });

    // Teach Bot
    const teachBtn = document.getElementById('teach-btn');
    if (teachBtn) {
        teachBtn.addEventListener('click', () => {
            document.getElementById('teach-modal').style.display = 'flex';
        });
        document.getElementById('close-teach-modal').addEventListener('click', () => {
            document.getElementById('teach-modal').style.display = 'none';
        });
        document.getElementById('save-concept-btn').addEventListener('click', saveConcept);
    }

    // Preview Modal
    setupPreviewModal();
}

function setupPreviewModal() {
    const closeBtn = document.getElementById('close-preview-modal');
    const refreshBtn = document.getElementById('refresh-preview-btn');
    const tabs = document.querySelectorAll('.preview-tab');

    if (closeBtn) {
        closeBtn.addEventListener('click', closePreviewModal);
    }

    if (refreshBtn) {
        refreshBtn.addEventListener('click', refreshPreview);
    }

    // Tab switching
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const tabName = tab.dataset.tab;
            switchPreviewTab(tabName);
        });
    });

    // Close on overlay click
    if (previewModal) {
        previewModal.addEventListener('click', (e) => {
            if (e.target === previewModal) {
                closePreviewModal();
            }
        });
    }
}

function setupCodeBlockObserver() {
    // Watch the chat messages container for new code blocks
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    // Find all code blocks in the new node
                    const codeBlocks = node.querySelectorAll ? node.querySelectorAll('code[class*="language-"]') : [];
                    codeBlocks.forEach(block => {
                        if (window.Prism && !block.classList.contains('prism-highlighted')) {
                            window.Prism.highlightElement(block);
                            block.classList.add('prism-highlighted');
                        }
                    });
                }
            });
        });
    });

    observer.observe(chatMessages, {
        childList: true,
        subtree: true
    });
}

// ============ SIDEBAR & HISTORY ============

async function loadConversations() {
    try {
        const response = await fetch('/api/conversations');
        const data = await response.json();

        if (data.success) {
            renderHistoryList(data.conversations);
        }
    } catch (error) {
        console.error('Failed to load conversations:', error);
        historyList.innerHTML = '<div class="history-error">Failed to load history</div>';
    }
}

function renderHistoryList(conversations) {
    if (!conversations || conversations.length === 0) {
        historyList.innerHTML = '<div class="no-history">No conversations yet</div>';
        return;
    }

    // Group by time
    const grouped = {};
    conversations.forEach(conv => {
        const group = conv.time_group;
        if (!grouped[group]) grouped[group] = [];
        grouped[group].push(conv);
    });

    let html = '';
    for (const [group, convs] of Object.entries(grouped)) {
        html += `<div class="history-group">
            <div class="history-label">${group}</div>`;

        convs.forEach(conv => {
            const isActive = conv.id === currentConversationId ? 'active' : '';
            html += `
            <div class="history-item ${isActive}" 
                 data-id="${conv.id}" 
                 onclick="loadConversation('${conv.id}')"
                 oncontextmenu="showContextMenu(event, '${conv.id}')">
                <span class="history-title">${escapeHtml(conv.title)}</span>
                <button class="history-menu-btn" onclick="event.stopPropagation(); showContextMenu(event, '${conv.id}')">
                    <span class="material-icons-round">more_horiz</span>
                </button>
            </div>`;
        });

        html += '</div>';
    }

    historyList.innerHTML = html;
}

async function loadConversation(convId) {
    try {
        const response = await fetch(`/api/conversations/${convId}`);
        const data = await response.json();

        if (data.success) {
            currentConversationId = convId;

            // Clear and hide empty state
            clearChatArea();
            hideEmptyState();

            // Render messages
            data.conversation.messages.forEach(msg => {
                if (msg.role === 'user') {
                    appendUserMessage(msg.content);
                } else {
                    appendBotMessage(msg.content);
                }
            });

            // Update active state in sidebar
            document.querySelectorAll('.history-item').forEach(item => {
                item.classList.remove('active');
                if (item.dataset.id === convId) {
                    item.classList.add('active');
                }
            });
        }
    } catch (error) {
        console.error('Failed to load conversation:', error);
    }
}

function startNewChat() {
    console.log('[BioStation] Starting new chat. Previous ID was:', currentConversationId);
    currentConversationId = null;
    console.log('[BioStation] Reset currentConversationId to:', currentConversationId);

    clearChatArea();
    showEmptyState();

    // Remove active state from all history items
    document.querySelectorAll('.history-item').forEach(item => {
        item.classList.remove('active');
    });

    userInput.focus();
}

function clearChatArea() {
    // Remove all message rows, keep empty state
    const messages = chatMessages.querySelectorAll('.message-row');
    messages.forEach(msg => msg.remove());
}

function showEmptyState() {
    if (emptyState) emptyState.style.display = 'flex';
}

function hideEmptyState() {
    if (emptyState) emptyState.style.display = 'none';
}

// Context Menu
let selectedConvId = null;

window.showContextMenu = function (event, convId) {
    event.preventDefault();
    event.stopPropagation();

    selectedConvId = convId;

    contextMenu.style.display = 'block';
    contextMenu.style.left = event.pageX + 'px';
    contextMenu.style.top = event.pageY + 'px';
};

document.getElementById('rename-chat').addEventListener('click', async () => {
    contextMenu.style.display = 'none';

    if (!selectedConvId) {
        console.error('[BioStation] No conversation selected for rename');
        return;
    }

    const newTitle = prompt('Enter new title:');
    if (newTitle && newTitle.trim()) {
        try {
            console.log('[BioStation] Renaming conversation:', selectedConvId, 'to:', newTitle.trim());
            const response = await fetch(`/api/conversations/${selectedConvId}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ title: newTitle.trim() })
            });
            const data = await response.json();

            if (data.success) {
                console.log('[BioStation] Rename successful');
                loadConversations();
            } else {
                console.error('[BioStation] Rename failed:', data.error);
                alert('Failed to rename: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[BioStation] Failed to rename:', error);
            alert('Failed to rename conversation');
        }
    }
});

document.getElementById('delete-chat').addEventListener('click', async () => {
    contextMenu.style.display = 'none';

    if (!selectedConvId) {
        console.error('[BioStation] No conversation selected for delete');
        return;
    }

    if (confirm('Delete this conversation?')) {
        try {
            console.log('[BioStation] Deleting conversation:', selectedConvId);
            const response = await fetch(`/api/conversations/${selectedConvId}`, {
                method: 'DELETE'
            });
            const data = await response.json();

            if (data.success) {
                console.log('[BioStation] Delete successful');

                // If deleted the current conversation, start new chat
                if (selectedConvId === currentConversationId) {
                    startNewChat();
                }

                loadConversations();
            } else {
                console.error('[BioStation] Delete failed:', data.error);
                alert('Failed to delete: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('[BioStation] Failed to delete:', error);
            alert('Failed to delete conversation');
        }
    }
});

function toggleSidebar() {
    sidebar.classList.toggle('collapsed');
}

// ============ CHAT MESSAGING ============

function handleInputChange() {
    // Auto-resize
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';

    // Toggle send button
    const hasContent = userInput.value.trim().length > 0 || pendingAttachment !== null;
    sendBtn.disabled = !hasContent;
}

function handleKeyDown(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

async function sendMessage() {
    const message = userInput.value.trim();
    if ((!message && !pendingAttachment) || isProcessing) return;

    hideEmptyState();
    hideEmptyState();
    isProcessing = true;
    sendBtn.disabled = true;

    // Create new abort controller
    abortController = new AbortController();
    toggleStopButton(true); // Show stop button

    // 1. Upload File if present
    if (pendingAttachment) {
        appendUserMessage(`📁 Uploading: ${pendingAttachment.name}...`);
        const loadingId = appendLoadingIndicator();

        try {
            const data = await uploadFileRequest(pendingAttachment);
            removeLoadingIndicator(loadingId);

            if (data.success) {
                // Build message with preview button
                let uploadMsg = `✅ **File Uploaded**: ${data.filename}\n`;
                uploadMsg += `**${data.rows.toLocaleString()}** rows × **${data.columns}** columns\n`;
                uploadMsg += `Variables: ${data.column_names.join(', ')}`;

                appendBotMessage(uploadMsg);

                // Add View Dataset button after upload
                addViewDatasetButton(data.preview);

                pendingAttachment = null;
                filePreviewArea.style.display = 'none';
                filePreviewArea.innerHTML = '';
                fileInput.value = '';
            } else {
                appendBotMessage(`❌ Upload Failed: ${data.error}`);
                isProcessing = false;
                handleInputChange(); // Reset button
                return;
            }
        } catch (e) {
            removeLoadingIndicator(loadingId);
            appendBotMessage("❌ Upload Network Error");
            isProcessing = false;
            handleInputChange();
            return;
        }
    }

    // 2. Send Message if present
    if (!message) {
        isProcessing = false;
        handleInputChange();
        return;
    }

    appendUserMessage(message);
    userInput.value = '';
    userInput.style.height = 'auto';

    const loadingId = appendLoadingIndicator();

    try {
        if (!currentConversationId) {
            const createRes = await fetch('/api/conversations', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({})
            });
            const createData = await createRes.json();
            if (createData.success) currentConversationId = createData.conversation_id;
        }

        const response = await fetch('/api/chat/stream', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: message,
                conversation_id: currentConversationId
            }),
            signal: abortController.signal
        });

        removeLoadingIndicator(loadingId);

        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);

        const botMessageId = 'bot-msg-' + Date.now();
        appendBotMessageStreaming(botMessageId);

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

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
                        if (data.type === 'prefix' || data.type === 'content') {
                            appendToStreamingMessage(botMessageId, data.content);
                        } else if (data.type === 'thinking') {
                            // Handle thinking indicators
                            handleThinkingIndicator(botMessageId, data.process, data.status);
                        } else if (data.type === 'done') {
                            // Re-run formatting on complete message to ensure code blocks are properly parsed
                            const messageEl = document.getElementById(botMessageId);
                            if (messageEl) {
                                const contentEl = messageEl.querySelector('.streaming-content');
                                if (contentEl && contentEl.dataset.rawMarkdown) {
                                    // Get raw markdown from data attribute and re-format completely
                                    contentEl.innerHTML = formatMessage(contentEl.dataset.rawMarkdown);
                                }
                            }
                            // Remove thinking indicators
                            removeThinkingIndicators(botMessageId);
                            // Note: Code explanation is now ON-DEMAND via Explain button (no auto-append)
                            enhanceCodeBlocks();
                            loadConversations();
                        } else if (data.type === 'error') {
                            appendToStreamingMessage(botMessageId, `\n\n⚠️ Error: ${data.content}`);
                        }
                    } catch (e) {
                        console.error('Error parsing SSE data:', e);
                    }
                }
            }
        }

    } catch (error) {
        removeLoadingIndicator(loadingId);
        if (error.name === 'AbortError') {
            appendBotMessage("🛑 **Response stopped by user.**");
        } else {
            appendBotMessage("⚠️ Network Error: Check your connection.");
            console.error('[BioStation] Error:', error);
        }
    } finally {
        isProcessing = false;
        abortController = null;
        toggleStopButton(false); // Hide stop button
        handleInputChange();
    }
}

function stopGeneration() {
    if (abortController) {
        abortController.abort();
        abortController = null;
    }
}

function toggleStopButton(show) {
    if (stopBtn) {
        stopBtn.style.display = show ? 'flex' : 'none';
        sendBtn.style.display = show ? 'none' : 'flex';
    }
}

// Quick action helper
window.setInput = function (text) {
    userInput.value = text;
    userInput.focus();
    handleInputChange();
};

// ============ MESSAGE RENDERING ============

function appendUserMessage(text) {
    const html = `
    <div class="message-row">
        <div class="message-container">
            <div class="message-content">
                <div class="message-sender-name">You</div>
                <div class="user-text">${formatMessage(text)}</div>
            </div>
        </div>
    </div>`;
    chatMessages.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
}

function appendBotMessage(text) {
    const html = `
    <div class="message-row">
        <div class="message-container">
            <div class="message-avatar bot-avatar-msg">🧬</div>
            <div class="message-content">
                <div class="message-sender-name">BioStation AI</div>
                <div class="bot-text">${formatMessage(text)}</div>
            </div>
        </div>
    </div>`;
    chatMessages.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
}

// === STREAMING HELPERS ===
function appendBotMessageStreaming(messageId) {
    const html = `
    <div class="message-row" id="${messageId}">
        <div class="message-container">
            <div class="message-avatar bot-avatar-msg">🧬</div>
            <div class="message-content">
                <div class="message-sender-name">BioStation AI</div>
                <div class="bot-text streaming-content"></div>
            </div>
        </div>
    </div>`;
    chatMessages.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
}

function appendToStreamingMessage(messageId, content) {
    const messageEl = document.getElementById(messageId);
    if (messageEl) {
        const contentEl = messageEl.querySelector('.streaming-content');
        if (contentEl) {
            // Store raw markdown in data attribute to preserve newlines and backticks
            const currentRaw = contentEl.dataset.rawMarkdown || '';
            contentEl.dataset.rawMarkdown = currentRaw + content;
            // Format from raw markdown, not textContent (which loses whitespace)
            contentEl.innerHTML = formatMessage(contentEl.dataset.rawMarkdown);
            scrollToBottom();
        }
    }
}

function appendLoadingIndicator() {
    const id = 'loading-' + Date.now();
    const html = `
    <div class="message-row" id="${id}">
        <div class="message-container">
            <div class="message-avatar bot-avatar-msg">🧬</div>
            <div class="message-content">
                <div class="message-sender-name">BioStation AI</div>
                <div class="bot-text"><span class="typing-dot">●</span><span class="typing-dot">●</span><span class="typing-dot">●</span></div>
            </div>
        </div>
    </div>`;
    chatMessages.insertAdjacentHTML('beforeend', html);
    scrollToBottom();
    return id;
}

function removeLoadingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function addViewDatasetButton(previewData) {
    // Add a View Dataset button after the last bot message
    const messages = chatMessages.querySelectorAll('.message-row');
    const lastMessage = messages[messages.length - 1];

    if (lastMessage) {
        const content = lastMessage.querySelector('.bot-text');
        if (content) {
            // Store preview data in window for access
            if (previewData) {
                window.lastUploadPreview = previewData;
            }

            const btnHtml = `
                <button class="view-dataset-btn" onclick="viewLastUpload()">
                    <span class="material-icons-round">table_view</span>
                    View Dataset
                </button>
            `;
            content.insertAdjacentHTML('beforeend', btnHtml);
        }
    }
}

// Function to view the last uploaded dataset
window.viewLastUpload = function () {
    if (window.lastUploadPreview) {
        openPreviewModal(window.lastUploadPreview);
    } else {
        // Fall back to fetching from API
        openPreviewModal();
    }
};

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatMessage(text) {
    // 1. Extract code blocks to prevent formatting interference
    const codeBlocks = [];
    // Allow any characters in language tag, and handle newline OR space separator
    let processed = text.replace(/```([^\n]*)\s+([\s\S]*?)```/g, (match, rawLang, code) => {
        // Sanitize language: remove non-alphanumeric chars (except -) and lower case
        let lang = (rawLang || '').trim().replace(/[^a-zA-Z0-9\-]/g, '').toLowerCase();
        if (lang === 'r#') lang = 'r'; // Explicit fix for common hallucination

        console.log('[formatMessage] Extracted code block:', { rawLang, lang, codeLength: code?.length });
        codeBlocks.push({ lang: lang || 'text', code: code });
        return `__CODE_BLOCK_${codeBlocks.length - 1}__`;
    });
    console.log('[formatMessage] Total code blocks found:', codeBlocks.length);

    // 2. Standard formatting
    // Inline code
    processed = processed.replace(/`([^`]+)`/g, '<code>$1</code>');
    // Bold
    processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Headers
    processed = processed.replace(/^## (.*?)$/gm, '<h3>$1</h3>');
    processed = processed.replace(/^### (.*?)$/gm, '<h4>$1</h4>');
    // Newlines -> <br> (only for non-code text)
    processed = processed.replace(/\n/g, '<br>');

    // 3. Restore code blocks WITH TOOLBARS
    processed = processed.replace(/__CODE_BLOCK_(\d+)__/g, (match, index) => {
        const block = codeBlocks[index];
        if (!block) {
            console.error('Code block not found:', index);
            return match; // Return placeholder as-is if block missing
        }

        const timestamp = Date.now() + index; // Unique ID for each code block

        // Create toolbar HTML
        const toolbar = `
            <div class="code-block-toolbar">
                <span class="code-lang">${block.lang || 'text'}</span>
                <div class="code-actions">
                    <button class="code-action-btn" onclick="copyCode(this)" title="Copy">
                        <span class="material-icons-round">content_copy</span>
                    </button>
                    <button class="code-action-btn" onclick="openInEditor(this)" title="Open in Editor">
                        <span class="material-icons-round">open_in_new</span>
                    </button>
                </div>
            </div>`;

        // Wrap in code-block-wrapper with toolbar
        return `
            <div class="code-block-wrapper" data-enhanced="true">
                ${toolbar}
                <pre><code class="language-${block.lang || 'text'}">${block.code || ''}</code></pre>
            </div>`;
    });

    // 4. Render markdown images with download button
    processed = processed.replace(/!\[(.*?)\]\((.*?)\)/g, (match, alt, url) => {
        return `
        <div class="result-image-wrapper">
            <img src="${url}" alt="${alt}" class="result-image">
            <a href="${url}" download="biostation_plot.jpg" class="download-plot-btn" title="Download Plot">
                <span class="material-icons-round">download</span>
            </a>
        </div>`;
    });

    return processed;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============ FILE UPLOAD ============

function handleFileUpload(e) {
    const file = e.target.files[0];
    if (!file) return;

    pendingAttachment = file;
    renderFilePreview(file);
    handleInputChange(); // Update button state

    // Clear input so same file can be selected again if cleared
    // But wait, if I clear input, file is gone from DOM element?
    // We stored it in pendingAttachment variable. So it's fine.
    // e.target.value = ''; 
    // Actually, don't clear e.target.value yet, clear it when removed/sent.
}

async function uploadFileRequest(file) {
    // Show hidden processing state if needed?
    // This function just handles the fetch.
    const formData = new FormData();
    formData.append('file', file);
    if (currentConversationId) {
        formData.append('conversation_id', currentConversationId);
    }

    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData
    });
    return await response.json();
}

// ============ FILE PREVIEW HELPERS ============

function renderFilePreview(file) {
    if (!file) return;
    filePreviewArea.style.display = 'block';

    const isCsv = file.name.endsWith('.csv');
    const isXls = file.name.match(/\.xlsx?$/);
    const icon = isCsv ? 'table_chart' : (isXls ? 'grid_on' : 'description');

    filePreviewArea.innerHTML = `
        <div class="file-chip">
            <div class="file-icon-wrapper">
                <span class="material-icons-round">${icon}</span>
            </div>
            <div class="file-info">
                <span class="file-name">${escapeHtml(file.name)}</span>
                <span class="file-type">${(file.size / 1024).toFixed(1)} KB</span>
            </div>
            <button class="file-remove-btn" onclick="clearAttachment()" title="Remove file">
                <span class="material-icons-round">close</span>
            </button>
        </div>
    `;
}

window.clearAttachment = function () {
    pendingAttachment = null;
    fileInput.value = '';
    filePreviewArea.style.display = 'none';
    filePreviewArea.innerHTML = '';
    handleInputChange();
};

// ============ TEACH BOT (Statistical Test) ============

async function saveConcept() {
    // Get all form elements
    const nameInput = document.getElementById('test-name');
    const keywordsInput = document.getElementById('test-keywords');
    const purposeInput = document.getElementById('test-purpose');
    const explanationInput = document.getElementById('test-explanation');
    const assumptionsInput = document.getElementById('test-assumptions');
    const rCodeInput = document.getElementById('test-r-code');
    const saveBtn = document.getElementById('save-concept-btn');
    const editTestId = document.getElementById('edit-test-id')?.value;

    // Collect values
    const name = nameInput.value.trim();
    const keywordsRaw = keywordsInput.value.trim();
    const purpose = purposeInput.value.trim();
    const explanation = explanationInput.value.trim();
    const assumptions = assumptionsInput.value.trim();
    const rCode = rCodeInput.value.trim();

    // Validate required fields
    if (!name) {
        alert("Please provide a Test Name.");
        nameInput.focus();
        return;
    }
    if (!explanation) {
        alert("Please provide an Explanation (this is used by the AI for interpretation).");
        explanationInput.focus();
        return;
    }
    if (!rCode) {
        alert("Please provide an R Code Template.");
        rCodeInput.focus();
        return;
    }

    const keywords = keywordsRaw.split(',').map(k => k.trim()).filter(k => k);

    saveBtn.disabled = true;
    const originalText = saveBtn.innerHTML;
    const isUpdate = !!editTestId;
    saveBtn.innerHTML = `<span class="material-icons-round">hourglass_empty</span> ${isUpdate ? 'Updating...' : 'Saving...'}`;

    try {
        // Determine endpoint and method based on create vs update
        const url = isUpdate ? `/teach/tests/${editTestId}` : '/teach';
        const method = isUpdate ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: name,
                keywords: keywords,
                purpose: purpose,
                explanation: explanation,
                assumptions: assumptions,
                r_code: rCode
            })
        });
        const result = await response.json();

        if (result.success) {
            const action = isUpdate ? 'updated' : 'learned';
            alert(`Statistical test "${name}" ${action} successfully!\n\nYou can now use it by asking questions like:\n"Run ${name} on my data"`);

            // Clear form and reset edit mode
            cancelEditTest();
            document.getElementById('teach-modal').style.display = 'none';
        } else {
            // Show validation errors nicely
            if (result.validation_error) {
                document.getElementById('r-code-validation').innerHTML =
                    `<span style="color: var(--error-color);">${result.error}</span>`;
                rCodeInput.focus();
            } else {
                alert("Error: " + (result.error || "Failed to save"));
            }
        }
    } catch (e) {
        console.error(e);
        alert("Network error: Failed to reach server.");
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

// Validate R code without saving
async function validateRCode() {
    const rCodeInput = document.getElementById('test-r-code');
    const validationDiv = document.getElementById('r-code-validation');
    const rCode = rCodeInput.value.trim();

    if (!rCode) {
        validationDiv.innerHTML = '<span style="color: var(--warning-color);">Please enter R code to validate.</span>';
        return;
    }

    validationDiv.innerHTML = '<span style="color: var(--text-secondary);">Validating...</span>';

    try {
        const response = await fetch('/teach/validate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ r_code: rCode })
        });
        const result = await response.json();

        if (result.valid) {
            validationDiv.innerHTML = '<span style="color: var(--success-color);">R code syntax is valid!</span>';
        } else {
            validationDiv.innerHTML = `<span style="color: var(--error-color);">Validation error: ${result.error}</span>`;
        }
    } catch (e) {
        console.error(e);
        validationDiv.innerHTML = '<span style="color: var(--error-color);">Failed to validate (network error)</span>';
    }
}

// Copy AI prompt to clipboard with fallback
function copyAIPrompt(btn) {
    const promptEl = document.getElementById('ai-prompt-template');
    const promptText = promptEl.innerText;

    // Try modern clipboard API first, with fallback
    copyToClipboard(promptText).then(success => {
        if (success) {
            const originalText = btn.innerText;
            btn.innerText = 'Copied!';
            btn.style.background = 'var(--success-color)';
            setTimeout(() => {
                btn.innerText = originalText;
                btn.style.background = 'var(--primary-color)';
            }, 2000);
        }
    });
}

// Universal clipboard copy with fallback
async function copyToClipboard(text) {
    // Try modern API first
    if (navigator.clipboard && navigator.clipboard.writeText) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.log('Clipboard API failed, using fallback');
        }
    }

    // Fallback: use textarea method
    try {
        const textarea = document.createElement('textarea');
        textarea.value = text;
        textarea.style.position = 'fixed';
        textarea.style.left = '-9999px';
        textarea.style.top = '-9999px';
        document.body.appendChild(textarea);
        textarea.focus();
        textarea.select();

        const success = document.execCommand('copy');
        document.body.removeChild(textarea);

        if (!success) {
            throw new Error('execCommand failed');
        }
        return true;
    } catch (err) {
        console.error('Fallback copy failed:', err);
        // Show manual copy instructions
        alert('Could not copy automatically.\n\nPlease select the text manually and press Ctrl+C to copy.');
        return false;
    }
}

// Make functions globally available
window.validateRCode = validateRCode;
window.copyAIPrompt = copyAIPrompt;
window.loadCustomTests = loadCustomTests;
window.editCustomTest = editCustomTest;
window.deleteCustomTest = deleteCustomTest;
window.cancelEditTest = cancelEditTest;
window.switchTeachTab = switchTeachTab;

// ============ TEACH MODAL - TAB SWITCHING ============

function setupTeachTabs() {
    const tabs = document.querySelectorAll('.teach-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            switchTeachTab(tab.dataset.tab);
        });
    });
}

function switchTeachTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.teach-tab').forEach(tab => {
        if (tab.dataset.tab === tabName) {
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
    document.getElementById('add-test-tab').style.display = tabName === 'add-test' ? 'block' : 'none';
    document.getElementById('manage-tests-tab').style.display = tabName === 'manage-tests' ? 'block' : 'none';

    // Load tests when switching to manage tab
    if (tabName === 'manage-tests') {
        loadCustomTests();
    }

    // Update modal title
    const title = document.getElementById('teach-modal-title');
    if (title) {
        title.textContent = tabName === 'add-test' ? 'Teach BioStation AI' : 'Manage Custom Tests';
    }
}

// ============ CUSTOM TEST MANAGEMENT ============

async function loadCustomTests() {
    const listContainer = document.getElementById('custom-tests-list');
    const noTestsMsg = document.getElementById('no-tests-message');

    listContainer.innerHTML = `
        <div class="loading-tests" style="text-align: center; padding: 40px; color: var(--text-secondary);">
            <span class="material-icons-round" style="font-size: 48px; margin-bottom: 10px;">hourglass_empty</span>
            <p>Loading your tests...</p>
        </div>
    `;
    noTestsMsg.style.display = 'none';

    try {
        const response = await fetch('/teach/tests');
        const result = await response.json();

        if (result.success && result.tests.length > 0) {
            listContainer.innerHTML = result.tests.map(test => `
                <div class="custom-test-item" style="background: var(--bg-secondary); border-radius: 8px; padding: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="flex: 1;">
                        <div style="font-weight: 600; color: var(--text-primary); margin-bottom: 5px;">
                            ${escapeHtml(test.name)}
                            <span style="font-size: 11px; padding: 2px 8px; background: var(--primary-color); color: white; border-radius: 10px; margin-left: 8px;">
                                ${escapeHtml(test.category)}
                            </span>
                        </div>
                        <div style="font-size: 13px; color: var(--text-secondary); margin-bottom: 5px;">
                            ${escapeHtml(test.purpose || 'No description')}
                        </div>
                        <div style="font-size: 11px; color: var(--text-tertiary);">
                            Keywords: ${test.keywords.slice(0, 5).map(k => `<code style="background: var(--bg-tertiary); padding: 1px 4px; border-radius: 3px;">${escapeHtml(k)}</code>`).join(' ')}
                            ${test.keywords.length > 5 ? `<span>+${test.keywords.length - 5} more</span>` : ''}
                        </div>
                    </div>
                    <div style="display: flex; gap: 8px; margin-left: 15px;">
                        <button onclick="editCustomTest('${test.id}')" class="btn-secondary" style="padding: 6px 12px; font-size: 12px; display: flex; align-items: center; gap: 4px;">
                            <span class="material-icons-round" style="font-size: 16px;">edit</span> Edit
                        </button>
                        <button onclick="deleteCustomTest('${test.id}', '${escapeHtml(test.name)}')" class="btn-danger" style="padding: 6px 12px; font-size: 12px; display: flex; align-items: center; gap: 4px; background: var(--error-color); color: white; border: none; border-radius: 6px; cursor: pointer;">
                            <span class="material-icons-round" style="font-size: 16px;">delete</span> Delete
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            listContainer.innerHTML = '';
            noTestsMsg.style.display = 'block';
        }
    } catch (e) {
        console.error('Failed to load custom tests:', e);
        listContainer.innerHTML = `
            <div style="text-align: center; padding: 40px; color: var(--error-color);">
                <span class="material-icons-round" style="font-size: 48px; margin-bottom: 10px;">error</span>
                <p>Failed to load tests. Please try again.</p>
            </div>
        `;
    }
}

async function editCustomTest(testId) {
    try {
        const response = await fetch(`/teach/tests/${testId}`);
        const result = await response.json();

        if (result.success && result.test) {
            const test = result.test;

            // Populate form fields
            document.getElementById('test-name').value = test.name || '';
            document.getElementById('test-keywords').value = (test.keywords || []).join(', ');
            document.getElementById('test-purpose').value = test.purpose || '';
            document.getElementById('test-explanation').value = test.explanation || '';
            document.getElementById('test-assumptions').value = test.assumptions || '';
            document.getElementById('test-r-code').value = test.r_template || '';

            // Set edit mode
            document.getElementById('edit-test-id').value = testId;
            document.getElementById('save-btn-text').textContent = 'Update Test';
            document.getElementById('cancel-edit-btn').style.display = 'inline-flex';

            // Switch to Add Test tab
            switchTeachTab('add-test');

            // Update modal title
            const title = document.getElementById('teach-modal-title');
            if (title) {
                title.textContent = `Edit: ${test.name}`;
            }
        } else {
            alert('Failed to load test details: ' + (result.error || 'Unknown error'));
        }
    } catch (e) {
        console.error('Failed to edit test:', e);
        alert('Network error: Failed to load test details.');
    }
}

async function deleteCustomTest(testId, testName) {
    if (!confirm(`Are you sure you want to delete "${testName}"?\n\nThis action cannot be undone.`)) {
        return;
    }

    try {
        const response = await fetch(`/teach/tests/${testId}`, {
            method: 'DELETE'
        });
        const result = await response.json();

        if (result.success) {
            alert(`Test "${testName}" deleted successfully.`);
            loadCustomTests(); // Refresh the list
        } else {
            alert('Failed to delete test: ' + (result.error || 'Unknown error'));
        }
    } catch (e) {
        console.error('Failed to delete test:', e);
        alert('Network error: Failed to delete test.');
    }
}

function cancelEditTest() {
    // Clear form
    document.getElementById('test-name').value = '';
    document.getElementById('test-keywords').value = '';
    document.getElementById('test-purpose').value = '';
    document.getElementById('test-explanation').value = '';
    document.getElementById('test-assumptions').value = '';
    document.getElementById('test-r-code').value = '';
    document.getElementById('r-code-validation').innerHTML = '';

    // Reset edit mode
    document.getElementById('edit-test-id').value = '';
    document.getElementById('save-btn-text').textContent = 'Save Statistical Test';
    document.getElementById('cancel-edit-btn').style.display = 'none';

    // Reset modal title
    const title = document.getElementById('teach-modal-title');
    if (title) {
        title.textContent = 'Teach BioStation AI';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Initialize teach tabs on page load
document.addEventListener('DOMContentLoaded', () => {
    setupTeachTabs();
});

// ============ CODE BLOCK ENHANCEMENT ============

function enhanceCodeBlocks() {
    // Toolbars are now embedded in formatMessage()
    // This function just triggers Prism highlighting
    const codeBlocks = document.querySelectorAll('pre code');
    codeBlocks.forEach((block) => {
        if (window.Prism && !block.classList.contains('prism-highlighted')) {
            window.Prism.highlightElement(block);
            block.classList.add('prism-highlighted');
        }
    });
}

function copyCode(btn) {
    const wrapper = btn.closest('.code-block-wrapper');
    const code = wrapper.querySelector('code').innerText;
    navigator.clipboard.writeText(code).then(() => {
        const icon = btn.querySelector('.material-icons-round');
        icon.textContent = 'check';
        setTimeout(() => icon.textContent = 'content_copy', 2000);
    });
}

function openInEditor(btn) {
    const wrapper = btn.closest('.code-block-wrapper');
    const code = wrapper.querySelector('code').innerText;
    if (window.openCodeEditor) {
        window.openCodeEditor(code);
    } else {
        console.error('Code Editor not loaded');
    }
}

// ============ DATA PREVIEW FUNCTIONS ============

async function openPreviewModal(previewData = null) {
    if (previewData) {
        currentPreviewData = previewData;
        renderPreview(previewData);
        document.getElementById('preview-modal').style.display = 'flex';
    } else {
        // Fetch from API
        await fetchAndShowPreview();
    }
}

function closePreviewModal() {
    document.getElementById('preview-modal').style.display = 'none';
}

async function fetchAndShowPreview() {
    const container = document.getElementById('preview-container');
    const modal = document.getElementById('preview-modal');

    // Show loading state
    modal.style.display = 'flex';
    showPreviewLoading();

    try {
        const response = await fetch('/api/dataset-preview');
        const data = await response.json();

        if (data.success && data.preview) {
            currentPreviewData = data.preview;
            document.getElementById('preview-modal-title').textContent = `Dataset Preview: ${data.filename}`;
            renderPreview(data.preview);
        } else {
            showPreviewError(data.error || 'No dataset loaded');
        }
    } catch (error) {
        console.error('Error fetching preview:', error);
        showPreviewError('Failed to load preview');
    }
}

async function refreshPreview() {
    const refreshBtn = document.getElementById('refresh-preview-btn');
    const originalText = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<span class="material-icons-round rotating">refresh</span> Refreshing...';
    refreshBtn.disabled = true;

    try {
        const response = await fetch('/api/dataset-preview/refresh', { method: 'POST' });
        const data = await response.json();

        if (data.success && data.preview) {
            currentPreviewData = data.preview;
            renderPreview(data.preview);
        } else {
            showPreviewError(data.error || 'Failed to refresh');
        }
    } catch (error) {
        console.error('Error refreshing preview:', error);
        showPreviewError('Failed to refresh preview');
    } finally {
        refreshBtn.innerHTML = originalText;
        refreshBtn.disabled = false;
    }
}

function showPreviewLoading() {
    const dataTab = document.getElementById('preview-data-tab');
    dataTab.innerHTML = `
        <div class="preview-loading">
            <span class="material-icons-round">hourglass_empty</span>
            <p>Loading preview...</p>
        </div>
    `;
}

function showPreviewError(message) {
    const dataTab = document.getElementById('preview-data-tab');
    dataTab.innerHTML = `
        <div class="preview-loading">
            <span class="material-icons-round" style="color: #ef4444;">error</span>
            <p>${escapeHtml(message)}</p>
        </div>
    `;
}

function switchPreviewTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.preview-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.tab === tabName);
    });

    // Show/hide tab content
    document.getElementById('preview-data-tab').style.display = tabName === 'data' ? 'block' : 'none';
    document.getElementById('preview-columns-tab').style.display = tabName === 'columns' ? 'block' : 'none';
    document.getElementById('preview-stats-tab').style.display = tabName === 'stats' ? 'block' : 'none';
}

function renderPreview(preview) {
    if (!preview || !preview.success) {
        showPreviewError('Invalid preview data');
        return;
    }

    renderDataTab(preview);
    renderColumnsTab(preview);
    renderStatsTab(preview);

    // Reset to data tab
    switchPreviewTab('data');
}

function renderDataTab(preview) {
    const container = document.getElementById('preview-data-tab');
    const head = preview.head;
    const shape = preview.shape;

    // Summary section
    let summaryHtml = `
        <div class="preview-summary" id="preview-summary">
            <div class="preview-summary-item">
                <span class="preview-summary-label">Rows</span>
                <span class="preview-summary-value">${shape.rows.toLocaleString()}</span>
            </div>
            <div class="preview-summary-item">
                <span class="preview-summary-label">Columns</span>
                <span class="preview-summary-value">${shape.columns}</span>
            </div>
            <div class="preview-summary-item">
                <span class="preview-summary-label">Numeric</span>
                <span class="preview-summary-value">${preview.summary.n_numeric}</span>
            </div>
            <div class="preview-summary-item">
                <span class="preview-summary-label">Categorical</span>
                <span class="preview-summary-value">${preview.summary.n_categorical}</span>
            </div>
            <div class="preview-summary-item">
                <span class="preview-summary-label">Memory</span>
                <span class="preview-summary-value">${preview.summary.memory_usage_mb} MB</span>
            </div>
        </div>
    `;

    // Table section
    let tableHtml = '<div class="preview-table-wrapper"><table class="preview-table">';

    // Header
    tableHtml += '<thead><tr>';
    tableHtml += '<th>#</th>'; // Row number
    head.column_names.forEach(col => {
        tableHtml += `<th>${escapeHtml(col)}</th>`;
    });
    tableHtml += '</tr></thead>';

    // Body
    tableHtml += '<tbody>';
    head.rows.forEach((row, idx) => {
        tableHtml += '<tr>';
        tableHtml += `<td style="color: #666;">${idx + 1}</td>`;
        row.forEach((val, colIdx) => {
            const colInfo = preview.columns[colIdx];
            const isNumeric = colInfo && colInfo.type_category === 'numeric';

            if (val === null || val === undefined) {
                tableHtml += '<td class="null-value">null</td>';
            } else if (isNumeric) {
                tableHtml += `<td class="numeric-value">${val}</td>`;
            } else {
                tableHtml += `<td>${escapeHtml(String(val))}</td>`;
            }
        });
        tableHtml += '</tr>';
    });
    tableHtml += '</tbody></table></div>';

    // Footer info
    let footerHtml = '';
    if (head.displayed_rows < head.total_rows) {
        footerHtml = `<p style="text-align: center; color: var(--text-secondary); font-size: 0.85rem; margin-top: 12px;">
            Showing ${head.displayed_rows} of ${head.total_rows.toLocaleString()} rows
        </p>`;
    }

    container.innerHTML = summaryHtml + tableHtml + footerHtml;
}

function renderColumnsTab(preview) {
    const container = document.getElementById('columns-list');
    let html = '';

    preview.columns.forEach(col => {
        const typeClass = col.type_category;
        const hasStats = col.stats && Object.keys(col.stats).length > 0;
        const hasUniqueValues = col.unique_values && col.unique_values.length > 0;

        html += `
            <div class="column-card">
                <div class="column-card-header">
                    <span class="column-name">${escapeHtml(col.name)}</span>
                    <span class="column-type-badge ${typeClass}">${col.type_category}</span>
                </div>
                <div class="column-info">
                    <div class="column-info-row">
                        <span>Data Type</span>
                        <span>${col.dtype}</span>
                    </div>
                    <div class="column-info-row">
                        <span>Non-null</span>
                        <span>${col.non_null_count.toLocaleString()}</span>
                    </div>
                    <div class="column-info-row">
                        <span>Missing</span>
                        <span style="color: ${col.null_count > 0 ? '#ef4444' : 'inherit'};">${col.null_count.toLocaleString()}</span>
                    </div>
                    ${col.n_unique !== undefined ? `
                    <div class="column-info-row">
                        <span>Unique Values</span>
                        <span>${col.n_unique}</span>
                    </div>` : ''}
                </div>
                ${hasStats ? renderColumnStats(col.stats) : ''}
                ${hasUniqueValues ? renderUniqueValues(col.unique_values) : ''}
            </div>
        `;
    });

    container.innerHTML = html;
}

function renderColumnStats(stats) {
    return `
        <div class="column-stats">
            <div class="column-stats-grid">
                <div class="column-stat-item">
                    <span class="column-stat-label">Min</span>
                    <span class="column-stat-value">${stats.min !== null ? stats.min : '-'}</span>
                </div>
                <div class="column-stat-item">
                    <span class="column-stat-label">Max</span>
                    <span class="column-stat-value">${stats.max !== null ? stats.max : '-'}</span>
                </div>
                <div class="column-stat-item">
                    <span class="column-stat-label">Mean</span>
                    <span class="column-stat-value">${stats.mean !== null ? stats.mean : '-'}</span>
                </div>
                <div class="column-stat-item">
                    <span class="column-stat-label">Median</span>
                    <span class="column-stat-value">${stats.median !== null ? stats.median : '-'}</span>
                </div>
            </div>
        </div>
    `;
}

function renderUniqueValues(values) {
    return `
        <div class="unique-values-list">
            <div class="unique-values-label">Values:</div>
            ${values.map(v => `<span class="unique-value-chip">${escapeHtml(v)}</span>`).join('')}
        </div>
    `;
}

function renderStatsTab(preview) {
    const container = document.getElementById('stats-container');
    const missing = preview.missing_values;
    const summary = preview.summary;

    let html = `
        <div class="stats-section">
            <div class="stats-section-title">
                <span class="material-icons-round">analytics</span>
                Overview
            </div>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-card-value">${preview.shape.rows.toLocaleString()}</div>
                    <div class="stat-card-label">Total Rows</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${preview.shape.columns}</div>
                    <div class="stat-card-label">Total Columns</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${summary.n_numeric}</div>
                    <div class="stat-card-label">Numeric Columns</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${summary.n_categorical}</div>
                    <div class="stat-card-label">Categorical Columns</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${summary.memory_usage_mb} MB</div>
                    <div class="stat-card-label">Memory Usage</div>
                </div>
            </div>
        </div>
    `;

    // Missing values section
    html += `
        <div class="stats-section">
            <div class="stats-section-title">
                <span class="material-icons-round">warning</span>
                Missing Values
            </div>
            <div class="stats-grid" style="margin-bottom: 16px;">
                <div class="stat-card">
                    <div class="stat-card-value" style="color: ${missing.total_missing > 0 ? '#ef4444' : 'var(--accent-color)'};">
                        ${missing.total_missing.toLocaleString()}
                    </div>
                    <div class="stat-card-label">Total Missing</div>
                </div>
                <div class="stat-card">
                    <div class="stat-card-value">${missing.missing_pct}%</div>
                    <div class="stat-card-label">Missing Percentage</div>
                </div>
            </div>
    `;

    if (missing.columns_with_missing.length > 0) {
        html += '<div class="missing-values-list">';
        missing.columns_with_missing.forEach(col => {
            html += `
                <div class="missing-item">
                    <span class="missing-item-name">${escapeHtml(col.column)}</span>
                    <div class="missing-item-value">
                        <span class="missing-count">${col.missing_count.toLocaleString()}</span>
                        <span class="missing-pct">(${col.missing_pct}%)</span>
                    </div>
                </div>
            `;
        });
        html += '</div>';
    } else {
        html += '<p style="color: var(--accent-color);">No missing values found!</p>';
    }

    html += '</div>';

    // Column types breakdown
    if (summary.numeric_columns.length > 0 || summary.categorical_columns.length > 0) {
        html += `
            <div class="stats-section">
                <div class="stats-section-title">
                    <span class="material-icons-round">category</span>
                    Column Types
                </div>
                <div style="display: flex; gap: 20px; flex-wrap: wrap;">
        `;

        if (summary.numeric_columns.length > 0) {
            html += `
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="color: var(--accent-color); margin-bottom: 8px; font-size: 0.9rem;">Numeric (${summary.numeric_columns.length})</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                        ${summary.numeric_columns.map(c => `<span class="unique-value-chip">${escapeHtml(c)}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        if (summary.categorical_columns.length > 0) {
            html += `
                <div style="flex: 1; min-width: 200px;">
                    <h4 style="color: #a390ff; margin-bottom: 8px; font-size: 0.9rem;">Categorical (${summary.categorical_columns.length})</h4>
                    <div style="display: flex; flex-wrap: wrap; gap: 4px;">
                        ${summary.categorical_columns.map(c => `<span class="unique-value-chip">${escapeHtml(c)}</span>`).join('')}
                    </div>
                </div>
            `;
        }

        html += '</div></div>';
    }

    container.innerHTML = html;
}

// Global function to open preview from anywhere
window.openDataPreview = openPreviewModal;
window.viewDataset = function () {
    openPreviewModal();
};

// ============ THINKING INDICATORS ============

function handleThinkingIndicator(messageId, process, status) {
    const messageEl = document.getElementById(messageId);
    if (!messageEl) return;

    let indicatorsContainer = messageEl.querySelector('.thinking-indicators');

    // Create container if it doesn't exist
    if (!indicatorsContainer) {
        indicatorsContainer = document.createElement('div');
        indicatorsContainer.className = 'thinking-indicators';
        const contentEl = messageEl.querySelector('.message-content');
        if (contentEl) {
            contentEl.insertBefore(indicatorsContainer, contentEl.querySelector('.bot-text'));
        }
    }

    const indicatorId = `thinking-${process}-${messageId}`;
    let indicator = document.getElementById(indicatorId);

    if (status === 'start') {
        // Create indicator if it doesn't exist
        if (!indicator) {
            indicator = document.createElement('div');
            indicator.id = indicatorId;
            indicator.className = `thinking-indicator ${process}`;

            const icon = process === 'interpretation' ? 'analytics' : 'psychology';
            const text = process === 'interpretation' ? 'Thinking...' : 'Generating explanation...';

            indicator.innerHTML = `
                <div class="thinking-spinner"></div>
                <span class="material-icons-round thinking-icon">${icon}</span>
                <span class="thinking-text">${text}</span>
            `;
            indicatorsContainer.appendChild(indicator);
        }
        indicator.classList.add('active');
        indicator.classList.remove('done');
    } else if (status === 'done') {
        if (indicator) {
            indicator.classList.remove('active');
            indicator.classList.add('done');
            // Update text to show completion
            const textEl = indicator.querySelector('.thinking-text');
            if (textEl) {
                const doneText = process === 'interpretation' ? 'Done!' : 'Explanation ready';
                textEl.textContent = doneText;
            }
            // Replace spinner with checkmark
            const spinnerEl = indicator.querySelector('.thinking-spinner');
            if (spinnerEl) {
                spinnerEl.outerHTML = '<span class="material-icons-round thinking-check">check_circle</span>';
            }
        }
    } else if (status === 'error') {
        if (indicator) {
            indicator.classList.remove('active');
            indicator.classList.add('error');
            const textEl = indicator.querySelector('.thinking-text');
            if (textEl) {
                textEl.textContent = process === 'interpretation' ? 'Interpretation failed' : 'Explanation failed';
            }
        }
    }
}

function removeThinkingIndicators(messageId) {
    const messageEl = document.getElementById(messageId);
    if (!messageEl) return;

    const indicatorsContainer = messageEl.querySelector('.thinking-indicators');
    if (indicatorsContainer) {
        // Fade out and remove after animation
        indicatorsContainer.classList.add('fade-out');
        setTimeout(() => {
            indicatorsContainer.remove();
        }, 500);
    }
}

// ============ CODE EXPLANATION SECTION ============

function appendCodeExplanationSection(messageId, explanationData) {
    const messageEl = document.getElementById(messageId);
    if (!messageEl) return;

    const contentEl = messageEl.querySelector('.bot-text, .streaming-content');
    if (!contentEl) return;

    const summary = explanationData.summary || {};
    const explanation = explanationData.content || '';
    const code = explanationData.code || '';

    // Generate unique ID for this code block
    const codeBlockId = 'explain-code-' + Date.now();

    // Create the explanation section HTML with code reference
    const sectionHtml = `
        <div class="code-explanation-section">
            <div class="code-explanation-header" onclick="toggleCodeExplanation(this)">
                <div class="code-explanation-title">
                    <span class="material-icons-round">psychology</span>
                    <span>AI Code Explanation</span>
                </div>
                <div class="code-explanation-summary-badges">
                    ${summary.detected_test ? `
                        <span class="explain-badge test-type">
                            <span class="material-icons-round">science</span>
                            ${escapeHtml(summary.detected_test)}
                        </span>
                    ` : ''}
                    ${summary.total_lines ? `
                        <span class="explain-badge">
                            <span class="material-icons-round">code</span>
                            ${summary.total_lines} lines
                        </span>
                    ` : ''}
                    ${summary.packages_used && summary.packages_used.length > 0 ? `
                        <span class="explain-badge">
                            <span class="material-icons-round">inventory_2</span>
                            ${summary.packages_used.join(', ')}
                        </span>
                    ` : ''}
                    ${summary.has_visualization ? `
                        <span class="explain-badge viz">
                            <span class="material-icons-round">bar_chart</span>
                            Visualization
                        </span>
                    ` : ''}
                </div>
                <span class="material-icons-round expand-icon">expand_more</span>
            </div>
            <div class="code-explanation-content collapsed">
                ${code ? `
                    <div class="explanation-code-reference">
                        <div class="explanation-code-header">
                            <span class="code-lang-label">r</span>
                            <button class="copy-explain-code-btn" onclick="copyExplanationCode(this, event)" data-code-id="${codeBlockId}">
                                <span class="material-icons-round">content_copy</span>
                                Copy code
                            </button>
                        </div>
                        <pre class="explanation-code-block"><code id="${codeBlockId}" class="language-r">${escapeHtml(code)}</code></pre>
                    </div>
                ` : ''}
                <div class="explanation-text-content">
                    ${formatExplanationContent(explanation)}
                </div>
            </div>
        </div>
    `;

    contentEl.insertAdjacentHTML('beforeend', sectionHtml);

    // Apply syntax highlighting to the code block if Prism is available
    if (window.Prism) {
        const codeEl = document.getElementById(codeBlockId);
        if (codeEl) {
            Prism.highlightElement(codeEl);
        }
    }
}

// Copy code from explanation section
window.copyExplanationCode = function (btn, event) {
    event.stopPropagation(); // Prevent toggle when clicking copy button

    const codeId = btn.dataset.codeId;
    const codeEl = document.getElementById(codeId);

    if (codeEl) {
        navigator.clipboard.writeText(codeEl.textContent).then(() => {
            btn.innerHTML = '<span class="material-icons-round">check</span> Copied!';
            setTimeout(() => {
                btn.innerHTML = '<span class="material-icons-round">content_copy</span> Copy code';
            }, 2000);
        });
    }
};

function formatExplanationContent(text) {
    if (!text) return '<p>No explanation available.</p>';

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

    // Paragraphs
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';

    // Clean up
    html = html.replace(/<p>\s*<\/p>/g, '');
    html = html.replace(/<p>(\s*<[hul])/g, '$1');
    html = html.replace(/(<\/[hul][^>]*>)\s*<\/p>/g, '$1');

    return html;
}

window.toggleCodeExplanation = function (headerEl) {
    const section = headerEl.closest('.code-explanation-section');
    const content = section.querySelector('.code-explanation-content');
    const expandIcon = section.querySelector('.expand-icon');

    if (content.classList.contains('collapsed')) {
        content.classList.remove('collapsed');
        content.classList.add('expanded');
        expandIcon.textContent = 'expand_less';
    } else {
        content.classList.remove('expanded');
        content.classList.add('collapsed');
        expandIcon.textContent = 'expand_more';
    }
};
