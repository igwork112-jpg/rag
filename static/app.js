/**
 * RAG Document Assistant - Frontend Logic
 */

// Session ID for conversation memory
const SESSION_ID = 'session_' + Date.now();

// DOM Elements
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const uploadProgress = document.getElementById('uploadProgress');
const progressFill = document.getElementById('progressFill');
const uploadStatus = document.getElementById('uploadStatus');
const documentsList = document.getElementById('documentsList');
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const clearMemoryBtn = document.getElementById('clearMemoryBtn');

// State
let documents = [];
let isProcessing = false;

// =========================================
// File Upload
// =========================================

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('drag-over');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('drag-over');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('drag-over');
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        uploadFile(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        uploadFile(e.target.files[0]);
    }
});

async function uploadFile(file) {
    const allowedTypes = ['.pdf', '.docx', '.xlsx', '.xls'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!allowedTypes.includes(ext)) {
        showError(`File type not supported. Please upload: ${allowedTypes.join(', ')}`);
        return;
    }

    // Show progress
    uploadProgress.classList.add('visible');
    progressFill.style.width = '30%';
    uploadStatus.textContent = 'Uploading...';

    const formData = new FormData();
    formData.append('file', file);

    try {
        progressFill.style.width = '60%';
        uploadStatus.textContent = 'Processing document...';

        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            progressFill.style.width = '100%';
            uploadStatus.textContent = 'Done!';

            documents.push(data.document);
            renderDocuments();

            // Hide progress after delay
            setTimeout(() => {
                uploadProgress.classList.remove('visible');
                progressFill.style.width = '0%';
            }, 1500);

            // Remove welcome message if present
            const welcome = chatMessages.querySelector('.welcome-message');
            if (welcome) {
                welcome.style.opacity = '0.5';
            }
        } else {
            throw new Error(data.error || 'Upload failed');
        }
    } catch (error) {
        uploadProgress.classList.remove('visible');
        progressFill.style.width = '0%';
        showError(error.message);
    }

    fileInput.value = '';
}

// =========================================
// Documents List
// =========================================

function renderDocuments() {
    if (documents.length === 0) {
        documentsList.innerHTML = `
            <div class="empty-state">
                <p>No documents uploaded yet</p>
            </div>
        `;
        return;
    }

    documentsList.innerHTML = documents.map(doc => `
        <div class="document-item" data-id="${doc.id}">
            <div class="document-icon ${doc.type.replace('.', '')}">${doc.type.replace('.', '')}</div>
            <div class="document-info">
                <div class="document-name" title="${doc.name}">${doc.name}</div>
                <div class="document-meta">${doc.chunks} chunks</div>
            </div>
            <button class="document-delete" onclick="deleteDocument('${doc.id}')" title="Remove">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <polyline points="3 6 5 6 21 6"></polyline>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                </svg>
            </button>
        </div>
    `).join('');
}

async function deleteDocument(id) {
    try {
        await fetch(`/api/documents/${id}`, { method: 'DELETE' });
        documents = documents.filter(d => d.id !== id);
        renderDocuments();
    } catch (error) {
        showError('Failed to delete document');
    }
}

// =========================================
// Chat
// =========================================

chatForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const question = questionInput.value.trim();
    if (!question || isProcessing) return;

    // Remove welcome message
    const welcome = chatMessages.querySelector('.welcome-message');
    if (welcome) welcome.remove();

    // Add user message
    addMessage('user', question);
    questionInput.value = '';
    autoResizeTextarea();

    // Show loading
    isProcessing = true;
    sendBtn.disabled = true;
    const loadingEl = addLoadingMessage();

    try {
        const response = await fetch('/api/query', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question: question,
                session_id: SESSION_ID
            })
        });

        const data = await response.json();

        // Remove loading
        loadingEl.remove();

        if (data.success) {
            addMessage('assistant', data.answer, data.sources);
        } else {
            throw new Error(data.error || 'Query failed');
        }
    } catch (error) {
        loadingEl.remove();
        addMessage('assistant', `Sorry, I encountered an error: ${error.message}`);
    }

    isProcessing = false;
    sendBtn.disabled = false;
});

function addMessage(role, text, sources = []) {
    const messageEl = document.createElement('div');
    messageEl.className = `message ${role}`;

    const avatarIcon = role === 'user'
        ? '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"></path><circle cx="12" cy="7" r="4"></circle></svg>'
        : '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>';

    let sourcesHtml = '';
    if (sources.length > 0) {
        const sourceTags = sources.map(s => `<span class="source-tag">${s.source}</span>`).join('');
        sourcesHtml = `
            <div class="message-sources">
                <div class="sources-title">Sources:</div>
                ${sourceTags}
            </div>
        `;
    }

    messageEl.innerHTML = `
        <div class="message-avatar">${avatarIcon}</div>
        <div class="message-content">
            <div class="message-text">${formatText(text)}</div>
            ${sourcesHtml}
        </div>
    `;

    chatMessages.appendChild(messageEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addLoadingMessage() {
    const messageEl = document.createElement('div');
    messageEl.className = 'message assistant loading';
    messageEl.innerHTML = `
        <div class="message-avatar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
            </svg>
        </div>
        <div class="message-content">
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
            <div class="typing-dot"></div>
        </div>
    `;
    chatMessages.appendChild(messageEl);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return messageEl;
}

function formatText(text) {
    // Basic markdown-like formatting
    return text
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// =========================================
// Clear Memory
// =========================================

clearMemoryBtn.addEventListener('click', async () => {
    try {
        await fetch('/api/clear-memory', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ session_id: SESSION_ID })
        });

        // Clear chat UI but keep documents
        chatMessages.innerHTML = `
            <div class="welcome-message">
                <div class="welcome-icon">
                    <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1">
                        <circle cx="12" cy="12" r="10"></circle>
                        <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path>
                        <line x1="12" y1="17" x2="12.01" y2="17"></line>
                    </svg>
                </div>
                <h2>Memory Cleared</h2>
                <p>Conversation history has been reset. Your documents are still available.</p>
            </div>
        `;
    } catch (error) {
        showError('Failed to clear memory');
    }
});

// =========================================
// Utilities
// =========================================

function showError(message) {
    // Simple error display - could be enhanced with toast notifications
    console.error(message);
    alert(message);
}

// Auto-resize textarea
questionInput.addEventListener('input', autoResizeTextarea);

function autoResizeTextarea() {
    questionInput.style.height = 'auto';
    questionInput.style.height = Math.min(questionInput.scrollHeight, 150) + 'px';
}

// Handle Enter key (submit) vs Shift+Enter (newline)
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.dispatchEvent(new Event('submit'));
    }
});

// Load existing documents on page load
async function loadDocuments() {
    try {
        const response = await fetch('/api/documents');
        const data = await response.json();
        if (data.success) {
            documents = data.documents;
            renderDocuments();
        }
    } catch (error) {
        console.error('Failed to load documents:', error);
    }
}

// Initialize
loadDocuments();
