// Sidebar management for conversations.
console.log('Sidebar.js loading...');

class SidebarManager {
    constructor() {
        this.sidebar = document.getElementById('sidebar');
        this.overlay = document.getElementById('sidebar-overlay');
        this.conversationList = document.getElementById('conversation-list');
        this.newChatBtn = document.getElementById('new-chat-btn');
        this.toggleSidebarBtn = document.getElementById('toggle-sidebar');

        this.conversations = [];
        this.activeConversationId = null;
        this.isCreatingChat = false; // Prevent duplicate creation

        this.init();
    }

    init() {
        console.log('SidebarManager.init() called');
        console.log('Sidebar elements:', {
            newChatBtn: !!this.newChatBtn,
            clearHistoryBtn: !!this.clearHistoryBtn,
            toggleSidebarBtn: !!this.toggleSidebarBtn
        });

        // Event listeners - only attach once
        this.newChatBtn.addEventListener('click', () => {
            console.log('New chat button clicked');
            this.createNewChat();
        });
        this.toggleSidebarBtn.addEventListener('click', () => this.toggleSidebar());
        this.overlay.addEventListener('click', () => this.closeSidebar());

        // Load conversations
        this.loadConversations();
    }

    toggleSidebar() {
        this.sidebar.classList.toggle('-translate-x-full');
        this.overlay.classList.toggle('hidden');
    }

    closeSidebar() {
        this.sidebar.classList.add('-translate-x-full');
        this.overlay.classList.add('hidden');
    }

    async loadConversations() {
        try {
            const data = await API.getConversations();
            this.conversations = data.conversations;
            this.renderConversations();
        } catch (error) {
            console.error('Failed to load conversations:', error);
        }
    }

    renderConversations() {
        this.conversationList.innerHTML = '';

        if (this.conversations.length === 0) {
            this.conversationList.innerHTML = `
                <div class="text-gray-500 dark:text-gray-400 text-sm text-center py-8 px-4">
                    No conversations yet
                </div>
            `;
            return;
        }

        // Group by date
        const groups = this.groupByDate(this.conversations);

        for (const [dateLabel, items] of Object.entries(groups)) {
            const groupEl = document.createElement('div');
            groupEl.className = 'mb-4';

            // Date header
            const header = document.createElement('div');
            header.className = 'text-xs text-gray-500 dark:text-gray-400 font-medium px-3 mb-1';
            header.textContent = dateLabel;
            groupEl.appendChild(header);

            // Conversation items
            items.forEach(conv => {
                const item = this.createConversationItem(conv);
                groupEl.appendChild(item);
            });

            this.conversationList.appendChild(groupEl);
        }
    }

    createConversationItem(conversation) {
        const div = document.createElement('div');
        const isActive = conversation.id === this.activeConversationId;

        div.className = `
            group flex items-center gap-3 px-3 py-2.5 mx-2 rounded-lg cursor-pointer
            transition-colors relative
            ${isActive
                ? 'bg-gray-200 dark:bg-gray-700 text-gray-900 dark:text-white'
                : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800'
            }
        `;

        const title = this.escapeHtml(conversation.title || 'New Chat');
        const shortTitle = title.length > 30 ? title.substring(0, 30) + '...' : title;

        div.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="flex-shrink-0 opacity-60">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
            </svg>
            <span class="flex-1 truncate text-sm font-medium">${shortTitle}</span>
            <button class="delete-btn opacity-0 group-hover:opacity-100 p-1.5 hover:bg-red-100 dark:hover:bg-red-900/30 text-gray-400 hover:text-red-600 dark:hover:text-red-400 rounded-md transition-all">
                <svg xmlns="http://www.w3.org/2000/svg" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M18 6 6 18"/><path d="m6 6 12 12"/>
                </svg>
            </button>
        `;

        // Click to load conversation
        div.addEventListener('click', (e) => {
            if (e.target.closest('.delete-btn')) return;
            this.loadConversation(conversation.id);
        });

        // Delete button
        const deleteBtn = div.querySelector('.delete-btn');
        deleteBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            this.deleteConversation(conversation.id);
        });

        return div;
    }

    groupByDate(conversations) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);

        const weekAgo = new Date(today);
        weekAgo.setDate(weekAgo.getDate() - 7);

        const groups = {
            'Today': [],
            'Yesterday': [],
            'Previous 7 Days': [],
            'Older': []
        };

        conversations.forEach(conv => {
            const date = new Date(conv.updated_at);
            date.setHours(0, 0, 0, 0);

            if (date.getTime() === today.getTime()) {
                groups['Today'].push(conv);
            } else if (date.getTime() === yesterday.getTime()) {
                groups['Yesterday'].push(conv);
            } else if (date > weekAgo) {
                groups['Previous 7 Days'].push(conv);
            } else {
                groups['Older'].push(conv);
            }
        });

        // Remove empty groups
        for (const key of Object.keys(groups)) {
            if (groups[key].length === 0) {
                delete groups[key];
            }
        }

        return groups;
    }

    isSameDay(date1, date2) {
        return date1.toDateString() === date2.toDateString();
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    async createNewChat() {
        // Prevent duplicate chat creation
        if (this.isCreatingChat) {
            console.log('Already creating a chat, skipping duplicate');
            return;
        }

        this.isCreatingChat = true;

        try {
            const data = await API.createConversation();
            this.activeConversationId = data.conversation.id;

            // Reload conversations
            await this.loadConversations();

            // Notify chat manager
            document.dispatchEvent(new CustomEvent('conversationCreated', {
                detail: data.conversation
            }));

            // Close sidebar on mobile
            if (window.innerWidth < 768) {
                this.closeSidebar();
            }
        } catch (error) {
            console.error('Failed to create conversation:', error);
            alert('Failed to create new chat');
        } finally {
            this.isCreatingChat = false;
        }
    }

    async loadConversation(id) {
        this.activeConversationId = id;
        this.renderConversations(); // Update active state

        document.dispatchEvent(new CustomEvent('conversationLoaded', {
            detail: { id }
        }));

        // Close sidebar on mobile
        if (window.innerWidth < 768) {
            this.closeSidebar();
        }
    }

    async deleteConversation(id) {
        if (!confirm('Delete this conversation?')) return;

        try {
            await API.deleteConversation(id);

            // If active conversation was deleted, create new one
            if (id === this.activeConversationId) {
                document.dispatchEvent(new CustomEvent('conversationDeleted'));
            }

            await this.loadConversations();
        } catch (error) {
            console.error('Failed to delete conversation:', error);
        }
    }

    async clearHistory() {
        if (!confirm('Clear all conversation history? This cannot be undone.')) return;

        try {
            // Delete all conversations
            for (const conv of this.conversations) {
                await API.deleteConversation(conv.id);
            }

            await this.loadConversations();
            document.dispatchEvent(new CustomEvent('historyCleared'));
        } catch (error) {
            console.error('Failed to clear history:', error);
        }
    }

    getActiveConversationId() {
        return this.activeConversationId;
    }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.sidebarManager = new SidebarManager();
});
