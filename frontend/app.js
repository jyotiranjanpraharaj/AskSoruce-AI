// DOM Elements
const btnAttach = document.getElementById('btn-attach');
const btnWelcomeUpload = document.getElementById('btn-welcome-upload');
const fileInput = document.getElementById('file-input');

// Real-time Upload Progress Bar Elements
const progressContainer = document.getElementById('progress-container');
const progressStatus = document.getElementById('progress-status');
const progressPercent = document.getElementById('progress-percent');
const progressBarFill = document.getElementById('progress-bar-fill');

// Selected File Chip (for removal/state display)
const fileChip = document.getElementById('file-chip');
const fileChipName = document.getElementById('file-chip-name');
const fileChipSpinner = document.getElementById('file-chip-spinner');
const btnRemoveFile = document.getElementById('btn-remove-file');

const docList = document.getElementById('documents-list');
const currentDocTitle = document.getElementById('current-doc-title');

const chatWelcome = document.getElementById('chat-welcome');
const chatMessages = document.getElementById('chat-messages');
const chatMessagesWrapper = document.querySelector('.chat-messages-wrapper');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const btnNewChat = document.getElementById('btn-new-chat');
const featureCards = document.querySelectorAll('.feature-card');

// App State
let activeDocName = null;
let isUploading = false;
const API_BASE_URL = window.location.origin;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkDatabaseStatus();
    setupAttachmentHandlers();
    setupChatHandlers();
    setupFeatureCards();
});

// Check Database Status
async function checkDatabaseStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/status`);
        if (!response.ok) throw new Error('Failed to fetch status');
        
        const data = await response.json();
        
        if (data.database_exists && data.filename) {
            // Restore active document but do NOT append system message or force transition to chat messages
            // Keep the chat messages clean and display the welcome screen by default on startup
            setActiveDocument(data.filename);
            showChatLogs(false); // Fix: Do not auto-switch to chat messages log on startup
        } else {
            setActiveDocument(null);
            showChatLogs(false);
        }
    } catch (error) {
        console.error('Error fetching database status:', error);
        setActiveDocument(null);
        showChatLogs(false);
    }
}

function setActiveDocument(filename) {
    activeDocName = filename;
    if (filename) {
        currentDocTitle.textContent = filename;
        docList.innerHTML = `
            <div class="doc-item active">
                <i class="fa-solid fa-file-lines"></i>
                <span class="doc-item-title" title="${escapeHtml(filename)}">${escapeHtml(filename)}</span>
                <button class="btn-delete-doc" id="btn-delete-doc" title="Delete document database">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
        `;
        enableChat(true);
        setupSidebarDeleteHandler();
    } else {
        currentDocTitle.textContent = 'Study mate';
        docList.innerHTML = '<div class="no-docs-text">No document loaded</div>';
        enableChat(false);
    }
}

function setupSidebarDeleteHandler() {
    const btnDeleteDoc = document.getElementById('btn-delete-doc');
    if (btnDeleteDoc) {
        btnDeleteDoc.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (confirm(`Are you sure you want to delete and reset the database for "${activeDocName}"?`)) {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/clear`, {
                        method: 'POST'
                    });
                    if (!response.ok) throw new Error('Failed to clear database');
                    
                    setActiveDocument(null);
                    showChatLogs(false);
                    alert('Database cleared successfully!');
                } catch (error) {
                    console.error('Error clearing database:', error);
                    alert(`Failed to delete: ${error.message}`);
                }
            }
        });
    }
}

function showChatLogs(show) {
    if (show) {
        chatWelcome.style.display = 'none';
        chatMessages.style.display = 'flex';
    } else {
        chatWelcome.style.display = 'flex';
        chatMessages.style.display = 'none';
        chatMessages.innerHTML = '';
    }
}

function enableChat(enabled) {
    chatInput.disabled = !enabled;
    btnSend.disabled = !enabled;
    if (enabled) {
        chatInput.placeholder = 'Ask Study mate...';
    } else {
        chatInput.placeholder = 'Attach a document below to start...';
    }
}

// Upload & Attachment Logic
function setupAttachmentHandlers() {
    // Both paperclip and welcome area buttons open file selector
    btnAttach.addEventListener('click', () => {
        if (!isUploading) fileInput.click();
    });

    if (btnWelcomeUpload) {
        btnWelcomeUpload.addEventListener('click', () => {
            if (!isUploading) fileInput.click();
        });
    }

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    btnRemoveFile.addEventListener('click', () => {
        fileChip.style.display = 'none';
        fileInput.value = '';
    });
}

function uploadFile(file) {
    isUploading = true;
    
    // Hide status chip and show progress bar
    fileChip.style.display = 'none';
    progressContainer.style.display = 'block';
    progressStatus.textContent = 'Uploading document...';
    progressPercent.textContent = '0%';
    progressBarFill.style.width = '0%';
    
    // Disable inputs
    btnAttach.disabled = true;
    if (btnWelcomeUpload) btnWelcomeUpload.disabled = true;
    enableChat(false);
    
    const formData = new FormData();
    formData.append('file', file);
    
    const xhr = new XMLHttpRequest();
    
    // Tracks upload progress (0% to 90% upload, 90% to 100% backend indexing)
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            const displayPercent = Math.round(percent * 0.9);
            progressPercent.textContent = `${displayPercent}%`;
            progressBarFill.style.width = `${displayPercent}%`;
            if (percent === 100) {
                progressStatus.textContent = 'Processing and indexing document...';
            }
        }
    });
    
    xhr.addEventListener('load', () => {
        if (xhr.status >= 200 && xhr.status < 300) {
            // Success
            progressPercent.textContent = '100%';
            progressBarFill.style.width = '100%';
            
            setTimeout(() => {
                progressContainer.style.display = 'none';
                
                setActiveDocument(file.name);
                showChatLogs(true);
                appendSystemMessage(`Document <strong>${escapeHtml(file.name)}</strong> processed and indexed successfully!`);
                
                isUploading = false;
                btnAttach.disabled = false;
                if (btnWelcomeUpload) btnWelcomeUpload.disabled = false;
            }, 600);
            
        } else {
            let errorMsg = 'Upload failed';
            try {
                const err = JSON.parse(xhr.responseText);
                errorMsg = err.detail || errorMsg;
            } catch (e) {}
            handleUploadError(errorMsg);
        }
    });
    
    xhr.addEventListener('error', () => {
        handleUploadError('Network error occurred during upload.');
    });
    
    xhr.open('POST', `${API_BASE_URL}/api/upload`);
    xhr.send(formData);
    
    function handleUploadError(message) {
        console.error('Upload failed:', message);
        alert(`Failed to load document: ${message}`);
        progressContainer.style.display = 'none';
        setActiveDocument(null);
        isUploading = false;
        btnAttach.disabled = false;
        if (btnWelcomeUpload) btnWelcomeUpload.disabled = false;
    }
}

// Chat Handlers
function setupChatHandlers() {
    btnSend.addEventListener('click', handleSend);
    
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    });

    // Auto-resize textarea
    chatInput.addEventListener('input', () => {
        chatInput.style.height = 'auto';
        chatInput.style.height = (chatInput.scrollHeight - 16) + 'px';
    });

    btnNewChat.addEventListener('click', () => {
        showChatLogs(false);
        if (activeDocName) {
            showChatLogs(true);
            appendSystemMessage(`Start a new conversation about <strong>${escapeHtml(activeDocName)}</strong>.`);
        }
    });
}

function setupFeatureCards() {
    featureCards.forEach(card => {
        card.addEventListener('click', () => {
            const promptText = card.getAttribute('data-prompt');
            if (promptText && !chatInput.disabled) {
                chatInput.value = promptText;
                chatInput.style.height = 'auto';
                chatInput.style.height = (chatInput.scrollHeight - 16) + 'px';
                handleSend();
            }
        });
    });
}

async function handleSend() {
    const question = chatInput.value.trim();
    if (!question || isUploading) return;
    
    chatInput.value = '';
    chatInput.style.height = 'auto';
    
    if (chatMessages.style.display === 'none') {
        showChatLogs(true);
    }
    
    appendMessage(question, 'user');
    scrollToBottom();
    
    const thinkingId = appendThinkingBubble();
    scrollToBottom();
    
    enableChat(false);
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Query failed');
        }
        
        const data = await response.json();
        removeThinkingBubble(thinkingId);
        appendMessageWithSources(data.answer, data.sources);
        
    } catch (error) {
        console.error('Error sending query:', error);
        removeThinkingBubble(thinkingId);
        appendMessage(`Query failed: ${error.message}`, 'bot', true);
    } finally {
        enableChat(true);
        chatInput.focus();
        scrollToBottom();
    }
}

// Dom Append Helpers
function appendMessage(text, sender, isError = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-msg`;
    
    const avatar = sender === 'user' 
        ? '<div class="message-avatar"><i class="fa-solid fa-user"></i></div>'
        : '<div class="message-avatar"><i class="fa-solid fa-graduation-cap"></i></div>';
        
    msgDiv.innerHTML = `
        ${avatar}
        <div class="message-content" ${isError ? 'style="color: var(--accent-red);"' : ''}>
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
}

function appendSystemMessage(html) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message system-msg';
    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-circle-info" style="color: var(--primary-color);"></i></div>
        <div class="message-content">
            <p>${html}</p>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
    scrollToBottom();
}

function appendThinkingBubble() {
    const id = 'think-' + Date.now();
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot-msg';
    msgDiv.id = id;
    
    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-graduation-cap"></i></div>
        <div class="message-content">
            <div class="thinking-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
        </div>
    `;
    chatMessages.appendChild(msgDiv);
    return id;
}

function removeThinkingBubble(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendMessageWithSources(answerText, sources) {
    const msgDiv = document.createElement('div');
    msgDiv.className = 'message bot-msg';
    
    let sourcesHTML = '';
    if (sources && sources.length > 0) {
        const toggleId = 'toggle-' + Date.now();
        const listId = 'list-' + Date.now();
        
        sourcesHTML = `
            <div class="sources-toggle">
                <button class="btn-sources-toggle" id="${toggleId}">
                    <i class="fa-solid fa-circle-nodes"></i> Sources (${sources.length})
                </button>
                <div class="sources-list" id="${listId}">
                    ${sources.map(src => `
                        <div class="source-item">
                            <div class="source-header">
                                <span>Reference [${src.index}]</span>
                                <span>Page ${src.page}</span>
                            </div>
                            <div class="source-content">"${escapeHtml(src.content)}"</div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
        
        setTimeout(() => {
            const btn = document.getElementById(toggleId);
            const list = document.getElementById(listId);
            if (btn && list) {
                btn.addEventListener('click', () => {
                    list.classList.toggle('show');
                    scrollToBottom();
                });
            }
        }, 50);
    }
    
    msgDiv.innerHTML = `
        <div class="message-avatar"><i class="fa-solid fa-graduation-cap"></i></div>
        <div class="message-content">
            <p>${escapeHtml(answerText).replace(/\n/g, '<br>')}</p>
            ${sourcesHTML}
        </div>
    `;
    chatMessages.appendChild(msgDiv);
}

function scrollToBottom() {
    chatMessagesWrapper.scrollTop = chatMessagesWrapper.scrollHeight;
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function(m) { return map[m]; });
}
