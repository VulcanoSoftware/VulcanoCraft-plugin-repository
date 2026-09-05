class UI {
    constructor() {
        this.pluginsContainer = document.getElementById('pluginsContainer');
        this.categorySidebar = document.getElementById('categorySidebar');
        this.versionFilter = document.getElementById('versionFilter');
        this.loaderFilters = document.getElementById('loaderFilters');
        this.username = document.getElementById('username');
        this.authButtons = document.getElementById('authButtons');
        this.userButtons = document.getElementById('userButtons');
        this.adminBtn = document.getElementById('adminBtn');
        this.paginationContainer = document.getElementById('paginationContainer');
        this.paginationControls = document.getElementById('paginationControls');
        this.perPageSelect = document.getElementById('perPageSelect');
        this.resultsCounter = null;
    }

    renderPlugins(plugins, authStatus, currentUser) {
        if (plugins.length === 0) {
            this.showEmptyMessage('Nog geen plugins beschikbaar.');
            return;
        }

        const pluginsHtml = plugins.map(plugin => this._createPluginCard(plugin, authStatus, currentUser)).join('');
        this.pluginsContainer.innerHTML = pluginsHtml;
    }

    showEmptyMessage(message) {
        this.pluginsContainer.innerHTML = `
            <div class="col-12 text-center">
                <div class="alert alert-info d-flex align-items-center justify-content-center" role="alert">
                    <img src="images/add-icon.png" class="warning-icon me-2" alt="Geen plugins">
                    ${message}
                </div>
            </div>`;
    }

    _createPluginCard(plugin, authStatus, currentUser) {
        const { logged_in, role } = authStatus;
        const formattedVersions = this._formatVersions(plugin.versions || '');
        const formattedLoaders = this._formatLoaders(plugin.loaders);
        const formattedAuthors = this._formatAuthors(plugin.author);
        const domain = this._getDomainFromUrl(plugin.url || '');
        const ownerInfo = plugin.owner ? `<small class="text-muted ms-2">door ${plugin.owner}</small>` : '';
        const canDelete = logged_in && (role === 'admin' || role === 'co-admin' || plugin.owner === currentUser);
        const firstLetter = (plugin.title || 'P')[0].toUpperCase();
        const iconHtml = plugin.icon
            ? `<img src="${plugin.icon}" alt="${plugin.title} icon" class="plugin-icon me-3" loading="lazy" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="plugin-icon-letter me-3" style="display:none;">${firstLetter}</div>`
            : `<div class="plugin-icon-letter me-3">${firstLetter}</div>`;

        return `
            <div class="col-12 mb-4 plugin-card" style="animation: fadeIn 0.6s ease-out both;">
                <div class="card h-100 shadow-sm">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center">
                            ${iconHtml}
                            <div>
                                <h5 class="card-title mb-0">${plugin.title || 'Geen titel'}${ownerInfo}</h5>
                            </div>
                        </div>
                        <div>
                            <span class="domain-badge">${domain}</span>
                            ${canDelete ? `
                                <button class="btn btn-delete ms-2 delete-btn" data-url="${plugin.url}" data-title="${plugin.title}" data-category-context="${plugin._categoryContext || ''}">
                                    <img src="images/delete-icon.png" class="btn-icon" alt="Verwijderen">
                                </button>` : ''
                            }
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="card-text description">${plugin.description || 'Geen beschrijving beschikbaar'}</p>
                        <div class="row mb-3">
                            <div class="col-12">
                                <div class="plugin-info d-flex align-items-center flex-wrap gap-2">
                                    <strong><img src="images/author-icon.png" class="info-icon" alt="Auteur"> <span data-i18n="common.author">Auteur</span>:</strong>
                                    <div class="authors-container d-inline-flex flex-wrap gap-1 align-items-center">
                                        ${formattedAuthors}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div class="versions-section">
                            <strong><img src="images/version-icon.png" class="info-icon" alt="Versies"> <span data-i18n="common.supported_versions">Ondersteunde Versies</span>:</strong>
                            <div class="versions-container">${formattedVersions}</div>
                        </div>
                        <div class="loaders-section mt-3">
                            <strong><img src="images/plugin-repo-icon.png" class="info-icon" alt="Loaders"> <span data-i18n="common.supported_loaders">Ondersteunde Loaders</span>:</strong>
                            <div class="loaders-container">${formattedLoaders}</div>
                        </div>
                    </div>
                    <div class="card-footer bg-transparent">
                        <div class="d-flex justify-content-between align-items-center">
                            <a href="${plugin.url || '#'}" class="btn btn-primary" target="_blank">
                                <img src="images/external-link-icon.png" class="btn-icon" alt="Externe link">
                                Bekijk Plugin
                            </a>
                            <div class="url-container">
                                <small class="text-muted plugin-url" title="${plugin.url || ''}">
                                    <img src="images/link-icon.png" class="footer-icon" alt="URL">
                                    ${this._truncateUrl(plugin.url || '')}
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>`;
    }

    _formatAuthors(authorInput) {
        if (!authorInput) {
            return `<span class="author-badge" data-i18n="common.unknown">Onbekend</span>`;
        }

        let authors = [];
        if (Array.isArray(authorInput)) {
            authors = authorInput.map(a => String(a).trim()).filter(Boolean);
        } else if (typeof authorInput === 'string') {
            const str = authorInput.trim();
            if (str.includes(',')) {
                authors = str.split(',').map(a => a.trim()).filter(Boolean);
            } else {
                authors = str.split(/\s+/).map(a => a.trim()).filter(Boolean);
            }
        }

        authors = Array.from(new Set(authors));

        if (authors.length === 0) {
            return `<span class="author-badge" data-i18n="common.unknown">Onbekend</span>`;
        }

        return authors.map(a => `<span class="author-badge">${a}</span>`).join('');
    }

    _formatVersions(versionsString) {
        if (!versionsString) return '<span class="badge bg-secondary">Geen versies</span>';
        const versions = versionsString.split(' ').filter(v => v);
        if (versions.length === 0) return '<span class="badge bg-secondary">Geen versies</span>';
        return versions.map((version, i) => `<span class="version-badge" style="animation-delay: ${i * 100}ms">${version}</span>`).join('');
    }

    _formatLoaders(loaders) {
        if (!loaders || loaders.length === 0) return '<span class="badge bg-secondary">Geen loaders</span>';
        return loaders.map(loader => `<span class="loader-badge">${loader}</span>`).join('');
    }

    _getDomainFromUrl(url) {
        try {
            const parsedUrl = new URL(url);
            return parsedUrl.hostname.replace(/^www\./, '');
        } catch (e) {
            return url;
        }
    }

    _truncateUrl(url, maxLength = 30) {
        if (url.length <= maxLength) return url;
        return `${url.substring(0, maxLength)}...`;
    }

    populateVersionFilter(versionsList) {
        let versions = [];
        if (Array.isArray(versionsList) && typeof versionsList[0] === 'string') {
            versions = versionsList;
        } else if (Array.isArray(versionsList)) {
            versions = Array.from(new Set(versionsList.flatMap(p => (p.versions ? p.versions.split(' ') : [])).filter(v => v)));
        }

        const sortedVersions = Array.from(new Set(versions)).sort((a, b) => {
            const aNum = parseFloat(a);
            const bNum = parseFloat(b);
            if (!isNaN(aNum) && !isNaN(bNum)) return bNum - aNum;
            return b.localeCompare(a);
        });

        const currentValue = this.versionFilter.value;
        this.versionFilter.innerHTML = '<option value="">Alle versies</option>';
        sortedVersions.forEach(version => {
            const option = document.createElement('option');
            option.value = version;
            option.textContent = version;
            if (version === currentValue) option.selected = true;
            this.versionFilter.appendChild(option);
        });
    }

    populateLoaderFilter(loadersList) {
        let loaders = [];
        if (Array.isArray(loadersList) && typeof loadersList[0] === 'string') {
            loaders = loadersList;
        } else if (Array.isArray(loadersList)) {
            loaders = Array.from(new Set(loadersList.flatMap(p => p.loaders || []).filter(l => l)));
        }

        const sortedLoaders = Array.from(new Set(loaders)).sort((a, b) => a.localeCompare(b));

        if (this.loaderFilters.children.length === 0) {
            this.loaderFilters.innerHTML = '';
            sortedLoaders.forEach(loader => {
                const div = document.createElement('div');
                div.className = 'form-check form-check-inline';
                div.innerHTML = `
                    <input class="form-check-input loader-filter" id="loader-${loader}" type="checkbox" value="${loader}" checked>
                    <label class="form-check-label" for="loader-${loader}">${loader}</label>
                `;
                this.loaderFilters.appendChild(div);
            });
        }
    }

    buildCategorySidebar(plugins = [], serverCategories = [], serverInfo = {}) {
        const list = this.categorySidebar;
        if (!list) return;

        const activeItem = list.querySelector('.category-item.active');
        const activeCategory = activeItem ? activeItem.dataset.category : '';

        const categoryMap = new Map();

        if (Array.isArray(serverCategories)) {
            serverCategories.forEach(cat => {
                const isObj = typeof cat === 'object' && cat !== null;
                const name = isObj ? cat.name : cat;
                if (name) {
                    categoryMap.set(name, isObj ? cat : { name });
                }
            });
        }

        if (Array.isArray(plugins)) {
            plugins.forEach(p => {
                const cats = p.categories || (p.category ? [p.category] : []) || p.tags || [];
                cats.forEach(cat => {
                    const catName = typeof cat === 'object' && cat !== null ? cat.name : cat;
                    if (catName && !categoryMap.has(catName)) {
                        categoryMap.set(catName, typeof cat === 'object' && cat !== null ? cat : { name: catName });
                    }
                });
            });
        }

        const sortedCategories = Array.from(categoryMap.values()).sort((a, b) =>
            (a.name || '').localeCompare(b.name || '')
        );

        list.innerHTML = `<li class="category-item ${activeCategory === '' ? 'active' : ''}" data-category="">Alles <span class="badge bg-primary rounded-pill ms-auto" title="Totaal aantal plugins op het platform">0 plugins</span></li>`;

        sortedCategories.forEach(cat => {
            const categoryName = cat.name;
            const li = document.createElement('li');
            li.className = `category-item ${activeCategory === categoryName ? 'active' : ''}`;
            li.dataset.category = categoryName;

            const img = document.createElement('img');
            img.className = 'category-icon';
            img.src = (cat.show_image && cat.image_url) ? cat.image_url : 'images/server-icon.png';
            img.onerror = function () {
                this.onerror = function() { this.style.display = 'none'; };
                this.src = 'images/server-icon.png';
            };
            img.alt = '';
            img.width = 32;
            img.height = 32;
            li.appendChild(img);

            const text = document.createElement('span');
            text.textContent = categoryName;
            text.className = 'category-text';
            li.appendChild(text);

            const info = (serverInfo && serverInfo[categoryName]) || {};
            if (info.software || info.version) {
                const serverInfoEl = document.createElement('small');
                serverInfoEl.className = 'server-info';
                serverInfoEl.textContent = `${info.software || ''} ${info.version || ''}`.trim();
                li.appendChild(serverInfoEl);
            }

            const badge = document.createElement('span');
            badge.className = 'badge bg-primary rounded-pill ms-auto';
            badge.textContent = '0 plugins';
            li.appendChild(badge);

            list.appendChild(li);
        });
    }

    updateCategoryCounts(categoryCountsMap, totalAllCount) {
        if (!categoryCountsMap) return;

        let totalAssignments = 0;
        Object.values(categoryCountsMap).forEach(c => totalAssignments += c);

        this.categorySidebar.querySelectorAll('.category-item').forEach(item => {
            const categoryName = item.dataset.category;
            const badge = item.querySelector('.badge');
            if (badge) {
                const num = (categoryName === '')
                    ? (totalAllCount !== undefined ? totalAllCount : totalAssignments)
                    : (categoryCountsMap[categoryName] || 0);
                badge.textContent = `${num} ${num === 1 ? 'plugin' : 'plugins'}`;
                badge.title = categoryName === ''
                    ? `Totaal aantal beschikbare plugins (${num})`
                    : `Aantal plugins in categorie ${categoryName} (${num})`;
            }
        });
    }

    renderPagination(currentPage, totalPages, onPageClick) {
        if (!this.paginationContainer || !this.paginationControls) return;

        this.paginationContainer.style.display = 'flex';

        if (totalPages <= 1) {
            this.paginationControls.innerHTML = `<li class="page-item active"><span class="page-link">1</span></li>`;
            return;
        }

        let html = '';

        // Previous button
        const prevDisabled = currentPage <= 1 ? 'disabled' : '';
        html += `<li class="page-item ${prevDisabled}">
            <button class="page-link" data-page="${currentPage - 1}" aria-label="Vorige">&laquo;</button>
        </li>`;

        // Page numbers
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

        // Next button
        const nextDisabled = currentPage >= totalPages ? 'disabled' : '';
        html += `<li class="page-item ${nextDisabled}">
            <button class="page-link" data-page="${currentPage + 1}" aria-label="Volgende">&raquo;</button>
        </li>`;

        this.paginationControls.innerHTML = html;

        // Attach click listener
        this.paginationControls.querySelectorAll('button.page-link').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const page = parseInt(btn.dataset.page, 10);
                if (page && page !== currentPage && page >= 1 && page <= totalPages) {
                    onPageClick(page);
                }
            });
        });
    }

    updateAuthUI(authData) {
        if (authData.logged_in) {
            this.authButtons.style.setProperty('display', 'none', 'important');
            this.userButtons.style.setProperty('display', 'flex', 'important');
            this.username.textContent = authData.username;
            this.adminBtn.style.display = (authData.role === 'admin' || authData.role === 'co-admin') ? 'inline-block' : 'none';
        } else {
            this.authButtons.style.setProperty('display', 'flex', 'important');
            this.userButtons.style.setProperty('display', 'none', 'important');
        }
    }

    updateResultsCount(pluginsOnCurrentPageCount, totalFilteredCount, totalAllPluginsCount, activeCategory = '') {
        if (!this.resultsCounter) {
            this.resultsCounter = document.createElement('div');
            this.resultsCounter.id = 'resultsCounter';
            this.resultsCounter.className = 'row justify-content-center mb-4';
            this.pluginsContainer.parentNode.insertBefore(this.resultsCounter, this.pluginsContainer);
        }

        const totalAll = totalAllPluginsCount !== undefined ? totalAllPluginsCount : 0;
        const filtered = totalFilteredCount !== undefined ? totalFilteredCount : 0;
        const onPage = pluginsOnCurrentPageCount !== undefined ? pluginsOnCurrentPageCount : 0;

        const colsClass = activeCategory ? 'row-cols-1 row-cols-sm-2 row-cols-lg-4' : 'row-cols-1 row-cols-sm-3';

        let html = `
            <div class="col-lg-10">
                <div class="card counter-bar-card p-3 text-light shadow-sm">
                    <div class="row g-3 ${colsClass}">
                    <div class="col">
                        <div class="counter-badge-item counter-total d-flex align-items-center gap-3">
                            <div class="counter-icon-box">
                                <i class="fas fa-database"></i>
                            </div>
                            <div class="text-start min-w-0">
                                <div class="counter-label text-truncate" data-i18n="counter.total">Totaal op platform</div>
                                <div class="counter-value">${totalAll} <span data-i18n="${totalAll === 1 ? 'common.plugin' : 'common.plugins'}">${totalAll === 1 ? 'plugin' : 'plugins'}</span></div>
                            </div>
                        </div>
                    </div>`;

        if (activeCategory) {
            html += `
                    <div class="col">
                        <div class="counter-badge-item counter-category d-flex align-items-center gap-3">
                            <div class="counter-icon-box">
                                <i class="fas fa-folder"></i>
                            </div>
                            <div class="text-start min-w-0">
                                <div class="counter-label text-truncate" title="${activeCategory}">${activeCategory}</div>
                                <div class="counter-value">${filtered} <span data-i18n="${filtered === 1 ? 'common.plugin' : 'common.plugins'}">${filtered === 1 ? 'plugin' : 'plugins'}</span></div>
                            </div>
                        </div>
                    </div>`;
        }

        html += `
                    <div class="col">
                        <div class="counter-badge-item counter-filtered d-flex align-items-center gap-3">
                            <div class="counter-icon-box">
                                <i class="fas fa-filter"></i>
                            </div>
                            <div class="text-start min-w-0">
                                <div class="counter-label text-truncate" data-i18n="counter.filtered">Gefilterd resultaat</div>
                                <div class="counter-value">${filtered} <span data-i18n="${filtered === 1 ? 'common.plugin' : 'common.plugins'}">${filtered === 1 ? 'plugin' : 'plugins'}</span></div>
                            </div>
                        </div>
                    </div>

                    <div class="col">
                        <div class="counter-badge-item counter-shown d-flex align-items-center gap-3">
                            <div class="counter-icon-box">
                                <i class="fas fa-eye"></i>
                            </div>
                            <div class="text-start min-w-0">
                                <div class="counter-label text-truncate" data-i18n="counter.shown">Getoond op pagina</div>
                                <div class="counter-value">${onPage} <span data-i18n="${onPage === 1 ? 'common.plugin' : 'common.plugins'}">${onPage === 1 ? 'plugin' : 'plugins'}</span></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>`;

        this.resultsCounter.innerHTML = html;
    }

    showSuccessMessage(message) {
        const successAlert = document.createElement("div");
        successAlert.className = "alert alert-success alert-dismissible fade show";
        successAlert.innerHTML = `
            <img src="images/success-icon.png" class="btn-icon" alt="Succes"> ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector(".container-fluid").prepend(successAlert);

        setTimeout(() => successAlert.remove(), 5000);
    }
}

export default new UI();
