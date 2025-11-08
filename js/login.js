document
    .getElementById("showRegister")
    .addEventListener("click", function (e) {
        e.preventDefault();

        // Check if registration is enabled
        fetch("/registration-status")
            .then((response) => response.json())
            .then((data) => {
                if (data.enabled) {
                    document.getElementById("loginForm").style.display = "none";
                    document.getElementById("registerForm").style.display = "block";
                } else {
                    showRegistrationDisabledMessage();
                }
            })
            .catch(() => {
                showRegistrationDisabledMessage();
            });
    });

function showRegistrationDisabledMessage() {
    const overlay = document.createElement("div");
    overlay.style.cssText =
        "position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;";

    const card = document.createElement("div");
    card.style.cssText =
        "background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); min-width: 400px; animation: bounceIn 0.6s ease-out;";

    card.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: white;">
                    <div style="margin-bottom: 1.5rem;">
                        <i class="fas fa-user-slash" style="font-size: 3rem; opacity: 0.9;"></i>
                    </div>
                    <h4 style="font-weight: bold; margin-bottom: 1.5rem;">Registratie Uitgeschakeld</h4>
                    <p style="margin-bottom: 2rem;">Nieuwe registraties zijn momenteel niet toegestaan. Neem contact op met de beheerder voor meer informatie.</p>
                    <button class="btn btn-light btn-lg" id="closeRegistrationMessage">
                        <i class="fas fa-times me-2"></i>Sluiten
                    </button>
                </div>
            `;

    overlay.appendChild(card);
    document.body.appendChild(overlay);

    // Add click event to close button
    document
        .getElementById("closeRegistrationMessage")
        .addEventListener("click", function () {
            overlay.remove();
        });
}

document
    .getElementById("showLogin")
    .addEventListener("click", function (e) {
        e.preventDefault();
        document.getElementById("registerForm").style.display = "none";
        document.getElementById("loginForm").style.display = "block";
    });

document
    .getElementById("loginBtn")
    .addEventListener("click", function () {
        const username = document.getElementById("loginUsername").value;
        const password = document.getElementById("loginPassword").value;

        fetch("/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    window.location.href = "/";
                } else {
                    document.getElementById("loginError").textContent = data.error;
                    document.getElementById("loginError").style.display = "block";
                }
            })
            .catch((error) => {
                document.getElementById("loginError").textContent =
                    "Fout bij inloggen";
                document.getElementById("loginError").style.display = "block";
            });
    });

document
    .getElementById("registerBtn")
    .addEventListener("click", function () {
        const username = document.getElementById("registerUsername").value;
        const password = document.getElementById("registerPassword").value;

        fetch("/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ username, password }),
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    showSuccessMessage(
                        "Registratie succesvol! Je kunt nu inloggen."
                    );
                    setTimeout(() => {
                        document.getElementById("registerForm").style.display =
                            "none";
                        document.getElementById("loginForm").style.display = "block";
                    }, 2000);
                } else {
                    document.getElementById("registerError").textContent =
                        data.error;
                    document.getElementById("registerError").style.display =
                        "block";
                }
            })
            .catch((error) => {
                document.getElementById("registerError").textContent =
                    "Fout bij registreren";
                document.getElementById("registerError").style.display = "block";
            });
    });

function showSuccessMessage(message) {
    const overlay = document.createElement("div");
    overlay.style.cssText =
        "position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 9999; display: flex; align-items: center; justify-content: center;";

    const card = document.createElement("div");
    card.style.cssText =
        "background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%); border-radius: 15px; box-shadow: 0 20px 40px rgba(0,0,0,0.3); min-width: 400px; animation: bounceIn 0.6s ease-out;";

    card.innerHTML = `
                <div style="padding: 2rem; text-align: center; color: white;">
                    <div style="margin-bottom: 1.5rem;">
                        <i class="fas fa-check-circle" style="font-size: 3rem; opacity: 0.9;"></i>
                    </div>
                    <h4 style="font-weight: bold; margin-bottom: 1.5rem;">Succes!</h4>
                    <p style="margin-bottom: 0;">${message}</p>
                </div>
            `;

    overlay.appendChild(card);
    document.body.appendChild(overlay);

    setTimeout(() => {
        if (overlay.parentNode) {
            overlay.remove();
        }
    }, 2000);
}