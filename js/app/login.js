import ApiAuth from './api-auth.js';

class LoginPage {
    constructor() {
        this.loginForm = document.getElementById('loginForm');
        this.registerForm = document.getElementById('registerForm');
        this.showRegisterLink = document.getElementById('showRegister');
        this.showLoginLink = document.getElementById('showLogin');
        this.loginBtn = document.getElementById('loginBtn');
        this.registerBtn = document.getElementById('registerBtn');
        this.loginError = document.getElementById('loginError');
        this.registerError = document.getElementById('registerError');

        this._addEventListeners();
    }

    _addEventListeners() {
        this.showRegisterLink.addEventListener('click', (e) => this.showRegisterForm(e));
        this.showLoginLink.addEventListener('click', (e) => this.showLoginForm(e));
        this.loginBtn.addEventListener('click', () => this.handleLogin());
        this.registerBtn.addEventListener('click', () => this.handleRegister());
    }

    async showRegisterForm(e) {
        e.preventDefault();
        try {
            const data = await ApiAuth.checkRegistrationStatus();
            if (data.enabled) {
                this.loginForm.style.display = 'none';
                this.registerForm.style.display = 'block';
            } else {
                this._showRegistrationDisabledMessage();
            }
        } catch (error) {
            this._showRegistrationDisabledMessage();
        }
    }

    showLoginForm(e) {
        e.preventDefault();
        this.registerForm.style.display = 'none';
        this.loginForm.style.display = 'block';
    }

    async handleLogin() {
        const username = document.getElementById('loginUsername').value;
        const password = document.getElementById('loginPassword').value;
        this.loginError.style.display = 'none';

        try {
            const data = await ApiAuth.login(username, password);
            if (data.success) {
                window.location.href = '/';
            } else {
                this.loginError.textContent = data.error;
                this.loginError.style.display = 'block';
            }
        } catch (error) {
            this.loginError.textContent = 'Fout bij inloggen';
            this.loginError.style.display = 'block';
        }
    }

    async handleRegister() {
        const username = document.getElementById('registerUsername').value;
        const password = document.getElementById('registerPassword').value;
        this.registerError.style.display = 'none';

        try {
            const data = await ApiAuth.register(username, password);
            if (data.success) {
                this._showSuccessMessage('Registratie succesvol! Je kunt nu inloggen.');
                setTimeout(() => {
                    this.registerForm.style.display = 'none';
                    this.loginForm.style.display = 'block';
                }, 2000);
            } else {
                this.registerError.textContent = data.error;
                this.registerError.style.display = 'block';
            }
        } catch (error) {
            this.registerError.textContent = 'Fout bij registreren';
            this.registerError.style.display = 'block';
        }
    }

    _showRegistrationDisabledMessage() {
        const overlay = this._createOverlay(`
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%);">
                <i class="fas fa-user-slash"></i>
                <h4>Registratie Uitgeschakeld</h4>
                <p>Nieuwe registraties zijn momenteel niet toegestaan.</p>
                <button class="btn btn-light btn-lg" id="closeRegistrationMessage">Sluiten</button>
            </div>
        `);
        overlay.querySelector('#closeRegistrationMessage').addEventListener('click', () => overlay.remove());
    }

    _showSuccessMessage(message) {
        const overlay = this._createOverlay(`
            <div style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <i class="fas fa-check-circle"></i>
                <h4>Succes!</h4>
                <p>${message}</p>
            </div>
        `);
        setTimeout(() => overlay.remove(), 2000);
    }

    _createOverlay(innerHTML) {
        const overlay = document.createElement('div');
        overlay.className = 'message-overlay';
        overlay.innerHTML = `<div class="message-card">${innerHTML}</div>`;
        document.body.appendChild(overlay);
        return overlay;
    }
}

document.addEventListener('DOMContentLoaded', () => new LoginPage());
