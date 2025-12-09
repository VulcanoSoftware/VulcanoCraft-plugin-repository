class ApiAdmin {
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

    checkSession() {
        return this._fetch('/admin/check-session');
    }

    login(username, password) {
        return this._fetch('/admin/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
    }

    logout() {
        return this._fetch('/admin/logout', { method: 'POST' });
    }

    getSettings() {
        return this._fetch('/admin/settings');
    }

    updateSettings(settings) {
        return this._fetch('/admin/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings),
        });
    }

    getUsers() {
        return this._fetch('/admin/users');
    }

    updateUserRole(username, role) {
        return this._fetch(`/admin/users/${username}/role`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ role }),
        });
    }

    deleteUser(username) {
        return this._fetch(`/admin/users/${username}`, { method: 'DELETE' });
    }

    getCategories() {
        return this._fetch('/admin/categories');
    }

    addCategory(name) {
        return this._fetch('/admin/categories', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name }),
        });
    }

    updateCategory(oldName, categoryData) {
        return this._fetch(`/admin/categories/${oldName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(categoryData),
        });
    }

    deleteCategory(name) {
        return this._fetch(`/admin/categories/${name}`, { method: 'DELETE' });
    }

    getPlugins() {
        return this._fetch('/admin/plugins');
    }

    updatePlugin(url, pluginData) {
        return this._fetch(`/admin/plugins/${encodeURIComponent(url)}/details`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(pluginData),
        });
    }

    deletePlugin(url) {
        return this._fetch(`/admin/plugins/${encodeURIComponent(url)}`, { method: 'DELETE' });
    }
}

export default new ApiAdmin();
