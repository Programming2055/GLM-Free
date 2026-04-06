// API client for communicating with the Flask backend.
console.log('API.js loading...');

const API_BASE = '';

// Store current provider
let currentProvider = 'huggingface';

const API = {
    // Provider management
    setProvider(provider) {
        currentProvider = provider;
        console.log('Provider set to:', provider);
    },

    getProvider() {
        return currentProvider;
    },

    async getProviders() {
        const response = await fetch(`${API_BASE}/api/providers`);
        if (!response.ok) throw new Error('Failed to load providers');
        return response.json();
    },

    async addCustomModel(modelData) {
        const response = await fetch(`${API_BASE}/api/providers/custom`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(modelData)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to add custom model');
        }
        return response.json();
    },

    // Conversations
    // Conversations
    async getConversations() {
        const response = await fetch(`${API_BASE}/api/conversations`);
        if (!response.ok) throw new Error('Failed to load conversations');
        return response.json();
    },

    async createConversation(title = 'New Chat') {
        const response = await fetch(`${API_BASE}/api/conversations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        if (!response.ok) throw new Error('Failed to create conversation');
        return response.json();
    },

    async getConversation(id) {
        const response = await fetch(`${API_BASE}/api/conversations/${id}`);
        if (!response.ok) throw new Error('Failed to load conversation');
        return response.json();
    },

    async deleteConversation(id) {
        const response = await fetch(`${API_BASE}/api/conversations/${id}`, {
            method: 'DELETE'
        });
        if (!response.ok) throw new Error('Failed to delete conversation');
        return response.json();
    },

    async updateConversationTitle(id, title) {
        const response = await fetch(`${API_BASE}/api/conversations/${id}/title`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ title })
        });
        if (!response.ok) throw new Error('Failed to update title');
        return response.json();
    },

    // Chat
    async sendMessage(conversationId, message, options = {}) {
        const body = {
            conversation_id: conversationId,
            message,
            temperature: options.temperature || 0.7,
            max_tokens: options.maxTokens || null,
            provider: currentProvider
        };

        // Add thinking parameter if enabled
        if (options.thinking !== undefined) {
            body.thinking = options.thinking;
        }

        const response = await fetch(`${API_BASE}/api/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to send message');
        }
        return response.json();
    },

    async sendMessageStream(conversationId, message, options = {}) {
        const body = {
            conversation_id: conversationId,
            message,
            temperature: options.temperature || 0.7,
            max_tokens: options.maxTokens || null,
            provider: currentProvider
        };

        // Add thinking parameter if enabled
        if (options.thinking !== undefined) {
            body.thinking = options.thinking;
        }

        const response = await fetch(`${API_BASE}/api/chat/stream`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!response.ok) throw new Error('Failed to start stream');
        return response;
    },

    // Vision
    async analyzeImage(conversationId, imageUrl, prompt, options = {}) {
        const response = await fetch(`${API_BASE}/api/vision`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                conversation_id: conversationId,
                image_url: imageUrl,
                prompt: prompt || 'Describe this image.',
                temperature: options.temperature || 0.7,
                max_tokens: options.maxTokens || null,
                provider: currentProvider
            })
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to analyze image');
        }
        return response.json();
    },

    // Upload
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${API_BASE}/api/upload`, {
            method: 'POST',
            body: formData
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to upload file');
        }
        return response.json();
    },

    // Legacy function for backwards compatibility
    async uploadImage(file) {
        return this.uploadFile(file);
    }
};
