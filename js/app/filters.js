import UI from './ui.js';

class Filters {
    constructor(onFilterChange) {
        this.onFilterChange = onFilterChange;

        this.searchInput = document.getElementById('searchInput');
        this.versionFilter = document.getElementById('versionFilter');
        this.sortSelect = document.getElementById('sortSelect');
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
        if (this.sortSelect) this.sortSelect.addEventListener('change', () => this.applyFilters());
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

    getFilterParams() {
        const activeCategoryEl = this.categorySidebar.querySelector('.active');
        const selectedCategory = activeCategoryEl ? activeCategoryEl.dataset.category : '';
        const loaderCheckboxes = document.querySelectorAll('.loader-filter');

        return {
            search: this.searchInput.value.trim(),
            version: this.versionFilter.value,
            sort: this.sortSelect ? this.sortSelect.value : 'name_asc',
            platforms: this._getSelectedValues('.platform-filter'),
            loaders: loaderCheckboxes.length > 0 ? this._getSelectedValues('.loader-filter') : undefined,
            category: selectedCategory,
            include: this.includeExcludeSwitch.checked
        };
    }

    applyFilters(resetPage = true) {
        const filterParams = this.getFilterParams();
        this.onFilterChange(filterParams, resetPage);
    }

    reset() {
        this.searchInput.value = '';
        this.versionFilter.value = '';
        if (this.sortSelect) this.sortSelect.value = 'name_asc';
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
