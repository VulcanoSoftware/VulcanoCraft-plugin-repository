// This file contains modal dialog handlers for the Vulcano plugin manager

// Modal for adding a new plugin
const addPluginModal = {
    element: null,
    form: null,
    submitButton: null,
    cancelButton: null,
    
    init() {
        this.element = document.getElementById('addPluginModal');
        this.form = document.getElementById('addPluginForm');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.cancelButton = this.form.querySelector('button[type="reset"]');
        
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        if (this.cancelButton) {
            this.cancelButton.addEventListener('click', () => this.close());
        }
    },
    
    open() {
        if (this.element) {
            this.element.style.display = 'block';
            this.form?.reset();
        }
    },
    
    close() {
        if (this.element) {
            this.element.style.display = 'none';
        }
    },
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (!this.form) return;
        
        const formData = new FormData(this.form);
        const pluginName = formData.get('pluginName');
        const pluginUrl = formData.get('pluginUrl');
        const pluginVersion = formData.get('pluginVersion');
        const pluginDescription = formData.get('pluginDescription');
        
        // Validate inputs
        if (!pluginName || !pluginUrl || !pluginVersion) {
            alert('Please fill in all required fields');
            return;
        }
        
        try {
            this.submitButton.disabled = true;
            this.submitButton.textContent = 'Adding...';
            
            const response = await fetch('/api/plugins', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: pluginName,
                    url: pluginUrl,
                    version: pluginVersion,
                    description: pluginDescription
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to add plugin: ${response.statusText}`);
            }
            
            const result = await response.json();
            
            // Reset form
            this.form.reset();
            
            // Reset cachedPluginData to trigger reload detection in main.js
            if (typeof window.cachedPluginData !== 'undefined') {
                window.cachedPluginData = null;
            }
            
            // Set success flag to indicate successful addition
            window.pluginAddedSuccessfully = true;
            
            // Hide the modal
            this.close();
            
            // Show success message
            alert('Plugin added successfully!');
            
            // Trigger reload by setting cachedPluginData to a non-null value
            // This allows the event listener in main.js to detect the change
            setTimeout(() => {
                window.cachedPluginData = { reloadTriggered: true, timestamp: Date.now() };
            }, 100);
            
        } catch (error) {
            console.error('Error adding plugin:', error);
            alert(`Error: ${error.message}`);
        } finally {
            this.submitButton.disabled = false;
            this.submitButton.textContent = 'Add Plugin';
        }
    }
};

// Modal for editing a plugin
const editPluginModal = {
    element: null,
    form: null,
    pluginId: null,
    submitButton: null,
    cancelButton: null,
    
    init() {
        this.element = document.getElementById('editPluginModal');
        this.form = document.getElementById('editPluginForm');
        this.submitButton = this.form.querySelector('button[type="submit"]');
        this.cancelButton = this.form.querySelector('button[type="reset"]');
        
        if (this.form) {
            this.form.addEventListener('submit', (e) => this.handleSubmit(e));
        }
        
        if (this.cancelButton) {
            this.cancelButton.addEventListener('click', () => this.close());
        }
    },
    
    open(pluginId) {
        this.pluginId = pluginId;
        if (this.element) {
            this.element.style.display = 'block';
        }
    },
    
    close() {
        if (this.element) {
            this.element.style.display = 'none';
        }
    },
    
    async handleSubmit(e) {
        e.preventDefault();
        
        if (!this.form || !this.pluginId) return;
        
        const formData = new FormData(this.form);
        const pluginName = formData.get('editPluginName');
        const pluginUrl = formData.get('editPluginUrl');
        const pluginVersion = formData.get('editPluginVersion');
        const pluginDescription = formData.get('editPluginDescription');
        
        try {
            this.submitButton.disabled = true;
            this.submitButton.textContent = 'Updating...';
            
            const response = await fetch(`/api/plugins/${this.pluginId}`, {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    name: pluginName,
                    url: pluginUrl,
                    version: pluginVersion,
                    description: pluginDescription
                })
            });
            
            if (!response.ok) {
                throw new Error(`Failed to update plugin: ${response.statusText}`);
            }
            
            // Reset cachedPluginData to trigger reload
            if (typeof window.cachedPluginData !== 'undefined') {
                window.cachedPluginData = null;
            }
            
            this.form.reset();
            this.close();
            
            alert('Plugin updated successfully!');
            
            // Trigger reload
            setTimeout(() => {
                window.cachedPluginData = { reloadTriggered: true, timestamp: Date.now() };
            }, 100);
            
        } catch (error) {
            console.error('Error updating plugin:', error);
            alert(`Error: ${error.message}`);
        } finally {
            this.submitButton.disabled = false;
            this.submitButton.textContent = 'Update Plugin';
        }
    }
};

// Initialize modals when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    addPluginModal.init();
    editPluginModal.init();
});
