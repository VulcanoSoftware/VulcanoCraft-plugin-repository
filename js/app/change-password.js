import ApiAuth from './api-auth.js';

class ChangePasswordPage {
    constructor() {
        this.changePasswordForm = document.getElementById('changePasswordForm');
        this.passwordChangeMessage = document.getElementById('passwordChangeMessage');

        this._addEventListeners();
    }

    _addEventListeners() {
        if (this.changePasswordForm) {
            this.changePasswordForm.addEventListener('submit', (e) => this.handleSubmit(e));
        }
    }

    async handleSubmit(e) {
        e.preventDefault();

        const oldPassword = document.getElementById('oldPassword').value;
        const newPassword = document.getElementById('newPassword').value;
        const confirmNewPassword = document.getElementById('confirmNewPassword').value;

        if (newPassword !== confirmNewPassword) {
            this._showMessage('Nieuwe wachtwoorden komen niet overeen.', 'danger');
            return;
        }

        try {
            const data = await ApiAuth.changePassword(oldPassword, newPassword);
            this._showMessage(data.message, 'success');
            this.changePasswordForm.reset();
        } catch (error) {
            this._showMessage(error.message, 'danger');
        }
    }

    _showMessage(message, type) {
        this.passwordChangeMessage.textContent = message;
        this.passwordChangeMessage.className = `alert alert-${type}`;
        this.passwordChangeMessage.classList.remove('hidden');
    }
}

document.addEventListener('DOMContentLoaded', () => new ChangePasswordPage());
