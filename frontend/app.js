// DOM Elements
const btnHomeHeader = document.getElementById('btn-home-header');
const btnHeaderNewSession = document.getElementById('btn-header-new-session');
const currentDocTitle = document.getElementById('current-doc-title');
const brandHeaderLogo = document.getElementById('brand-header-logo');
const headerNavDivider = document.getElementById('header-nav-divider');
const landingScreen = document.getElementById('landing-screen');
const btnTryNow = document.getElementById('btn-try-now');

// Ingestion Form Elements
const youtubeUrlInput = document.getElementById('youtube-url-input');
const btnProcessYoutube = document.getElementById('btn-process-youtube');
const languageSelect = document.getElementById('language-select');
const btnWelcomeUpload = document.getElementById('btn-welcome-upload');
const fileInput = document.getElementById('file-input');

// Dashboard Tabs & Contents
const tabButtons = document.querySelectorAll('.tab-btn');
const tabContents = document.querySelectorAll('.tab-content');
const assistantDashboard = document.getElementById('assistant-dashboard');
const chatWelcome = document.getElementById('chat-welcome');

// Text Elements in Cards
const summaryText = document.getElementById('summary-text');
const actionItemsText = document.getElementById('action-items-text');
const keyDecisionsText = document.getElementById('key-decisions-text');
const openQuestionsText = document.getElementById('open-questions-text');
const transcriptText = document.getElementById('transcript-text');
const btnDownloadTranscript = document.getElementById('btn-download-transcript');

// Real-time Upload Progress Bar Elements
const progressContainer = document.getElementById('progress-container');
const progressStatus = document.getElementById('progress-status');
const progressPercent = document.getElementById('progress-percent');
const progressCircleFill = document.getElementById('progress-circle-fill');

// Chat elements
const chatInputContainer = document.getElementById('chat-input-container');
const chatInput = document.getElementById('chat-input');
const btnSend = document.getElementById('btn-send');
const chatMessages = document.getElementById('chat-messages');
const chatMessagesWrapper = document.querySelector('.chat-messages-wrapper');

// App State
let activeSession = null;
let activeSessionData = null;
let isProcessing = false;
let progressInterval = null;
const API_BASE_URL = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
    ? 'http://localhost:8000'
    : 'https://rag-with-pdf-backend.onrender.com'; // Replace with your Render URL

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkDatabaseStatus();
    setupCustomDropdown();
    setupAttachmentHandlers();
    setupChatHandlers();
    setupTabHandlers();
    setupHeaderMenuAndDropdown();
    setupDownloadHandler();

    // Initialize Lucide Icons
    if (window.lucide) {
        lucide.createIcons();
    }

    // Initialize Example Questions cycler
    startExampleQuestionsCycler();

    // Initialize capabilities cycler
    startCapabilitiesCycler();
});

// Check Database Status on startup
async function checkDatabaseStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/status`);
        if (!response.ok) throw new Error('Failed to fetch status');

        const data = await response.json();

        if (data.active) {
            activeSessionData = data;
            activeSession = data.source_name;
        } else {
            activeSessionData = null;
            activeSession = null;
        }
        // Always reset view to default home (landing screen) on startup!
        resetUIState();
    } catch (error) {
        console.error('Error fetching database status:', error);
        if (btnResumeSession) btnResumeSession.style.display = 'none';
        resetUIState();
    }
}

// Enable/Disable interactive controls
function enableControls(enabled) {
    btnProcessYoutube.disabled = !enabled;
    youtubeUrlInput.disabled = !enabled;
    languageSelect.disabled = !enabled;
    btnWelcomeUpload.disabled = !enabled;
    if (btnHeaderNewSession) btnHeaderNewSession.disabled = !enabled;
    if (enabled) {
        btnWelcomeUpload.classList.remove('disabled');
    } else {
        btnWelcomeUpload.classList.add('disabled');
    }

    // Toggle state for custom select wrapper
    const selectWrapper = document.getElementById('language-select-wrapper');
    if (selectWrapper) {
        if (enabled) {
            selectWrapper.classList.remove('disabled');
        } else {
            selectWrapper.classList.add('disabled');
        }
    }
}

function enableChat(enabled) {
    chatInput.disabled = !enabled;
    btnSend.disabled = !enabled;
    if (enabled) {
        chatInput.placeholder = 'Ask a question about this meeting...';
    } else {
        chatInput.placeholder = 'Chat is disabled during processing...';
    }
}

// Ingestion Progress Bar step indicators
function startProgressSimulation() {
    isProcessing = true;
    progressContainer.style.display = 'flex';
    if (progressCircleFill) {
        progressCircleFill.style.strokeDashoffset = '339.292';
    }
    progressPercent.textContent = '0%';
    progressStatus.textContent = 'Starting pipeline...';

    // Reset steps UI
    const steps = [1, 2, 3, 4, 5];
    steps.forEach(s => {
        setStepState(s, 'pending');
    });

    setStepState(1, 'running');

    let elapsed = 0;
    progressInterval = setInterval(() => {
        elapsed += 0.5; // half-second intervals

        let percent = 0;
        if (elapsed < 8) {
            setStepState(1, 'running');
            percent = Math.min(Math.round((elapsed / 8) * 15), 15);
            progressStatus.textContent = 'Downloading and preparing media source...';
        } else if (elapsed < 25) {
            setStepState(1, 'completed');
            setStepState(2, 'running');
            percent = 15 + Math.min(Math.round(((elapsed - 8) / 17) * 45), 45);
            progressStatus.textContent = 'Transcribing audio content...';
        } else if (elapsed < 35) {
            setStepState(2, 'completed');
            setStepState(3, 'running');
            percent = 60 + Math.min(Math.round(((elapsed - 25) / 10) * 15), 15);
            progressStatus.textContent = 'Generating executive summary...';
        } else if (elapsed < 48) {
            setStepState(3, 'completed');
            setStepState(4, 'running');
            percent = 75 + Math.min(Math.round(((elapsed - 35) / 13) * 15), 15);
            progressStatus.textContent = 'Extracting key deliverables & action items...';
        } else {
            setStepState(4, 'completed');
            setStepState(5, 'running');
            percent = 90 + Math.min(Math.round(((elapsed - 48) / 12) * 8), 8); // caps at 98%
            progressStatus.textContent = 'Structuring content for Q&A chat...';
        }

        if (progressCircleFill) {
            const circumference = 339.292;
            const offset = circumference - (percent / 100) * circumference;
            progressCircleFill.style.strokeDashoffset = offset;
        }
        progressPercent.textContent = `${percent}%`;
    }, 500);
}

function setStepState(stepNum, state) {
    const el = document.getElementById(`step-${stepNum}`);
    if (!el) return;

    if (state === 'pending') {
        el.className = 'step-item pending';
        el.querySelector('i').className = 'fa-regular fa-circle';
    } else if (state === 'running') {
        el.className = 'step-item running';
        el.querySelector('i').className = 'fa-solid fa-circle-notch fa-spin';
    } else if (state === 'completed') {
        el.className = 'step-item completed';
        el.querySelector('i').className = 'fa-solid fa-circle-check';
    }
}

function stopProgressSimulation(success = true) {
    clearInterval(progressInterval);
    if (success) {
        if (progressCircleFill) {
            progressCircleFill.style.strokeDashoffset = '0';
        }
        progressPercent.textContent = '100%';
        progressStatus.textContent = 'Analysis complete!';
        for (let s = 1; s <= 5; s++) {
            setStepState(s, 'completed');
        }
    }
    setTimeout(() => {
        progressContainer.style.display = 'none';
        isProcessing = false;
    }, 600);
}

// Reset UI state to Welcome Screen
function resetUIState() {
    activeSession = null;
    currentDocTitle.textContent = 'Welcome to AskSource-AI';

    // Toggle header nav elements: Only show brand logo
    if (brandHeaderLogo) brandHeaderLogo.style.display = 'flex';
    if (headerNavDivider) headerNavDivider.style.display = 'none';
    if (currentDocTitle) currentDocTitle.style.display = 'none';

    // Show landing screen, hide ingest and dashboard
    if (landingScreen) landingScreen.style.display = 'flex';
    chatWelcome.style.display = 'none';
    assistantDashboard.style.display = 'none';
    chatInputContainer.style.display = 'none';
    enableChat(false);
    enableControls(true);

    // Clear inputs
    youtubeUrlInput.value = '';
    fileInput.value = '';
}

// Load state into UI after ingestion or reload
function loadStateIntoUI(state) {
    activeSession = state.source_name;

    currentDocTitle.textContent = state.title || "Meeting Assistant";

    // Toggle header nav elements: Show brand logo + divider + active document name
    if (brandHeaderLogo) brandHeaderLogo.style.display = 'flex';
    if (headerNavDivider) headerNavDivider.style.display = 'inline';
    if (currentDocTitle) currentDocTitle.style.display = 'inline-block';

    // Set content in tabs
    summaryText.innerHTML = renderMarkdown(state.summary);
    actionItemsText.innerHTML = renderMarkdown(state.action_items);
    keyDecisionsText.innerHTML = renderMarkdown(state.key_decisions);
    openQuestionsText.innerHTML = renderMarkdown(state.open_questions);
    transcriptText.textContent = state.transcript;

    // Setup message boards
    chatMessages.innerHTML = '';
    appendSystemMessage(`Meeting <strong>${escapeHtml(state.title)}</strong> successfully indexed! You can now explore summary highlights or ask custom questions in the Q&A Chat tab.`);

    if (landingScreen) landingScreen.style.display = 'none';
    chatWelcome.style.display = 'none';
    assistantDashboard.style.display = 'flex';
    chatInputContainer.style.display = 'flex';

    enableChat(true);
    enableControls(true);

    // Ensure view starts at the top
    if (chatMessagesWrapper) {
        chatMessagesWrapper.scrollTop = 0;
    }
}

function setupSidebarDeleteHandler() {
    const btnDeleteDoc = document.getElementById('btn-delete-doc');
    if (btnDeleteDoc) {
        btnDeleteDoc.addEventListener('click', async (e) => {
            e.stopPropagation();
            const confirmed = await showCustomConfirm(`Are you sure you want to clear this active session and delete the database?`);
            if (confirmed) {
                try {
                    const response = await fetch(`${API_BASE_URL}/api/clear`, {
                        method: 'POST'
                    });
                    if (!response.ok) throw new Error('Failed to clear database');
                    resetUIState();
                    showCustomAlert('Database Reset', 'Active database and state cleared successfully!');
                } catch (error) {
                    console.error('Error clearing database:', error);
                    showCustomAlert('Error', `Failed to delete session: ${error.message}`);
                }
            }
        });
    }
}

// Ingestion Handlers (YouTube URL + file uploads)
function setupAttachmentHandlers() {
    btnWelcomeUpload.addEventListener('click', () => {
        if (!isProcessing) fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            triggerUpload(e.target.files[0]);
        }
    });

    btnProcessYoutube.addEventListener('click', () => {
        const url = youtubeUrlInput.value.trim();
        if (!url) {
            showCustomAlert('Input Error', 'Please enter a valid YouTube Video URL.');
            return;
        }
        triggerYouTubeProcess(url);
    });

    youtubeUrlInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            btnProcessYoutube.click();
        }
    });
}

// Setup custom dropdown behavior to replace standard browser select element
function setupCustomDropdown() {
    const customSelectWrapper = document.getElementById('language-select-wrapper');
    const customSelectTrigger = document.getElementById('language-select-trigger');
    const customSelectLabel = document.getElementById('language-select-label');
    const customOptions = document.querySelectorAll('.custom-option');
    const hiddenLanguageInput = document.getElementById('language-select');

    if (customSelectTrigger && customSelectWrapper) {
        customSelectTrigger.addEventListener('click', (e) => {
            if (customSelectWrapper.classList.contains('disabled')) return;
            customSelectWrapper.classList.toggle('open');
            e.stopPropagation();
        });

        document.addEventListener('click', () => {
            customSelectWrapper.classList.remove('open');
        });

        customOptions.forEach(opt => {
            opt.addEventListener('click', (e) => {
                const val = opt.getAttribute('data-value');
                const text = opt.textContent;

                // Update hidden input value
                if (hiddenLanguageInput) {
                    hiddenLanguageInput.value = val;
                    hiddenLanguageInput.dispatchEvent(new Event('change'));
                }

                // Update label
                if (customSelectLabel) {
                    customSelectLabel.textContent = text;
                }

                // Update selected class
                customOptions.forEach(o => o.classList.remove('selected'));
                opt.classList.add('selected');

                customSelectWrapper.classList.remove('open');
                e.stopPropagation();
            });
        });
    }
}

async function triggerYouTubeProcess(url) {
    enableControls(false);
    startProgressSimulation();

    const formData = new FormData();
    formData.append('youtube_url', url);
    formData.append('language', languageSelect.value);

    try {
        const response = await fetch(`${API_BASE_URL}/api/process`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to process YouTube audio');
        }

        const data = await response.json();
        stopProgressSimulation(true);
        loadStateIntoUI(data);

    } catch (error) {
        console.error('YouTube process failed:', error);
        stopProgressSimulation(false);
        showCustomAlert('Ingestion Failed', `Failed to analyze YouTube video: ${error.message}`);
        enableControls(true);
    }
}

async function triggerUpload(file) {
    enableControls(false);
    startProgressSimulation();

    const formData = new FormData();
    formData.append('file', file);
    formData.append('language', languageSelect.value);

    try {
        const response = await fetch(`${API_BASE_URL}/api/process`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to process file upload');
        }

        const data = await response.json();
        stopProgressSimulation(true);
        loadStateIntoUI(data);

    } catch (error) {
        console.error('File process failed:', error);
        stopProgressSimulation(false);
        showCustomAlert('Upload Failed', `Failed to process uploaded file: ${error.message}`);
        enableControls(true);
    }
}

// Tab handlers
function setupTabHandlers() {
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            const targetTab = btn.getAttribute('data-tab');

            tabButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            tabContents.forEach(content => {
                if (content.id === targetTab) {
                    content.classList.add('active');
                } else {
                    content.classList.remove('active');
                }
            });

            if (targetTab === 'chat-tab') {
                scrollToBottom();
            } else {
                if (chatMessagesWrapper) {
                    chatMessagesWrapper.scrollTop = 0;
                }
            }
        });
    });
}

// Download transcript action
function setupDownloadHandler() {
    btnDownloadTranscript.addEventListener('click', () => {
        if (!transcriptText.textContent) return;

        const blob = new Blob([transcriptText.textContent], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${currentDocTitle.textContent.replace(/\s+/g, '_')}_transcript.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    });
}

// Chat handlers
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

}

function setupFeatureCards() {
    const featureCards = document.querySelectorAll('.feature-card');
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
    if (!question || isProcessing) return;

    chatInput.value = '';
    chatInput.style.height = 'auto';

    // Auto-switch to Q&A Chat tab if not active
    const chatTabBtn = document.querySelector('.tab-btn[data-tab="chat-tab"]');
    if (chatTabBtn && !chatTabBtn.classList.contains('active')) {
        chatTabBtn.click();
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

// Dom Helpers
function appendMessage(text, sender, isError = false) {
    const msgDiv = document.createElement('div');
    msgDiv.className = `message ${sender}-msg`;

    const avatar = sender === 'user'
        ? '<div class="message-avatar"><i class="fa-solid fa-user"></i></div>'
        : '<div class="message-avatar"><i class="fa-solid fa-video"></i></div>';

    msgDiv.innerHTML = `
        ${avatar}
        <div class="message-content" ${isError ? 'style="color: var(--accent-red);"' : ''}>
            <p>${escapeHtml(text).replace(/\n/g, '<br>')}</p>
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
        <div class="message-avatar"><i class="fa-solid fa-video"></i></div>
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
                                <span>${src.page}</span>
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
        <div class="message-avatar"><i class="fa-solid fa-video"></i></div>
        <div class="message-content">
            <p>${renderMarkdown(answerText)}</p>
            ${sourcesHTML}
        </div>
    `;
    chatMessages.appendChild(msgDiv);
}

function scrollToBottom() {
    chatMessagesWrapper.scrollTop = chatMessagesWrapper.scrollHeight;
}

function escapeHtml(text) {
    if (!text) return "";
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, function (m) { return map[m]; });
}

// Simple custom Markdown rendering for bullet points, lists, and headers
function renderMarkdown(text) {
    if (!text) return "";

    // Escape HTML first to prevent code injection
    let escaped = escapeHtml(text);

    // Bold text (**bold**)
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');

    const lines = escaped.split('\n');
    let html = "";
    let inList = false;
    let listType = null;

    for (let line of lines) {
        let trimmed = line.trim();
        if (!trimmed) {
            if (inList) {
                html += `</${listType}>`;
                inList = false;
                listType = null;
            }
            continue;
        }

        // Headers: # Header 1, ## Header 2, ### Header 3, etc.
        if (trimmed.startsWith('#')) {
            if (inList) {
                html += `</${listType}>`;
                inList = false;
                listType = null;
            }
            let level = 0;
            while (level < trimmed.length && trimmed.charAt(level) === '#') {
                level++;
            }
            let headerText = trimmed.substring(level).trim();
            let hTag = level <= 6 ? `h${level}` : 'h6';
            html += `<${hTag}>${headerText}</${hTag}>`;
        }
        // Unordered list
        else if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
            if (!inList || listType !== 'ul') {
                if (inList) html += `</${listType}>`;
                html += '<ul>';
                inList = true;
                listType = 'ul';
            }
            html += `<li>${trimmed.substring(2)}</li>`;
        }
        // Ordered list
        else if (/^\d+\.\s/.test(trimmed)) {
            if (!inList || listType !== 'ol') {
                if (inList) html += `</${listType}>`;
                html += '<ol>';
                inList = true;
                listType = 'ol';
            }
            const matchIndex = trimmed.indexOf('.');
            html += `<li>${trimmed.substring(matchIndex + 2)}</li>`;
        }
        // Normal paragraph
        else {
            if (inList) {
                html += `</${listType}>`;
                inList = false;
                listType = null;
            }
            html += `<p>${trimmed}</p>`;
        }
    }

    if (inList) {
        html += `</${listType}>`;
    }

    return html;
}

// Custom confirmation dialog
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

// Custom Alert Dialog
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

// Setup dropdown options menu (FAQ, Tech, Author)
function setupHeaderMenuAndDropdown() {
    const btnMoreOptions = document.getElementById('btn-more-options');
    const headerDropdown = document.getElementById('header-dropdown');

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

    // Home button in top left
    if (btnHomeHeader) {
        btnHomeHeader.addEventListener('click', () => {
            resetUIState();
        });
    }

    // Try Now button in landing screen
    if (btnTryNow) {
        btnTryNow.addEventListener('click', () => {
            if (landingScreen) landingScreen.style.display = 'none';
            chatWelcome.style.display = 'flex';
        });
    }

    // New Session button (+) in top right
    if (btnHeaderNewSession) {
        btnHeaderNewSession.addEventListener('click', async () => {
            if (activeSession) {
                const confirmed = await showCustomConfirm(`Are you sure you want to clear this active session and start a new one?`);
                if (!confirmed) return;

                try {
                    const response = await fetch(`${API_BASE_URL}/api/clear`, {
                        method: 'POST'
                    });
                    if (!response.ok) throw new Error('Failed to clear database');
                } catch (error) {
                    console.error('Error clearing database:', error);
                    showCustomAlert('Error', `Failed to reset session: ${error.message}`);
                    return;
                }
            }

            // Clear memory
            activeSession = null;
            activeSessionData = null;

            resetUIState();
            // Directly show the ingestion screen
            if (landingScreen) landingScreen.style.display = 'none';
            chatWelcome.style.display = 'flex';
        });
    }

    document.getElementById('btn-faq')?.addEventListener('click', () => {
        const modal = document.getElementById('info-modal');
        document.getElementById('info-modal-title').textContent = 'FAQ & Guide';
        document.getElementById('info-modal-body').innerHTML = `
            <div class="faq-item">
                <div class="faq-question"><i class="fa-solid fa-circle-question"></i> What is AskSource-AI?</div>
                <div class="faq-answer">AskSource-AI is an advanced meeting and audio assistant designed to transcribe, summarize, and extract deliverables from YouTube videos or local audio files. It also allows interactive semantic Q&A using RAG.</div>
            </div>
            <div class="faq-item">
                <div class="faq-question"><i class="fa-solid fa-circle-question"></i> How do I process a source?</div>
                <div class="faq-answer">Select your transcription language, then paste a YouTube Video URL and click "Process", or upload a local audio file (MP3, WAV, M4A, etc.) to start the automated pipeline.</div>
            </div>
            <div class="faq-item">
                <div class="faq-question"><i class="fa-solid fa-circle-question"></i> What does the dashboard display?</div>
                <div class="faq-answer">The dashboard has four tabs: Summary (overall executive bullet highlights), Deliverables (structured action items, key decisions, open questions), Transcript (full raw audio transcript text), and Q&A Chat (ask semantic questions to the AI about the discussion).</div>
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
                    <div class="tech-group-title"><i class="fa-solid fa-code"></i> Frontend UI</div>
                    <div class="tech-list">HTML5, Vanilla CSS3 (custom responsive dashboard with warm-light design system), and Vanilla JavaScript (ES6+).</div>
                </div>
                <div class="tech-group">
                    <div class="tech-group-title"><i class="fa-solid fa-server"></i> Backend Server</div>
                    <div class="tech-list">FastAPI (Python), Uvicorn Web Server, and Pydantic validation.</div>
                </div>
                <div class="tech-group">
                    <div class="tech-group-title"><i class="fa-solid fa-brain"></i> RAG & Speech AI</div>
                    <div class="tech-list">Groq Whisper API (Whisper-large-v3 cloud speech-to-text), Mistral AI LLM (mistral-small), LangChain (LCEL Orchestration), Pinecone (Vector Database), and HuggingFace Embeddings (MiniLM-L6-v2).</div>
                </div>
            </div>
        `;
        modal.style.display = 'flex';
        setupInfoModalClose();
    });

    document.getElementById('btn-author')?.addEventListener('click', () => {
        const modal = document.getElementById('info-modal');
        document.getElementById('info-modal-title').textContent = 'Reference GitHub Repo';
        document.getElementById('info-modal-body').innerHTML = `
            <div class="github-modal-content">
                <p>Explore the full source code, architecture diagrams, and documentation for AskSource-AI on GitHub.</p>
                <div class="github-repo-link-box">
                    <span class="repo-url-text" id="repo-url-text">https://github.com/jyotiranjanpraharaj/AskSoruce-AI</span>
                    <button class="btn-copy-repo" id="btn-copy-repo" title="Copy Link">
                        <i class="fa-regular fa-copy"></i> Copy
                    </button>
                </div>
                <div class="github-modal-actions">
                    <a href="https://github.com/jyotiranjanpraharaj/AskSoruce-AI" target="_blank" class="btn btn-open-github">
                        <i class="fa-brands fa-github"></i> Open Repo <i class="fa-solid fa-arrow-up-right-from-square"></i>
                    </a>
                </div>
            </div>
        `;

        const btnCopy = document.getElementById('btn-copy-repo');
        if (btnCopy) {
            btnCopy.addEventListener('click', async () => {
                try {
                    await navigator.clipboard.writeText('https://github.com/jyotiranjanpraharaj/AskSoruce-AI');
                    btnCopy.innerHTML = '<i class="fa-solid fa-check"></i> Copied!';
                    btnCopy.classList.add('copied');
                    setTimeout(() => {
                        btnCopy.innerHTML = '<i class="fa-regular fa-copy"></i> Copy';
                        btnCopy.classList.remove('copied');
                    }, 2000);
                } catch (err) {
                    console.error('Failed to copy text: ', err);
                }
            });
        }

        modal.style.display = 'flex';
        setupInfoModalClose();
    });
}

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

// Reference GitHub Repo helper is loaded

// Example Questions Cycler widget
let exampleQuestionsInterval = null;
function startExampleQuestionsCycler() {
    if (exampleQuestionsInterval) clearInterval(exampleQuestionsInterval);

    const questionsList = [
        "Summarize this meeting",
        "What decisions were made?",
        "What are the action items?",
        "Give me key takeaways",
        "Who spoke the most?"
    ];
    let questionIndex = 0;

    exampleQuestionsInterval = setInterval(() => {
        const el = document.getElementById('rotating-question');
        if (el) {
            el.style.opacity = '0';
            el.style.transform = 'translateY(-6px)';
            setTimeout(() => {
                questionIndex = (questionIndex + 1) % questionsList.length;
                el.textContent = questionsList[questionIndex];
                el.style.opacity = '1';
                el.style.transform = 'translateY(0)';
            }, 300);
        }
    }, 2500);
}

// Capabilities tab cycler & click handler
let capabilitiesInterval = null;
let activeCapabilityIndex = 0;

function switchCapability(index) {
    const tabs = document.querySelectorAll('.cap-tab-btn');
    const panels = document.querySelectorAll('.capability-panel');

    if (tabs.length === 0 || panels.length === 0) return;

    // Deactivate previous active elements
    tabs.forEach(t => t.classList.remove('active'));
    panels.forEach(p => p.classList.remove('active'));

    // Activate targeted elements
    activeCapabilityIndex = index;
    if (tabs[index]) tabs[index].classList.add('active');
    if (panels[index]) panels[index].classList.add('active');
}

function startCapabilitiesCycler() {
    if (capabilitiesInterval) clearInterval(capabilitiesInterval);

    // Handle tab clicking
    const tabs = document.querySelectorAll('.cap-tab-btn');
    tabs.forEach((tab, index) => {
        // Clone tab to strip duplicate event listeners if initialized multiple times
        const newTab = tab.cloneNode(true);
        tab.parentNode.replaceChild(newTab, tab);

        newTab.addEventListener('click', () => {
            switchCapability(index);
            // Restart cycler after click to reset timer
            startCapabilitiesCycler();
        });
    });

    // Auto-cycle every 1.5 seconds
    capabilitiesInterval = setInterval(() => {
        const nextIndex = (activeCapabilityIndex + 1) % 4;
        switchCapability(nextIndex);
    }, 1500);
}
