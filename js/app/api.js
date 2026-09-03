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

    getPlugins(params = {}) {
        const query = new URLSearchParams();
        if (params.page !== undefined) query.set('page', params.page);
        if (params.perPage !== undefined) query.set('per_page', params.perPage);
        if (params.search) query.set('search', params.search);
        if (params.version) query.set('version', params.version);
        if (params.platforms !== undefined) query.set('platforms', Array.isArray(params.platforms) ? params.platforms.join(',') : params.platforms);
        if (params.loaders !== undefined) query.set('loaders', Array.isArray(params.loaders) ? params.loaders.join(',') : params.loaders);
        if (params.category) query.set('category', params.category);
        if (params.include !== undefined) query.set('include', params.include);
        if (params.sort) query.set('sort', params.sort);

        const queryString = query.toString();
        const url = queryString ? `/api/plugins/public?${queryString}` : '/api/plugins/public';
        return this._fetch(url);
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

    clearPlugins(all = false, category = null) {
        return this._fetch('/api/plugins/clear', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ all, category }),
        });
    }

    deletePlugin(url, category) {
        return this._fetch('/delete_plugin', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url, category }),
        });
    }

    getServerInfo() {
        return this._fetch('/api/server_info').catch(() => ({})); // Return empty object on error
    }

    async getServerCategories() {
        try {
            const response = await fetch('/api/server_categories');
            if (!response.ok) {
                return [];
            }
            const data = await response.json();
            return Array.isArray(data) ? data : [];
        } catch (error) {
            return [];
        }
    }
}

export default new API();
