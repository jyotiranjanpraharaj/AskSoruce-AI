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
    setupHeaderMenuAndDropdown();
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
    const btnHeaderHome = document.getElementById('btn-header-home');
    
    if (filename) {
        currentDocTitle.textContent = filename;
        if (btnHeaderHome) btnHeaderHome.style.display = 'inline-flex';
        
        docList.innerHTML = `
            <div class="doc-item active">
                <i class="fa-solid fa-file-lines"></i>
                <span class="doc-item-title" title="${escapeHtml(filename)}">${escapeHtml(filename)}</span>
                <button class="btn-delete-doc" id="btn-delete-doc" title="Delete document database">
                    <i class="fa-solid fa-trash-can"></i>
                </button>
            </div>
            <button class="btn-sidebar-upload-another" id="btn-sidebar-upload-another" title="Upload another document">
                <i class="fa-solid fa-cloud-arrow-up"></i> Upload Another
            </button>
        `;
        enableChat(true);
        setupSidebarDeleteHandler();
        
        // Setup sidebar upload another button listener
        document.getElementById('btn-sidebar-upload-another')?.addEventListener('click', () => {
            if (!isUploading) fileInput.click();
        });
    } else {
        currentDocTitle.textContent = '';
        if (btnHeaderHome) btnHeaderHome.style.display = 'none';
        
        docList.innerHTML = '<div class="no-docs-text">No document loaded</div>';
        enableChat(false);
    }
}

function setupSidebarDeleteHandler() {
    const btnDeleteDoc = document.getElementById('btn-delete-doc');
    if (btnDeleteDoc) {
        btnDeleteDoc.addEventListener('click', async (e) => {
            e.stopPropagation();
            const confirmed = await showCustomConfirm(`Are you sure you want to delete and reset the database for "${activeDocName}"?`);
            if (confirmed) {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/clear`, {
                        method: 'POST'
                    });
                    if (!response.ok) throw new Error('Failed to clear database');
                    
                    setActiveDocument(null);
                    showChatLogs(false);
                    showCustomAlert('Database Reset', 'Database cleared successfully!');
                } catch (error) {
                    console.error('Error clearing database:', error);
                    showCustomAlert('Error', `Failed to delete: ${error.message}`);
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
        chatInput.placeholder = 'Ask LearnFLux...';
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
        showCustomAlert('Upload Failed', `Failed to load document: ${message}`);
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

// Custom Promise-based Confirmation Dialog
function showCustomConfirm(message) {
    return new Promise((resolve) => {
        const modal = document.getElementById('custom-confirm-modal');
        const msgEl = document.getElementById('confirm-modal-message');
        const btnOk = document.getElementById('btn-confirm-ok');
        const btnCancel = document.getElementById('btn-confirm-cancel');
        const btnClose = document.getElementById('btn-close-confirm');
        
        msgEl.textContent = message;
        modal.style.display = 'flex';
        
        function cleanup() {
            modal.style.display = 'none';
            btnOk.removeEventListener('click', onOk);
            btnCancel.removeEventListener('click', onCancel);
            btnClose.removeEventListener('click', onCancel);
        }
        
        function onOk() {
            cleanup();
            resolve(true);
        }
        
        function onCancel() {
            cleanup();
            resolve(false);
        }
        
        btnOk.addEventListener('click', onOk);
        btnCancel.addEventListener('click', onCancel);
        btnClose.addEventListener('click', onCancel);
    });
}

// Custom Alert Dialog (using the info modal structure)
function showCustomAlert(title, message) {
    const modal = document.getElementById('info-modal');
    const titleEl = document.getElementById('info-modal-title');
    const bodyEl = document.getElementById('info-modal-body');
    const btnOk = document.getElementById('btn-close-info-ok');
    const btnClose = document.getElementById('btn-close-info');
    
    titleEl.textContent = title;
    bodyEl.innerHTML = `<p>${escapeHtml(message)}</p>`;
    modal.style.display = 'flex';
    
    function cleanup() {
        modal.style.display = 'none';
        btnOk.removeEventListener('click', cleanup);
        btnClose.removeEventListener('click', cleanup);
    }
    
    btnOk.addEventListener('click', cleanup);
    btnClose.addEventListener('click', cleanup);
}

// Setup Hamburger Menu Options, Modal, and Navigation
function setupHeaderMenuAndDropdown() {
    const btnMoreOptions = document.getElementById('btn-more-options');
    const headerDropdown = document.getElementById('header-dropdown');
    const btnHeaderHome = document.getElementById('btn-header-home');

    if (btnMoreOptions && headerDropdown) {
        btnMoreOptions.addEventListener('click', (e) => {
            e.stopPropagation();
            const isHidden = headerDropdown.style.display === 'none';
            headerDropdown.style.display = isHidden ? 'flex' : 'none';
        });

        document.addEventListener('click', () => {
            headerDropdown.style.display = 'none';
        });
    }

    if (btnHeaderHome) {
        btnHeaderHome.addEventListener('click', () => {
            showChatLogs(false);
        });
    }

    document.getElementById('btn-faq')?.addEventListener('click', () => {
        const modal = document.getElementById('info-modal');
        document.getElementById('info-modal-title').textContent = 'Q&A Session';
        document.getElementById('info-modal-body').innerHTML = `
            <div class="faq-item">
                <div class="faq-question"><i class="fa-solid fa-circle-question"></i> What is LearnFLux?</div>
                <div class="faq-answer">LearnFLux is an advanced AI-powered assistant designed to help you interact, query, and learn from your uploaded documents (PDFs, text files, and DOCX documents) using Retrieval-Augmented Generation (RAG).</div>
            </div>
            <div class="faq-item">
                <div class="faq-question"><i class="fa-solid fa-circle-question"></i> How does the document upload work?</div>
                <div class="faq-answer">When you upload a document, the system splits it into manageable text chunks, computes vector embeddings for each chunk, and stores them in a local Chroma vector database. The AI then retrieves relevant context from these chunks to provide accurate, grounded answers.</div>
            </div>
            <div class="faq-item">
                <div class="faq-question"><i class="fa-solid fa-circle-question"></i> What file formats are supported?</div>
                <div class="faq-answer">Supported formats include PDF, DOCX, TXT, Markdown, CSV, HTML, CSS, JavaScript, JSON, and Python files.</div>
            </div>
        `;
        modal.style.display = 'flex';
        setupInfoModalClose();
    });

    document.getElementById('btn-tech')?.addEventListener('click', () => {
        const modal = document.getElementById('info-modal');
        document.getElementById('info-modal-title').textContent = 'Technologies Used';
        document.getElementById('info-modal-body').innerHTML = `
            <div class="tech-section">
                <div class="tech-group">
                    <div class="tech-group-title"><i class="fa-solid fa-code"></i> Frontend</div>
                    <div class="tech-list">HTML5, Vanilla CSS3 (Custom design system with warm-light theme), and Vanilla JavaScript (ES6+).</div>
                </div>
                <div class="tech-group">
                    <div class="tech-group-title"><i class="fa-solid fa-server"></i> Backend & API</div>
                    <div class="tech-list">FastAPI (Python) and Uvicorn.</div>
                </div>
                <div class="tech-group">
                    <div class="tech-group-title"><i class="fa-solid fa-brain"></i> RAG & AI Orchestration</div>
                    <div class="tech-list">LangChain, Chroma DB (Vector Database), HuggingFace Embeddings (MiniLM-L6-v2), and Mistral AI (mistral-small LLM).</div>
                </div>
            </div>
        `;
        modal.style.display = 'flex';
        setupInfoModalClose();
    });

    document.getElementById('btn-author')?.addEventListener('click', () => {
        const modal = document.getElementById('info-modal');
        document.getElementById('info-modal-title').textContent = 'About the Engineer';
        document.getElementById('info-modal-body').innerHTML = `
            <div class="author-card">
                <div class="author-avatar">JP</div>
                <div class="author-name">Jyotiranjan Praharaj</div>
                <div class="author-role">AI/ML Engineer</div>
                <div class="author-bio">Jyotiranjan Praharaj is an AI/ML Engineer specializing in designing and deploying intelligent agents, natural language processing solutions, and advanced Retrieval-Augmented Generation (RAG) pipelines. With expertise in Large Language Models (LLMs), semantic search infrastructure, and modern web architectures, he builds scalable, production-ready AI applications that connect complex data sources with intuitive conversational interfaces.</div>
            </div>
        `;
        modal.style.display = 'flex';
        setupInfoModalClose();
    });

    // Clicking document item goes back to active chat logs view
    document.getElementById('documents-list')?.addEventListener('click', (e) => {
        const docItem = e.target.closest('.doc-item');
        if (docItem && activeDocName && !e.target.closest('.btn-delete-doc') && !e.target.closest('.btn-sidebar-upload-another')) {
            showChatLogs(true);
        }
    });
}

// Setup Hamburger Menu Options, Modal, and Navigation close helper
function setupInfoModalClose() {
    const modal = document.getElementById('info-modal');
    const btnOk = document.getElementById('btn-close-info-ok');
    const btnClose = document.getElementById('btn-close-info');
    
    function close() {
        modal.style.display = 'none';
        btnOk.removeEventListener('click', close);
        btnClose.removeEventListener('click', close);
    }
    
    btnOk.addEventListener('click', close);
    btnClose.addEventListener('click', close);
}
