import API from './api.js';
import UI from './ui.js';

class Modals {
    constructor() {
        this.addModalEl = document.getElementById('addPluginModal');
        this.deleteModalEl = document.getElementById('deleteConfirmModal');
        this.addModal = new bootstrap.Modal(this.addModalEl);
        this.deleteModal = new bootstrap.Modal(this.deleteModalEl);

        this.pluginUrlInput = document.getElementById('pluginUrl');
        this.bulkPluginUrlsInput = document.getElementById('bulkPluginUrls');
        this.fetchButton = document.getElementById('fetchButton');
        this.confirmYes = document.getElementById('confirmYes');
        this.confirmNo = document.getElementById('confirmNo');
        this.confirmDeleteButton = document.getElementById('confirmDeleteButton');
        this.errorMessage = document.getElementById('errorMessage');
        this.selectAllBtn = document.getElementById('selectAllBtn');
        this.deselectAllBtn = document.getElementById('deselectAllBtn');

        this.steps = {
            1: document.getElementById('step1'),
            2: document.getElementById('step2'),
            3: document.getElementById('step3'),
        };

        this.cachedPluginData = null;
        this.cachedBulkPlugins = []; // [{ url, plugin, status, error, selected }]
        this.isBulkMode = false;
        this.currentDeleteUrl = null;
        this.addSuccess = false;

        this._addEventListeners();
    }

    _addEventListeners() {
        this.fetchButton.addEventListener('click', () => this.handleFetch());
        this.confirmYes.addEventListener('click', () => this.handleAddConfirm());
        this.confirmNo.addEventListener('click', () => this.handleAddCancel());
        this.confirmDeleteButton.addEventListener('click', () => this.handleDeleteConfirm());

        if (this.selectAllBtn) {
            this.selectAllBtn.addEventListener('click', () => this._toggleAllBulkCheckboxes(true));
        }
        if (this.deselectAllBtn) {
            this.deselectAllBtn.addEventListener('click', () => this._toggleAllBulkCheckboxes(false));
        }

        if (this.pluginUrlInput) {
            this.pluginUrlInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    this.handleFetch();
                }
            });
        }

        if (this.bulkPluginUrlsInput) {
            this.bulkPluginUrlsInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                    e.preventDefault();
                    this.handleFetch();
                }
            });
        }

        // Delegate bulk item checkbox changes
        const bulkPreviewList = document.getElementById('bulkPreviewList');
        if (bulkPreviewList) {
            bulkPreviewList.addEventListener('change', (e) => {
                if (e.target.matches('.bulk-item-checkbox')) {
                    const idx = parseInt(e.target.dataset.index, 10);
                    if (!isNaN(idx) && this.cachedBulkPlugins[idx]) {
                        this.cachedBulkPlugins[idx].selected = e.target.checked;
                        this._updateBulkSelectedCount();
                    }
                }
            });
        }

        this.deleteModalEl.addEventListener('shown.bs.modal', () => this.startDeleteAnimation());
    }

    async handleFetch() {
        const activeTab = document.querySelector('#addPluginTabs .nav-link.active');
        this.isBulkMode = activeTab && activeTab.id === 'bulkUrlTab';

        if (!this.isBulkMode) {
            await this._handleSingleFetch();
        } else {
            await this._handleBulkFetch();
        }
    }

    async _handleSingleFetch() {
        const url = this.pluginUrlInput.value.trim();
        if (!url) {
            this.showError('Vul een URL in');
            return;
        }

        this.showStep(2);
        this.hideError();

        const fetchProgressText = document.getElementById('fetchProgressText');
        const progressBarContainer = document.getElementById('fetchProgressBarContainer');
        if (fetchProgressText) fetchProgressText.textContent = 'Plugin informatie wordt opgehaald...';
        if (progressBarContainer) progressBarContainer.style.display = 'none';

        try {
            const plugin = await API.fetchPlugin(url);
            this.cachedPluginData = plugin;
            this.updateAddModalPreview(plugin);

            document.getElementById('singlePreviewContainer').style.display = 'block';
            document.getElementById('bulkPreviewContainer').style.display = 'none';
            document.getElementById('selectedCountBadge').style.display = 'none';
            document.getElementById('confirmationQuestionText').textContent = 'Is dit de correcte plugin?';

            this.showStep(3);
            this._toggleAddModalButtons(false);
            this._setModalStatic(true);
        } catch (error) {
            this.showError(`Fout bij ophalen plugin: ${error.message}`);
            this.showStep(1);
        }
    }

    async _handleBulkFetch() {
        const rawText = this.bulkPluginUrlsInput.value.trim();
        if (!rawText) {
            this.showError('Vul ten minste één URL in');
            return;
        }

        const urls = Array.from(new Set(
            rawText.split(/[\n\s]+/).map(u => u.trim()).filter(u => u.length > 0)
        ));

        if (urls.length === 0) {
            this.showError('Geen geldige URL\'s gevonden');
            return;
        }

        this.showStep(2);
        this.hideError();

        const fetchProgressText = document.getElementById('fetchProgressText');
        const progressBarContainer = document.getElementById('fetchProgressBarContainer');
        const progressBar = document.getElementById('fetchProgressBar');

        if (progressBarContainer) progressBarContainer.style.display = 'block';
        if (progressBar) progressBar.style.width = '0%';

        this.cachedBulkPlugins = [];

        for (let i = 0; i < urls.length; i++) {
            const url = urls[i];
            const currentNum = i + 1;
            const percent = Math.round((currentNum / urls.length) * 100);

            if (fetchProgressText) {
                fetchProgressText.textContent = `Plugin ${currentNum} van ${urls.length} ophalen... (${url})`;
            }
            if (progressBar) {
                progressBar.style.width = `${percent}%`;
            }

            try {
                const plugin = await API.fetchPlugin(url);
                this.cachedBulkPlugins.push({
                    url,
                    plugin,
                    status: 'success',
                    selected: true
                });
            } catch (err) {
                this.cachedBulkPlugins.push({
                    url,
                    plugin: null,
                    status: 'error',
                    error: err.message,
                    selected: false
                });
            }
        }

        this._renderBulkPreviewList();

        document.getElementById('singlePreviewContainer').style.display = 'none';
        document.getElementById('bulkPreviewContainer').style.display = 'block';
        document.getElementById('selectedCountBadge').style.display = 'inline-block';
        document.getElementById('confirmationQuestionText').textContent = 'Wilt u de geselecteerde plugins toevoegen?';

        this.showStep(3);
        this._toggleAddModalButtons(false);
        this._setModalStatic(true);
    }

    _renderBulkPreviewList() {
        const bulkListEl = document.getElementById('bulkPreviewList');
        if (!bulkListEl) return;

        let html = '';
        this.cachedBulkPlugins.forEach((item, index) => {
            if (item.status === 'success') {
                const plugin = item.plugin;
                const versionsStr = plugin.versions ? plugin.versions.split(' ').slice(0, 3).join(', ') : 'Geen';
                const firstLetter = (plugin.title || 'P')[0].toUpperCase();
                const iconHtml = plugin.icon
                    ? `<img src="${plugin.icon}" class="bulk-preview-icon me-2" alt="icon" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="bulk-preview-icon-letter me-2" style="display:none;">${firstLetter}</div>`
                    : `<div class="bulk-preview-icon-letter me-2">${firstLetter}</div>`;

                html += `
                    <div class="bulk-review-item">
                        <div class="d-flex align-items-center">
                            <div class="form-check me-3">
                                <input class="form-check-input bulk-item-checkbox" type="checkbox" data-index="${index}" id="bulkCheck_${index}" ${item.selected ? 'checked' : ''}>
                            </div>
                            ${iconHtml}
                            <div class="flex-grow-1 min-w-0">
                                <div class="d-flex justify-content-between align-items-center">
                                    <h6 class="mb-0 text-truncate" title="${plugin.title || 'Geen titel'}">${plugin.title || 'Geen titel'}</h6>
                                    <small class="text-muted ms-2">${plugin.author || 'Onbekend'}</small>
                                </div>
                                <div class="small text-muted text-truncate">${plugin.description || 'Geen beschrijving'}</div>
                                <div class="small mt-1">
                                    <span class="badge bg-info text-dark me-1">v: ${versionsStr}</span>
                                    <span class="badge bg-secondary">${item.url}</span>
                                </div>
                            </div>
                        </div>
                    </div>`;
            } else {
                html += `
                    <div class="bulk-review-item border-danger">
                        <div class="d-flex align-items-center">
                            <div class="form-check me-3">
                                <input class="form-check-input bulk-item-checkbox" type="checkbox" data-index="${index}" id="bulkCheck_${index}" disabled>
                            </div>
                            <div class="flex-grow-1">
                                <h6 class="mb-0 text-danger"><i class="fas fa-exclamation-circle me-1"></i> Fout bij ophalen</h6>
                                <div class="small text-muted">${item.url}</div>
                                <div class="small text-danger">${item.error}</div>
                            </div>
                        </div>
                    </div>`;
            }
        });

        bulkListEl.innerHTML = html;
        this._updateBulkSelectedCount();
    }

    _toggleAllBulkCheckboxes(selectAll) {
        this.cachedBulkPlugins.forEach(item => {
            if (item.status === 'success') {
                item.selected = selectAll;
            }
        });
        const checkboxes = document.querySelectorAll('.bulk-item-checkbox:not(:disabled)');
        checkboxes.forEach(cb => cb.checked = selectAll);
        this._updateBulkSelectedCount();
    }

    _updateBulkSelectedCount() {
        const selectedCount = this.cachedBulkPlugins.filter(i => i.selected && i.status === 'success').length;
        const totalSuccess = this.cachedBulkPlugins.filter(i => i.status === 'success').length;
        const totalTotal = this.cachedBulkPlugins.length;

        const countBadge = document.getElementById('selectedCountBadge');
        if (countBadge) {
            countBadge.textContent = `${selectedCount} geselecteerd`;
        }

        const summaryText = document.getElementById('bulkSummaryText');
        if (summaryText) {
            summaryText.textContent = `${selectedCount} van de ${totalSuccess} succesvol opgevraagde plugins geselecteerd (${totalTotal} totaal)`;
        }

        if (this.confirmYes) {
            this.confirmYes.disabled = (selectedCount === 0 && this.isBulkMode);
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

            if (!this.isBulkMode) {
                await this._addSinglePlugin(activeCategory);
            } else {
                await this._addBulkPlugins(activeCategory);
            }
        } catch (error) {
            this.showError(`Fout bij toevoegen: ${error.message}`);
        } finally {
            this._setConfirmYesLoading(false);
        }
    }

    async _addSinglePlugin(activeCategory) {
        if (activeCategory) {
            this.cachedPluginData.category = activeCategory;
        }
        const data = await API.addPlugin(this.cachedPluginData);
        if (data.success) {
            this.addSuccess = true;
            UI.showSuccessMessage('Plugin succesvol toegevoegd!');
            this.addModal.hide();
        } else {
            this.showError(`Fout bij toevoegen: ${data.error}`);
        }
    }

    async _addBulkPlugins(activeCategory) {
        const selectedItems = this.cachedBulkPlugins.filter(i => i.selected && i.status === 'success');
        if (selectedItems.length === 0) {
            this.showError('Selecteer ten minste één plugin om toe te voegen.');
            return;
        }

        let addedCount = 0;
        let failCount = 0;

        for (const item of selectedItems) {
            if (activeCategory) {
                item.plugin.category = activeCategory;
            }
            try {
                const data = await API.addPlugin(item.plugin);
                if (data.success) {
                    addedCount++;
                } else {
                    failCount++;
                }
            } catch (err) {
                failCount++;
            }
        }

        if (addedCount > 0) {
            this.addSuccess = true;
            UI.showSuccessMessage(`${addedCount} plugin(s) succesvol toegevoegd!${failCount > 0 ? ` (${failCount} mislukt)` : ''}`);
            this.addModal.hide();
        } else {
            this.showError(`Fout bij toevoegen van plugins (${failCount} mislukt)`);
        }
    }

    handleAddCancel() {
        this.showStep(1);
        if (this.pluginUrlInput) this.pluginUrlInput.value = '';
        if (this.bulkPluginUrlsInput) this.bulkPluginUrlsInput.value = '';
        this.cachedPluginData = null;
        this.cachedBulkPlugins = [];
        this._toggleAddModalButtons(true);
        this._setModalStatic(false);
    }

    async handleDeleteConfirm() {
        const pluginTitle = document.getElementById('pluginToDeleteTitle').textContent;
        const categoryContext = this.currentDeleteCategory || '';
        try {
            const data = await API.deletePlugin(this.currentDeleteUrl, categoryContext || undefined);
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

    showDeleteModal(url, title, categoryContext = '') {
        document.getElementById('pluginToDeleteTitle').textContent = title;
        this.currentDeleteUrl = url;
        this.currentDeleteCategory = categoryContext;
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
