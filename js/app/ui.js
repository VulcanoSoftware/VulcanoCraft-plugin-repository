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
        const domain = this._getDomainFromUrl(plugin.url || '');
        const ownerInfo = plugin.owner ? `<small class="text-muted ms-2">door ${plugin.owner}</small>` : '';
        const canDelete = logged_in && (role === 'admin' || role === 'co-admin' || plugin.owner === currentUser);
        const firstLetter = (plugin.title || 'P')[0].toUpperCase();
        const iconHtml = plugin.icon
            ? `<img src="${plugin.icon}" alt="${plugin.title} icon" class="plugin-icon me-3" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="plugin-icon-letter me-3" style="display:none;">${firstLetter}</div>`
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
                                <button class="btn btn-delete ms-2 delete-btn" data-url="${plugin.url}" data-title="${plugin.title}">
                                    <img src="images/delete-icon.png" class="btn-icon" alt="Verwijderen">
                                </button>` : ''
                            }
                        </div>
                    </div>
                    <div class="card-body">
                        <p class="card-text description">${plugin.description || 'Geen beschrijving beschikbaar'}</p>
                        <div class="row mb-3">
                            <div class="col-md-6">
                                <div class="plugin-info">
                                    <strong><img src="images/author-icon.png" class="info-icon" alt="Auteur"> Auteur:</strong>
                                    <span class="author-badge">${plugin.author || 'Onbekend'}</span>
                                </div>
                            </div>
                        </div>
                        <div class="versions-section">
                            <strong><img src="images/version-icon.png" class="info-icon" alt="Versies"> Ondersteunde Versies:</strong>
                            <div class="versions-container">${formattedVersions}</div>
                        </div>
                        <div class="loaders-section mt-3">
                            <strong><img src="images/plugin-repo-icon.png" class="info-icon" alt="Loaders"> Ondersteunde Loaders:</strong>
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

    populateVersionFilter(plugins) {
        const allVersions = new Set(
            plugins.flatMap(p => (p.versions ? p.versions.split(' ') : [])).filter(v => v)
        );
        const sortedVersions = Array.from(allVersions).sort((a, b) => {
            const aNum = parseFloat(a);
            const bNum = parseFloat(b);
            if (!isNaN(aNum) && !isNaN(bNum)) return bNum - aNum;
            return b.localeCompare(a);
        });

        this.versionFilter.innerHTML = '<option value="">Alle versies</option>';
        sortedVersions.forEach(version => {
            const option = document.createElement('option');
            option.value = version;
            option.textContent = version;
            this.versionFilter.appendChild(option);
        });
    }

    populateLoaderFilter(plugins) {
        const allLoaders = new Set(
            plugins.flatMap(p => p.loaders || []).filter(l => l)
        );
        const sortedLoaders = Array.from(allLoaders).sort((a, b) => a.localeCompare(b));

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

    buildCategorySidebar(plugins, serverCategories, serverInfo) {
        const list = this.categorySidebar;
        if (!list) return;

        let finalCategories = [];
        if (serverCategories && serverCategories.length) {
            finalCategories = serverCategories;
        } else {
            const categories = new Set(
                 plugins.flatMap(p => p.categories || [p.category] || p.tags || []).filter(c => c)
            );
            finalCategories = Array.from(categories).sort((a, b) => a.localeCompare(b));
        }

        list.innerHTML = '<li class="category-item active" data-category="">Alles <span class="badge bg-primary rounded-pill ms-auto">0</span></li>';

        finalCategories.forEach(cat => {
            const isObject = typeof cat === 'object' && cat !== null;
            const categoryName = isObject ? cat.name : cat;
            if (!categoryName) return;

            const li = document.createElement('li');
            li.className = 'category-item';
            li.dataset.category = categoryName;

            if (isObject && cat.show_image && cat.image_url) {
                li.innerHTML += `<img class="category-icon" src="${cat.image_url}" alt="${categoryName} icon" width="32" height="32" onerror="this.style.display='none';">`;
            }

            li.innerHTML += `<span class="category-text">${categoryName}</span>`;

            const info = serverInfo[categoryName] || {};
            if (info.software || info.version) {
                li.innerHTML += `<small class="server-info">${info.software || ''} ${info.version || ''}</small>`;
            }

            li.innerHTML += '<span class="badge bg-primary rounded-pill ms-auto">0</span>';
            list.appendChild(li);
        });
    }

    updateCategoryCounts(allPlugins) {
        const categoryCounts = {};
        this.categorySidebar.querySelectorAll('.category-item').forEach(item => {
            const categoryName = item.dataset.category;
            if (categoryName) categoryCounts[categoryName] = 0;
        });

        allPlugins.forEach(plugin => {
            const pluginCategories = new Set(plugin.categories || [plugin.category] || plugin.tags || []);
            pluginCategories.forEach(cat => {
                if (cat in categoryCounts) categoryCounts[cat]++;
            });
        });

        this.categorySidebar.querySelectorAll('.category-item').forEach(item => {
            const categoryName = item.dataset.category;
            const badge = item.querySelector('.badge');
            if (badge) {
                if (categoryName === '') {
                    badge.textContent = allPlugins.length;
                } else {
                    badge.textContent = categoryCounts[categoryName] || 0;
                }
            }
        });
    }

    updateAuthUI(authData) {
        if (authData.logged_in) {
            this.authButtons.classList.add('hidden');
            this.userButtons.classList.remove('hidden');
            this.username.textContent = authData.username;
            this.adminBtn.classList.toggle('hidden', !(authData.role === 'admin' || authData.role === 'co-admin'));
        } else {
            this.authButtons.classList.remove('hidden');
            this.userButtons.classList.add('hidden');
        }
    }

    updateResultsCount(filteredCount, totalCount) {
        if (!this.resultsCounter) {
            this.resultsCounter = document.createElement('div');
            this.resultsCounter.id = 'resultsCounter';
            this.resultsCounter.className = 'text-center mb-3 text-muted';
            this.pluginsContainer.parentNode.insertBefore(this.resultsCounter, this.pluginsContainer);
        }

        this.resultsCounter.innerHTML = (totalCount === filteredCount)
            ? `<small>Alle ${totalCount} plugins worden weergegeven</small>`
            : `<small>${filteredCount} van ${totalCount} plugins gevonden</small>`;
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
