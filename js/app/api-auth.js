class ApiAuth {
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

    checkRegistrationStatus() {
        return this._fetch('/registration-status');
    }

    login(username, password) {
        return this._fetch('/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
    }

    register(username, password) {
        return this._fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password }),
        });
    }

    changePassword(oldPassword, newPassword) {
        return this._fetch('/api/change-password', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ old_password: oldPassword, new_password: newPassword }),
        });
    }
}

export default new ApiAuth();
