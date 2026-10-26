import API from './api.js';
import UI from './ui.js';
import i18n from './i18n.js';

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
                            <i class="fas fa-info-circle me-2 text-primary" id="genericAlertModalIcon"></i><span id="genericAlertModalTitleText" data-i18n="common.notice">${i18n.t('common.notice')}</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="genericAlertModalBody"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-primary" data-bs-dismiss="modal" id="genericAlertOkBtn" data-i18n="common.ok">${i18n.t('common.ok')}</button>
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
                            <i class="fas fa-question-circle me-2 text-warning" id="genericConfirmModalIcon"></i><span id="genericConfirmModalTitleText" data-i18n="common.confirm_title">${i18n.t('common.confirm_title')}</span>
                        </h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="genericConfirmModalBody"></div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="genericConfirmCancelBtn" data-i18n="common.cancel">${i18n.t('common.cancel')}</button>
                        <button type="button" class="btn btn-danger" id="genericConfirmOkBtn" data-i18n="common.confirm">${i18n.t('common.confirm')}</button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modalEl);
    }
    return modalEl;
}

export function showAlertModal(message, title = null, iconClass = 'fas fa-info-circle text-primary') {
    return new Promise((resolve) => {
        const modalEl = ensureAlertModalExists();
        const titleTextEl = document.getElementById('genericAlertModalTitleText');
        const bodyEl = document.getElementById('genericAlertModalBody');
        const iconEl = document.getElementById('genericAlertModalIcon');

        if (titleTextEl) titleTextEl.textContent = title || i18n.t('common.notice');
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

function ensurePinVersionModalExists() {
    let modalEl = document.getElementById('pinVersionModal');
    if (!modalEl) {
        modalEl = document.createElement('div');
        modalEl.className = 'modal fade';
        modalEl.id = 'pinVersionModal';
        modalEl.tabIndex = -1;
        modalEl.setAttribute('aria-hidden', 'true');
        modalEl.innerHTML = `
            <div class="modal-dialog modal-lg modal-dialog-centered">
                <div class="modal-content shadow-lg border-0 rounded-4 overflow-hidden">
                    <div class="modal-header bg-dark text-white px-4 py-3">
                        <h5 class="modal-title d-flex align-items-center gap-2" id="pinVersionModalTitle">
                            <i class="fas fa-thumbtack text-warning fs-5"></i><span data-i18n="modal.pin_version_title">${i18n.t('modal.pin_version_title')}</span>
                        </h5>
                        <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body p-4">
                        <div class="mb-3 p-3 rounded-3 border d-flex align-items-center gap-3 shadow-sm" style="background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);">
                            <img id="pinModalPluginIcon" src="images/server-icon.png" class="plugin-icon flex-shrink-0" style="width: 52px; height: 52px; object-fit: contain;" alt="icon">
                            <div class="min-w-0">
                                <h5 id="pinModalPluginTitle" class="mb-1 fw-bold text-dark text-truncate">Plugin Title</h5>
                                <small id="pinModalPluginAuthor" class="text-muted d-block text-truncate"></small>
                            </div>
                        </div>
                        <p class="small text-muted mb-3" data-i18n="modal.pin_version_help">${i18n.t('modal.pin_version_help')}</p>

                        <div id="pinModalLoading" class="text-center py-4" style="display: none;">
                            <img src="images/loading-icon.gif" class="loading-icon mb-2" alt="Loading">
                            <div class="small text-muted" data-i18n="common.loading">${i18n.t('common.loading')}</div>
                        </div>

                        <div id="pinModalVersionContent">
                            <label class="form-label fw-bold text-dark mb-2" data-i18n="modal.select_version">${i18n.t('modal.select_version')}</label>
                            <div id="pinModalVersionsList" class="mb-3 pe-1" style="max-height: 320px; overflow-y: auto;"></div>

                            <div class="p-3 rounded-3 border shadow-sm" style="background: #f8fafc;">
                                <label class="form-label small fw-bold text-dark mb-1" data-i18n="modal.manual_version_label">${i18n.t('modal.manual_version_label') || 'Voer plugin en/of ingame versie in:'}</label>
                                <input type="text" id="pinModalManualVersionInput" class="form-control" placeholder="${i18n.t('modal.manual_version_placeholder') || 'Bijv. 2.4.1 (1.21.6)'}" data-i18n-placeholder="modal.manual_version_placeholder">
                            </div>
                        </div>
                    </div>
                    <div class="modal-footer bg-light px-4 py-3">
                        <button type="button" class="btn btn-outline-danger me-auto" id="pinModalUnpinBtn">
                            <i class="fas fa-unlink me-1"></i><span data-i18n="modal.unpin_version">${i18n.t('modal.unpin_version')}</span>
                        </button>
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" data-i18n="common.cancel">${i18n.t('common.cancel')}</button>
                        <button type="button" class="btn btn-primary" id="pinModalSaveBtn">
                            <i class="fas fa-save me-1"></i><span data-i18n="common.confirm">${i18n.t('common.confirm')}</span>
                        </button>
                    </div>
                </div>
            </div>`;
        document.body.appendChild(modalEl);
    }
    return modalEl;
}

function _populatePinModalHeader(plugin, manualInputEl) {
    const iconEl = document.getElementById('pinModalPluginIcon');
    const titleEl = document.getElementById('pinModalPluginTitle');
    const authorEl = document.getElementById('pinModalPluginAuthor');

    if (titleEl) titleEl.textContent = plugin.title || i18n.t('common.no_title');
    if (authorEl) authorEl.textContent = plugin.author ? `${i18n.t('common.by')} ${plugin.author}` : '';
    if (iconEl) iconEl.src = plugin.icon || 'images/server-icon.png';
    if (manualInputEl) manualInputEl.value = plugin.pinned_version || '';
}

function _groupVersionsByPluginVersion(versionsArray) {
    const groups = [];
    const map = new Map();

    (versionsArray || []).forEach(item => {
        const str = String(item).trim();
        if (!str) return;
        const match = str.match(/^(.+?)\s*\((.+?)\)$/);
        let pVer = str;
        let gVer = null;
        if (match) {
            pVer = match[1].trim();
            gVer = match[2].trim();
        }

        if (!map.has(pVer)) {
            const groupObj = { pluginVersion: pVer, gameVersions: [] };
            map.set(pVer, groupObj);
            groups.push(groupObj);
        }

        if (gVer && !map.get(pVer).gameVersions.includes(gVer)) {
            map.get(pVer).gameVersions.push(gVer);
        }
    });

    return groups;
}

function _renderPinModalVersionList(versionsListEl, versionsArray, state, manualInputEl) {
    if (!versionsListEl) return;
    if (!state.expanded) state.expanded = {};

    const groups = _groupVersionsByPluginVersion(versionsArray);
    if (groups.length === 0) {
        versionsListEl.innerHTML = `<div class="small text-muted p-3 text-center bg-light rounded-3 border">${i18n.t('common.no_versions')}</div>`;
        return;
    }

    let html = '';
    groups.forEach(group => {
        const pVer = group.pluginVersion;
        const isPluginActive = (state.selectedVersion === pVer || state.selectedVersion.startsWith(`${pVer} (`));
        const isExpanded = !!state.expanded[pVer];

        html += `
            <div class="version-group-card mb-2 p-3 border rounded-3 bg-white shadow-sm ${isPluginActive ? 'active-group-card' : ''}">
                <div class="d-flex align-items-center justify-content-between gap-2 flex-wrap">
                    <button type="button" class="version-item-btn border-0 rounded-3 p-2 mb-0 flex-grow-1 text-start d-flex align-items-center justify-content-between ${isPluginActive ? 'active' : ''}" data-version="${pVer}">
                        <div class="d-flex align-items-center gap-2">
                            <i class="fas fa-tag ${isPluginActive ? 'text-white' : 'text-primary'}"></i>
                            <span class="fw-bold fs-6">${pVer}</span>
                        </div>
                        ${isPluginActive ? '<span class="badge bg-white text-primary fw-bold ms-2"><i class="fas fa-check me-1"></i>Geselecteerd</span>' : '<span class="text-muted small">Pinnen</span>'}
                    </button>
                    ${group.gameVersions.length > 0 ? `
                        <button type="button" class="btn btn-sm btn-outline-secondary toggle-game-versions-btn text-nowrap rounded-pill px-3 ms-auto" data-pver="${pVer}">
                            <i class="fas fa-gamepad me-1 text-info"></i><span>${i18n.t('modal.show_game_versions') || 'Ingame versies'} (${group.gameVersions.length})</span>
                            <i class="fas fa-chevron-${isExpanded ? 'up' : 'down'} ms-1 small"></i>
                        </button>
                    ` : ''}
                </div>
                ${group.gameVersions.length > 0 ? `
                    <div class="game-versions-collapse mt-3 p-3 rounded-3 border" style="display: ${isExpanded ? 'block' : 'none'}; background: #f8fafc;">
                        <div class="small text-muted mb-2 fw-bold d-flex align-items-center gap-1">
                            <i class="fas fa-cubes text-primary"></i>
                            <span>${i18n.t('modal.supported_game_versions') || 'Ondersteunde ingame versies:'}</span>
                        </div>
                        <div class="d-flex flex-wrap gap-2">
                            ${group.gameVersions.map(gv => {
                                const fullVer = `${pVer} (${gv})`;
                                const isGvActive = (state.selectedVersion === fullVer);
                                return `<button type="button" class="btn btn-sm ${isGvActive ? 'btn-primary shadow-sm fw-bold' : 'btn-outline-dark'} version-badge-pill" data-fullversion="${fullVer}">
                                    <i class="fas fa-gamepad me-1 small"></i>${gv}
                                </button>`;
                            }).join('')}
                        </div>
                    </div>
                ` : ''}
            </div>`;
    });
    versionsListEl.innerHTML = html;

    versionsListEl.querySelectorAll('.version-item-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const pickedVer = btn.dataset.version;
            state.selectedVersion = pickedVer;
            if (manualInputEl) {
                manualInputEl.value = pickedVer;
            }
            _renderPinModalVersionList(versionsListEl, versionsArray, state, manualInputEl);
        });
    });

    versionsListEl.querySelectorAll('.toggle-game-versions-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const pVer = btn.dataset.pver;
            state.expanded[pVer] = !state.expanded[pVer];
            _renderPinModalVersionList(versionsListEl, versionsArray, state, manualInputEl);
        });
    });

    versionsListEl.querySelectorAll('.version-badge-pill[data-fullversion]').forEach(badge => {
        badge.addEventListener('click', (e) => {
            e.stopPropagation();
            const pickedVer = badge.dataset.fullversion;
            state.selectedVersion = pickedVer;
            if (manualInputEl) {
                manualInputEl.value = pickedVer;
            }
            _renderPinModalVersionList(versionsListEl, versionsArray, state, manualInputEl);
        });
    });
}

function _fetchPinModalVersions(plugin, state, loadingEl, versionsListEl, manualInputEl) {
    if (loadingEl) loadingEl.style.display = 'block';
    if (versionsListEl) versionsListEl.style.display = 'none';

    API.fetchPinModalVersions(plugin.url).then(res => {
        let list = (res && res.versions && res.versions.length > 0) ? res.versions : [];
        if (list.length === 0 && plugin.versions) {
            list = plugin.versions.split(/\s+/).filter(Boolean);
        }
        _renderPinModalVersionList(versionsListEl, list, state, manualInputEl);
    }).catch(err => {
        console.warn('Failed to fetch pin modal versions:', err);
        const fallback = plugin.versions ? plugin.versions.split(/\s+/).filter(Boolean) : [];
        _renderPinModalVersionList(versionsListEl, fallback, state, manualInputEl);
    }).finally(() => {
        if (loadingEl) loadingEl.style.display = 'none';
        if (versionsListEl) versionsListEl.style.display = 'block';
    });
}

export function showPinVersionModal(plugin) {
    return new Promise((resolve) => {
        const modalEl = ensurePinVersionModalExists();
        const loadingEl = document.getElementById('pinModalLoading');
        const versionsListEl = document.getElementById('pinModalVersionsList');
        const manualInputEl = document.getElementById('pinModalManualVersionInput');
        const saveBtn = document.getElementById('pinModalSaveBtn');
        const unpinBtn = document.getElementById('pinModalUnpinBtn');

        _populatePinModalHeader(plugin, manualInputEl);

        const state = { selectedVersion: plugin.pinned_version || '' };
        _fetchPinModalVersions(plugin, state, loadingEl, versionsListEl, manualInputEl);

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        let actionResult = null;

        const handleSave = async () => {
            const finalVersion = (manualInputEl && manualInputEl.value.trim()) ? manualInputEl.value.trim() : state.selectedVersion;
            if (!finalVersion) return;
            try {
                const res = await API.pinPluginVersion(plugin.url, finalVersion);
                if (res.success) {
                    actionResult = { action: 'save', version: finalVersion };
                    modal.hide();
                } else {
                    showAlertModal(res.error || i18n.t('common.error'), i18n.t('common.error'));
                }
            } catch (err) {
                showAlertModal(err.message, i18n.t('common.error'));
            }
        };

        const handleUnpin = async () => {
            try {
                const res = await API.pinPluginVersion(plugin.url, null);
                if (res.success) {
                    actionResult = { action: 'unpin', version: null };
                    modal.hide();
                } else {
                    showAlertModal(res.error || i18n.t('common.error'), i18n.t('common.error'));
                }
            } catch (err) {
                showAlertModal(err.message, i18n.t('common.error'));
            }
        };

        const onHide = () => {
            if (saveBtn) saveBtn.removeEventListener('click', handleSave);
            if (unpinBtn) unpinBtn.removeEventListener('click', handleUnpin);
            modalEl.removeEventListener('hidden.bs.modal', onHide);
            resolve(actionResult);
        };

        if (saveBtn) saveBtn.addEventListener('click', handleSave);
        if (unpinBtn) unpinBtn.addEventListener('click', handleUnpin);
        modalEl.addEventListener('hidden.bs.modal', onHide);
        modal.show();
    });
}

export function showConfirmModal({ title = null, message, confirmText = null, confirmClass = 'btn-danger', iconClass = 'fas fa-question-circle text-warning' }) {
    return new Promise((resolve) => {
        const modalEl = ensureConfirmModalExists();
        const titleTextEl = document.getElementById('genericConfirmModalTitleText');
        const bodyEl = document.getElementById('genericConfirmModalBody');
        const iconEl = document.getElementById('genericConfirmModalIcon');
        const okBtn = document.getElementById('genericConfirmOkBtn');

        if (titleTextEl) titleTextEl.textContent = title || i18n.t('common.confirm_title');
        if (bodyEl) bodyEl.innerHTML = message;
        if (iconEl) iconEl.className = `${iconClass} me-2`;
        if (okBtn) {
            okBtn.textContent = confirmText || i18n.t('common.confirm');
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
        this._addModal = null;
        this._deleteModal = null;

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
        this.currentDeleteCategory = null;
        this.addSuccess = false;

        this.bulkCurrentPage = 1;
        this.bulkPerPage = 5;
        this.bulkPerPageSelect = document.getElementById('bulkPerPageSelect');
        this.bulkPaginationControls = document.getElementById('bulkPaginationControls');

        this._addEventListeners();
    }

    get addModal() {
        if (!this._addModal && this.addModalEl && window.bootstrap) {
            this._addModal = bootstrap.Modal.getOrCreateInstance(this.addModalEl);
        }
        return this._addModal;
    }

    get deleteModal() {
        if (!this._deleteModal && this.deleteModalEl && window.bootstrap) {
            this._deleteModal = bootstrap.Modal.getOrCreateInstance(this.deleteModalEl);
        }
        return this._deleteModal;
    }

    _addEventListeners() {
        if (this.fetchButton) this.fetchButton.addEventListener('click', () => this.handleFetch());
        if (this.confirmYes) this.confirmYes.addEventListener('click', () => this.handleAddConfirm());
        if (this.confirmNo) this.confirmNo.addEventListener('click', () => this.handleAddCancel());
        if (this.confirmDeleteButton) this.confirmDeleteButton.addEventListener('click', () => this.handleDeleteConfirm());

        if (this.selectAllBtn) {
            this.selectAllBtn.addEventListener('click', () => this._toggleAllBulkCheckboxes(true));
        }
        if (this.deselectAllBtn) {
            this.deselectAllBtn.addEventListener('click', () => this._toggleAllBulkCheckboxes(false));
        }

        if (this.bulkPerPageSelect) {
            this.bulkPerPageSelect.addEventListener('change', (e) => {
                const parsed = parseInt(e.target.value, 10);
                this.bulkPerPage = isNaN(parsed) ? 5 : parsed;
                this.bulkCurrentPage = 1;
                this._renderBulkPreviewList();
            });
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

        if (this.deleteModalEl) {
            this.deleteModalEl.addEventListener('shown.bs.modal', () => this.startDeleteAnimation());
        }
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
            this.showError(i18n.t('error.enter_url'));
            return;
        }

        this.showStep(2);
        this.hideError();

        const fetchProgressText = document.getElementById('fetchProgressText');
        const progressBarContainer = document.getElementById('fetchProgressBarContainer');
        if (fetchProgressText) fetchProgressText.textContent = i18n.t('modal.fetch_info');
        if (progressBarContainer) progressBarContainer.style.display = 'none';

        try {
            const plugin = await API.fetchPlugin(url);
            this.cachedPluginData = plugin;
            this.updateAddModalPreview(plugin);

            document.getElementById('singlePreviewContainer').style.display = 'block';
            document.getElementById('bulkPreviewContainer').style.display = 'none';
            document.getElementById('selectedCountBadge').style.display = 'none';
            document.getElementById('confirmationQuestionText').textContent = i18n.t('modal.confirm_question');

            this.showStep(3);
            this._toggleAddModalButtons(false);
            this._setModalStatic(true);
        } catch (error) {
            this.showError(`${error.message}`);
            this.showStep(1);
        }
    }

    async _handleBulkFetch() {
        const rawText = this.bulkPluginUrlsInput.value.trim();
        if (!rawText) {
            this.showError(i18n.t('error.enter_url_bulk'));
            return;
        }

        const urls = Array.from(new Set(
            rawText.split(/[\n\s]+/).map(u => u.trim()).filter(u => u.length > 0)
        ));

        if (urls.length === 0) {
            this.showError(i18n.t('error.no_valid_urls'));
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
                fetchProgressText.textContent = `${i18n.t('common.plugin')} ${currentNum} / ${urls.length} (${url})`;
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
        document.getElementById('confirmationQuestionText').textContent = i18n.t('modal.add_selected_question');

        this.showStep(3);
        this._toggleAddModalButtons(false);
        this._setModalStatic(true);
    }

    _renderBulkPreviewList() {
        const bulkListEl = document.getElementById('bulkPreviewList');
        if (!bulkListEl) return;

        const totalItems = this.cachedBulkPlugins.length;
        const perPage = this.bulkPerPage === 0 ? totalItems : this.bulkPerPage;
        const totalPages = perPage > 0 ? Math.ceil(totalItems / perPage) : 1;

        if (this.bulkCurrentPage > totalPages) this.bulkCurrentPage = totalPages || 1;

        const startIndex = (this.bulkCurrentPage - 1) * perPage;
        const pageItems = this.bulkPerPage === 0 ? this.cachedBulkPlugins : this.cachedBulkPlugins.slice(startIndex, startIndex + perPage);

        let html = '';
        pageItems.forEach((item, pageIdx) => {
            const realIndex = this.bulkPerPage === 0 ? pageIdx : startIndex + pageIdx;
            if (item.status === 'success') {
                const plugin = item.plugin;
                const versionsStr = plugin.versions ? plugin.versions.split(' ').slice(0, 3).join(', ') : i18n.t('common.no_versions');
                const firstLetter = (plugin.title || 'P')[0].toUpperCase();
                const iconHtml = plugin.icon
                    ? `<img src="${plugin.icon}" class="bulk-preview-icon flex-shrink-0 me-2" alt="icon" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="bulk-preview-icon-letter flex-shrink-0 me-2" style="display:none;">${firstLetter}</div>`
                    : `<div class="bulk-preview-icon-letter flex-shrink-0 me-2">${firstLetter}</div>`;

                html += `
                    <div class="bulk-review-item">
                        <div class="d-flex align-items-center min-w-0">
                            <div class="form-check me-3 flex-shrink-0">
                                <input class="form-check-input bulk-item-checkbox" type="checkbox" data-index="${realIndex}" id="bulkCheck_${realIndex}" ${item.selected ? 'checked' : ''}>
                            </div>
                            ${iconHtml}
                            <div class="flex-grow-1 min-w-0">
                                <div class="d-flex justify-content-between align-items-center gap-2 min-w-0">
                                    <h6 class="mb-0 text-truncate min-w-0" title="${plugin.title || i18n.t('common.no_title')}">${plugin.title || i18n.t('common.no_title')}</h6>
                                    <small class="text-muted text-nowrap flex-shrink-0">${plugin.author || i18n.t('common.unknown')}</small>
                                </div>
                                <div class="small text-muted text-truncate min-w-0" title="${plugin.description || i18n.t('common.no_description')}">${plugin.description || i18n.t('common.no_description')}</div>
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
                                <input class="form-check-input bulk-item-checkbox" type="checkbox" data-index="${realIndex}" id="bulkCheck_${realIndex}" disabled>
                            </div>
                            <div class="flex-grow-1 min-w-0">
                                <h6 class="mb-0 text-danger"><i class="fas fa-exclamation-circle me-1"></i> ${i18n.t('modal.fetch_error')}</h6>
                                <div class="small text-muted text-truncate min-w-0" title="${item.url}">${item.url}</div>
                                <div class="small text-danger text-truncate min-w-0" title="${item.error}">${item.error}</div>
                            </div>
                        </div>
                    </div>`;
            }
        });

        bulkListEl.innerHTML = html;
        this._renderBulkPaginationControls(this.bulkPaginationControls, this.bulkCurrentPage, totalPages, (newPage) => {
            this.bulkCurrentPage = newPage;
            this._renderBulkPreviewList();
        });
        this._updateBulkSelectedCount();
    }

    _renderBulkPaginationControls(container, currentPage, totalPages, onPageClick) {
        if (!container) return;
        if (totalPages <= 1) {
            container.innerHTML = `<li class="page-item active"><span class="page-link">1</span></li>`;
            return;
        }

        let html = '';
        const prevDisabled = currentPage <= 1 ? 'disabled' : '';
        html += `<li class="page-item ${prevDisabled}"><button class="page-link" data-page="${currentPage - 1}" aria-label="Previous">&laquo;</button></li>`;

        const maxVisiblePages = 5;
        let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
        let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);

        if (endPage - startPage + 1 < maxVisiblePages) {
            startPage = Math.max(1, endPage - maxVisiblePages + 1);
        }

        if (startPage > 1) {
            html += `<li class="page-item"><button class="page-link" data-page="1">1</button></li>`;
            if (startPage > 2) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let p = startPage; p <= endPage; p++) {
            const active = p === currentPage ? 'active' : '';
            html += `<li class="page-item ${active}"><button class="page-link" data-page="${p}">${p}</button></li>`;
        }

        if (endPage < totalPages) {
            if (endPage < totalPages - 1) {
                html += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            html += `<li class="page-item"><button class="page-link" data-page="${totalPages}">${totalPages}</button></li>`;
        }

        const nextDisabled = currentPage >= totalPages ? 'disabled' : '';
        html += `<li class="page-item ${nextDisabled}"><button class="page-link" data-page="${currentPage + 1}" aria-label="Next">&raquo;</button></li>`;

        container.innerHTML = html;

        container.querySelectorAll('button.page-link').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(btn.dataset.page, 10);
                if (page && page !== currentPage && page >= 1 && page <= totalPages) {
                    onPageClick(page);
                }
            });
        });
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
            countBadge.innerHTML = `<i class="fas fa-check-square me-1"></i>${i18n.t('modal.selected')}: ${selectedCount} / ${totalSuccess}`;
        }

        const summaryText = document.getElementById('bulkSummaryText');
        if (summaryText) {
            summaryText.innerHTML = `
                <span class="badge bg-primary me-1"><i class="fas fa-check-square me-1"></i>${i18n.t('modal.selected_for_import')}: ${selectedCount}</span>
                <span class="badge bg-success me-1"><i class="fas fa-check-circle me-1"></i>${i18n.t('modal.successful_fetched')}: ${totalSuccess}</span>
                <span class="badge bg-secondary"><i class="fas fa-list me-1"></i>${i18n.t('modal.total_urls_file')}: ${totalTotal}</span>`;
        }

        if (this.confirmYes) {
            this.confirmYes.disabled = (selectedCount === 0 && this.isBulkMode);
        }
    }

    async handleAddConfirm() {
        try {
            const authData = await API.getAuthStatus();
            if (!authData.logged_in) {
                this.showError(i18n.t('error.login_required'));
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
            this.showError(`${error.message}`);
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
            UI.showSuccessMessage(i18n.t('success.plugin_added'));
            this.addModal.hide();
        } else {
            this.showError(`${data.error}`);
        }
    }

    async _addBulkPlugins(activeCategory) {
        const selectedItems = this.cachedBulkPlugins.filter(i => i.selected && i.status === 'success');
        if (selectedItems.length === 0) {
            this.showError(i18n.t('error.select_at_least_one'));
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
            UI.showSuccessMessage(`${addedCount} ${i18n.t('success.bulk_plugins_added')}`);
            this.addModal.hide();
        } else {
            this.showError(i18n.t('error.bulk_add_failed', { count: failCount }));
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
        const questionEl = document.getElementById('deleteConfirmModalQuestion');
        const pluginTitle = questionEl ? questionEl.textContent.trim() : '';
        const categoryContext = this.currentDeleteCategory || '';
        try {
            const data = await API.deletePlugin(this.currentDeleteUrl, categoryContext || undefined);
            if (data.success) {
                UI.showSuccessMessage(i18n.t('success.plugin_deleted', { title: pluginTitle }));
                this.deleteModal.hide();
            } else {
                this.showError(`${data.error}`);
            }
        } catch (error) {
            this.showError(`${error.message}`);
        }
    }

    showDeleteModal(url, title, categoryContext = '') {
        const questionEl = document.getElementById('deleteConfirmModalQuestion');
        if (questionEl) {
            questionEl.innerHTML = i18n.t('modal.delete_confirm_question', { title });
        }
        this.currentDeleteUrl = url;
        this.currentDeleteCategory = categoryContext;
        this.deleteModal.show();
    }

    updateAddModalPreview(plugin) {
        document.getElementById('previewTitle').textContent = plugin.title || i18n.t('common.no_title');
        document.getElementById('previewDescription').textContent = plugin.description || i18n.t('common.no_description');

        let authorsHtml = i18n.t('common.unknown');
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
            : `<span class="badge bg-secondary">${i18n.t('common.no_versions')}</span>`;
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
            btn.innerHTML = `<img src="images/loading-icon.gif" class="loading-icon me-2" alt="Laden"> ${i18n.t('modal.adding')}`;
            btn.disabled = true;
        } else {
            btn.innerHTML = `<img src="images/confirm-icon.png" class="btn-icon" alt="Ja"> <span data-i18n="modal.yes_add">${i18n.t('modal.yes_add')}</span>`;
            btn.disabled = false;
        }
    }

    _setModalStatic(isStatic) {
        this.addModalEl.dataset.bsBackdrop = isStatic ? 'static' : 'true';
        this.addModalEl.dataset.bsKeyboard = isStatic ? 'false' : 'true';
    }
}

export default new Modals();
