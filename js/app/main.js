import API from './api.js';
import UI from './ui.js';
import Modals from './modals.js';
import Filters from './filters.js';
import Auth from './auth.js';

class App {
    constructor() {
        this.authStatus = {};
        this.currentPage = 1;
        this.perPage = 20;
    }

    async init() {
        document.getElementById('currentYear').textContent = new Date().getFullYear();

        this.authStatus = await Auth.checkStatus();

        this.filters = new Filters((filterParams, resetPage) => {
            if (resetPage) this.currentPage = 1;
            this.loadAndRenderPlugins(filterParams);
        });

        const [serverCategories, serverInfo] = await Promise.all([
            API.getServerCategories(),
            API.getServerInfo()
        ]);

        UI.buildCategorySidebar([], serverCategories, serverInfo);

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

            UI.renderPlugins(data.plugins || [], this.authStatus, Auth.currentUser);
            UI.updateResultsCount(data.plugins ? data.plugins.length : 0, data.total || 0, data.total_all);
            UI.updateCategoryCounts(data.category_counts || {});

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

    async exportCurrentPlugins() {
        try {
            const filterParams = this.filters ? this.filters.getFilterParams() : {};
            const data = await API.getPlugins({ perPage: 0, ...filterParams });
            const plugins = data.plugins || [];
            const urls = Array.from(new Set(plugins.map(p => p.url).filter(Boolean)));

            if (urls.length === 0) {
                UI.showEmptyMessage('Geen plugins om te exporteren.');
                return;
            }

            const textContent = urls.join('\n');
            const blob = new Blob([textContent], { type: 'text/plain;charset=utf-8' });
            const downloadUrl = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = 'plugin-list.txt';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(downloadUrl);
            UI.showSuccessMessage('Plugin lijst succesvol geëxporteerd als TXT-bestand!');
        } catch (error) {
            console.error('Export failed:', error);
            UI.showEmptyMessage('Fout bij het exporteren van plugins.');
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
        if (exportBtn) exportBtn.addEventListener('click', () => this.exportCurrentPlugins());
        if (exportUserBtn) exportUserBtn.addEventListener('click', () => this.exportCurrentPlugins());

        const replaceBtn = document.getElementById('replaceTxtBtn');
        const replaceFileInput = document.getElementById('replaceFileInput');
        if (replaceBtn && replaceFileInput) {
            replaceBtn.addEventListener('click', () => replaceFileInput.click());
            replaceFileInput.addEventListener('change', (e) => this.handleReplaceFileSelect(e));
        }

        const appendBtn = document.getElementById('appendTxtBtn');
        const appendFileInput = document.getElementById('appendFileInput');
        if (appendBtn && appendFileInput) {
            appendBtn.addEventListener('click', () => appendFileInput.click());
            appendFileInput.addEventListener('change', (e) => this.handleAppendFileSelect(e));
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

    handleReplaceFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            const urls = Array.from(new Set(
                text.split(/[\n\r]+/).map(u => u.trim()).filter(u => u.length > 0 && (u.startsWith('http://') || u.startsWith('https://')))
            ));

            if (urls.length === 0) {
                alert('Geen geldige plugin URL\'s gevonden in het TXT bestand.');
                e.target.value = '';
                return;
            }

            if (confirm(`Weet je zeker dat je de huidige plugin lijst wilt VERVANGEN door de ${urls.length} URL's uit "${file.name}"? Alle huidige plugins in jouw lijst worden verwijderd bij het bevestigen.`)) {
                Modals.openWithBulkUrls(urls, true);
            }
            e.target.value = '';
        };
        reader.readAsText(file);
    }

    handleAppendFileSelect(e) {
        const file = e.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            const urls = Array.from(new Set(
                text.split(/[\n\r]+/).map(u => u.trim()).filter(u => u.length > 0 && (u.startsWith('http://') || u.startsWith('https://')))
            ));

            if (urls.length === 0) {
                alert('Geen geldige plugin URL\'s gevonden in het TXT bestand.');
                e.target.value = '';
                return;
            }

            Modals.openWithBulkUrls(urls, false);
            e.target.value = '';
        };
        reader.readAsText(file);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
