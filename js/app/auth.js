import API from './api.js';
import UI from './ui.js';

class Auth {
    constructor() {
        this.logoutBtn = document.getElementById('logoutBtn');
        this.currentUser = null;
        this.authStatus = { logged_in: false, role: 'user' };
        this._addEventListeners();
    }

    _addEventListeners() {
        this.logoutBtn.addEventListener('click', () => this.handleLogout());
    }

    async checkStatus() {
        try {
            this.authStatus = await API.getAuthStatus();
            this.currentUser = this.authStatus.username || null;
        } catch (error) {
            console.error('Failed to get auth status:', error);
            this.authStatus = { logged_in: false, role: 'user' };
            this.currentUser = null;
        }
        UI.updateAuthUI(this.authStatus);
        return this.authStatus;
    }

    async handleLogout() {
        try {
            await API.logout();
            window.location.reload();
        } catch (error) {
            console.error('Logout failed:', error);
            // Still try to update UI
            this.checkStatus();
        }
    }
}

export default new Auth();
