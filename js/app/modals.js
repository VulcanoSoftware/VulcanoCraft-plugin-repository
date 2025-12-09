import API from './api.js';
import UI from './ui.js';

class Modals {
    constructor() {
        this.addModalEl = document.getElementById('addPluginModal');
        this.deleteModalEl = document.getElementById('deleteConfirmModal');
        this.addModal = new bootstrap.Modal(this.addModalEl);
        this.deleteModal = new bootstrap.Modal(this.deleteModalEl);

        this.pluginUrlInput = document.getElementById('pluginUrl');
        this.fetchButton = document.getElementById('fetchButton');
        this.confirmYes = document.getElementById('confirmYes');
        this.confirmNo = document.getElementById('confirmNo');
        this.confirmDeleteButton = document.getElementById('confirmDeleteButton');
        this.errorMessage = document.getElementById('errorMessage');

        this.steps = {
            1: document.getElementById('step1'),
            2: document.getElementById('step2'),
            3: document.getElementById('step3'),
        };

        this.cachedPluginData = null;
        this.currentDeleteUrl = null;
        this.addSuccess = false;

        this._addEventListeners();
    }

    _addEventListeners() {
        this.fetchButton.addEventListener('click', () => this.handleFetch());
        this.confirmYes.addEventListener('click', () => this.handleAddConfirm());
        this.confirmNo.addEventListener('click', () => this.handleAddCancel());
        this.confirmDeleteButton.addEventListener('click', () => this.handleDeleteConfirm());

        this.deleteModalEl.addEventListener('shown.bs.modal', () => this.startDeleteAnimation());
    }

    async handleFetch() {
        const url = this.pluginUrlInput.value.trim();
        if (!url) {
            this.showError('Vul een URL in');
            return;
        }

        this.showStep(2);
        this.hideError();

        try {
            const plugin = await API.fetchPlugin(url);
            this.cachedPluginData = plugin;
            this.updateAddModalPreview(plugin);
            this.showStep(3);
            this._toggleAddModalButtons(false);
            this._setModalStatic(true);
        } catch (error) {
            this.showError(`Fout bij ophalen plugin: ${error.message}`);
            this.showStep(1);
        }
    }

    async handleAddConfirm() {
        try {
            const authData = await API.getAuthStatus();
            if (!authData.logged_in) {
                this.showError('Je moet ingelogd zijn om plugins toe te voegen.');
                return;
            }

            this._setConfirmYesLoading(true);

            const activeCategory = document.querySelector('#categorySidebar .category-item.active')?.dataset.category;
            if (activeCategory) {
                this.cachedPluginData.category = activeCategory;
            }

            const data = await API.addPlugin(this.cachedPluginData);
            if (data.success) {
                this.addSuccess = true;
                UI.showSuccessMessage('Plugin succesvol toegevoegd!');
                this.addModal.hide();
                // The main controller will listen for the modal close and reload plugins.
            } else {
                this.showError(`Fout bij toevoegen: ${data.error}`);
            }
        } catch (error) {
            this.showError(`Fout bij toevoegen: ${error.message}`);
        } finally {
            this._setConfirmYesLoading(false);
        }
    }

    handleAddCancel() {
        this.showStep(1);
        this.pluginUrlInput.value = '';
        this.pluginUrlInput.focus();
        this._toggleAddModalButtons(true);
        this._setModalStatic(false);
    }

    async handleDeleteConfirm() {
        const pluginTitle = document.getElementById('pluginToDeleteTitle').textContent;
        try {
            const data = await API.deletePlugin(this.currentDeleteUrl);
            if (data.success) {
                UI.showSuccessMessage(`Plugin "${pluginTitle}" succesvol verwijderd!`);
                this.deleteModal.hide();
            } else {
                this.showError(`Fout bij verwijderen: ${data.error}`);
            }
        } catch (error) {
            this.showError(`Fout bij verwijderen: ${error.message}`);
        }
    }

    showDeleteModal(url, title) {
        document.getElementById('pluginToDeleteTitle').textContent = title;
        this.currentDeleteUrl = url;
        this.deleteModal.show();
    }

    updateAddModalPreview(plugin) {
        document.getElementById('previewTitle').textContent = plugin.title || 'Geen titel';
        document.getElementById('previewDescription').textContent = plugin.description || 'Geen beschrijving beschikbaar';
        document.getElementById('previewAuthor').textContent = plugin.author || 'Onbekend';
        document.getElementById('previewIcon').src = plugin.icon || 'images/plugin-placeholder.png';

        const versionsContainer = document.getElementById('previewVersions');
        versionsContainer.innerHTML = (plugin.versions)
            ? plugin.versions.split(' ').map((v, i) => `<span class="version-badge" style="animation-delay: ${i*100}ms">${v}</span>`).join('')
            : '<span class="badge bg-secondary">Geen versies</span>';
    }

    resetAddModal() {
        this.showStep(1);
        this.hideError();
        this.pluginUrlInput.value = '';
        this.cachedPluginData = null;
        this.addSuccess = false;
        this._toggleAddModalButtons(true);
        this._setConfirmYesLoading(false);
        this._setModalStatic(false);
    }

    startDeleteAnimation() {
        const deleteIcon = this.deleteModalEl.querySelector('.delete-modal-icon');
        if (deleteIcon) {
            deleteIcon.style.animation = 'none';
            void deleteIcon.offsetWidth; // Trigger reflow
            deleteIcon.style.animation = 'wiggle 1.2s ease-in-out';
        }
    }

    showStep(stepNum) {
        for (const key in this.steps) {
            this.steps[key].style.display = (key == stepNum) ? 'block' : 'none';
        }
    }

    showError(message) {
        this.errorMessage.querySelector('span').textContent = message;
        this.errorMessage.style.display = 'flex';
    }

    hideError() {
        this.errorMessage.style.display = 'none';
    }

    _toggleAddModalButtons(showMain) {
        this.fetchButton.style.display = showMain ? 'inline-block' : 'none';
        this.addModalEl.querySelector('.modal-footer .btn-secondary').style.display = showMain ? 'inline-block' : 'none';
    }

    _setConfirmYesLoading(isLoading) {
        const btn = this.confirmYes;
        if (isLoading) {
            btn.innerHTML = '<img src="images/loading-icon.gif" class="loading-icon me-2" alt="Laden"> Toevoegen...';
            btn.disabled = true;
        } else {
            btn.innerHTML = '<img src="images/confirm-icon.png" class="btn-icon" alt="Ja"> Ja';
            btn.disabled = false;
        }
    }

    _setModalStatic(isStatic) {
        this.addModalEl.dataset.bsBackdrop = isStatic ? 'static' : 'true';
        this.addModalEl.dataset.bsKeyboard = isStatic ? 'false' : 'true';
    }
}

export default new Modals();
