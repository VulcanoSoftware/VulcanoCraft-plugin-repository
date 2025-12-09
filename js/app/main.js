import API from './api.js';
import UI from './ui.js';
import Modals from './modals.js';
import Filters from './filters.js';
import Auth from './auth.js';

class App {
    constructor() {
        this.allPlugins = [];
        this.authStatus = {};
    }

    async init() {
        document.getElementById('currentYear').textContent = new Date().getFullYear();

        this.authStatus = await Auth.checkStatus();

        await this.loadPluginData();

        this.filters = new Filters(this.allPlugins, (filteredPlugins) => this.render(filteredPlugins));

        this.setupEventListeners();

        this.render(this.allPlugins);
    }

    async loadPluginData() {
        try {
            const [plugins, serverCategories, serverInfo] = await Promise.all([
                API.getPlugins(),
                API.getServerCategories(),
                API.getServerInfo()
            ]);
            this.allPlugins = plugins;

            UI.populateVersionFilter(this.allPlugins);
            UI.populateLoaderFilter(this.allPlugins);
            UI.buildCategorySidebar(this.allPlugins, serverCategories, serverInfo);
        } catch (error) {
            console.error('Failed to load plugin data:', error);
            UI.showEmptyMessage('Fout bij het laden van plugins.');
        }
    }

    render(pluginsToRender) {
        UI.renderPlugins(pluginsToRender, this.authStatus, Auth.currentUser);
        UI.updateResultsCount(pluginsToRender.length, this.allPlugins.length);
        UI.updateCategoryCounts(this.allPlugins);
    }

    setupEventListeners() {
        // Reload plugins when a plugin is successfully added or deleted
        Modals.addModalEl.addEventListener('hidden.bs.modal', async (event) => {
            // Check if the modal was closed after a successful add operation
            if (Modals.cachedPluginData) {
                await this.loadPluginData();
                this.filters.allPlugins = this.allPlugins;
                this.filters.applyFilters();
            }
        });

        Modals.deleteModalEl.addEventListener('hidden.bs.modal', async () => {
             await this.loadPluginData();
             this.filters.allPlugins = this.allPlugins;
             this.filters.applyFilters();
        });

        // Event delegation for delete buttons
        UI.pluginsContainer.addEventListener('click', (event) => {
            const deleteButton = event.target.closest('.delete-btn');
            if (deleteButton) {
                const url = deleteButton.dataset.url;
                const title = deleteButton.dataset.title;
                Modals.showDeleteModal(url, title);
            }
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const app = new App();
    app.init();
});
