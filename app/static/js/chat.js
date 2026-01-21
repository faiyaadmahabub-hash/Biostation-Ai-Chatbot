// BioStation AI - Chat Interface with History Management

let currentConversationId = null;
let isProcessing = false;
let abortController = null; // New: controller for stopping requests

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const stopBtn = document.getElementById('stop-btn'); // New
const uploadBtn = document.getElementById('upload-btn');
const fileInput = document.getElementById('file-input');
const filePreviewArea = document.getElementById('file-preview-area'); // New
const emptyState = document.getElementById('empty-state');

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
                appendBotMessage(`✅ **File Uploaded**: ${data.filename}\nVariables: ${data.column_names.join(', ')}`);
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

// ============ TEACH BOT ============

async function saveConcept() {
    const titleInput = document.getElementById('concept-title');
    const keywordsInput = document.getElementById('concept-keywords');
    const contentInput = document.getElementById('concept-content');
    const saveBtn = document.getElementById('save-concept-btn');

    const title = titleInput.value.trim();
    const keywordsRaw = keywordsInput.value.trim();
    const content = contentInput.value.trim();

    if (!title || !content) {
        alert("Please provide at least a Title and Explanation.");
        return;
    }

    const keywords = keywordsRaw.split(',').map(k => k.trim()).filter(k => k);

    saveBtn.disabled = true;
    const originalText = saveBtn.innerHTML;
    saveBtn.textContent = "Saving...";

    try {
        const response = await fetch('/teach', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                title: title,
                content: content,
                keywords: keywords
            })
        });
        const result = await response.json();

        if (result.success) {
            alert("🎓 Knowledge added successfully! I can now answer questions about this.");
            document.getElementById('teach-modal').style.display = 'none';

            // Clear form
            titleInput.value = '';
            keywordsInput.value = '';
            contentInput.value = '';
        } else {
            alert("Error: " + (result.error || "Failed to save"));
        }
    } catch (e) {
        console.error(e);
        alert("Network error: Failed to reach server.");
    } finally {
        saveBtn.disabled = false;
        saveBtn.innerHTML = originalText;
    }
}

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
