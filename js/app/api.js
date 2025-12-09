class API {
    async _fetch(url, options = {}) {
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({ error: `Server responded with status: ${response.status}` }));
                throw new Error(errorData.error || `Server responded with status: ${response.status}`);
            }
            return response.json();
        } catch (error) {
            console.error(`Fetch error for ${url}:`, error);
            throw error;
        }
    }

    getAuthStatus() {
        return this._fetch('/auth-status');
    }

    logout() {
        return this._fetch('/logout', { method: 'POST' });
    }

    getPlugins() {
        return this._fetch('/api/plugins/public');
    }

    fetchPlugin(url) {
        return this._fetch('/fetch_plugin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
    }

    addPlugin(pluginData) {
        return this._fetch('/add_plugin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ plugin_data: pluginData }),
        });
    }

    deletePlugin(url) {
        return this._fetch('/delete_plugin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
        });
    }

    getServerInfo() {
        return this._fetch('/api/server_info').catch(() => ({})); // Return empty object on error
    }

    async getServerCategories() {
         try {
            const response = await fetch('/api/server_categories');
            if (!response.ok) {
                return this.getServerCategoriesFallback();
            }
            const data = await response.json();
            return (Array.isArray(data) && data.length) ? data : this.getServerCategoriesFallback();
        } catch (error) {
            return this.getServerCategoriesFallback();
        }
    }

    getServerCategoriesFallback() {
        return this._fetch('/server_categories.json').catch(() => null);
    }
}

export default new API();
