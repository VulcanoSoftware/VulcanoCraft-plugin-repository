document.addEventListener('DOMContentLoaded', () => {
    const changePasswordForm = document.getElementById('changePasswordForm');
    const passwordChangeMessage = document.getElementById('passwordChangeMessage');

    if (changePasswordForm) {
        changePasswordForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const oldPassword = document.getElementById('oldPassword').value;
            const newPassword = document.getElementById('newPassword').value;
            const confirmNewPassword = document.getElementById('confirmNewPassword').value;

            if (newPassword !== confirmNewPassword) {
                passwordChangeMessage.textContent = 'Nieuwe wachtwoorden komen niet overeen.';
                passwordChangeMessage.className = 'alert alert-danger';
                passwordChangeMessage.style.display = 'block';
                return;
            }

            try {
                const response = await fetch('/api/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ old_password: oldPassword, new_password: newPassword })
                });

                const data = await response.json();

                if (response.ok) {
                    passwordChangeMessage.textContent = data.message;
                    passwordChangeMessage.className = 'alert alert-success';
                    passwordChangeMessage.style.display = 'block';
                    changePasswordForm.reset();
                    // Optionally redirect or show success message
                } else {
                    passwordChangeMessage.textContent = data.error;
                    passwordChangeMessage.className = 'alert alert-danger';
                    passwordChangeMessage.style.display = 'block';
                }
            } catch (error) {
                passwordChangeMessage.textContent = 'Er is een fout opgetreden bij het wijzigen van het wachtwoord.';
                passwordChangeMessage.className = 'alert alert-danger';
                passwordChangeMessage.style.display = 'block';
                console.error('Error:', error);
            }
        });
    }
});