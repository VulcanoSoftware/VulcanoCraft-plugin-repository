let currentRole = null;

document.addEventListener("DOMContentLoaded", function () {
    checkAdminSession();
    document
        .getElementById("adminLoginForm")
        .addEventListener("submit", function (e) {
            e.preventDefault();
            adminLogin();
        });
});

function checkAdminSession() {
    fetch("/admin/check-session")
        .then((response) => response.json())
        .then((data) => {
            if (data.logged_in) {
                currentRole = data.role;
                showAdminPanel();
            }
        });
}

function adminLogin() {
    const username = document.getElementById("adminUsername").value;
    const password = document.getElementById("adminPassword").value;

    fetch("/admin/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                currentRole = data.role;
                showAdminPanel();
            } else {
                showLoginError(data.error);
            }
        })
        .catch(() => showLoginError("Login failed"));
}

function showAdminPanel() {
    document.getElementById("loginForm").style.display = "none";
    document.getElementById("adminPanel").style.display = "block";
    document.getElementById("adminRole").textContent =
        currentRole.toUpperCase();
    loadSettings();
    loadUsers();
    loadCategories();
    loadPlugins();
    setupEventListeners();
}

function logout() {
    fetch("/admin/logout", { method: "POST" }).then(() => {
        document.getElementById("loginForm").style.display = "block";
        document.getElementById("adminPanel").style.display = "none";
        document.getElementById("adminUsername").value = "";
        document.getElementById("adminPassword").value = "";
    });
}

function showLoginError(message) {
    const errorDiv = document.getElementById("loginError");
    errorDiv.textContent = message;
    errorDiv.style.display = "block";
}

function setupEventListeners() {
    document
        .getElementById("registrationToggle")
        .addEventListener("change", function () {
            const enabled = this.checked;
            fetch("/admin/settings", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ registration_enabled: enabled }),
            })
                .then((response) => response.json())
                .then((data) => {
                    if (!data.success) {
                        alert("Fout bij opslaan instellingen");
                        this.checked = !enabled;
                    }
                });
        });
}

function loadSettings() {
    fetch("/admin/settings")
        .then((response) => response.json())
        .then((data) => {
            document.getElementById("registrationToggle").checked =
                data.registration_enabled;
        });
}

function loadUsers() {
    fetch("/admin/users")
        .then((response) => response.json())
        .then((users) => {
            const grid = document.getElementById("usersGrid");
            grid.innerHTML = users
                .map(
                    (user) => `
                        <div class="col-md-4 col-lg-3 mb-3">
                            <div class="card h-100">
                                <div class="card-body text-center">
                                    <div class="mb-3">
                                        <i class="fas fa-user-circle" style="font-size: 3rem; color: #6c757d;"></i>
                                    </div>
                                    <h6 class="card-title">${user.username}</h6>
                                    <div class="mb-3">
                                        <span class="badge ${getRoleBadgeClass(
                        user.role
                    )}">${user.role}</span>
                                    </div>
                                    <div class="mb-3">
                                        <span class="badge bg-primary">
                                            <i class="fas fa-puzzle-piece me-1"></i>${user.plugin_count
                        } plugins
                                        </span>
                                    </div>
                                    ${currentRole === "admin" &&
                            user.username !== "admin"
                            ? `
                                        <select class="form-select form-select-sm mb-2" onchange="changeRole('${user.username
                            }', this.value)">
                                            <option value="user" ${user.role === "user"
                                ? "selected"
                                : ""
                            }>User</option>
                                            <option value="co-admin" ${user.role === "co-admin"
                                ? "selected"
                                : ""
                            }>Co-Admin</option>
                                            <option value="admin" ${user.role === "admin"
                                ? "selected"
                                : ""
                            }>Admin</option>
                                        </select>
                                        <button class="btn btn-danger btn-sm" onclick="deleteUser('${user.username
                            }')">
                                            <i class="fas fa-trash me-1"></i>Verwijderen
                                        </button>
                                    `
                            : ""
                        }
                                </div>
                            </div>
                        </div>
                    `
                )
                .join("");
        });
}

function loadCategories() {
    fetch("/admin/categories")
        .then((response) => response.json())
        .then((categories) => {
            const grid = document.getElementById("categoriesGrid");
            grid.innerHTML = categories.map((category) => {
                const safeCatName = category.name.replace(/'/g, "\\'");
                return `
                    <div class="col-lg-6 mb-4">
                        <div class="card h-100">
                            <div class="card-body">
                                <div class="d-flex justify-content-between align-items-center mb-3">
                                    <h5 class="card-title mb-0">${category.name}</h5>
                                    <button class="btn btn-danger btn-sm" onclick="deleteCategory('${safeCatName}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-2">
                                        <label for="cat-name-${category.name}" class="form-label-sm">Naam</label>
                                        <input type="text" class="form-control form-control-sm" value="${category.name}" id="cat-name-${category.name}" onchange="updateCategory('${safeCatName}')">
                                    </div>
                                    <div class="col-md-6 mb-2">
                                        <label for="cat-image-${category.name}" class="form-label-sm">Afbeelding URL</label>
                                        <input type="text" class="form-control form-control-sm" value="${category.image_url || ''}" id="cat-image-${category.name}" onchange="updateCategory('${safeCatName}')">
                                    </div>
                                </div>
                                <div class="row">
                                    <div class="col-md-6 mb-2">
                                        <label for="cat-software-${category.name}" class="form-label-sm">Software</label>
                                        <input type="text" class="form-control form-control-sm" value="${category.software || ''}" id="cat-software-${category.name}" onchange="updateCategory('${safeCatName}')">
                                    </div>
                                    <div class="col-md-6 mb-2">
                                        <label for="cat-version-${category.name}" class="form-label-sm">Versie</label>
                                        <input type="text" class="form-control form-control-sm" value="${category.version || ''}" id="cat-version-${category.name}" onchange="updateCategory('${safeCatName}')">
                                    </div>
                                </div>
                                <div class="form-check form-switch mt-2">
                                    <input class="form-check-input" type="checkbox" id="cat-show-${category.name}" ${category.show_image ? 'checked' : ''} onchange="updateCategory('${safeCatName}')">
                                    <label class="form-check-label" for="cat-show-${category.name}">Afbeelding tonen</label>
                                </div>
                            </div>
                        </div>
                    </div>
                `
            }).join("");
        });
}

function addCategory() {
    const name = document.getElementById("newCategoryName").value.trim();
    if (!name) return;

    fetch("/admin/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                document.getElementById("newCategoryName").value = "";
                loadCategories();
                loadPlugins(); // Refresh dropdowns
            } else {
                alert("Fout bij toevoegen categorie: " + data.error);
            }
        });
}

function updateCategory(oldName) {
    const newName = document.getElementById(`cat-name-${oldName}`).value.trim();
    const imageUrl = document.getElementById(`cat-image-${oldName}`).value.trim();
    const showImage = document.getElementById(`cat-show-${oldName}`).checked;
    const software = document.getElementById(`cat-software-${oldName}`).value.trim();
    const version = document.getElementById(`cat-version-${oldName}`).value.trim();

    if (!newName) {
        alert("Categorie naam mag niet leeg zijn.");
        loadCategories(); // revert
        return;
    }

    const body = {
        new_name: newName,
        image_url: imageUrl,
        show_image: showImage,
        software: software,
        version: version,
    };

    fetch(`/admin/categories/${oldName}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                loadCategories();
                loadPlugins();
            } else {
                alert("Fout bij bijwerken categorie: " + data.error);
            }
        });
}

function deleteCategory(name) {
    if (!confirm(`Weet je zeker dat je categorie "${name}" wilt verwijderen?`)) return;

    fetch(`/admin/categories/${name}`, {
        method: "DELETE",
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                loadCategories();
                loadPlugins(); // Refresh dropdowns
            } else {
                alert("Fout bij verwijderen categorie: " + data.error);
            }
        });
}

function loadPlugins() {
    // Need categories for the dropdown
    Promise.all([
        fetch("/admin/plugins").then((r) => r.json()),
        fetch("/admin/categories").then((r) => r.json())
    ]).then(([plugins, categories]) => {
            const grid = document.getElementById("pluginsGrid");
            grid.innerHTML = plugins
                .map((plugin) => {
                    const categoryOptions = categories.map(cat =>
                        `<option value="${cat.name}" ${plugin.category === cat.name ? 'selected' : ''}>${cat.name}</option>`
                    ).join('');

                    return `
                        <div class="col-md-6 mb-3">
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex align-items-center mb-2">
                                        <img src="${plugin.icon ||
                        "/images/plugin-placeholder.png"
                        }" style="width: 40px; height: 40px; margin-right: 10px;" alt="icon">
                                        <div style="flex-grow: 1;">
                                            <input type="text" class="form-control form-control-sm mb-1" value="${plugin.title}" id="pluginTitle-${plugin.url.replace(/[^a-zA-Z0-9]/g, '_')}" onchange="updatePluginDetails('${plugin.url}', '${plugin.url.replace(/[^a-zA-Z0-9]/g, '_')}')">
                                            <input type="text" class="form-control form-control-sm mb-1" value="${plugin.author || 'Onbekend'}" id="pluginAuthor-${plugin.url.replace(/[^a-zA-Z0-9]/g, '_')}" onchange="updatePluginDetails('${plugin.url}', '${plugin.url.replace(/[^a-zA-Z0-9]/g, '_')}')">
                                            <select class="form-select form-select-sm" id="pluginCategory-${plugin.url.replace(/[^a-zA-Z0-9]/g, '_')}" onchange="updatePluginDetails('${plugin.url}', '${plugin.url.replace(/[^a-zA-Z0-9]/g, '_')}')">
                                                <option value="">Geen categorie</option>
                                                ${categoryOptions}
                                            </select>
                                        </div>
                                    </div>
                                    <button class="btn btn-danger btn-sm" onclick="deletePlugin('${plugin.url
                        }', '${plugin.title}')">
                                        <i class="fas fa-trash me-1"></i>Verwijderen
                                    </button>
                                </div>
                            </div>
                        </div>
                    `;
                })
                .join("");
        });
}

function getRoleBadgeClass(role) {
    if (role === "admin") return "bg-danger";
    if (role === "co-admin") return "bg-warning";
    return "bg-secondary";
}

function changeRole(username, newRole) {
    fetch(`/admin/users/${username}/role`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ role: newRole }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                loadUsers();
            } else {
                alert("Fout bij wijzigen rol");
            }
        });
}

function deleteUser(username) {
    if (
        confirm(
            `Weet je zeker dat je gebruiker "${username}" wilt verwijderen?`
        )
    ) {
        fetch(`/admin/users/${username}`, { method: "DELETE" })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    loadUsers();
                } else {
                    alert("Fout bij verwijderen gebruiker");
                }
            });
    }
}

function deletePlugin(url, title) {
    if (
        confirm(`Weet je zeker dat je plugin "${title}" wilt verwijderen?`)
    ) {
        fetch(`/admin/plugins/${encodeURIComponent(url)}`, {
            method: "DELETE",
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    loadPlugins();
                } else {
                    alert("Fout bij verwijderen plugin");
                }
            });
    }
}

function updatePluginDetails(originalUrl, encodedUrl) {
    const titleInput = document.getElementById(`pluginTitle-${encodedUrl}`);
    const authorInput = document.getElementById(`pluginAuthor-${encodedUrl}`);
    const categoryInput = document.getElementById(`pluginCategory-${encodedUrl}`);

    const newTitle = titleInput.value;
    const newAuthor = authorInput.value;
    const newCategory = categoryInput.value;

    fetch(`/admin/plugins/${encodeURIComponent(originalUrl)}/details`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title: newTitle, author: newAuthor, category: newCategory }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                loadPlugins();
            } else {
                alert("Fout bij bijwerken plugin details: " + data.error);
            }
        })
        .catch((error) => {
            console.error("Error:", error);
            alert("Fout bij bijwerken plugin details.");
        });
}