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
            UI.updateResultsCount(data.plugins ? data.plugins.length : 0, data.total || 0);
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

    setupEventListeners() {
        if (UI.perPageSelect) {
            UI.perPageSelect.addEventListener('change', (e) => {
                this.perPage = parseInt(e.target.value, 10) || 20;
                this.currentPage = 1;
                this.loadAndRenderPlugins(this.filters.getFilterParams());
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
