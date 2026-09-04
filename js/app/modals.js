import API from './api.js';
import UI from './ui.js';

function ensureAlertModalExists() {
    let modalEl = document.getElementById('genericAlertModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade';
        modalEl.id = 'genericAlertModal';
        modalEl.tabIndex = -1;
        modalEl.setAttribute('aria-hidden', 'true');
        modalEl.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="genericAlertModalTitle">
                            <i class="fas fa-info-circle me-2 text-primary" id="genericAlertModalIcon"></i><span id="genericAlertModalTitleText">Melding</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="genericAlertModalBody"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal" id="genericAlertOkBtn">OK</button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modalEl);
    }
    return modalEl;
}

function ensureConfirmModalExists() {
    let modalEl = document.getElementById('genericConfirmModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade';
        modalEl.id = 'genericConfirmModal';
        modalEl.tabIndex = -1;
        modalEl.setAttribute('aria-hidden', 'true');
        modalEl.innerHTML = `
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="genericConfirmModalTitle">
                            <i class="fas fa-question-circle me-2 text-warning" id="genericConfirmModalIcon"></i><span id="genericConfirmModalTitleText">Bevestiging</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="genericConfirmModalBody"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="genericConfirmCancelBtn">Annuleren</button>
                        <button type="button" class="btn btn-danger" id="genericConfirmOkBtn">Bevestigen</button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modalEl);
    }
    return modalEl;
}

export function showAlertModal(message, title = 'Melding', iconClass = 'fas fa-info-circle text-primary') {
    return new Promise((resolve) => {
        const modalEl = ensureAlertModalExists();
        const titleTextEl = document.getElementById('genericAlertModalTitleText');
        const bodyEl = document.getElementById('genericAlertModalBody');
        const iconEl = document.getElementById('genericAlertModalIcon');

        if (titleTextEl) titleTextEl.textContent = title;
        if (bodyEl) bodyEl.innerHTML = message;
        if (iconEl) iconEl.className = `${iconClass} me-2`;

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

        const onHide = () => {
            modalEl.removeEventListener('hidden.bs.modal', onHide);
            resolve();
        };
        modalEl.addEventListener('hidden.bs.modal', onHide);
        modal.show();
    });
}

export function showConfirmModal({ title = 'Bevestiging', message, confirmText = 'Bevestigen', confirmClass = 'btn-danger', iconClass = 'fas fa-question-circle text-warning' }) {
    return new Promise((resolve) => {
        const modalEl = ensureConfirmModalExists();
        const titleTextEl = document.getElementById('genericConfirmModalTitleText');
        const bodyEl = document.getElementById('genericConfirmModalBody');
        const iconEl = document.getElementById('genericConfirmModalIcon');
        const okBtn = document.getElementById('genericConfirmOkBtn');

        if (titleTextEl) titleTextEl.textContent = title;
        if (bodyEl) bodyEl.innerHTML = message;
        if (iconEl) iconEl.className = `${iconClass} me-2`;
        if (okBtn) {
            okBtn.textContent = confirmText;
            okBtn.className = `btn ${confirmClass}`;
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);

        let confirmed = false;
        const handleConfirm = () => {
            confirmed = true;
            modal.hide();
        };

        const onHide = () => {
            if (okBtn) okBtn.removeEventListener('click', handleConfirm);
            modalEl.removeEventListener('hidden.bs.modal', onHide);
            resolve(confirmed);
        };

        if (okBtn) okBtn.addEventListener('click', handleConfirm);
        modalEl.addEventListener('hidden.bs.modal', onHide);
        modal.show();
    });
}

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
        this.isReplaceMode = false;
        this.targetCategory = null;
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

            const itemCategory = (this.bulkItemMap && this.bulkItemMap.has(url))
                ? this.bulkItemMap.get(url)
                : (this.targetCategory && this.targetCategory !== 'ALL' ? this.targetCategory : null);

            try {
                const plugin = await API.fetchPlugin(url);
                this.cachedBulkPlugins.push({
                    url,
                    targetCategory: itemCategory,
                    plugin,
                    status: 'success',
                    selected: true
                });
            } catch (err) {
                this.cachedBulkPlugins.push({
                    url,
                    targetCategory: itemCategory,
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
                    ? `<img src="${plugin.icon}" class="bulk-preview-icon flex-shrink-0 me-2" alt="icon" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="bulk-preview-icon-letter flex-shrink-0 me-2" style="display:none;">${firstLetter}</div>`
                    : `<div class="bulk-preview-icon-letter flex-shrink-0 me-2">${firstLetter}</div>`;

                html += `
                    <div class="bulk-review-item">
                        <div class="d-flex align-items-center min-w-0">
                            <div class="form-check me-3 flex-shrink-0">
                                <input class="form-check-input bulk-item-checkbox" type="checkbox" data-index="${index}" id="bulkCheck_${index}" ${item.selected ? 'checked' : ''}>
                            </div>
                            ${iconHtml}
                            <div class="flex-grow-1 min-w-0">
                                <div class="d-flex justify-content-between align-items-center gap-2 min-w-0">
                                    <h6 class="mb-0 text-truncate min-w-0" title="${plugin.title || 'Geen titel'}">${plugin.title || 'Geen titel'}</h6>
                                    <small class="text-muted text-nowrap flex-shrink-0">${plugin.author || 'Onbekend'}</small>
                                </div>
                                <div class="small text-muted text-truncate min-w-0" title="${plugin.description || 'Geen beschrijving'}">${plugin.description || 'Geen beschrijving'}</div>
                                <div class="small mt-1 d-flex flex-wrap align-items-center gap-1 min-w-0">
                                    ${item.targetCategory ? `<span class="badge bg-primary text-truncate flex-shrink-0"><i class="fas fa-folder me-1"></i>${item.targetCategory}</span>` : ''}
                                    <span class="badge bg-info text-dark flex-shrink-0">v: ${versionsStr}</span>
                                    <span class="badge bg-secondary text-truncate mw-100" title="${item.url}">${item.url}</span>
                                </div>
                            </div>
                        </div>
                    </div>`;
            } else {
                html += `
                    <div class="bulk-review-item border-danger">
                        <div class="d-flex align-items-center min-w-0">
                            <div class="form-check me-3 flex-shrink-0">
                                <input class="form-check-input bulk-item-checkbox" type="checkbox" data-index="${index}" id="bulkCheck_${index}" disabled>
                            </div>
                            <div class="flex-grow-1 min-w-0">
                                <h6 class="mb-0 text-danger"><i class="fas fa-exclamation-circle me-1"></i> Fout bij ophalen</h6>
                                <div class="small text-muted text-truncate min-w-0" title="${item.url}">${item.url}</div>
                                <div class="small text-danger text-truncate min-w-0" title="${item.error}">${item.error}</div>
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
            countBadge.innerHTML = `<i class="fas fa-check-square me-1"></i>Geselecteerd: ${selectedCount} / ${totalSuccess}`;
        }

        const summaryText = document.getElementById('bulkSummaryText');
        if (summaryText) {
            summaryText.innerHTML = `
                <span class="badge bg-primary me-1"><i class="fas fa-check-square me-1"></i>Geselecteerd voor import: ${selectedCount}</span>
                <span class="badge bg-success me-1"><i class="fas fa-check-circle me-1"></i>Succesvol opgehaald: ${totalSuccess}</span>
                <span class="badge bg-secondary"><i class="fas fa-list me-1"></i>Totaal URL's in bestand: ${totalTotal}</span>`;
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
            const targetCat = this.targetCategory !== null && this.targetCategory !== undefined
                ? this.targetCategory
                : (document.querySelector('#categorySidebar .category-item.active')?.dataset.category || '');

            if (this.isReplaceMode) {
                await API.clearPlugins(false, targetCat || null);
                this.isReplaceMode = false;
            }

            if (!this.isBulkMode) {
                await this._addSinglePlugin(targetCat);
            } else {
                await this._addBulkPlugins(targetCat);
            }
        } catch (error) {
            this.showError(`Fout bij toevoegen: ${error.message}`);
        } finally {
            this._setConfirmYesLoading(false);
        }
    }

    openWithBulkUrls(urls, isReplace = false, category = null) {
        this.isReplaceMode = isReplace;
        this.targetCategory = category !== null ? category : (document.querySelector('#categorySidebar .category-item.active')?.dataset.category || '');
        this.showStep(1);

        const bulkTabBtn = document.getElementById('bulkUrlTab');
        if (bulkTabBtn) {
            const tab = bootstrap.Tab.getOrCreateInstance(bulkTabBtn);
            tab.show();
        }

        if (this.bulkPluginUrlsInput) {
            this.bulkPluginUrlsInput.value = urls.join('\n');
        }

        this.addModal.show();
        this.handleFetch();
    }

    openWithBulkItems(items, isReplace = false, category = null) {
        this.bulkItemMap = new Map();
        items.forEach(i => {
            if (i.url && i.category) {
                this.bulkItemMap.set(i.url, i.category);
            }
        });
        const urls = Array.from(new Set(items.map(i => i.url)));
        this.openWithBulkUrls(urls, isReplace, category);
    }

    async _addSinglePlugin(activeCategory) {
        const catToAssign = (this.targetCategory && this.targetCategory !== 'ALL')
            ? this.targetCategory
            : (activeCategory !== undefined && activeCategory !== null ? activeCategory : '');
        if (catToAssign) {
            this.cachedPluginData.category = catToAssign;
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
            const catToAssign = item.targetCategory || (this.targetCategory && this.targetCategory !== 'ALL' ? this.targetCategory : (activeCategory !== undefined && activeCategory !== null ? activeCategory : ''));
            if (catToAssign) {
                item.plugin.category = catToAssign;
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
        this.bulkItemMap = null;
        this.isReplaceMode = false;
        this.targetCategory = null;
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

        let authorsHtml = 'Onbekend';
        if (plugin.author) {
            let authors = [];
            if (Array.isArray(plugin.author)) {
                authors = plugin.author.map(a => String(a).trim()).filter(Boolean);
            } else if (typeof plugin.author === 'string') {
                const str = plugin.author.trim();
                authors = str.includes(',') ? str.split(',').map(a => a.trim()).filter(Boolean) : str.split(/\s+/).map(a => a.trim()).filter(Boolean);
            }
            authors = Array.from(new Set(authors));
            if (authors.length > 0) {
                authorsHtml = authors.map(a => `<span class="author-badge">${a}</span>`).join('');
            }
        }
        document.getElementById('previewAuthor').innerHTML = authorsHtml;
        document.getElementById('previewIcon').src = plugin.icon || 'images/plugin-placeholder.png';

        const versionsContainer = document.getElementById('previewVersions');
        versionsContainer.innerHTML = (plugin.versions)
            ? plugin.versions.split(' ').map((v, i) => `<span class="version-badge" style="animation-delay: ${i*100}ms">${v}</span>`).join('')
            : '<span class="badge bg-secondary">Geen versies</span>';
    }

    resetAddModal() {
        this.showStep(1);
        this.hideError();
        if (this.pluginUrlInput) this.pluginUrlInput.value = '';
        if (this.bulkPluginUrlsInput) this.bulkPluginUrlsInput.value = '';
        this.cachedPluginData = null;
        this.cachedBulkPlugins = [];
        this.bulkItemMap = null;
        this.isReplaceMode = false;
        this.targetCategory = null;
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
