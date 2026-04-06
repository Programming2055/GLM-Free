// Main application initialization and utilities.
console.log('App.js loading...');

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    console.log('Gemma Chat initialized');

    // Check API connectivity
    checkApiConnection();

    // Setup model selector
    setupModelSelector();

    // Setup custom model modal
    setupCustomModelModal();

    // Focus input on load
    const messageInput = document.getElementById('message-input');
    if (messageInput) {
        messageInput.focus();
    }
});

// Setup custom model modal
function setupCustomModelModal() {
    const modal = document.getElementById('add-model-modal');
    const addBtn = document.getElementById('add-model-btn');
    const cancelBtn = document.getElementById('cancel-add-model');
    const form = document.getElementById('add-model-form');

    if (!modal || !addBtn) return;

    // Show modal
    addBtn.addEventListener('click', () => {
        modal.classList.remove('hidden');
        document.getElementById('custom-model-id').focus();
    });

    // Hide modal
    function hideModal() {
        modal.classList.add('hidden');
        form.reset();
    }

    cancelBtn.addEventListener('click', hideModal);

    // Close on backdrop click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) hideModal();
    });

    // Handle form submit
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const modelId = document.getElementById('custom-model-id').value.trim();
        const name = document.getElementById('custom-model-name').value.trim();
        const type = document.getElementById('custom-model-type').value;
        const description = document.getElementById('custom-model-description').value.trim();

        try {
            await API.addCustomModel({
                model_id: modelId,
                name: name,
                type: type,
                description: description
            });

            alert(`Model '${name}' added successfully!`);
            hideModal();

            // Refresh the model list
            await setupModelSelector();

            // Select the newly added model
            const selector = document.getElementById('model-selector');
            const newOption = selector.querySelector(`option[value="zai:${modelId}"]`);
            if (newOption) {
                selector.value = `zai:${modelId}`;
                selector.dispatchEvent(new Event('change'));
            }
        } catch (error) {
            alert('Error: ' + error.message);
        }
    });
}

// Setup model selector
async function setupModelSelector() {
    const selector = document.getElementById('model-selector');
    if (!selector) return;

    try {
        // Load available providers
        const data = await API.getProviders();
        console.log('Available providers:', data.providers);

        // Clear existing options
        selector.innerHTML = '';

        // Group providers by type
        const huggingFaceProviders = data.providers.filter(p => p.id === 'huggingface');
        const zaiTextProviders = data.providers.filter(p => p.id.startsWith('zai:') && p.type === 'text');
        const zaiVisionProviders = data.providers.filter(p => p.id.startsWith('zai:') && p.type === 'vision');

        // Add Hugging Face option
        huggingFaceProviders.forEach(provider => {
            const option = document.createElement('option');
            option.value = provider.id;
            option.textContent = provider.name;
            option.disabled = !provider.available;
            if (!provider.available) {
                option.textContent += ' (not configured)';
            }
            selector.appendChild(option);
        });

        // Add Z.AI Text Models group
        if (zaiTextProviders.length > 0) {
            const zaiGroup = document.createElement('optgroup');
            zaiGroup.label = 'Z.AI Text Models';

            zaiTextProviders.forEach(provider => {
                const option = document.createElement('option');
                option.value = provider.id;
                option.textContent = provider.name;
                option.disabled = !provider.available;
                if (!provider.available) {
                    option.textContent += ' (not configured)';
                }
                zaiGroup.appendChild(option);
            });

            selector.appendChild(zaiGroup);
        }

        // Add Z.AI Vision Models group
        if (zaiVisionProviders.length > 0) {
            const visionGroup = document.createElement('optgroup');
            visionGroup.label = 'Z.AI Vision Models';

            zaiVisionProviders.forEach(provider => {
                const option = document.createElement('option');
                option.value = provider.id;
                option.textContent = provider.name;
                option.disabled = !provider.available;
                if (!provider.available) {
                    option.textContent += ' (not configured)';
                }
                visionGroup.appendChild(option);
            });

            selector.appendChild(visionGroup);
        }

        // Set initial provider (prefer first available)
        const availableProvider = data.providers.find(p => p.available);
        if (availableProvider) {
            selector.value = availableProvider.id;
            API.setProvider(availableProvider.id);

            // Update sidebar model name
            const sidebarModelName = document.getElementById('sidebar-model-name');
            if (sidebarModelName) {
                sidebarModelName.textContent = availableProvider.name;
            }
        }
    } catch (error) {
        console.error('Failed to load providers:', error);
    }

    // Handle provider change
    selector.addEventListener('change', (e) => {
        const provider = e.target.value;
        API.setProvider(provider);
        console.log('Switched to provider:', provider);

        // Update UI to reflect provider change
        const providerName = e.target.options[e.target.selectedIndex].text;
        console.log(`Model switched to: ${providerName}`);

        // Update sidebar model name
        const sidebarModelName = document.getElementById('sidebar-model-name');
        if (sidebarModelName) {
            sidebarModelName.textContent = providerName.replace(' (not configured)', '');
        }
    });
}

// Check if the API is reachable
async function checkApiConnection() {
    try {
        const response = await fetch('/api/conversations');
        if (response.ok) {
            console.log('API connection successful');
        } else {
            console.error('API connection failed');
            showConnectionError();
        }
    } catch (error) {
        console.error('API connection error:', error);
        showConnectionError();
    }
}

// Show connection error message
function showConnectionError() {
    const container = document.getElementById('messages-container');
    container.innerHTML = `
        <div class="flex flex-col items-center justify-center min-h-[60vh] px-4">
            <div class="w-16 h-16 bg-red-100 dark:bg-red-900/30 rounded-2xl flex items-center justify-center mb-6">
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-red-500">
                    <path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>
                    <line x1="12" x2="12" y1="9" y2="13"/>
                    <line x1="12" x2="12.01" y1="17" y2="17"/>
                </svg>
            </div>
            <h2 class="text-2xl font-semibold text-gray-900 dark:text-white mb-2">Connection Error</h2>
            <p class="text-gray-500 dark:text-gray-400 text-center max-w-md mb-6">
                Unable to connect to the chat server. Please make sure the Flask backend is running.
            </p>
            <div class="text-sm text-gray-600 dark:text-gray-400 text-center">
                <p class="mb-2">To start the server, run:</p>
                <code class="bg-gray-100 dark:bg-gray-800 px-4 py-2 rounded-lg block text-left font-mono">
                    cd web<br>
                    python app.py
                </code>
            </div>
        </div>
    `;
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    // Escape to close sidebar on mobile
    if (e.key === 'Escape') {
        const sidebar = document.getElementById('sidebar');
        const overlay = document.getElementById('sidebar-overlay');

        if (!sidebar.classList.contains('-translate-x-full') && window.innerWidth < 768) {
            sidebar.classList.add('-translate-x-full');
            overlay.classList.add('hidden');
        }
    }

    // Cmd/Ctrl + K to focus input
    if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        const messageInput = document.getElementById('message-input');
        if (messageInput) {
            messageInput.focus();
        }
    }
});

// Handle window resize
window.addEventListener('resize', () => {
    const sidebar = document.getElementById('sidebar');
    const overlay = document.getElementById('sidebar-overlay');

    // Reset sidebar on desktop
    if (window.innerWidth >= 768) {
        sidebar.classList.remove('-translate-x-full');
        overlay.classList.add('hidden');
    } else {
        sidebar.classList.add('-translate-x-full');
    }
});

// Prevent leaving page while streaming
window.addEventListener('beforeunload', (e) => {
    if (window.chatManager?.isStreaming) {
        e.preventDefault();
        e.returnValue = 'A response is being generated. Are you sure you want to leave?';
        return e.returnValue;
    }
});

// Auto-detect dark mode
if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
}

// Listen for dark mode changes
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (e.matches) {
        document.documentElement.classList.add('dark');
    } else {
        document.documentElement.classList.remove('dark');
    }
});
