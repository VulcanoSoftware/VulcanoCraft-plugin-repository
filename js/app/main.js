import API from './api.js';
import UI from './ui.js';
import Modals, { showAlertModal, showConfirmModal, showPinVersionModal } from './modals.js';
import Filters from './filters.js';
import Auth from './auth.js';
import i18n from './i18n.js';

class App {
    constructor() {
        this.authStatus = {};
        this.currentPage = 1;
        this.perPage = 20;
    }

    async init() {
        await i18n.init();
        document.getElementById('currentYear').textContent = new Date().getFullYear();

        this.authStatus = await Auth.checkStatus();

        if (this.authStatus.logged_in && this.authStatus.language) {
            await i18n.setLanguage(this.authStatus.language, false);
        } else {
            await i18n.applyTranslations();
        }

        this.filters = new Filters((filterParams, resetPage) => {
            if (resetPage) this.currentPage = 1;
            this.loadAndRenderPlugins(filterParams);
        });

        const [serverCategories, serverInfo, cronStatus, notifications] = await Promise.all([
            API.getServerCategories(),
            API.getServerInfo(),
            API.getCronStatus(),
            API.getNotifications()
        ]);

        this.serverCategories = serverCategories || [];
        this.serverInfo = serverInfo || {};

        UI.buildCategorySidebar([], this.serverCategories, this.serverInfo);
        UI.renderCronStatus(cronStatus);
        UI.renderNotifications(notifications);

        this.setupEventListeners();

        await this.loadAndRenderPlugins(this.filters.getFilterParams());
    }

    async loadAndRenderPlugins(filterParams) {
        try {
            const params = {
                page: this.currentPage,
                perPage: this.perPage,
                ...filterParams
            };

            const data = await API.getPlugins(params);
            this.lastLoadedPlugins = data.plugins || [];

            if (data.all_versions) UI.populateVersionFilter(data.all_versions);
            if (data.all_loaders) UI.populateLoaderFilter(data.all_loaders);

            if (data.category_counts) {
                const countCategoryNames = Object.keys(data.category_counts);
                const extraPlugins = countCategoryNames.map(name => ({ category: name }));
                UI.buildCategorySidebar(extraPlugins, this.serverCategories, this.serverInfo);
            }

            UI.renderPlugins(data.plugins || [], this.authStatus, Auth.currentUser);
            UI.updateResultsCount(data.plugins ? data.plugins.length : 0, data.total || 0, data.total_all, filterParams.category, data.category_counts);
            UI.updateCategoryCounts(data.category_counts || {}, data.total_all);
            this.updateCategoryActionHeader(filterParams.category, data.category_counts);

            UI.renderPagination(data.page || 1, data.total_pages || 1, (newPage) => {
                this.currentPage = newPage;
                this.loadAndRenderPlugins(this.filters.getFilterParams());
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        } catch (error) {
            console.error('Failed to load plugin data:', error);
            UI.showEmptyMessage(i18n.t('error.load_plugins'));
        }
    }

    openExportModal() {
        const modalEl = document.getElementById('exportTxtModal');
        if (!modalEl) return;

        const select = document.getElementById('exportCategorySelect');
        if (select) {
            let html = `<option value="ALL">${i18n.t('modal.all_categories')}</option>`;
            this.serverCategories.forEach(cat => {
                const name = typeof cat === 'object' ? cat.name : cat;
                if (name) {
                    html += `<option value="${name}">${name}</option>`;
                }
            });
            select.innerHTML = html;

            const activeCat = document.querySelector('#categorySidebar .category-item.active')?.dataset.category;
            select.value = activeCat ? activeCat : 'ALL';
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    async executeExport() {
        const select = document.getElementById('exportCategorySelect');
        const selectedCategory = select ? select.value : 'ALL';

        const modalEl = document.getElementById('exportTxtModal');
        if (modalEl) {
            const modal = bootstrap.Modal.getInstance(modalEl);
            if (modal) modal.hide();
        }

        try {
            if (selectedCategory === 'ALL') {
                const data = await API.getPlugins({ perPage: 0 });
                const plugins = data.plugins || [];
                if (plugins.length === 0) {
                    UI.showEmptyMessage(i18n.t('error.no_plugins_export'));
                    return;
                }

                const categoryMap = new Map();
                plugins.forEach(p => {
                    if (!p.url) return;
                    const cats = (p.categories && p.categories.length > 0)
                        ? p.categories
                        : (p.category ? [p.category] : ['Algemeen']);
                    cats.forEach(c => {
                        const catName = c || 'Algemeen';
                        if (!categoryMap.has(catName)) {
                            categoryMap.set(catName, new Set());
                        }
                        categoryMap.get(catName).add(p.url);
                    });
                });

                let textContent = '';
                for (const [catName, urlsSet] of categoryMap.entries()) {
                    if (textContent.length > 0) textContent += '\n\n';
                    textContent += `[${catName}]\n` + Array.from(urlsSet).join('\n');
                }

                this.triggerDownload(textContent, 'plugin-list-all.txt');
                UI.showSuccessMessage(i18n.t('success.export_all'));
            } else {
                const data = await API.getPlugins({ perPage: 0, category: selectedCategory });
                const plugins = data.plugins || [];
                const urls = Array.from(new Set(plugins.map(p => p.url).filter(Boolean)));

                if (urls.length === 0) {
                    UI.showEmptyMessage(i18n.t('error.no_plugins_export'));
                    return;
                }

                const textContent = `[${selectedCategory}]\n` + urls.join('\n');
                this.triggerDownload(textContent, `plugin-list-${selectedCategory}.txt`);
                UI.showSuccessMessage(i18n.t('success.export_category', { category: selectedCategory }));
            }
        } catch (error) {
            console.error('Export failed:', error);
            UI.showEmptyMessage(i18n.t('error.export_failed'));
        }
    }

    triggerDownload(content, fileName) {
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const downloadUrl = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = downloadUrl;
        a.download = fileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(downloadUrl);
    }

    openImportModal(isReplace) {
        this.isReplaceMode = isReplace;
        const modalEl = document.getElementById('importTxtModal');
        if (!modalEl) return;

        const titleText = document.getElementById('importModalTitleText');
        if (titleText) {
            titleText.textContent = isReplace ? i18n.t('nav.replace_txt') : i18n.t('nav.append_txt');
        }

        const select = document.getElementById('importCategorySelect');
        if (select) {
            let html = `<option value="ALL">${i18n.t('modal.all_categories')}</option>`;
            this.serverCategories.forEach(cat => {
                const name = typeof cat === 'object' ? cat.name : cat;
                if (name) {
                    html += `<option value="${name}">${name}</option>`;
                }
            });
            select.innerHTML = html;

            const activeCat = document.querySelector('#categorySidebar .category-item.active')?.dataset.category;
            select.value = activeCat ? activeCat : 'ALL';
        }

        const fileInput = document.getElementById('importModalFileInput');
        const fileNameSpan = document.getElementById('customFileNameText');
        if (fileInput) fileInput.value = '';
        if (fileNameSpan) {
            fileNameSpan.setAttribute('data-i18n', 'modal.no_file_chosen');
            fileNameSpan.textContent = i18n.t('modal.no_file_chosen');
        }

        const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
        modal.show();
    }

    updateCategoryActionHeader(selectedCategory, categoryCounts) {
        const container = document.getElementById('categoryHeaderActionContainer');
        const titleEl = document.getElementById('selectedCategoryTitle');
        const badgeEl = document.getElementById('selectedCategoryBadge');
        const clearBtn = document.getElementById('clearCategoryPluginsHomeBtn');

        if (!container) return;

        if (selectedCategory && selectedCategory !== '') {
            container.style.display = 'block';
            if (titleEl) titleEl.textContent = `${i18n.t('counter.category')}: ${selectedCategory}`;
            const count = (categoryCounts && categoryCounts[selectedCategory]) || 0;
            if (badgeEl) badgeEl.textContent = `${count} ${count === 1 ? i18n.t('common.plugin') : i18n.t('common.plugins')}`;

            if (clearBtn) {
                clearBtn.style.display = this.authStatus.logged_in ? 'inline-block' : 'none';
                clearBtn.dataset.category = selectedCategory;
                clearBtn.dataset.count = count;
            }
        } else {
            container.style.display = 'none';
        }
    }

    async handleClearCategoryPlugins(category, count) {
        if (!category) return;

        const isUserAdmin = this.authStatus.role === 'admin' || this.authStatus.role === 'co-admin';

        const confirmed = await showConfirmModal({
            title: i18n.t('clear_category.title'),
            message: i18n.t('clear_category.confirm', { category }),
            confirmText: i18n.t('modal.yes_delete_all'),
            confirmClass: 'btn-danger',
            iconClass: 'fas fa-trash-alt text-danger'
        });

        if (!confirmed) return;

        try {
            const data = await API.clearPlugins(isUserAdmin, category);
            if (data.success) {
                UI.showSuccessMessage(i18n.t('success.clear_category', { category }));
                await this.loadAndRenderPlugins(this.filters.getFilterParams());
            } else {
                await showAlertModal(data.error, i18n.t('warning.title'), 'fas fa-exclamation-triangle text-danger');
            }
        } catch (err) {
            await showAlertModal(err.message, i18n.t('warning.title'), 'fas fa-exclamation-triangle text-danger');
        }
    }

    async handleImportSubmit() {
        const select = document.getElementById('importCategorySelect');
        const selectedCategory = select ? select.value : 'ALL';
        const fileInput = document.getElementById('importModalFileInput');
        const file = fileInput ? fileInput.files[0] : null;

        if (!file) {
            await showAlertModal(i18n.t('warning.select_txt'), i18n.t('warning.title'), 'fas fa-exclamation-circle text-warning');
            return;
        }

        const modalEl = document.getElementById('importTxtModal');
        const importModal = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;

        const reader = new FileReader();
        reader.onload = async (event) => {
            const text = event.target.result;
            const items = this.parseTxtContent(text, selectedCategory);

            if (items.length === 0) {
                await showAlertModal(i18n.t('warning.no_valid_urls_txt'), i18n.t('warning.title'), 'fas fa-exclamation-circle text-warning');
                return;
            }

            if (importModal) importModal.hide();

            // Check for missing categories
            const existingCatNames = this.serverCategories.map(c => typeof c === 'object' ? c.name : c);
            const fileCategories = Array.from(new Set(items.map(i => i.category)));
            const missingCats = fileCategories.filter(c => c && c !== 'Algemeen' && !existingCatNames.includes(c));

            if (missingCats.length > 0) {
                this.promptForMissingCategories(missingCats, () => {
                    this.proceedToBulkImport(items, this.isReplaceMode, selectedCategory, file.name);
                });
            } else {
                this.proceedToBulkImport(items, this.isReplaceMode, selectedCategory, file.name);
            }
        };
        reader.readAsText(file);
    }

    parseTxtContent(text, defaultCategory) {
        const lines = text.split(/[\r\n]+/);
        let currentCategory = (defaultCategory && defaultCategory !== 'ALL') ? defaultCategory : 'Algemeen';
        const items = [];
        const isAllMode = (defaultCategory === 'ALL');

        for (let line of lines) {
            line = line.trim();
            if (!line) continue;

            const catHeaderMatch = line.match(/^(?:\[(?:Categorie:\s*|Category:\s*)?([^\]]+)\]|#\s*(?:Categorie|Category):\s*(.+))$/i);
            if (catHeaderMatch) {
                const extractedCat = (catHeaderMatch[1] || catHeaderMatch[2]).trim();
                if (extractedCat && isAllMode) {
                    currentCategory = extractedCat;
                }
                continue;
            }

            if (line.startsWith('http://') || line.startsWith('https://')) {
                const cat = (defaultCategory && defaultCategory !== 'ALL') ? defaultCategory : currentCategory;
                items.push({ url: line, category: cat });
            }
        }
        return items;
    }

    promptForMissingCategories(missingCats, onComplete) {
        const modalEl = document.getElementById('missingCategoriesModal');
        if (!modalEl) {
            onComplete();
            return;
        }

        const listEl = document.getElementById('missingCategoriesList');
        if (listEl) {
            listEl.innerHTML = missingCats.map(c => `
                <li class="list-group-item d-flex align-items-center">
                    <i class="fas fa-folder me-2 text-primary"></i>${c}
                </li>`).join('');
        }

        const missingModal = bootstrap.Modal.getOrCreateInstance(modalEl);

        const confirmBtn = document.getElementById('confirmCreateCategoriesBtn');
        const skipBtn = document.getElementById('skipCreateCategoriesBtn');

        const cleanupAndRun = () => {
            confirmBtn.replaceWith(confirmBtn.cloneNode(true));
            skipBtn.replaceWith(skipBtn.cloneNode(true));
            missingModal.hide();
            onComplete();
        };

        const onConfirm = async () => {
            try {
                await API.ensureCategories(missingCats);
                this.serverCategories = await API.getServerCategories();
                UI.buildCategorySidebar([], this.serverCategories, this.serverInfo);
            } catch (err) {
                console.error('Fout bij aanmaken nieuwe categorieën:', err);
            }
            cleanupAndRun();
        };

        const onSkip = () => {
            cleanupAndRun();
        };

        confirmBtn.addEventListener('click', onConfirm, { once: true });
        skipBtn.addEventListener('click', onSkip, { once: true });

        missingModal.show();
    }

    async proceedToBulkImport(items, isReplaceMode, selectedCategory, fileName) {
        const catText = selectedCategory === 'ALL'
            ? i18n.t('modal.all_categories_text')
            : i18n.t('modal.category_text', { category: selectedCategory });

        const confirmMsg = isReplaceMode
            ? i18n.t('modal.confirm_replace_msg', { catText, count: items.length, fileName })
            : i18n.t('modal.confirm_append_msg', { catText, count: items.length, fileName });

        const confirmed = await showConfirmModal({
            title: isReplaceMode ? i18n.t('nav.replace_txt') : i18n.t('nav.append_txt'),
            message: confirmMsg,
            confirmText: isReplaceMode ? i18n.t('modal.yes_replace') : i18n.t('modal.yes_append'),
            confirmClass: isReplaceMode ? 'btn-warning' : 'btn-primary',
            iconClass: 'fas fa-file-import text-info'
        });

        if (confirmed) {
            Modals.openWithBulkItems(items, isReplaceMode, selectedCategory);
        }
    }

    setupEventListeners() {
        this._setupPaginationAndExportListeners();
        this._setupImportListeners();
        this._setupLanguageAndHomeListeners();
        this._setupNotificationsAndDiscordListeners();
        this._setupModalEventsAndDelegation();
    }

    _setupNotificationsAndDiscordListeners() {
        const clearNotifsBtn = document.getElementById('clearNotificationsBtn');
        if (clearNotifsBtn) {
            clearNotifsBtn.addEventListener('click', async (e) => {
                e.stopPropagation();
                try {
                    await API.clearNotifications();
                    UI.renderNotifications([]);
                } catch (err) {
                    console.error('Failed to clear notifications:', err);
                }
            });
        }

        const discordBtn = document.getElementById('discordWebhookBtn');
        if (discordBtn) {
            discordBtn.addEventListener('click', async () => {
                const modalEl = document.getElementById('discordWebhookModal');
                if (!modalEl) return;
                const alertEl = document.getElementById('discordWebhookAlert');
                if (alertEl) alertEl.style.display = 'none';

                try {
                    const data = await API.getDiscordWebhook();
                    const urlInput = document.getElementById('discordWebhookUrlInput');
                    const enabledSwitch = document.getElementById('discordWebhookEnabledSwitch');
                    if (urlInput) urlInput.value = data.webhook_url || '';
                    if (enabledSwitch) enabledSwitch.checked = Boolean(data.enabled);
                } catch (err) {
                    console.error('Failed to load discord webhook data:', err);
                }

                const modal = bootstrap.Modal.getOrCreateInstance(modalEl);
                modal.show();
            });
        }

        const saveDiscordBtn = document.getElementById('saveDiscordWebhookBtn');
        if (saveDiscordBtn) {
            saveDiscordBtn.addEventListener('click', async () => {
                const urlInput = document.getElementById('discordWebhookUrlInput');
                const enabledSwitch = document.getElementById('discordWebhookEnabledSwitch');
                const alertEl = document.getElementById('discordWebhookAlert');

                const webhookUrl = urlInput ? urlInput.value.trim() : '';
                const enabled = enabledSwitch ? enabledSwitch.checked : false;

                try {
                    const res = await API.saveDiscordWebhook(webhookUrl, enabled);
                    if (res && res.success) {
                        if (alertEl) {
                            alertEl.className = 'alert alert-success small mb-0 mt-2';
                            alertEl.textContent = i18n.t('discord.save_success');
                            alertEl.style.display = 'block';
                        }
                    } else {
                        if (alertEl) {
                            alertEl.className = 'alert alert-danger small mb-0 mt-2';
                            alertEl.textContent = res.error || i18n.t('discord.save_error');
                            alertEl.style.display = 'block';
                        }
                    }
                } catch (err) {
                    if (alertEl) {
                        alertEl.className = 'alert alert-danger small mb-0 mt-2';
                        alertEl.textContent = err.message;
                        alertEl.style.display = 'block';
                    }
                }
            });
        }

        const testDiscordBtn = document.getElementById('testDiscordWebhookBtn');
        if (testDiscordBtn) {
            testDiscordBtn.addEventListener('click', async () => {
                const urlInput = document.getElementById('discordWebhookUrlInput');
                const alertEl = document.getElementById('discordWebhookAlert');
                const webhookUrl = urlInput ? urlInput.value.trim() : '';

                if (alertEl) {
                    alertEl.className = 'alert alert-info small mb-0 mt-2';
                    alertEl.textContent = i18n.t('discord.testing');
                    alertEl.style.display = 'block';
                }

                try {
                    const res = await API.testDiscordWebhook(webhookUrl);
                    if (res && res.success) {
                        if (alertEl) {
                            alertEl.className = 'alert alert-success small mb-0 mt-2';
                            alertEl.textContent = res.message || i18n.t('discord.test_success');
                            alertEl.style.display = 'block';
                        }
                    } else {
                        if (alertEl) {
                            alertEl.className = 'alert alert-danger small mb-0 mt-2';
                            alertEl.textContent = res.error || i18n.t('discord.test_failed');
                            alertEl.style.display = 'block';
                        }
                    }
                } catch (err) {
                    if (alertEl) {
                        alertEl.className = 'alert alert-danger small mb-0 mt-2';
                        alertEl.textContent = err.message;
                        alertEl.style.display = 'block';
                    }
                }
            });
        }
    }

    _setupPaginationAndExportListeners() {
        if (UI.perPageSelect) {
            UI.perPageSelect.addEventListener('change', (e) => {
                const parsed = parseInt(e.target.value, 10);
                this.perPage = isNaN(parsed) ? 20 : parsed;
                this.currentPage = 1;
                this.loadAndRenderPlugins(this.filters.getFilterParams());
            });
        }

        const exportBtn = document.getElementById('exportTxtBtn');
        const exportUserBtn = document.getElementById('exportTxtUserBtn');
        if (exportBtn) exportBtn.addEventListener('click', () => this.openExportModal());
        if (exportUserBtn) exportUserBtn.addEventListener('click', () => this.openExportModal());

        const confirmExportBtn = document.getElementById('confirmExportBtn');
        if (confirmExportBtn) confirmExportBtn.addEventListener('click', () => this.executeExport());
    }

    _setupImportListeners() {
        const replaceBtn = document.getElementById('replaceTxtBtn');
        if (replaceBtn) replaceBtn.addEventListener('click', () => this.openImportModal(true));

        const appendBtn = document.getElementById('appendTxtBtn');
        if (appendBtn) appendBtn.addEventListener('click', () => this.openImportModal(false));

        const confirmImportBtn = document.getElementById('confirmImportBtn');
        if (confirmImportBtn) confirmImportBtn.addEventListener('click', () => this.handleImportSubmit());

        const fileInput = document.getElementById('importModalFileInput');
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                const fileNameSpan = document.getElementById('customFileNameText');
                if (fileNameSpan) {
                    if (e.target.files && e.target.files.length > 0) {
                        fileNameSpan.removeAttribute('data-i18n');
                        fileNameSpan.textContent = e.target.files[0].name;
                    } else {
                        fileNameSpan.setAttribute('data-i18n', 'modal.no_file_chosen');
                        fileNameSpan.textContent = i18n.t('modal.no_file_chosen');
                    }
                }
            });
        }
    }

    _setupLanguageAndHomeListeners() {
        const langMenu = document.getElementById('languageDropdownMenu');
        if (langMenu) {
            langMenu.addEventListener('click', async (e) => {
                const langItem = e.target.closest('[data-lang]');
                if (langItem) {
                    e.preventDefault();
                    const selectedLang = langItem.getAttribute('data-lang');
                    if (selectedLang) {
                        await i18n.setLanguage(selectedLang, this.authStatus.logged_in);
                        this.loadAndRenderPlugins(this.filters.getFilterParams());
                    }
                }
            });
        }

        const clearCategoryHomeBtn = document.getElementById('clearCategoryPluginsHomeBtn');
        if (clearCategoryHomeBtn) {
            clearCategoryHomeBtn.addEventListener('click', () => {
                const cat = clearCategoryHomeBtn.dataset.category;
                const count = clearCategoryHomeBtn.dataset.count || 0;
                this.handleClearCategoryPlugins(cat, count);
            });
        }
    }

    _setupModalEventsAndDelegation() {
        Modals.addModalEl.addEventListener('hidden.bs.modal', async () => {
            if (Modals.addSuccess) {
                await this.loadAndRenderPlugins(this.filters.getFilterParams());
            }
            Modals.resetAddModal();
        });

        Modals.deleteModalEl.addEventListener('hidden.bs.modal', async () => {
            await this.loadAndRenderPlugins(this.filters.getFilterParams());
        });

        UI.pluginsContainer.addEventListener('click', async (event) => {
            const deleteButton = event.target.closest('.delete-btn');
            if (deleteButton) {
                this._handleDeleteBtnClick(deleteButton);
                return;
            }

            const pinButton = event.target.closest('.pin-version-btn');
            if (pinButton) {
                await this._handlePinBtnClick(pinButton);
                return;
            }

            const updateBadge = event.target.closest('.update-badge-click');
            if (updateBadge) {
                await this._handleUpdateBadgeClick(updateBadge);
            }
        });
    }

    _handleDeleteBtnClick(deleteButton) {
        const url = deleteButton.dataset.url;
        const title = deleteButton.dataset.title;
        const categoryContext = deleteButton.dataset.categoryContext || '';
        Modals.showDeleteModal(url, title, categoryContext);
    }

    async _handlePinBtnClick(pinButton) {
        const url = pinButton.dataset.url;
        const plugin = this.lastLoadedPlugins ? this.lastLoadedPlugins.find(p => p.url === url) : { url };
        if (plugin) {
            const result = await showPinVersionModal(plugin);
            if (result) {
                const msg = result.action === 'save' ? i18n.t('success.version_pinned') : i18n.t('success.version_unpinned');
                UI.showSuccessMessage(msg);
                await this.loadAndRenderPlugins(this.filters.getFilterParams());
            }
        }
    }

    async _handleUpdateBadgeClick(updateBadge) {
        const url = updateBadge.dataset.url;
        let pinned = updateBadge.dataset.pinned || '';
        let latest = updateBadge.dataset.latest || '';

        if (url) {
            try {
                const res = await API.fetchPinModalVersions(url);
                if (res && res.versions && res.versions.length > 0) {
                    const pinnedMatch = res.versions.find(v => v === pinned || v.startsWith(`${pinned} `) || v.startsWith(`${pinned}(`));
                    if (pinnedMatch) pinned = pinnedMatch;

                    const latestMatch = res.versions.find(v => v === latest || v.startsWith(`${latest} `) || v.startsWith(`${latest}(`));
                    if (latestMatch) {
                        latest = latestMatch;
                    } else if (res.versions[0]) {
                        latest = res.versions[0];
                    }
                }
            } catch (e) {
                console.warn('Failed to fetch full version pairings for update modal:', e);
            }
        }

        showAlertModal(
            `<div class="text-center py-3 px-2">
                <div class="update-modal-icon-circle mx-auto mb-3">
                    <i class="fas fa-arrow-alt-circle-up text-danger fa-3x"></i>
                </div>
                <h4 class="fw-bold text-dark mb-3">${i18n.t('common.update_available')}</h4>
                <div class="d-flex align-items-center justify-content-center flex-wrap gap-3 p-3 rounded-3 bg-light border shadow-sm">
                    <div class="text-center min-w-0">
                        <small class="text-muted d-block fw-bold mb-1">${i18n.t('common.pinned')}</small>
                        <span class="badge bg-warning text-dark fs-6 px-3 py-2 fw-bold text-wrap">${pinned}</span>
                    </div>
                    <i class="fas fa-arrow-right text-muted fs-4 d-none d-sm-inline-block"></i>
                    <i class="fas fa-arrow-down text-muted fs-4 d-inline-block d-sm-none"></i>
                    <div class="text-center min-w-0">
                        <small class="text-muted d-block fw-bold mb-1">${i18n.t('common.latest') || 'Nieuwste'}</small>
                        <span class="badge bg-success fs-6 px-3 py-2 fw-bold text-wrap">${latest}</span>
                    </div>
                </div>
            </div>`,
            i18n.t('common.update_available'),
            'fas fa-arrow-alt-circle-up text-danger'
        );
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
