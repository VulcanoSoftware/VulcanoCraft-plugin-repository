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
            grid.innerHTML = categories
                .map(
                    (category) => `
                        <div class="col-md-4 col-sm-6 mb-3">
                            <div class="card h-100">
                                <div class="card-body">
                                    <input type="text" class="form-control form-control-sm mb-2" value="${category.name}" id="cat-name-${category.name}" onchange="updateCategory('${category.name}')">
                                    <input type="text" class="form-control form-control-sm mb-2" value="${category.software || ''}" placeholder="Software" id="cat-software-${category.name}" onchange="updateCategory('${category.name}')">
                                    <input type="text" class="form-control form-control-sm mb-2" value="${category.version || ''}" placeholder="Versie" id="cat-version-${category.name}" onchange="updateCategory('${category.name}')">
                                    <button class="btn btn-danger btn-sm" onclick="deleteCategory('${category.name}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    `
                )
                .join("");
        });
}

function addCategory() {
    const name = document.getElementById("newCategoryName").value.trim();
    const software = document.getElementById("newCategorySoftware").value.trim();
    const version = document.getElementById("newCategoryVersion").value.trim();
    if (!name) return;

    fetch("/admin/categories", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, software, version }),
    })
        .then((response) => response.json())
        .then((data) => {
            if (data.success) {
                document.getElementById("newCategoryName").value = "";
                document.getElementById("newCategorySoftware").value = "";
                document.getElementById("newCategoryVersion").value = "";
                loadCategories();
                loadPlugins(); // Refresh dropdowns
            } else {
                alert("Fout bij toevoegen categorie: " + data.error);
            }
        });
}

function updateCategory(oldName) {
    const newName = document.getElementById(`cat-name-${oldName}`).value.trim();
    const software = document.getElementById(`cat-software-${oldName}`).value.trim();
    const version = document.getElementById(`cat-version-${oldName}`).value.trim();

    if (!newName) return;

    fetch(`/admin/categories/${oldName}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: newName, software, version }),
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
                        `<option value="${cat}" ${plugin.category === cat ? 'selected' : ''}>${cat}</option>`
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