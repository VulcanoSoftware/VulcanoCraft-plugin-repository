import ApiAdmin from './api-admin.js';

class AdminPage {
    constructor() {
        this.loginForm = document.getElementById('loginForm');
        this.adminPanel = document.getElementById('adminPanel');
        this.adminLoginForm = document.getElementById('adminLoginForm');
        this.logoutBtn = this.adminPanel.querySelector('button');
        this.registrationToggle = document.getElementById('registrationToggle');
        this.usersGrid = document.getElementById('usersGrid');
        this.categoriesGrid = document.getElementById('categoriesGrid');
        this.pluginsGrid = document.getElementById('pluginsGrid');
        this.newCategoryName = document.getElementById('newCategoryName');
        this.addCategoryBtn = document.querySelector('#categoryManagement button');
        this.currentRole = null;
    }

    async init() {
        this._setupEventListeners();
        try {
            const data = await ApiAdmin.checkSession();
            if (data.logged_in) {
                this.currentRole = data.role;
                this._showAdminPanel();
            }
        } catch (error) {
            // Not logged in
        }
    }

    _setupEventListeners() {
        this.adminLoginForm.addEventListener('submit', (e) => this._handleLogin(e));
        this.logoutBtn.addEventListener('click', () => this._handleLogout());
        this.registrationToggle.addEventListener('change', (e) => this._handleRegistrationToggle(e));
        this.addCategoryBtn.addEventListener('click', () => this._handleAddCategory());

        this._setupDynamicEventListeners();
    }

    _setupDynamicEventListeners() {
        // Use event delegation for dynamically created elements
        document.body.addEventListener('change', (e) => {
            if (e.target.matches('.user-role-select')) {
                this._handleRoleChange(e.target);
            } else if (e.target.matches('.category-field')) {
                this._handleCategoryUpdate(e.target);
            } else if (e.target.matches('.plugin-field')) {
                this._handlePluginUpdate(e.target);
            }
        });

        document.body.addEventListener('click', (e) => {
            if (e.target.closest('.delete-user-btn')) {
                this._handleDeleteUser(e.target.closest('.delete-user-btn'));
            } else if (e.target.closest('.delete-category-btn')) {
                this._handleDeleteCategory(e.target.closest('.delete-category-btn'));
            } else if (e.target.closest('.delete-plugin-btn')) {
                this._handleDeletePlugin(e.target.closest('.delete-plugin-btn'));
            }
        });
    }

    async _handleLogin(e) {
        e.preventDefault();
        const username = document.getElementById('adminUsername').value;
        const password = document.getElementById('adminPassword').value;
        const errorDiv = document.getElementById('loginError');

        try {
            const data = await ApiAdmin.login(username, password);
            if (data.success) {
                this.currentRole = data.role;
                this._showAdminPanel();
            } else {
                errorDiv.textContent = data.error;
                errorDiv.style.display = 'block';
            }
        } catch (error) {
            errorDiv.textContent = 'Login failed';
            errorDiv.style.display = 'block';
        }
    }

    async _handleLogout() {
        await ApiAdmin.logout();
        this.loginForm.style.display = 'block';
        this.adminPanel.style.display = 'none';
        document.getElementById('adminUsername').value = '';
        document.getElementById('adminPassword').value = '';
    }

    async _handleRegistrationToggle(e) {
        const enabled = e.target.checked;
        try {
            await ApiAdmin.updateSettings({ registration_enabled: enabled });
        } catch (error) {
            alert('Fout bij opslaan instellingen');
            e.target.checked = !enabled;
        }
    }

    async _handleAddCategory() {
        const name = this.newCategoryName.value.trim();
        if (!name) return;

        try {
            await ApiAdmin.addCategory(name);
            this.newCategoryName.value = '';
            this._loadCategories();
            this._loadPlugins(); // Refresh plugin category dropdowns
        } catch (error) {
            alert(`Fout bij toevoegen categorie: ${error.message}`);
        }
    }

    async _handleRoleChange(selectElement) {
        const username = selectElement.dataset.username;
        const newRole = selectElement.value;
        try {
            await ApiAdmin.updateUserRole(username, newRole);
            this._loadUsers();
        } catch (error) {
            alert('Fout bij wijzigen rol');
        }
    }

    async _handleDeleteUser(button) {
        const username = button.dataset.username;
        if (confirm(`Weet je zeker dat je gebruiker "${username}" wilt verwijderen?`)) {
            try {
                await ApiAdmin.deleteUser(username);
                this._loadUsers();
            } catch (error) {
                alert('Fout bij verwijderen gebruiker');
            }
        }
    }

    async _handleCategoryUpdate(inputElement) {
        const oldName = inputElement.dataset.name;
        const card = inputElement.closest('.card-body');
        const newName = card.querySelector(`.cat-name`).value.trim();
        if (!newName) {
            alert("Categorie naam mag niet leeg zijn.");
            this._loadCategories();
            return;
        }

        const categoryData = {
            new_name: newName,
            image_url: card.querySelector(`.cat-image`).value.trim(),
            show_image: card.querySelector(`.cat-show`).checked,
            software: card.querySelector(`.cat-software`).value.trim(),
            version: card.querySelector(`.cat-version`).value.trim(),
        };

        try {
            await ApiAdmin.updateCategory(oldName, categoryData);
            if (oldName !== newName) {
                this._loadCategories();
                this._loadPlugins();
            }
        } catch (error) {
            alert(`Fout bij bijwerken categorie: ${error.message}`);
            this._loadCategories();
        }
    }

    async _handleDeleteCategory(button) {
        const name = button.dataset.name;
        if (confirm(`Weet je zeker dat je categorie "${name}" wilt verwijderen?`)) {
            try {
                await ApiAdmin.deleteCategory(name);
                this._loadCategories();
                this._loadPlugins();
            } catch (error) {
                alert(`Fout bij verwijderen categorie: ${error.message}`);
            }
        }
    }

    async _handlePluginUpdate(inputElement) {
        const url = inputElement.dataset.url;
        const card = inputElement.closest('.card-body');
        const pluginData = {
            title: card.querySelector('.plugin-title').value,
            author: card.querySelector('.plugin-author').value,
            category: card.querySelector('.plugin-category').value,
        };
        try {
            await ApiAdmin.updatePlugin(url, pluginData);
        } catch (error) {
            alert(`Fout bij bijwerken plugin: ${error.message}`);
            this._loadPlugins();
        }
    }

    async _handleDeletePlugin(button) {
        const url = button.dataset.url;
        const title = button.dataset.title;
        if (confirm(`Weet je zeker dat je plugin "${title}" wilt verwijderen?`)) {
            try {
                await ApiAdmin.deletePlugin(url);
                this._loadPlugins();
            } catch (error) {
                alert('Fout bij verwijderen plugin');
            }
        }
    }

    _showAdminPanel() {
        this.loginForm.style.display = 'none';
        this.adminPanel.style.display = 'block';
        document.getElementById('adminRole').textContent = this.currentRole.toUpperCase();
        this._loadAllData();
    }

    _loadAllData() {
        this._loadSettings();
        this._loadUsers();
        this._loadCategories();
        this._loadPlugins();
    }

    async _loadSettings() {
        const data = await ApiAdmin.getSettings();
        this.registrationToggle.checked = data.registration_enabled;
    }

    async _loadUsers() {
        const users = await ApiAdmin.getUsers();
        this.usersGrid.innerHTML = users.map(user => this._renderUser(user)).join('');
    }

    async _loadCategories() {
        const categories = await ApiAdmin.getCategories();
        this.categoriesGrid.innerHTML = categories.map(cat => this._renderCategory(cat)).join('');
    }

    async _loadPlugins() {
        const [plugins, categories] = await Promise.all([ApiAdmin.getPlugins(), ApiAdmin.getCategories()]);
        this.pluginsGrid.innerHTML = plugins.map(plugin => this._renderPlugin(plugin, categories)).join('');
    }

    _renderUser(user) {
        const canEdit = this.currentRole === 'admin' && user.username !== 'admin';
        const roleOptions = ['user', 'co-admin', 'admin']
            .map(r => `<option value="${r}" ${user.role === r ? 'selected' : ''}>${r.charAt(0).toUpperCase() + r.slice(1)}</option>`)
            .join('');

        return `
            <div class="col-md-4 col-lg-3 mb-3">
                <div class="card h-100">
                    <div class="card-body text-center">
                        <i class="fas fa-user-circle" style="font-size: 3rem; color: #6c757d;"></i>
                        <h6 class="card-title">${user.username}</h6>
                        <span class="badge ${this._getRoleBadgeClass(user.role)}">${user.role}</span>
                        <span class="badge bg-primary"><i class="fas fa-puzzle-piece me-1"></i>${user.plugin_count} plugins</span>
                        ${canEdit ? `
                            <select class="form-select form-select-sm mb-2 user-role-select" data-username="${user.username}">${roleOptions}</select>
                            <button class="btn btn-danger btn-sm delete-user-btn" data-username="${user.username}"><i class="fas fa-trash me-1"></i>Verwijderen</button>
                        ` : ''}
                    </div>
                </div>
            </div>`;
    }

    _renderCategory(category) {
        const safeCatName = category.name.replace(/'/g, "\\'");
        return `
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-body" data-name="${safeCatName}">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <h5 class="card-title mb-0">${category.name}</h5>
                            <button class="btn btn-danger btn-sm delete-category-btn" data-name="${safeCatName}"><i class="fas fa-trash"></i></button>
                        </div>
                        <input type="text" class="form-control form-control-sm mb-2 category-field cat-name" value="${category.name}" data-name="${safeCatName}">
                        <input type="text" class="form-control form-control-sm mb-2 category-field cat-image" value="${category.image_url || ''}" data-name="${safeCatName}" placeholder="Image URL">
                        <div class="form-check form-switch mb-2">
                            <input class="form-check-input category-field cat-show" type="checkbox" ${category.show_image ? 'checked' : ''} data-name="${safeCatName}">
                            <label class="form-check-label">Afbeelding tonen</label>
                        </div>
                        <div class="row g-2">
                            <div class="col"><input type="text" class="form-control form-control-sm category-field cat-software" value="${category.software || ''}" data-name="${safeCatName}" placeholder="Software"></div>
                            <div class="col"><input type="text" class="form-control form-control-sm category-field cat-version" value="${category.version || ''}" data-name="${safeCatName}" placeholder="Versie"></div>
                        </div>
                    </div>
                </div>
            </div>`;
    }

    _renderPlugin(plugin, categories) {
        const categoryOptions = categories.map(cat => `<option value="${cat.name}" ${plugin.category === cat.name ? 'selected' : ''}>${cat.name}</option>`).join('');
        return `
            <div class="col-md-6 mb-3">
                <div class="card">
                    <div class="card-body">
                        <div class="d-flex align-items-center mb-2">
                            <img src="${plugin.icon || '/images/plugin-placeholder.png'}" style="width: 40px; height: 40px; margin-right: 10px;" alt="icon">
                            <div style="flex-grow: 1;">
                                <input type="text" class="form-control form-control-sm mb-1 plugin-field plugin-title" value="${plugin.title}" data-url="${plugin.url}">
                                <input type="text" class="form-control form-control-sm mb-1 plugin-field plugin-author" value="${plugin.author || 'Onbekend'}" data-url="${plugin.url}">
                                <select class="form-select form-select-sm plugin-field plugin-category" data-url="${plugin.url}">
                                    <option value="">Geen categorie</option>${categoryOptions}
                                </select>
                            </div>
                        </div>
                        <button class="btn btn-danger btn-sm delete-plugin-btn" data-url="${plugin.url}" data-title="${plugin.title}"><i class="fas fa-trash me-1"></i>Verwijderen</button>
                    </div>
                </div>
            </div>`;
    }

    _getRoleBadgeClass(role) {
        if (role === 'admin') return 'bg-danger';
        if (role === 'co-admin') return 'bg-warning';
        return 'bg-secondary';
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const adminPage = new AdminPage();
    adminPage.init();
});
