import ApiAdmin from './api-admin.js';
import { showAlertModal, showConfirmModal } from './modals.js';

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
        this.checkUpdateBtn = document.getElementById('checkUpdateBtn');
        this.applyUpdateBtn = document.getElementById('applyUpdateBtn');
        this.rollbackUpdateBtn = document.getElementById('rollbackUpdateBtn');
        this.syncToHostToggle = document.getElementById('syncToHostToggle');
        this.updateStatusBadge = document.getElementById('updateStatusBadge');
        this.updateDetails = document.getElementById('updateDetails');
        this.updateAlert = document.getElementById('updateAlert');
        this.softwareUpdateSection = document.getElementById('softwareUpdateSection');

        this.rollbackSection = document.getElementById('rollbackSection');
        this.rollbackCommitSelect = document.getElementById('rollbackCommitSelect');
        this.selectedCommitDetails = document.getElementById('selectedCommitDetails');
        this.rollbackSelectedSha = document.getElementById('rollbackSelectedSha');
        this.rollbackSelectedAuthor = document.getElementById('rollbackSelectedAuthor');
        this.rollbackSelectedDate = document.getElementById('rollbackSelectedDate');
        this.rollbackSelectedMsg = document.getElementById('rollbackSelectedMsg');
        this.rollbackSyncToHostToggle = document.getElementById('rollbackSyncToHostToggle');
        this.rollbackAlert = document.getElementById('rollbackAlert');

        this.commitHistory = [];
        this.currentRole = null;
        this.pluginsCache = [];
        this.categoriesCache = [];
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
        if (this.newCategoryName) {
            this.newCategoryName.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this._handleAddCategory();
                }
            });
        }
        if (this.checkUpdateBtn) {
            this.checkUpdateBtn.addEventListener('click', () => this._handleCheckUpdate());
        }
        if (this.applyUpdateBtn) {
            this.applyUpdateBtn.addEventListener('click', () => this._handleApplyUpdate());
        }
        if (this.rollbackUpdateBtn) {
            this.rollbackUpdateBtn.addEventListener('click', () => this._handleRollbackUpdate());
        }
        if (this.rollbackCommitSelect) {
            this.rollbackCommitSelect.addEventListener('change', () => this._handleRollbackSelectChange());
        }

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

        document.body.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.target.matches('.category-field') || e.target.matches('.plugin-field'))) {
                e.preventDefault();
                e.target.blur();
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
            await showAlertModal('Fout bij opslaan instellingen', 'Fout', 'fas fa-exclamation-triangle text-danger');
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
            await showAlertModal(`Fout bij toevoegen categorie: ${error.message}`, 'Fout', 'fas fa-exclamation-triangle text-danger');
        }
    }

    async _handleRoleChange(selectElement) {
        const username = selectElement.dataset.username;
        const newRole = selectElement.value;
        try {
            await ApiAdmin.updateUserRole(username, newRole);
            this._loadUsers();
        } catch (error) {
            await showAlertModal('Fout bij wijzigen rol', 'Fout', 'fas fa-exclamation-triangle text-danger');
        }
    }

    async _handleDeleteUser(button) {
        const username = button.dataset.username;
        const confirmed = await showConfirmModal({
            title: 'Gebruiker Verwijderen',
            message: `Weet je zeker dat je gebruiker "<strong>${username}</strong>" wilt verwijderen?`,
            confirmText: 'Verwijderen',
            confirmClass: 'btn-danger',
            iconClass: 'fas fa-user-times text-danger'
        });

        if (confirmed) {
            try {
                await ApiAdmin.deleteUser(username);
                this._loadUsers();
            } catch (error) {
                await showAlertModal('Fout bij verwijderen gebruiker', 'Fout', 'fas fa-exclamation-triangle text-danger');
            }
        }
    }

    async _handleCategoryUpdate(inputElement) {
        const oldName = inputElement.dataset.name;
        const card = inputElement.closest('.card-body');
        const newName = card.querySelector(`.cat-name`).value.trim();
        if (!newName) {
            await showAlertModal("Categorie naam mag niet leeg zijn.", "Waarschuwing", "fas fa-exclamation-circle text-warning");
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
            await showAlertModal(`Fout bij bijwerken categorie: ${error.message}`, "Fout", "fas fa-exclamation-triangle text-danger");
            this._loadCategories();
        }
    }

    async _handleDeleteCategory(button) {
        const name = button.dataset.name;
        const categoryPlugins = (this.pluginsCache || []).filter(p => p.category === name || (Array.isArray(p.categories) && p.categories.includes(name)));
        const pluginCount = categoryPlugins.length;

        let message = '';
        if (pluginCount > 0) {
            message = `<div class="alert alert-warning mb-3"><i class="fas fa-exclamation-triangle me-2"></i>Deze categorie bevat <strong>${pluginCount} plugin(s)</strong>!</div>Weet je zeker dat je de categorie "<strong>${name}</strong>" wilt verwijderen?<br><br><span class="text-danger"><strong>Belangrijk:</strong> De categorie inclusief alle ${pluginCount} bijbehorende plugins/inhoud worden definitief verwijderd.</span>`;
        } else {
            message = `Weet je zeker dat je de categorie "<strong>${name}</strong>" wilt verwijderen?`;
        }

        const confirmed = await showConfirmModal({
            title: 'Categorie Verwijderen',
            message: message,
            confirmText: pluginCount > 0 ? 'Verwijderen inclusief plugins' : 'Verwijderen',
            confirmClass: 'btn-danger',
            iconClass: 'fas fa-trash-alt text-danger'
        });

        if (confirmed) {
            try {
                const res = await ApiAdmin.deleteCategory(name);
                this._loadCategories();
                this._loadPlugins();
                if (res && res.deleted_plugins_count !== undefined) {
                    await showAlertModal(`Categorie "${name}" ${res.deleted_plugins_count > 0 ? `en ${res.deleted_plugins_count} bijbehorende plugin(s)` : ''} succesvol verwijderd.`, 'Succes', 'fas fa-check-circle text-success');
                }
            } catch (error) {
                await showAlertModal(`Fout bij verwijderen categorie: ${error.message}`, 'Fout', 'fas fa-exclamation-triangle text-danger');
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
            await showAlertModal(`Fout bij bijwerken plugin: ${error.message}`, 'Fout', 'fas fa-exclamation-triangle text-danger');
            this._loadPlugins();
        }
    }

    async _handleDeletePlugin(button) {
        const url = button.dataset.url;
        const title = button.dataset.title;
        const confirmed = await showConfirmModal({
            title: 'Plugin Verwijderen',
            message: `Weet je zeker dat je plugin "<strong>${title}</strong>" wilt verwijderen?`,
            confirmText: 'Verwijderen',
            confirmClass: 'btn-danger',
            iconClass: 'fas fa-trash-alt text-danger'
        });

        if (confirmed) {
            try {
                await ApiAdmin.deletePlugin(url);
                this._loadPlugins();
            } catch (error) {
                await showAlertModal('Fout bij verwijderen plugin', 'Fout', 'fas fa-exclamation-triangle text-danger');
            }
        }
    }

    async _handleCheckUpdate() {
        if (!this.checkUpdateBtn) return;
        this.checkUpdateBtn.disabled = true;
        this.checkUpdateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Controleren...';
        this.updateAlert.style.display = 'none';

        try {
            const data = await ApiAdmin.checkUpdate();
            this.updateDetails.style.display = 'block';
            document.getElementById('currentCommit').textContent = data.current_commit || '-';
            document.getElementById('latestCommit').textContent = data.latest_commit || '-';
            document.getElementById('commitMessage').textContent = data.commit_message || '-';
            document.getElementById('commitDate').textContent = data.commit_date ? new Date(data.commit_date).toLocaleString('nl-NL') : '-';

            if (data.update_available) {
                this.updateStatusBadge.className = 'badge bg-warning text-dark';
                this.updateStatusBadge.textContent = 'Update beschikbaar!';
                if (this.currentRole === 'admin') {
                    this.applyUpdateBtn.style.display = 'inline-block';
                } else {
                    this.applyUpdateBtn.style.display = 'none';
                }
            } else {
                this.updateStatusBadge.className = 'badge bg-success';
                this.updateStatusBadge.textContent = 'Up-to-date';
                this.applyUpdateBtn.style.display = 'none';
            }

            this._populateRollbackHistory(data);
        } catch (error) {
            this.updateStatusBadge.className = 'badge bg-danger';
            this.updateStatusBadge.textContent = 'Fout bij controleren';
            this.updateAlert.className = 'alert alert-danger mt-3 mb-0';
            this.updateAlert.textContent = `Fout bij controleren van updates: ${error.message}`;
            this.updateAlert.style.display = 'block';
        } finally {
            this.checkUpdateBtn.disabled = false;
            this.checkUpdateBtn.innerHTML = '<i class="fas fa-search me-1"></i>Check op Updates';
        }
    }

    _populateRollbackHistory(data) {
        if (!this.rollbackCommitSelect) return;
        this.commitHistory = data.history || [];
        this.rollbackCommitSelect.innerHTML = '';

        if (this.commitHistory.length === 0) {
            const opt = document.createElement('option');
            opt.value = '';
            opt.textContent = 'Geen commit historie beschikbaar';
            this.rollbackCommitSelect.appendChild(opt);
            if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.disabled = true;
            return;
        }

        const defaultTargetSha = data.full_previous_commit || '';
        let defaultSelectedIndex = -1;

        this.commitHistory.forEach((item, index) => {
            const opt = document.createElement('option');
            opt.value = item.sha;
            let label = `[${item.short_sha}] ${item.message} (${item.author}, ${new Date(item.date).toLocaleDateString('nl-NL')})`;
            if (item.is_current) {
                label += ' - (HUIDIGE VERSIE)';
            } else if (item.sha === defaultTargetSha) {
                label += ' - (VORIGE RELEASE)';
            }
            opt.textContent = label;
            this.rollbackCommitSelect.appendChild(opt);

            if (item.sha === defaultTargetSha && defaultSelectedIndex === -1) {
                defaultSelectedIndex = index;
            }
        });

        // If previous commit SHA not matched directly, select second item in history (if current is first)
        if (defaultSelectedIndex === -1 && this.commitHistory.length > 1) {
            if (this.commitHistory[0].is_current) {
                defaultSelectedIndex = 1;
            } else {
                defaultSelectedIndex = 0;
            }
        } else if (defaultSelectedIndex === -1) {
            defaultSelectedIndex = 0;
        }

        this.rollbackCommitSelect.selectedIndex = defaultSelectedIndex;
        this._handleRollbackSelectChange();
    }

    _handleRollbackSelectChange() {
        if (!this.rollbackCommitSelect) return;
        const selectedSha = this.rollbackCommitSelect.value;
        const item = this.commitHistory.find(c => c.sha === selectedSha);

        if (item) {
            this.selectedCommitDetails.style.display = 'block';
            this.rollbackSelectedSha.textContent = item.sha;
            this.rollbackSelectedAuthor.textContent = item.author || '-';
            this.rollbackSelectedDate.textContent = item.date ? new Date(item.date).toLocaleString('nl-NL') : '-';
            this.rollbackSelectedMsg.textContent = item.message || '-';

            if (this.rollbackUpdateBtn) {
                this.rollbackUpdateBtn.disabled = (this.currentRole !== 'admin');
            }
        } else {
            this.selectedCommitDetails.style.display = 'none';
            if (this.rollbackUpdateBtn) {
                this.rollbackUpdateBtn.disabled = true;
            }
        }
    }

    async _handleApplyUpdate() {
        const confirmed = await showConfirmModal({
            title: 'Software Update Toepassen',
            message: 'Weet je zeker dat je de update wilt downloaden en toepassen? De server herstart automatisch na het updaten.',
            confirmText: 'Update Toepassen',
            confirmClass: 'btn-success',
            iconClass: 'fas fa-download text-success'
        });

        if (!confirmed) {
            return;
        }

        const syncToHost = this.syncToHostToggle ? this.syncToHostToggle.checked : false;

        this.applyUpdateBtn.disabled = true;
        this.checkUpdateBtn.disabled = true;
        if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.disabled = true;
        this.applyUpdateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Updaten...';

        try {
            const data = await ApiAdmin.applyUpdate(syncToHost);
            this.updateAlert.className = 'alert alert-success mt-3 mb-0';
            this.updateAlert.textContent = `${data.message || 'Update succesvol toegepast!'} Pagina wordt over 5 seconden herladen...`;
            this.updateAlert.style.display = 'block';
            this.applyUpdateBtn.style.display = 'none';

            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } catch (error) {
            this.updateAlert.className = 'alert alert-danger mt-3 mb-0';
            this.updateAlert.textContent = `Fout bij toepassen van update: ${error.message}`;
            this.updateAlert.style.display = 'block';
            this.applyUpdateBtn.disabled = false;
            this.checkUpdateBtn.disabled = false;
            if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.disabled = false;
            this.applyUpdateBtn.innerHTML = '<i class="fas fa-download me-1"></i>Update Toepassen';
        }
    }

    async _handleRollbackUpdate() {
        const selectedCommit = this.rollbackCommitSelect ? this.rollbackCommitSelect.value : '';
        if (!selectedCommit) {
            await showAlertModal('Selecteer eerst een commit om naar terug te rollen.', 'Waarschuwing', 'fas fa-exclamation-circle text-warning');
            return;
        }

        const confirmed = await showConfirmModal({
            title: 'Versie Terugrollen',
            message: `Weet je zeker dat je wilt terugrollen naar commit <code>${selectedCommit.slice(0, 7)}</code>? De server herstart automatisch na het terugrollen.`,
            confirmText: 'Terugrollen',
            confirmClass: 'btn-warning',
            iconClass: 'fas fa-undo text-warning'
        });

        if (!confirmed) {
            return;
        }

        const syncToHost = this.rollbackSyncToHostToggle ? this.rollbackSyncToHostToggle.checked : false;

        if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.disabled = true;
        if (this.checkUpdateBtn) this.checkUpdateBtn.disabled = true;
        if (this.applyUpdateBtn) this.applyUpdateBtn.disabled = true;
        if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Terugrollen...';
        this.rollbackAlert.style.display = 'none';

        try {
            const data = await ApiAdmin.rollbackUpdate(selectedCommit, syncToHost);
            this.rollbackAlert.className = 'alert alert-success mt-3 mb-0';
            this.rollbackAlert.textContent = `${data.message || 'Succesvol teruggerold!'} Pagina wordt over 5 seconden herladen...`;
            this.rollbackAlert.style.display = 'block';

            setTimeout(() => {
                window.location.reload();
            }, 5000);
        } catch (error) {
            this.rollbackAlert.className = 'alert alert-danger mt-3 mb-0';
            this.rollbackAlert.textContent = `Fout bij terugrollen van update: ${error.message}`;
            this.rollbackAlert.style.display = 'block';
            if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.disabled = false;
            if (this.checkUpdateBtn) this.checkUpdateBtn.disabled = false;
            if (this.applyUpdateBtn) this.applyUpdateBtn.disabled = false;
            if (this.rollbackUpdateBtn) this.rollbackUpdateBtn.innerHTML = '<i class="fas fa-undo me-1"></i>Geselecteerde Versie Terugrollen';
        }
    }

    _showAdminPanel() {
        this.loginForm.style.display = 'none';
        this.adminPanel.style.display = 'block';
        document.getElementById('adminRole').textContent = this.currentRole.toUpperCase();

        if (this.softwareUpdateSection) {
            this.softwareUpdateSection.style.display = (this.currentRole === 'admin') ? 'block' : 'none';
        }
        if (this.rollbackSection) {
            this.rollbackSection.style.display = (this.currentRole === 'admin') ? 'block' : 'none';
        }

        this._loadAllData();
        if (this.currentRole === 'admin') {
            this._handleCheckUpdate();
        }
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

    async _loadUsers(page = 1) {
        const res = await ApiAdmin.getUsers({ page, per_page: 12 });
        const users = Array.isArray(res) ? res : (res.users || []);
        const total = Array.isArray(res) ? users.length : (res.total || 0);
        const userBadge = document.getElementById('userCountBadge');
        if (userBadge) {
            userBadge.innerHTML = `<i class="fas fa-users me-1"></i>Totaal: ${total} ${total === 1 ? 'gebruiker' : 'gebruikers'}`;
        }
        this.usersGrid.innerHTML = users.map(user => this._renderUser(user)).join('');
    }

    async _loadCategories() {
        const categories = await ApiAdmin.getCategories();
        this.categoriesCache = categories || [];
        const catBadge = document.getElementById('categoryCountBadge');
        if (catBadge) {
            catBadge.innerHTML = `<i class="fas fa-tags me-1"></i>Totaal: ${categories.length} ${categories.length === 1 ? 'categorie' : 'categorieën'}`;
        }
        this.categoriesGrid.innerHTML = categories.map(cat => this._renderCategory(cat)).join('');
    }

    async _loadPlugins(page = 1) {
        const [resPlugins, categories] = await Promise.all([
            ApiAdmin.getPlugins({ page, per_page: 20 }),
            ApiAdmin.getCategories()
        ]);
        const plugins = Array.isArray(resPlugins) ? resPlugins : (resPlugins.plugins || []);
        const total = Array.isArray(resPlugins) ? plugins.length : (resPlugins.total || 0);
        this.pluginsCache = plugins || [];
        this.categoriesCache = categories || [];
        const pluginBadge = document.getElementById('pluginCountBadge');
        if (pluginBadge) {
            pluginBadge.innerHTML = `<i class="fas fa-puzzle-piece me-1"></i>Totaal: ${total} ${total === 1 ? 'plugin' : 'plugins'}`;
        }
        this.categoriesGrid.innerHTML = categories.map(cat => this._renderCategory(cat)).join('');
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
        const catPluginsCount = (this.pluginsCache || []).filter(p => p.category === category.name || (Array.isArray(p.categories) && p.categories.includes(category.name))).length;
        return `
            <div class="col-lg-6 mb-4">
                <div class="card h-100">
                    <div class="card-body" data-name="${safeCatName}">
                        <div class="d-flex justify-content-between align-items-center mb-3">
                            <div class="d-flex align-items-center gap-2">
                                <h5 class="card-title mb-0">${category.name}</h5>
                                <span class="badge bg-info text-dark" title="Aantal plugins in deze categorie"><i class="fas fa-puzzle-piece me-1"></i>${catPluginsCount} ${catPluginsCount === 1 ? 'plugin' : 'plugins'}</span>
                            </div>
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
                            <img src="${plugin.icon || '/images/plugin-placeholder.png'}" style="width: 40px; height: 40px; margin-right: 10px;" alt="icon" loading="lazy">
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
