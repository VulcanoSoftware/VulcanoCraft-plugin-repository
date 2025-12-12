import UI from './ui.js';

class Filters {
    constructor(allPlugins, onFilterChange) {
        this.allPlugins = allPlugins;
        this.onFilterChange = onFilterChange;

        this.searchInput = document.getElementById('searchInput');
        this.versionFilter = document.getElementById('versionFilter');
        this.platformFilters = document.querySelectorAll('.platform-filter');
        this.loaderFiltersContainer = document.getElementById('loaderFilters');
        this.categorySidebar = document.getElementById('categorySidebar');
        this.resetButton = document.getElementById('resetFilters');
        this.includeExcludeSwitch = document.getElementById('includeExcludeSwitch');

        this._addEventListeners();
        this._setupPlatformLoadersCheckboxes();
    }

    _addEventListeners() {
        this.searchInput.addEventListener('input', this._debounce(() => this.applyFilters(), 300));
        this.versionFilter.addEventListener('change', () => this.applyFilters());
        this.platformFilters.forEach(filter => filter.addEventListener('change', () => this.applyFilters()));
        this.loaderFiltersContainer.addEventListener('change', (e) => {
            if (e.target.classList.contains('loader-filter')) this.applyFilters();
        });
        this.categorySidebar.addEventListener('click', (e) => {
            const item = e.target.closest('.category-item');
            if (item) {
                this.categorySidebar.querySelector('.active').classList.remove('active');
                item.classList.add('active');
                this.applyFilters();
            }
        });
        this.resetButton.addEventListener('click', () => this.reset());
        this.includeExcludeSwitch.addEventListener('change', () => {
            document.querySelector(`label[for=${this.includeExcludeSwitch.id}]`).textContent = this.includeExcludeSwitch.checked ? 'Include' : 'Exclude';
            this.applyFilters();
        });
    }

    _setupPlatformLoadersCheckboxes() {
        const checkAll = (selector, checked) => {
            document.querySelectorAll(selector).forEach(checkbox => checkbox.checked = checked);
            this.applyFilters();
        };

        document.getElementById('checkAllPlatforms').addEventListener('click', () => checkAll('.platform-filter', true));
        document.getElementById('uncheckAllPlatforms').addEventListener('click', () => checkAll('.platform-filter', false));
        document.getElementById('checkAllLoaders').addEventListener('click', () => checkAll('.loader-filter', true));
        document.getElementById('uncheckAllLoaders').addEventListener('click', () => checkAll('.loader-filter', false));
    }

    applyFilters() {
        const searchTerm = this.searchInput.value.toLowerCase().trim();
        const selectedVersion = this.versionFilter.value;
        const selectedPlatforms = this._getSelectedValues('.platform-filter');
        const selectedLoaders = this._getSelectedValues('.loader-filter');
        const selectedCategory = this.categorySidebar.querySelector('.active').dataset.category;
        const include = this.includeExcludeSwitch.checked;

        const filteredPlugins = this.allPlugins.filter(plugin => {
            const matchesSearch = !searchTerm || ['title', 'description', 'author'].some(prop => plugin[prop]?.toLowerCase().includes(searchTerm));
            const matchesVersion = !selectedVersion || plugin.versions?.includes(selectedVersion);
            const matchesPlatform = selectedPlatforms.length === 0 || selectedPlatforms.includes(this._getPlatformFromUrl(plugin.url));
            const matchesLoader = selectedLoaders.length === 0 || plugin.loaders?.some(loader => selectedLoaders.includes(loader));
            const pluginCategories = new Set(plugin.categories || [plugin.category] || plugin.tags || []);
            const matchesCategory = !selectedCategory || pluginCategories.has(selectedCategory);

            const match = matchesSearch && matchesVersion && matchesPlatform && matchesLoader && matchesCategory;
            return include ? match : !match;
        });

        this.onFilterChange(filteredPlugins);
    }

    reset() {
        this.searchInput.value = '';
        this.versionFilter.value = '';
        this.platformFilters.forEach(cb => cb.checked = true);
        document.querySelectorAll('.loader-filter').forEach(cb => cb.checked = true);
        this.categorySidebar.querySelector('.active').classList.remove('active');
        this.categorySidebar.querySelector('[data-category=""]').classList.add('active');
        this.includeExcludeSwitch.checked = true;

        this.applyFilters();

        this.resetButton.style.transform = 'scale(0.95)';
        setTimeout(() => this.resetButton.style.transform = 'scale(1)', 150);
    }

    _getSelectedValues(selector) {
        return Array.from(document.querySelectorAll(`${selector}:checked`)).map(cb => cb.value);
    }

    _getPlatformFromUrl(url) {
        if (!url) return 'unknown';
        if (url.includes('hangar.papermc.io')) return 'hangar';
        if (url.includes('spigotmc.org')) return 'spigot';
        if (url.includes('modrinth.com')) return 'modrinth';
        if (url.includes('dev.bukkit.org')) return 'bukkitdev';
        if (url.includes('github.com')) return 'github';
        if (url.includes('curseforge.com')) return 'curseforge';
        if (url.includes('planetminecraft.com')) return 'planetminecraft';
        return 'unknown';
    }

    _debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
}

export default Filters;
