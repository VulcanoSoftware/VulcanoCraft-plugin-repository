import API from './api.js';
import UI from './ui.js';
import Modals, { showAlertModal, showConfirmModal } from './modals.js';
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
        document.getElementById('currentYear').textContent = new Date().getFullYear();

        this.authStatus = await Auth.checkStatus();

        if (this.authStatus.logged_in && this.authStatus.language) {
            i18n.setLanguage(this.authStatus.language, false);
        } else {
            i18n.applyTranslations();
        }

        this.filters = new Filters((filterParams, resetPage) => {
            if (resetPage) this.currentPage = 1;
            this.loadAndRenderPlugins(filterParams);
        });

        const [serverCategories, serverInfo] = await Promise.all([
            API.getServerCategories(),
            API.getServerInfo()
        ]);

        this.serverCategories = serverCategories || [];
        this.serverInfo = serverInfo || {};

        UI.buildCategorySidebar([], this.serverCategories, this.serverInfo);

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

            if (data.all_versions) UI.populateVersionFilter(data.all_versions);
            if (data.all_loaders) UI.populateLoaderFilter(data.all_loaders);

            if (data.category_counts) {
                const countCategoryNames = Object.keys(data.category_counts);
                const extraPlugins = countCategoryNames.map(name => ({ category: name }));
                UI.buildCategorySidebar(extraPlugins, this.serverCategories, this.serverInfo);
            }

            UI.renderPlugins(data.plugins || [], this.authStatus, Auth.currentUser);
            UI.updateResultsCount(data.plugins ? data.plugins.length : 0, data.total || 0, data.total_all, filterParams.category);
            UI.updateCategoryCounts(data.category_counts || {}, data.total_all);
            this.updateCategoryActionHeader(filterParams.category, data.category_counts);

            UI.renderPagination(data.page || 1, data.total_pages || 1, (newPage) => {
                this.currentPage = newPage;
                this.loadAndRenderPlugins(this.filters.getFilterParams());
                window.scrollTo({ top: 0, behavior: 'smooth' });
            });
        } catch (error) {
            console.error('Failed to load plugin data:', error);
            UI.showEmptyMessage('Fout bij het laden van plugins.');
        }
    }

    openExportModal() {
        const modalEl = document.getElementById('exportTxtModal');
        if (!modalEl) return;

        const select = document.getElementById('exportCategorySelect');
        if (select) {
            let html = '<option value="ALL">Alle categorieën</option>';
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
                    UI.showEmptyMessage('Geen plugins om te exporteren.');
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
                UI.showSuccessMessage('Alle categorieën succesvol geëxporteerd als TXT-bestand!');
            } else {
                const data = await API.getPlugins({ perPage: 0, category: selectedCategory });
                const plugins = data.plugins || [];
                const urls = Array.from(new Set(plugins.map(p => p.url).filter(Boolean)));

                if (urls.length === 0) {
                    UI.showEmptyMessage(`Geen plugins te exporteren voor categorie "${selectedCategory}".`);
                    return;
                }

                const textContent = `[${selectedCategory}]\n` + urls.join('\n');
                this.triggerDownload(textContent, `plugin-list-${selectedCategory}.txt`);
                UI.showSuccessMessage(`Categorie "${selectedCategory}" succesvol geëxporteerd als TXT-bestand!`);
            }
        } catch (error) {
            console.error('Export failed:', error);
            UI.showEmptyMessage('Fout bij het exporteren van plugins.');
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
            titleText.textContent = isReplace ? 'Lijst Vervangen (TXT)' : 'TXT Bijvoegen';
        }

        const select = document.getElementById('importCategorySelect');
        if (select) {
            let html = '<option value="ALL">Alle categorieën</option>';
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
        if (fileInput) fileInput.value = '';

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
            if (titleEl) titleEl.textContent = `Categorie: ${selectedCategory}`;
            const count = (categoryCounts && categoryCounts[selectedCategory]) || 0;
            if (badgeEl) badgeEl.textContent = `${count} ${count === 1 ? 'plugin' : 'plugins'}`;

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
            title: 'Categorie Plugins Verwijderen',
            message: `<div class="alert alert-warning mb-3"><i class="fas fa-exclamation-triangle me-2"></i>Weet je zeker dat je alle plugins in de categorie "<strong>${category}</strong>" wilt verwijderen?</div><p class="mb-0 text-muted">Aantal plugins in deze categorie: <strong>${count}</strong>. Deze actie kan niet ongedaan worden gemaakt.</p>`,
            confirmText: 'Ja, alle plugins verwijderen',
            confirmClass: 'btn-danger',
            iconClass: 'fas fa-trash-alt text-danger'
        });

        if (!confirmed) return;

        try {
            const data = await API.clearPlugins(isUserAdmin, category);
            if (data.success) {
                UI.showSuccessMessage(`Alle plugins in de categorie "${category}" zijn succesvol verwijderd!`);
                await this.loadAndRenderPlugins(this.filters.getFilterParams());
            } else {
                await showAlertModal(`Fout bij verwijderen: ${data.error}`, 'Fout', 'fas fa-exclamation-triangle text-danger');
            }
        } catch (err) {
            await showAlertModal(`Fout bij verwijderen: ${err.message}`, 'Fout', 'fas fa-exclamation-triangle text-danger');
        }
    }

    async handleImportSubmit() {
        const select = document.getElementById('importCategorySelect');
        const selectedCategory = select ? select.value : 'ALL';
        const fileInput = document.getElementById('importModalFileInput');
        const file = fileInput ? fileInput.files[0] : null;

        if (!file) {
            await showAlertModal('Selecteer a.u.b. een TXT bestand.', 'Waarschuwing', 'fas fa-exclamation-circle text-warning');
            return;
        }

        const modalEl = document.getElementById('importTxtModal');
        const importModal = modalEl ? bootstrap.Modal.getInstance(modalEl) : null;

        const reader = new FileReader();
        reader.onload = async (event) => {
            const text = event.target.result;
            const items = this.parseTxtContent(text, selectedCategory);

            if (items.length === 0) {
                await showAlertModal('Geen geldige plugin URL\'s gevonden in het TXT bestand.', 'Waarschuwing', 'fas fa-exclamation-circle text-warning');
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
        let confirmMsg = '';
        const catText = selectedCategory === 'ALL' ? 'ALLE categorieën' : `categorie "${selectedCategory}"`;

        if (isReplaceMode) {
            confirmMsg = `Weet je zeker dat je de huidige plugin lijst van ${catText} wilt <strong>VERVANGEN</strong> door de ${items.length} URL's uit "<strong>${fileName}</strong>"?`;
        } else {
            confirmMsg = `Weet je zeker dat je de ${items.length} URL's uit "<strong>${fileName}</strong>" wilt bijvoegen bij ${catText}?`;
        }

        const confirmed = await showConfirmModal({
            title: isReplaceMode ? 'Lijst Vervangen' : 'TXT Bijvoegen',
            message: confirmMsg,
            confirmText: isReplaceMode ? 'Ja, Vervangen' : 'Ja, Bijvoegen',
            confirmClass: isReplaceMode ? 'btn-warning' : 'btn-primary',
            iconClass: 'fas fa-file-import text-info'
        });

        if (confirmed) {
            Modals.openWithBulkItems(items, isReplaceMode, selectedCategory);
        }
    }

    setupEventListeners() {
        if (UI.perPageSelect) {
            UI.perPageSelect.addEventListener('change', (e) => {
                this.perPage = parseInt(e.target.value, 10) || 20;
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

        const replaceBtn = document.getElementById('replaceTxtBtn');
        if (replaceBtn) replaceBtn.addEventListener('click', () => this.openImportModal(true));

        const appendBtn = document.getElementById('appendTxtBtn');
        if (appendBtn) appendBtn.addEventListener('click', () => this.openImportModal(false));

        const confirmImportBtn = document.getElementById('confirmImportBtn');
        if (confirmImportBtn) confirmImportBtn.addEventListener('click', () => this.handleImportSubmit());

        const langNlBtn = document.getElementById('langSelectNl');
        const langEnBtn = document.getElementById('langSelectEn');

        if (langNlBtn) {
            langNlBtn.addEventListener('click', (e) => {
                e.preventDefault();
                i18n.setLanguage('nl', this.authStatus.logged_in);
                this.loadAndRenderPlugins(this.filters.getFilterParams());
            });
        }

        if (langEnBtn) {
            langEnBtn.addEventListener('click', (e) => {
                e.preventDefault();
                i18n.setLanguage('en', this.authStatus.logged_in);
                this.loadAndRenderPlugins(this.filters.getFilterParams());
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

        // Reload plugins when a plugin is successfully added or deleted
        Modals.addModalEl.addEventListener('hidden.bs.modal', async () => {
            if (Modals.addSuccess) {
                await this.loadAndRenderPlugins(this.filters.getFilterParams());
            }
            Modals.resetAddModal();
        });

        Modals.deleteModalEl.addEventListener('hidden.bs.modal', async () => {
            await this.loadAndRenderPlugins(this.filters.getFilterParams());
        });

        // Event delegation for delete buttons
        UI.pluginsContainer.addEventListener('click', (event) => {
            const deleteButton = event.target.closest('.delete-btn');
            if (deleteButton) {
                const url = deleteButton.dataset.url;
                const title = deleteButton.dataset.title;
                const categoryContext = deleteButton.dataset.categoryContext || '';
                Modals.showDeleteModal(url, title, categoryContext);
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
