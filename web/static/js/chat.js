// Chat functionality for message handling and streaming.
console.log('Chat.js loading...');

class ChatManager {
    constructor() {
        this.messagesContainer = document.getElementById('messages-container');
        this.chatForm = document.getElementById('chat-form');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.chatTitle = document.getElementById('chat-title');

        this.currentConversation = null;
        this.isStreaming = false;
        this.currentFile = null;
        this.scrollTimeout = null;
        this.isCreatingConversation = false; // Prevent duplicate creation

        this.init();
    }

    init() {
        console.log('ChatManager.init() called');
        console.log('Elements:', {
            chatForm: !!this.chatForm,
            messageInput: !!this.messageInput,
            sendBtn: !!this.sendBtn
        });

        // Event listeners
        this.chatForm.addEventListener('submit', (e) => {
            console.log('Form submitted');
            this.handleSubmit(e);
        });

        this.messageInput.addEventListener('input', () => {
            this.autoResizeTextarea();
            this.updateSendButton();
        });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.chatForm.dispatchEvent(new Event('submit'));
            }
        });

        // Image upload
        this.setupImageUpload();
        console.log('Image upload setup complete');

        // Listen for conversation events
        document.addEventListener('conversationCreated', (e) => {
            this.setConversation(e.detail);
        });

        document.addEventListener('conversationLoaded', async (e) => {
            await this.loadConversation(e.detail.id);
        });

        document.addEventListener('conversationDeleted', () => {
            this.clearChat();
        });

        document.addEventListener('historyCleared', () => {
            this.clearChat();
        });

        // Don't create initial conversation here - let sidebar handle it
        // or wait for user to start chatting
        this.checkAndCreateInitialConversation();
    }

    async checkAndCreateInitialConversation() {
        // Only create initial conversation if no conversations exist
        try {
            const conversations = await API.getConversations();
            if (conversations.conversations.length === 0) {
                await this.createNewConversation();
            }
        } catch (error) {
            console.log('Could not check conversations:', error);
        }
    }

    setupImageUpload() {
        const uploadBtn = document.getElementById('upload-btn');
        const imageInput = document.getElementById('image-input');
        const imagePreview = document.getElementById('image-preview');
        const previewImg = document.getElementById('preview-img');
        const removeImageBtn = document.getElementById('remove-image');

        console.log('Upload elements:', { uploadBtn: !!uploadBtn, imageInput: !!imageInput });

        if (!uploadBtn || !imageInput) {
            console.error('Upload button or file input not found!');
            return;
        }

        // Update file input to accept more file types
        imageInput.setAttribute('accept', '.png,.jpg,.jpeg,.gif,.bmp,.webp,.svg,.txt,.pdf,.doc,.docx,.md,.csv,.json,.xml,.yaml,.yml,.toml,.ini,.cfg,.log,.py,.js,.html,.css,.java,.cpp,.c,.h,.go,.rs,.ts,.tsx,.jsx');

        uploadBtn.addEventListener('click', () => {
            console.log('Upload button clicked');
            imageInput.click();
        });

        imageInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            // Show loading state on button
            uploadBtn.classList.add('animate-pulse');

            try {
                const data = await API.uploadFile(file);
                this.currentFile = data;
                this.showFilePreview(data);
                this.messageInput.focus();
            } catch (error) {
                console.error('Failed to upload file:', error);
                alert(error.message || 'Failed to upload file. Please try again.');
            } finally {
                uploadBtn.classList.remove('animate-pulse');
            }
        });

        removeImageBtn.addEventListener('click', () => {
            this.currentFile = null;
            imagePreview.classList.add('hidden');
            // Reset preview content
            previewImg.src = '';
            previewImg.style.display = 'block';
            // Remove any extra info elements
            const extraInfo = imagePreview.querySelectorAll('div:not(:first-child)');
            extraInfo.forEach(el => el.remove());
            imageInput.value = '';
            this.messageInput.focus();
        });

        // Drag and drop
        this.chatForm.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.chatForm.classList.add('border-orange-400', 'bg-orange-50', 'dark:bg-orange-900/20');
        });

        this.chatForm.addEventListener('dragleave', () => {
            this.chatForm.classList.remove('border-orange-400', 'bg-orange-50', 'dark:bg-orange-900/20');
        });

        this.chatForm.addEventListener('drop', async (e) => {
            e.preventDefault();
            this.chatForm.classList.remove('border-orange-400', 'bg-orange-50', 'dark:bg-orange-900/20');

            const file = e.dataTransfer.files[0];
            if (file) {
                uploadBtn.classList.add('animate-pulse');
                try {
                    const data = await API.uploadFile(file);
                    this.currentFile = data;
                    this.showFilePreview(data);
                    this.messageInput.focus();
                } catch (error) {
                    console.error('Failed to upload file:', error);
                    alert(error.message || 'Failed to upload file');
                } finally {
                    uploadBtn.classList.remove('animate-pulse');
                }
            }
        });
    }

    showFilePreview(fileData) {
        const imagePreview = document.getElementById('image-preview');
        const previewImg = document.getElementById('preview-img');

        if (fileData.type === 'image') {
            previewImg.src = fileData.url;
            imagePreview.classList.remove('hidden');
        } else if (fileData.type === 'text') {
            // For text files, show filename in preview
            previewImg.style.display = 'none';
            imagePreview.classList.remove('hidden');
            const filename = document.createElement('div');
            filename.className = 'text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2';
            filename.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                ${fileData.filename} (${this.formatFileSize(fileData.size)})
            `;
            imagePreview.appendChild(filename);
        } else {
            // For other files
            previewImg.style.display = 'none';
            imagePreview.classList.remove('hidden');
            const info = document.createElement('div');
            info.className = 'text-sm text-gray-600 dark:text-gray-400 flex items-center gap-2';
            info.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                ${fileData.filename} (${this.formatFileSize(fileData.size)})
            `;
            imagePreview.appendChild(info);
        }
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        const newHeight = Math.min(this.messageInput.scrollHeight, 200);
        this.messageInput.style.height = `${newHeight}px`;
    }

    updateSendButton() {
        const hasContent = this.messageInput.value.trim().length > 0;
        const hasFile = this.currentFile != null;
        const shouldEnable = (hasContent || hasFile) && !this.isStreaming;
        this.sendBtn.disabled = !shouldEnable;

        // Visual feedback
        if (shouldEnable) {
            this.sendBtn.classList.remove('opacity-40', 'cursor-not-allowed');
        } else {
            this.sendBtn.classList.add('opacity-40', 'cursor-not-allowed');
        }
    }

    async createNewConversation() {
        // Prevent duplicate creation
        if (this.isCreatingConversation) {
            console.log('Already creating conversation, skipping');
            return;
        }

        this.isCreatingConversation = true;

        try {
            const data = await API.createConversation();
            this.setConversation(data.conversation);
        } catch (error) {
            console.error('Failed to create conversation:', error);
        } finally {
            this.isCreatingConversation = false;
        }
    }

    setConversation(conversation) {
        this.currentConversation = conversation;
        this.chatTitle.textContent = conversation.title || 'New Chat';
        this.clearMessages();
        this.showWelcomeMessage();
    }

    async loadConversation(id) {
        try {
            const data = await API.getConversation(id);
            this.currentConversation = data.conversation;
            this.chatTitle.textContent = data.conversation.title || 'Chat';

            this.clearMessages();

            // Render messages
            data.messages.forEach(msg => {
                this.renderMessage(msg);
            });

            this.scrollToBottom();
        } catch (error) {
            console.error('Failed to load conversation:', error);
        }
    }

    clearChat() {
        this.currentConversation = null;
        this.chatTitle.textContent = 'New Chat';
        this.clearMessages();
        this.showWelcomeMessage();
        this.createNewConversation();
    }

    clearMessages() {
        this.messagesContainer.innerHTML = '';
    }

    showWelcomeMessage() {
        this.messagesContainer.innerHTML = `
            <div class="flex flex-col items-center justify-center min-h-[60vh] px-4">
                <div class="w-16 h-16 bg-gradient-to-br from-orange-400 via-orange-500 to-red-500 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-orange-500/20">
                    <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-sparkles">
                        <path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/>
                        <path d="M5 3v4"/><path d="M19 17v4"/><path d="M3 5h4"/><path d="M17 19h4"/>
                    </svg>
                </div>
                <h2 class="text-3xl font-semibold text-gray-900 dark:text-white mb-3">How can I help you today?</h2>
                <p class="text-gray-500 dark:text-gray-400 text-center max-w-md">
                    Ask me anything, share an image for analysis, or get help with coding tasks.
                </p>
            </div>
        `;
    }

    async handleSubmit(e) {
        e.preventDefault();

        if (this.isStreaming) return;

        const message = this.messageInput.value.trim();
        if (!message && !this.currentFile) return;

        if (!this.currentConversation) {
            await this.createNewConversation();
        }

        // Get options for API call
        const options = {};

        // Clear welcome message if present
        if (this.messagesContainer.querySelector('[class*="min-h-60vh"], [class*="min-h-[60vh]"]')) {
            this.clearMessages();
        }

        // Build user content based on file type
        let userContent = message;
        let imageUrl = null;

        if (this.currentFile) {
            if (this.currentFile.type === 'image') {
                // For images, use vision API
                imageUrl = this.currentFile.url;
            } else if (this.currentFile.type === 'text') {
                // For text files, include content in the message
                userContent = message + (message ? '\n\n' : '') + `File: ${this.currentFile.filename}\n\`\`\`\n${this.currentFile.content.substring(0, 10000)}\n\`\`\``;
            } else if (this.currentFile.type === 'pdf' || this.currentFile.type === 'document') {
                // For PDFs and documents
                userContent = message + (message ? '\n\n' : '') + `[Uploaded file: ${this.currentFile.filename}]`;
            }
        }

        // Render user message
        this.renderMessage({
            role: 'user',
            content: userContent,
            image_url: imageUrl,
            timestamp: new Date().toISOString()
        });

        // Clear input
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.updateSendButton();

        // Show loading indicator
        this.showLoading();

        try {
            if (imageUrl) {
                // Vision request for images
                const response = await API.analyzeImage(
                    this.currentConversation.id,
                    imageUrl,
                    message || 'Describe this image.'
                );

                this.hideLoading();
                this.renderMessage({
                    role: 'assistant',
                    content: response.message.content,
                    timestamp: new Date().toISOString()
                });
            } else {
                // Stream response for text
                await this.streamResponse(userContent, options);
            }
        } catch (error) {
            this.hideLoading();
            console.error('Failed to get response:', error);
            this.renderMessage({
                role: 'assistant',
                content: `Sorry, I encountered an error: ${error.message}`,
                timestamp: new Date().toISOString()
            });
        } finally {
            // Clear file
            this.currentFile = null;
            document.getElementById('image-preview').classList.add('hidden');
            document.getElementById('image-input').value = '';
        }
    }

    async streamResponse(message, options = {}) {
        console.log('Starting stream response...', options);
        let receivedAnyData = false;
        const startTime = Date.now();

        try {
            const response = await API.sendMessageStream(
                this.currentConversation.id,
                message,
                options
            );
            console.log('Got stream response:', response.status);

            this.hideLoading();

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            console.log('Stream reader created');

            // Use TextDecoderStream for better performance
            let buffer = '';

            // Create assistant message container
            const messageEl = this.createMessageElement({
                role: 'assistant',
                content: '',
                timestamp: new Date().toISOString()
            });
            this.messagesContainer.appendChild(messageEl);

            const contentEl = messageEl.querySelector('.content');
            let fullContent = '';

            this.isStreaming = true;
            this.updateSendButton();

            // Add stop button during streaming
            this.addStopButton();

            while (true) {
                const { done, value } = await reader.read();
                if (done) {
                    console.log('Stream done');
                    break;
                }

                // Decode chunk and add to buffer
                buffer += decoder.decode(value, { stream: true });

                // Process complete lines from buffer
                const lines = buffer.split('\n');
                buffer = lines.pop(); // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const data = JSON.parse(line.slice(6));

                            if (data.content) {
                                receivedAnyData = true;
                                fullContent += data.content;
                                contentEl.innerHTML = this.formatMessage(fullContent);
                                contentEl.classList.add('stream-cursor');

                                // Throttle scroll to every 100ms for performance
                                if (!this.scrollTimeout) {
                                    this.scrollTimeout = setTimeout(() => {
                                        this.scrollToBottom();
                                        this.scrollTimeout = null;
                                    }, 50);
                                }
                            }

                            if (data.done) {
                                contentEl.classList.remove('stream-cursor');
                                break;
                            }

                            if (data.error) {
                                contentEl.innerHTML = `Error: ${data.error}`;
                                contentEl.classList.remove('stream-cursor');
                                break;
                            }
                        } catch (e) {
                            // Ignore parse errors for malformed lines
                        }
                    }
                }
            }

            // Process any remaining buffer
            if (buffer.startsWith('data: ')) {
                try {
                    const data = JSON.parse(buffer.slice(6));
                    if (data.content) {
                        fullContent += data.content;
                        contentEl.innerHTML = this.formatMessage(fullContent);
                    }
                } catch (e) {
                    // Ignore
                }
            }

            this.isStreaming = false;
            this.updateSendButton();
            this.removeStopButton();
            this.scrollToBottom();

            const duration = Date.now() - startTime;
            console.log(`Response completed in ${duration}ms`);

            // If no data was received, fall back to non-streaming
            if (!receivedAnyData) {
                console.log('No streaming data received, falling back to non-streaming');
                contentEl.innerHTML = 'Loading response...';
                const response = await API.sendMessage(
                    this.currentConversation.id,
                    message
                );
                contentEl.innerHTML = this.formatMessage(response.message.content);
            }

        } catch (error) {
            this.hideLoading();
            this.isStreaming = false;
            this.updateSendButton();
            this.removeStopButton();
            throw error;
        }
    }

    addStopButton() {
        const existingBtn = document.getElementById('stop-btn');
        if (existingBtn) return;

        const stopBtn = document.createElement('button');
        stopBtn.id = 'stop-btn';
        stopBtn.className = 'absolute bottom-20 left-1/2 transform -translate-x-1/2 px-4 py-2 bg-gray-800 hover:bg-gray-700 text-white rounded-full text-sm flex items-center gap-2 shadow-lg z-10';
        stopBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="6" y="6" width="12" height="12"/></svg>
            Stop generating
        `;
        stopBtn.addEventListener('click', () => {
            this.isStreaming = false;
            this.updateSendButton();
            this.removeStopButton();
        });

        this.messagesContainer.parentElement.appendChild(stopBtn);
    }

    removeStopButton() {
        const stopBtn = document.getElementById('stop-btn');
        if (stopBtn) stopBtn.remove();
    }

    renderMessage(message) {
        const messageEl = this.createMessageElement(message);
        this.messagesContainer.appendChild(messageEl);
        this.scrollToBottom();
    }

    createMessageElement(message) {
        const div = document.createElement('div');
        const isUser = message.role === 'user';

        div.className = 'message-enter py-6 px-4 md:px-8 lg:px-12 border-b border-gray-100 dark:border-gray-800/50 hover:bg-gray-50 dark:hover:bg-gray-800/30 transition-colors';
        div.dataset.messageId = message.id || '';

        // Avatar
        const avatarClass = isUser
            ? 'bg-gray-700'
            : 'bg-gradient-to-br from-orange-400 to-red-500';

        const avatarIcon = isUser
            ? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>'
            : '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m12 3-1.912 5.813a2 2 0 0 1-1.275 1.275L3 12l5.813 1.912a2 2 0 0 1 1.275 1.275L12 21l1.912-5.813a2 2 0 0 1 1.275-1.275L21 12l-5.813-1.912a2 2 0 0 1-1.275-1.275L12 3Z"/></svg>';

        // Format content
        let contentHtml = this.formatMessage(message.content);

        // Add image if present
        if (message.image_url) {
            contentHtml += `
                <div class="mt-3">
                    <img src="${message.image_url}" alt="Uploaded image" class="max-h-96 rounded-lg border border-gray-300 dark:border-gray-600 object-cover">
                </div>
            `;
        }

        // Add file attachment indicator if present
        if (message.file_info) {
            contentHtml += `
                <div class="mt-3 flex items-center gap-2 p-3 bg-gray-100 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                    <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-gray-500"><path d="M14.5 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7.5L14.5 2z"/><polyline points="14 2 14 8 20 8"/></svg>
                    <span class="text-sm text-gray-700 dark:text-gray-300">${this.escapeHtml(message.file_info.filename)}</span>
                    <span class="text-xs text-gray-500">${this.formatFileSize(message.file_info.size)}</span>
                </div>
            `;
        }

        // Format timestamp
        const timestamp = message.timestamp
            ? new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
            : '';

        div.innerHTML = `
            <div class="max-w-3xl mx-auto flex gap-4">
                <div class="w-8 h-8 rounded-full ${avatarClass} flex items-center justify-center flex-shrink-0 mt-0.5">
                    ${avatarIcon}
                </div>
                <div class="flex-1 min-w-0">
                    <div class="flex items-center gap-2 mb-1">
                        <span class="font-semibold text-sm ${isUser ? 'text-gray-900 dark:text-gray-100' : 'text-orange-600 dark:text-orange-400'}">
                            ${isUser ? 'You' : 'Gemma'}
                        </span>
                        <span class="text-xs text-gray-400">${timestamp}</span>
                    </div>
                    <div class="content text-gray-800 dark:text-gray-200 leading-relaxed">${contentHtml}</div>
                </div>
            </div>
        `;

        return div;
    }

    formatMessage(content) {
        if (!content) return '';

        // Escape HTML
        let html = content
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Convert code blocks (```language\ncode\n```)
        html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (match, lang, code) => {
            return `
                <div class="relative group my-4 rounded-lg overflow-hidden border border-gray-200 dark:border-gray-700">
                    <div class="flex items-center justify-between bg-gray-100 dark:bg-gray-800 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
                        <span class="text-xs font-medium text-gray-600 dark:text-gray-400">${lang || 'plaintext'}</span>
                        <button onclick="navigator.clipboard.writeText(this.parentElement.nextElementSibling.querySelector('code').textContent)" class="text-xs text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 flex items-center gap-1 transition-colors">
                            <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="14" height="14" x="8" y="8" rx="2" ry="2"/><path d="M4 16c-1.1 0-2-.9-2-2V4c0-1.1.9-2 2-2h10c1.1 0 2 .9 2 2"/></svg>
                            Copy
                        </button>
                    </div>
                    <pre class="bg-gray-50 dark:bg-[#0d1117] p-4 overflow-x-auto"><code class="text-sm text-gray-800 dark:text-gray-200 font-mono">${code.trim()}</code></pre>
                </div>
            `;
        });

        // Convert inline code
        html = html.replace(/`([^`]+)`/g, '<code class="bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded text-sm font-mono text-orange-600 dark:text-orange-400">$1</code>');

        // Convert bold
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>');

        // Convert italic
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');

        // Convert links
        html = html.replace(/\[([^\]]+)\]\(([^\)]+)\)/g, '<a href="$2" target="_blank" class="text-orange-600 dark:text-orange-400 hover:underline">$1</a>');

        // Convert newlines to breaks (only outside code blocks)
        html = html.replace(/\n/g, '<br>');

        return html;
    }

    showLoading() {
        const template = document.getElementById('loading-template');
        const loadingEl = template.content.cloneNode(true);
        const container = loadingEl.querySelector('.message-enter');
        container.id = 'loading-indicator';
        this.messagesContainer.appendChild(container);
        this.scrollToBottom();
    }

    hideLoading() {
        const loading = document.getElementById('loading-indicator');
        if (loading) loading.remove();
    }

    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.chatManager = new ChatManager();
});
