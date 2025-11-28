document.addEventListener("DOMContentLoaded", function () {
    // Check auth status on load
    checkAuthStatus();

    // Load plugins on startup
    loadPlugins();

    const addModal = new bootstrap.Modal(
        document.getElementById("addPluginModal")
    );
    const pluginUrlInput = document.getElementById("pluginUrl");
    const fetchButton = document.getElementById("fetchButton");
    const confirmYes = document.getElementById("confirmYes");
    const confirmNo = document.getElementById("confirmNo");
    const errorMessage = document.getElementById("errorMessage");
    const step1 = document.getElementById("step1");
    const step2 = document.getElementById("step2");
    const step3 = document.getElementById("step3");
    const confirmDeleteButton = document.getElementById(
        "confirmDeleteButton"
    );

    // Huidige plugin die wordt verwijderd
    let currentDeleteUrl = "";
    let cachedPluginData = null;

    // Verberg error message bij opstarten
    hideError();

    // Reset modal wanneer hij gesloten wordt
    document
        .getElementById("addPluginModal")
        .addEventListener("hidden.bs.modal", function () {
            step1.style.display = "block";
            step2.style.display = "none";
            step3.style.display = "none";
            hideError();
            pluginUrlInput.value = "";
            cachedPluginData = null;

            // Toon de knoppen weer
            document.getElementById("fetchButton").style.display =
                "inline-block";
            document.querySelector(
                ".modal-footer .btn-secondary"
            ).style.display = "inline-block";

            // Reset Ja-knop
            const confirmYesBtn = document.getElementById("confirmYes");
            confirmYesBtn.innerHTML =
                '<img src="images/confirm-icon.png" class="btn-icon" alt="Ja"> Ja';
            confirmYesBtn.disabled = false;

            // Reset modal backdrop instellingen
            const modalElement = document.getElementById("addPluginModal");
            modalElement.setAttribute("data-bs-backdrop", "true");
            modalElement.setAttribute("data-bs-keyboard", "true");
        });

    // Fetch knop
    fetchButton.addEventListener("click", function () {
        const url = pluginUrlInput.value.trim();
        if (!url) {
            showError("Vul een URL in");
            return;
        }

        // Toon laadanimatie
        step1.style.display = "none";
        step2.style.display = "block";
        step3.style.display = "none";
        hideError();

        // Haal plugin data op van de server
        fetch("/fetch_plugin", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url: url }),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        "Server reageerde met status: " + response.status
                    );
                }
                return response.json();
            })
            .then((plugin) => {
                cachedPluginData = plugin;
                // Verberg laadanimatie
                step2.style.display = "none";

                // Vul de preview met de opgehaalde data
                document.getElementById("previewTitle").textContent =
                    plugin.title || "Geen titel";
                document.getElementById("previewDescription").textContent =
                    plugin.description || "Geen beschrijving beschikbaar";
                document.getElementById("previewAuthor").textContent =
                    plugin.author || "Onbekend";
                // Toon versies als badges
                const versionsContainer =
                    document.getElementById("previewVersions");
                if (plugin.versions) {
                    const versions = plugin.versions.split(" ");
                    let versionBadges = "";
                    let delay = 0;

                    versions.forEach((version) => {
                        versionBadges += `<span class="version-badge" style="animation-delay: ${delay}ms">${version}</span>`;
                        delay += 100;
                    });

                    versionsContainer.innerHTML = versionBadges;
                } else {
                    versionsContainer.innerHTML =
                        '<span class="badge bg-secondary">Geen versies</span>';
                }

                // Toon altijd een afbeelding (plugin icon of placeholder)
                if (plugin.icon) {
                    document.getElementById("previewIcon").src = plugin.icon;
                } else {
                    document.getElementById("previewIcon").src =
                        "images/plugin-placeholder.png";
                }
                document.getElementById("previewIcon").style.display = "block";

                // Toon stap 3 (plugin informatie) en zorg dat deze zichtbaar blijft
                step3.style.display = "block";

                // Verberg de "Ophalen" knop en "Annuleren" knop in de footer
                document.getElementById("fetchButton").style.display = "none";
                document.querySelector(
                    ".modal-footer .btn-secondary"
                ).style.display = "none";

                // Voorkom dat de modal sluit bij klikken buiten de modal
                const modalElement = document.getElementById("addPluginModal");
                const modalInstance = bootstrap.Modal.getInstance(modalElement);

                // Verwijder de standaard click handler van de modal backdrop
                modalElement.removeAttribute("data-bs-backdrop");
                modalElement.setAttribute("data-bs-backdrop", "static");
                modalElement.removeAttribute("data-bs-keyboard");
                modalElement.setAttribute("data-bs-keyboard", "false");
            })
            .catch((error) => {
                console.error("Fout bij ophalen plugin:", error);
                showError("Fout bij ophalen plugin: " + error);
                step2.style.display = "none";
                step1.style.display = "block";
            });
    });

    // Ja-knop
    confirmYes.addEventListener("click", function () {
        // Check if user is logged in
        fetch("/auth-status")
            .then((response) => response.json())
            .then((authData) => {
                if (!authData.logged_in) {
                    showError(
                        "Je moet ingelogd zijn om plugins toe te voegen. Ga naar de login pagina."
                    );
                    return;
                }

                // Toon loading icon in de Ja-knop
                const originalContent = confirmYes.innerHTML;
                confirmYes.innerHTML =
                    '<img src="images/loading-icon.gif" class="loading-icon me-2" alt="Laden"> Toevoegen...';
                confirmYes.disabled = true;

                // Check active category
                const activeCategoryEl = document.querySelector('#categorySidebar .category-item.active');
                if (activeCategoryEl) {
                    const activeCategory = activeCategoryEl.getAttribute('data-category');
                    if (activeCategory && activeCategory !== "") {
                        cachedPluginData.category = activeCategory;
                    }
                }

                // Voeg plugin toe via de server met cached data
                fetch("/add_plugin", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ plugin_data: cachedPluginData }),
                })
                    .then((response) => {
                        if (!response.ok) {
                            throw new Error("Login vereist");
                        }
                        return response.json();
                    })
                    .then((data) => {
                        if (data.success) {
                            // Toon succesbericht
                            const successAlert = document.createElement("div");
                            successAlert.className =
                                "alert alert-success alert-dismissible fade show";
                            successAlert.innerHTML = `
                                    <img src="images/success-icon.png" class="btn-icon" alt="Succes"> Plugin succesvol toegevoegd!
                                    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                                `;
                            document
                                .querySelector(".container-fluid")
                                .prepend(successAlert);

                            // Herlaad plugins
                            loadPlugins();

                            addModal.hide();
                        } else {
                            // Reset knop bij fout
                            confirmYes.innerHTML = originalContent;
                            confirmYes.disabled = false;
                            showError("Fout bij toevoegen: " + data.error);
                        }
                    })
                    .catch((error) => {
                        // Reset knop bij fout
                        confirmYes.innerHTML = originalContent;
                        confirmYes.disabled = false;
                        showError("Fout bij toevoegen: " + error);
                    });
            })
            .catch(() => {
                showError("Je moet ingelogd zijn om plugins toe te voegen.");
            });
    });

    // Nee-knop
    confirmNo.addEventListener("click", function () {
        step3.style.display = "none";
        step1.style.display = "block";
        pluginUrlInput.value = "";
        pluginUrlInput.focus();
    });

    // Verwijderknop functionaliteit
    confirmDeleteButton.addEventListener("click", function () {
        const pluginTitle = document.getElementById(
            "pluginToDeleteTitle"
        ).textContent;
        const deleteModalElement =
            document.getElementById("deleteConfirmModal");
        const deleteModal =
            bootstrap.Modal.getInstance(deleteModalElement) ||
            new bootstrap.Modal(deleteModalElement);

        // Verwijder de plugin via de server
        fetch("/delete_plugin", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ url: currentDeleteUrl }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    // Sluit eerst de modal
                    deleteModal.hide();

                    // Wacht tot modal volledig gesloten is voordat we de plugins herladen
                    deleteModalElement.addEventListener(
                        "hidden.bs.modal",
                        function modalHiddenHandler() {
                            // Verwijder deze event listener om duplicatie te voorkomen
                            deleteModalElement.removeEventListener(
                                "hidden.bs.modal",
                                modalHiddenHandler
                            );

                            // Herlaad alle plugins om de gefilterde lijst bij te werken
                            loadPlugins();

                            // Toon succesbericht
                            const successAlert = document.createElement("div");
                            successAlert.className =
                                "alert alert-success alert-dismissible fade show";
                            successAlert.innerHTML = `
                                <img src="images/success-icon.png" class="btn-icon" alt="Succes"> Plugin "${pluginTitle}" succesvol verwijderd!
                                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
                            `;
                            document
                                .querySelector(".container-fluid")
                                .prepend(successAlert);

                            // Verwijder succesbericht na 5 seconden
                            setTimeout(() => {
                                if (successAlert.parentNode) {
                                    successAlert.remove();
                                }
                            }, 5000);
                        },
                        { once: true }
                    );
                } else {
                    showError("Fout bij verwijderen: " + data.error);
                }
            })
            .catch((error) => {
                showError("Fout bij verwijderen: " + error);
            });
    });

    // Voeg event listener toe voor het herstarten van de animatie wanneer de modal wordt geopend
    document
        .getElementById("deleteConfirmModal")
        .addEventListener("shown.bs.modal", function () {
            const deleteIcon = this.querySelector(".delete-modal-icon");
            if (deleteIcon) {
                // Herstart de animatie door de class tijdelijk te verwijderen en weer toe te voegen
                deleteIcon.style.animation = "none";
                deleteIcon.offsetHeight; // Trigger reflow
                deleteIcon.style.animation = "wiggle 1.2s ease-in-out";
            }
        });

    function showError(message) {
        errorMessage.querySelector("span").textContent = message;
        errorMessage.style.display = "flex";
        errorMessage.classList.add("show");
    }

    function hideError() {
        errorMessage.style.display = "none";
        errorMessage.classList.remove("show");
    }

    // Auth event listeners
    document
        .getElementById("logoutBtn")
        .addEventListener("click", handleLogout);

    // Don't load plugins on startup - wait for auth check

    function checkAuthStatus() {
        fetch("/auth-status")
            .then((response) => response.json())
            .then((data) => {
                if (data.logged_in) {
                    document.getElementById("authButtons").style.display = "none";
                    document.getElementById("userButtons").style.display = "flex";
                    document.getElementById("username").textContent = data.username;
                    if (data.role === "admin" || data.role === "co-admin") {
                        document.getElementById("adminBtn").style.display =
                            "inline-block";
                    }
                } else {
                    document.getElementById("authButtons").style.display = "block";
                    document.getElementById("userButtons").style.display = "none";
                }
            })
            .catch(() => {
                document.getElementById("authButtons").style.display = "block";
                document.getElementById("userButtons").style.display = "none";
            });
    }

    function handleLogout() {
        fetch("/logout", { method: "POST" })
            .then(() => {
                checkAuthStatus();
                window.location.reload();
            })
            .catch(() => checkAuthStatus());
    }

    function loadPlugins() {
        fetch("/auth-status")
            .then((response) => response.json())
            .then((authData) => {
                // Haal alle plugins op voor alle gebruikers
                fetch("/api/plugins/public")
                    .then((response) => response.json())
                    .then((plugins) => {
                        renderPlugins(plugins, authData.logged_in, authData.role);
                    })
                    .catch((error) => {
                        console.error("Fout bij laden plugins:", error);
                        showNoPluginsMessage();
                    });
            })
            .catch(() => {
                // Fallback: toon alle plugins in read-only mode
                fetch("/api/plugins/public")
                    .then((response) => response.json())
                    .then((plugins) => {
                        renderPlugins(plugins, false, "user");
                    })
                    .catch(() => {
                        showNoPluginsMessage();
                    });
            });
    }

    function showNoPluginsMessage() {
        const pluginsContainer = document.getElementById("pluginsContainer");
        pluginsContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-info d-flex align-items-center justify-content-center" role="alert">
                            <img src="images/add-icon.png" class="warning-icon me-2" alt="Geen plugins">
                            Je hebt nog geen plugins toegevoegd. Klik op "Toevoegen" om te beginnen.
                        </div>
                    </div>
                `;
    }

    function showLoginRequiredMessage() {
        const pluginsContainer = document.getElementById("pluginsContainer");
        pluginsContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-warning d-flex align-items-center justify-content-center" role="alert">
                            <img src="images/warning-icon.png" class="warning-icon me-2" alt="Login vereist">
                            <a href="/login-page" class="btn btn-primary ms-2">Inloggen om plugins te bekijken</a>
                        </div>
                    </div>
                `;
    }

    function renderPlugins(plugins, isLoggedIn = false, userRole = "user") {
        const pluginsContainer = document.getElementById("pluginsContainer");
        const currentUser = isLoggedIn
            ? document.getElementById("username").textContent
            : null;

        if (plugins.length === 0) {
            const message = isLoggedIn
                ? "Nog geen plugins beschikbaar."
                : "Nog geen plugins beschikbaar.";
            pluginsContainer.innerHTML = `
                    <div class="col-12 text-center">
                        <div class="alert alert-info d-flex align-items-center justify-content-center" role="alert">
                            <img src="images/add-icon.png" class="warning-icon me-2" alt="Geen plugins">
                            ${message}
                        </div>
                    </div>
                    `;
            return;
        }

        let pluginsHtml = "";
        let animationDelay = 0;

        plugins.forEach((plugin) => {
            const formattedVersions = formatVersions(plugin.versions || "");
            const domain = getDomainFromUrl(plugin.url || "");
            const ownerInfo = plugin.owner
                ? `<small class="text-muted ms-2">door ${plugin.owner}</small>`
                : "";
            const canDelete =
                isLoggedIn &&
                (userRole === "admin" ||
                    userRole === "co-admin" ||
                    plugin.owner === currentUser);
            const firstLetter = (plugin.title || "P")[0].toUpperCase();
            const iconHtml = plugin.icon
                ? `<img src="${plugin.icon}" alt="${plugin.title} icon" class="plugin-icon me-3" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="plugin-icon-letter me-3" style="display:none;">${firstLetter}</div>`
                : `<div class="plugin-icon-letter me-3">${firstLetter}</div>`;

            pluginsHtml += `
                    <div class="col-12 mb-4">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <div class="d-flex align-items-center">
                                    ${iconHtml}
                                    <div>
                                        <h5 class="card-title mb-0">${plugin.title || "Geen titel"
                }${ownerInfo}</h5>
                                    </div>
                                </div>
                                <div>
                                    <span class="domain-badge">${domain}</span>
                                    ${canDelete
                    ? `<button class="btn btn-delete ms-2 delete-btn" data-url="${plugin.url}" data-title="${plugin.title}">
                                        <img src="images/delete-icon.png" class="btn-icon" alt="Verwijderen">
                                    </button>`
                    : ""
                }
                                </div>
                            </div>
                            <div class="card-body">
                                <p class="card-text description">${plugin.description ||
                "Geen beschrijving beschikbaar"
                }</p>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <div class="plugin-info">
                                            <strong><img src="images/author-icon.png" class="info-icon" alt="Auteur"> Auteur:</strong>
                                            <span class="author-badge">${plugin.author || "Onbekend"
                }</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="versions-section">
                                    <strong><img src="images/version-icon.png" class="info-icon" alt="Versies"> Ondersteunde Versies:</strong>
                                    <div class="versions-container">
                                        ${formattedVersions}
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer bg-transparent">
                                <div class="d-flex justify-content-between align-items-center">
                                    <a href="${plugin.url || "#"
                }" class="btn btn-primary" target="_blank">
                                        <img src="images/external-link-icon.png" class="btn-icon" alt="Externe link">
                                        Bekijk Plugin
                                    </a>
                                    <div class="url-container">
                                        <small class="text-muted plugin-url" title="${plugin.url || ""
                }">
                                            <img src="images/link-icon.png" class="footer-icon" alt="URL">
                                            ${truncateUrl(plugin.url || "")}
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
        });

        pluginsContainer.innerHTML = pluginsHtml;

        // Voeg event listeners toe aan verwijderknoppen
        document.querySelectorAll(".delete-btn").forEach((button) => {
            button.addEventListener("click", function () {
                const url = this.getAttribute("data-url");
                const title = this.getAttribute("data-title");

                document.getElementById("pluginToDeleteTitle").textContent =
                    title;
                currentDeleteUrl = url;

                const deleteModal = new bootstrap.Modal(
                    document.getElementById("deleteConfirmModal")
                );
                deleteModal.show();
            });
        });
    }

    function formatVersions(versionsString) {
        if (!versionsString) {
            return '<span class="badge bg-secondary">Geen versies</span>';
        }

        const versions = versionsString.split(" ");

        if (versions.length === 0) {
            return '<span class="badge bg-secondary">Geen versies</span>';
        }

        let versionBadges = "";
        let delay = 0;

        versions.forEach((version) => {
            versionBadges += `<span class="version-badge" style="animation-delay: ${delay}ms">${version}</span>`;
            delay += 100;
        });

        return versionBadges;
    }

    function getDomainFromUrl(url) {
        try {
            const parsedUrl = new URL(url);
            let domain = parsedUrl.hostname;
            if (domain.startsWith("www.")) {
                domain = domain.substring(4);
            }
            return domain;
        } catch (e) {
            return url;
        }
    }

    function truncateUrl(url, maxLength = 30) {
        if (url.length <= maxLength) return url;
        return url.substring(0, maxLength) + "...";
    }

    // Filter en Zoek Functionaliteit
    let allPlugins = [];
    let filteredPlugins = [];

    // Overschrijf de renderPlugins functie om filtering te ondersteunen
    const originalRenderPlugins = renderPlugins;
    renderPlugins = function (
        plugins,
        isLoggedIn = false,
        userRole = "user"
    ) {
        allPlugins = plugins;
        filteredPlugins = plugins;
        populateVersionFilter(plugins);
        populateCategorySidebar(plugins);
        originalRenderPlugins(plugins, isLoggedIn, userRole);
        setupFilterEventListeners(isLoggedIn, userRole);
        setupCategoryListeners(isLoggedIn, userRole);
    };

    function populateVersionFilter(plugins) {
        const versionFilter = document.getElementById("versionFilter");
        const allVersions = new Set();

        plugins.forEach((plugin) => {
            if (plugin.versions) {
                const versions = plugin.versions.split(" ");
                versions.forEach((version) => allVersions.add(version.trim()));
            }
        });

        // Sorteer versies
        const sortedVersions = Array.from(allVersions).sort((a, b) => {
            // Probeer numeriek te sorteren
            const aNum = parseFloat(a);
            const bNum = parseFloat(b);
            if (!isNaN(aNum) && !isNaN(bNum)) {
                return bNum - aNum; // Nieuwste eerst
            }
            return b.localeCompare(a); // Alfabetisch
        });

        // Vul dropdown
        versionFilter.innerHTML = '<option value="">Alle versies</option>';
        sortedVersions.forEach((version) => {
            const option = document.createElement("option");
            option.value = version;
            option.textContent = version;
            versionFilter.appendChild(option);
        });
    }

    // Populate categories sidebar based on plugin data
    function populateCategorySidebar(plugins) {
        const list = document.getElementById("categorySidebar");
        if (!list) return;

        // Prefer server_categories.json if available (loaded into window.serverCategoriesList)
        if (window.serverCategoriesList && Array.isArray(window.serverCategoriesList) && window.serverCategoriesList.length > 0) {
            // Reset list (keep 'Alles' as first)
            list.innerHTML = '<li class="category-item active" data-category="">Alles</li>';
            window.serverCategoriesList.forEach((cat) => {
                const li = document.createElement('li');
                li.className = 'category-item';
                li.setAttribute('data-category', cat);
                li.textContent = cat;
                list.appendChild(li);
            });
            return;
        }

        const categories = new Map();

        plugins.forEach((plugin) => {
            // Try common fields for categories: categories (array), category (string), tags
            if (plugin.categories && Array.isArray(plugin.categories)) {
                plugin.categories.forEach((c) => {
                    if (c && c.toString().trim()) categories.set(c.toString().trim(), true);
                });
            } else if (plugin.category && plugin.category.toString().trim()) {
                categories.set(plugin.category.toString().trim(), true);
            } else if (plugin.tags && Array.isArray(plugin.tags)) {
                plugin.tags.forEach((t) => {
                    if (t && t.toString().trim()) categories.set(t.toString().trim(), true);
                });
            }
        });

        // Convert to array and sort
        const sorted = Array.from(categories.keys()).sort((a, b) => a.localeCompare(b, undefined, { sensitivity: 'base' }));

        // Reset list (keep 'Alles' as first)
        list.innerHTML = '<li class="category-item active" data-category="">Alles</li>';

        // If no categories found from plugins, fall back to defaults
        const finalCategories = (sorted && sorted.length) ? sorted : (DEFAULT_SERVER_CATEGORIES || []);

        finalCategories.forEach((cat) => {
            const li = document.createElement('li');
            li.className = 'category-item';
            li.setAttribute('data-category', cat);

            // Create icon image for category
            const img = document.createElement('img');
            img.className = 'category-icon';
            // slugify category name for filename
            const slug = cat.toString().toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '');
            img.src = `images/category-${slug}.svg`;
            // fallback to default icon when not found
            img.onerror = function () { this.onerror = null; this.src = 'images/category-default.svg'; };
            img.alt = cat + ' icon';
            img.width = 32;
            img.height = 32;

            const text = document.createElement('span');
            text.textContent = cat;
            text.className = 'category-text';

            li.appendChild(img);
            li.appendChild(text);
            list.appendChild(li);
        });
    }

    // Try to load categories dynamically from backend API first, then static JSON as fallback
    function loadServerCategoriesConfig() {
        // First try dynamic API endpoint
        fetch('/api/server_categories')
            .then((res) => {
                if (!res.ok) throw new Error('No API categories');
                return res.json();
            })
            .then((data) => {
                if (Array.isArray(data) && data.length) {
                    window.serverCategoriesList = data;
                    if (allPlugins && allPlugins.length) {
                        populateCategorySidebar(allPlugins);
                        setupCategoryListeners();
                    }
                }
            })
            .catch(() => {
                // If API fails, try static JSON fallback
                fetch('/server_categories.json')
                    .then((res) => {
                        if (!res.ok) throw new Error('No static categories');
                        return res.json();
                    })
                    .then((data) => {
                        if (Array.isArray(data) && data.length) {
                            window.serverCategoriesList = data;
                            if (allPlugins && allPlugins.length) {
                                populateCategorySidebar(allPlugins);
                                setupCategoryListeners();
                            }
                        }
                    })
                    .catch(() => {
                        // silent fallback to plugin-derived categories
                        window.serverCategoriesList = null;
                    });
            });
    }

    // load config immediately (non-blocking)
    loadServerCategoriesConfig();

    // Default fallback categories (used if API/static/plugin-derived categories are empty)
    const DEFAULT_SERVER_CATEGORIES = [
        'Survival',
        'Creative',
        'PvP',
        'Economy',
        'Minigames',
        'Roleplay',
        'Adventure',
        'Hubs'
    ];

    function setupCategoryListeners(isLoggedIn = false, userRole = 'user') {
        const list = document.getElementById('categorySidebar');
        if (!list) return;

        list.querySelectorAll('.category-item').forEach((el) => {
            el.addEventListener('click', function () {
                // Toggle active class
                list.querySelectorAll('.category-item').forEach((it) => it.classList.remove('active'));
                this.classList.add('active');

                // Re-apply filters using existing UI state
                applyFilters(isLoggedIn, userRole);
            });
        });
    }

    function setupFilterEventListeners(
        isLoggedIn = false,
        userRole = "user"
    ) {
        const searchInput = document.getElementById("searchInput");
        const versionFilter = document.getElementById("versionFilter");
        const loaderFilter = document.getElementById("loaderFilter");
        const platformFilters = document.querySelectorAll(".platform-filter");
        const resetButton = document.getElementById("resetFilters");

        const filterHandler = debounce(() => applyFilters(isLoggedIn, userRole), 300);

        searchInput.addEventListener("input", filterHandler);
        versionFilter.addEventListener("change", filterHandler);
        loaderFilter.addEventListener("change", filterHandler);
        platformFilters.forEach((filter) => {
            filter.addEventListener("change", filterHandler);
        });
        resetButton.addEventListener("click", () => resetFilters(isLoggedIn, userRole));
    }

    function applyFilters(isLoggedIn = false, userRole = "user") {
        const searchTerm = document.getElementById("searchInput").value.toLowerCase().trim();
        const selectedLoader = document.getElementById("loaderFilter").value;
        const selectedVersion = document.getElementById("versionFilter").value;
        const selectedPlatforms = Array.from(document.querySelectorAll(".platform-filter:checked")).map(cb => cb.value);
        const selectedCategoryEl = document.querySelector('#categorySidebar .category-item.active');
        const selectedCategory = selectedCategoryEl ? selectedCategoryEl.getAttribute('data-category') : '';

        filteredPlugins = allPlugins.filter((plugin) => {
            const matchesSearch = !searchTerm ||
                (plugin.title && plugin.title.toLowerCase().includes(searchTerm)) ||
                (plugin.description && plugin.description.toLowerCase().includes(searchTerm)) ||
                (plugin.author && plugin.author.toLowerCase().includes(searchTerm));
            const matchesVersion = !selectedVersion || (plugin.versions && plugin.versions.includes(selectedVersion));
            const matchesLoader = !selectedLoader || (plugin.loaders && plugin.loaders.toLowerCase().includes(selectedLoader.toLowerCase()));
            const pluginPlatform = getPlatformFromUrl(plugin.url);
            const matchesPlatform = selectedPlatforms.length === 0 || selectedPlatforms.includes(pluginPlatform);
            let pluginCategories = [];
            if (plugin.categories && Array.isArray(plugin.categories)) pluginCategories = plugin.categories.map(c => c.toString());
            else if (plugin.category) pluginCategories = [plugin.category.toString()];
            else if (plugin.tags && Array.isArray(plugin.tags)) pluginCategories = plugin.tags.map(t => t.toString());
            const matchesCategory = !selectedCategory || pluginCategories.some(pc => pc && pc.toLowerCase() === selectedCategory.toLowerCase());

            return matchesSearch && matchesVersion && matchesPlatform && matchesCategory && matchesLoader;
        });

        renderFilteredPlugins(isLoggedIn, userRole);
        updateResultsCount();
    }

    function getPlatformFromUrl(url) {
        if (!url) return "unknown";
        if (url.includes("hangar.papermc.io")) return "hangar";
        if (url.includes("spigotmc.org")) return "spigot";
        if (url.includes("modrinth.com")) return "modrinth";
        if (url.includes("curseforge.com")) return "curseforge";
        return "unknown";
    }

    function renderFilteredPlugins(isLoggedIn = false, userRole = "user") {
        const pluginsContainer = document.getElementById("pluginsContainer");
        const currentUser = isLoggedIn
            ? document.getElementById("username").textContent
            : null;

        if (filteredPlugins.length === 0) {
            pluginsContainer.innerHTML = `
                        <div class="col-12 text-center">
                            <div class="alert alert-info d-flex align-items-center justify-content-center" role="alert">
                                <img src="images/fetch-icon.png" class="warning-icon me-2" alt="Geen resultaten">
                                Geen plugins voldoen aan de filters.
                            </div>
                        </div>
                    `;
            return;
        }

        let pluginsHtml = "";
        let animationDelay = 0;

        filteredPlugins.forEach((plugin) => {
            const formattedVersions = formatVersions(plugin.versions || "");
            const domain = getDomainFromUrl(plugin.url || "");
            const ownerInfo = plugin.owner
                ? `<small class="text-muted ms-2">door ${plugin.owner}</small>`
                : "";
            const canDelete =
                isLoggedIn &&
                (userRole === "admin" ||
                    userRole === "co-admin" ||
                    plugin.owner === currentUser);
            const firstLetter = (plugin.title || "P")[0].toUpperCase();
            const iconHtml = plugin.icon
                ? `<img src="${plugin.icon}" alt="${plugin.title} icon" class="plugin-icon me-3" onerror="this.style.display='none';this.nextElementSibling.style.display='flex';"><div class="plugin-icon-letter me-3" style="display:none;">${firstLetter}</div>`
                : `<div class="plugin-icon-letter me-3">${firstLetter}</div>`;

            pluginsHtml += `
                    <div class="col-12 mb-4 plugin-card" style="animation: fadeIn 0.6s ease-out ${animationDelay}ms both;">
                        <div class="card h-100 shadow-sm">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <div class="d-flex align-items-center">
                                    ${iconHtml}
                                    <div>
                                        <h5 class="card-title mb-0">${plugin.title || "Geen titel"
                }${ownerInfo}</h5>
                                    </div>
                                </div>
                                <div>
                                    <span class="domain-badge">${domain}</span>
                                    ${canDelete
                    ? `<button class="btn btn-delete ms-2 delete-btn" data-url="${plugin.url}" data-title="${plugin.title}">
                                        <img src="images/delete-icon.png" class="btn-icon" alt="Verwijderen">
                                    </button>`
                    : ""
                }
                                </div>
                            </div>
                            <div class="card-body">
                                <p class="card-text description">${plugin.description ||
                "Geen beschrijving beschikbaar"
                }</p>
                                
                                <div class="row mb-3">
                                    <div class="col-md-6">
                                        <div class="plugin-info">
                                            <strong><img src="images/author-icon.png" class="info-icon" alt="Auteur"> Auteur:</strong>
                                            <span class="author-badge">${plugin.author || "Onbekend"
                }</span>
                                        </div>
                                    </div>
                                </div>
                                
                                <div class="versions-section">
                                    <strong><img src="images/version-icon.png" class="info-icon" alt="Versies"> Ondersteunde Versies:</strong>
                                    <div class="versions-container">
                                        ${formattedVersions}
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer bg-transparent">
                                <div class="d-flex justify-content-between align-items-center">
                                    <a href="${plugin.url || "#"
                }" class="btn btn-primary" target="_blank">
                                        <img src="images/external-link-icon.png" class="btn-icon" alt="Externe link">
                                        Bekijk Plugin
                                    </a>
                                    <div class="url-container">
                                        <small class="text-muted plugin-url" title="${plugin.url || ""
                }">
                                            <img src="images/link-icon.png" class="footer-icon" alt="URL">
                                            ${truncateUrl(plugin.url || "")}
                                        </small>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    `;
            animationDelay += 100;
        });

        pluginsContainer.innerHTML = pluginsHtml;

        // Voeg event listeners toe aan verwijderknoppen
        document.querySelectorAll(".delete-btn").forEach((button) => {
            button.addEventListener("click", function () {
                const url = this.getAttribute("data-url");
                const title = this.getAttribute("data-title");

                document.getElementById("pluginToDeleteTitle").textContent =
                    title;
                currentDeleteUrl = url;

                const deleteModal = new bootstrap.Modal(
                    document.getElementById("deleteConfirmModal")
                );
                deleteModal.show();
            });
        });
    }

    function updateResultsCount() {
        // Voeg een resultaten teller toe als die nog niet bestaat
        let resultsCounter = document.getElementById("resultsCounter");
        if (!resultsCounter) {
            resultsCounter = document.createElement("div");
            resultsCounter.id = "resultsCounter";
            resultsCounter.className = "text-center mb-3 text-muted";
            const pluginsContainer =
                document.getElementById("pluginsContainer");
            pluginsContainer.parentNode.insertBefore(
                resultsCounter,
                pluginsContainer
            );
        }

        const total = allPlugins.length;
        const filtered = filteredPlugins.length;

        if (total === filtered) {
            resultsCounter.innerHTML = `<small>Alle ${total} plugins worden weergegeven</small>`;
        } else {
            resultsCounter.innerHTML = `<small>${filtered} van ${total} plugins gevonden</small>`;
        }
    }

    function resetFilters(isLoggedIn = false, userRole = "user") {
        document.getElementById("searchInput").value = "";
        document.getElementById("versionFilter").value = "";
        document.getElementById("loaderFilter").value = "";
        document
            .querySelectorAll(".platform-filter")
            .forEach((cb) => (cb.checked = true));

        // Herlaad de originele lijst met plugins
        filteredPlugins = allPlugins;
        renderFilteredPlugins(isLoggedIn, userRole);
        updateResultsCount();

        // Animatie voor reset knop
        const resetBtn = document.getElementById("resetFilters");
        resetBtn.style.transform = "scale(0.95)";
        setTimeout(() => {
            resetBtn.style.transform = "scale(1)";
        }, 150);
    }

    // Debounce functie voor zoeken
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
});
// Set the current year dynamically in the footer
document.addEventListener("DOMContentLoaded", function () {
    const currentYear = new Date().getFullYear();
    document.getElementById("currentYear").textContent = currentYear;
});