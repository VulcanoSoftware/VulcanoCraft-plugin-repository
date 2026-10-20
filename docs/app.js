// VulcanoCraft GitHub Pages Configurator Logic

document.addEventListener('DOMContentLoaded', () => {
  const elements = {
    mongoUser: document.getElementById('mongoUser'),
    mongoPassword: document.getElementById('mongoPassword'),
    mongoDbName: document.getElementById('mongoDbName'),
    flaskSecretKey: document.getElementById('flaskSecretKey'),
    adminDefaultPassword: document.getElementById('adminDefaultPassword'),
    appPort: document.getElementById('appPort'),
    curseforgeApiKey: document.getElementById('curseforgeApiKey'),
    githubToken: document.getElementById('githubToken'),
    enableBackups: document.getElementById('enableBackups'),
    backupIntervalHours: document.getElementById('backupIntervalHours'),
    backupIntervalGroup: document.getElementById('backupIntervalGroup'),
    envPreview: document.getElementById('envPreview'),
    appUrlLink: document.getElementById('appUrlLink'),
    btnCopyEnv: document.getElementById('btnCopyEnv'),
    btnDownloadEnv: document.getElementById('btnDownloadEnv'),
    btnGenerateAllSecrets: document.getElementById('btnGenerateAllSecrets'),
    appToast: document.getElementById('appToast'),
    toastMessage: document.getElementById('toastMessage')
  };

  const bsToast = new bootstrap.Toast(elements.appToast, { delay: 3000 });

  function showToast(message, isSuccess = true) {
    elements.appToast.className = `toast text-white border-0 ${isSuccess ? 'bg-success' : 'bg-danger'}`;
    elements.toastMessage.textContent = message;
    bsToast.show();
  }

  function generateRandomSecret(length = 32) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=';
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[array[i] % chars.length];
    }
    return result;
  }

  function generateAlphanumericSecret(length = 24) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[array[i] % chars.length];
    }
    return result;
  }

  function renderEnv() {
    const user = elements.mongoUser.value.trim() || 'vulcano_root';
    const pass = elements.mongoPassword.value.trim() || 'change-me-strong-mongo-password';
    const dbName = elements.mongoDbName.value.trim() || 'vulcanocraft';
    const flaskKey = elements.flaskSecretKey.value.trim() || 'change-me-strong-flask-secret-key';
    const adminPass = elements.adminDefaultPassword.value.trim() || 'admin123';
    const port = elements.appPort.value.trim() || '5000';
    const cfKey = elements.curseforgeApiKey.value.trim();
    const ghToken = elements.githubToken.value.trim();
    const backups = elements.enableBackups.checked;
    const interval = elements.backupIntervalHours.value.trim() || '24';

    const mongoUri = `mongodb://${encodeURIComponent(user)}:${encodeURIComponent(pass)}@mongo:27017/${dbName}?authSource=admin`;

    let envContent = `# ==========================================\n`;
    envContent += `# VulcanoCraft Configuration File (.env)\n`;
    envContent += `# Genereerd via VulcanoCraft Static Configurator\n`;
    envContent += `# ==========================================\n\n`;

    envContent += `# MongoDB Database Config\n`;
    envContent += `MONGO_ROOT_USERNAME=${user}\n`;
    envContent += `MONGO_ROOT_PASSWORD=${pass}\n`;
    envContent += `MONGO_DB_NAME=${dbName}\n`;
    envContent += `MONGO_URI=${mongoUri}\n`;
    envContent += `MONGO_BACKUP_URI=${mongoUri}\n\n`;

    envContent += `# Webserver & Beveiliging\n`;
    envContent += `FLASK_SECRET_KEY=${flaskKey}\n`;
    envContent += `ADMIN_DEFAULT_PASSWORD=${adminPass}\n\n`;

    if (cfKey) {
      envContent += `# API Integration Key\n`;
      envContent += `CURSEFORGE_API_KEY=${cfKey}\n\n`;
    } else {
      envContent += `# CURSEFORGE_API_KEY=\n\n`;
    }

    if (ghToken) {
      envContent += `# GitHub Access Token (Voorkomt rate-limiting bij update checks)\n`;
      envContent += `GITHUB_TOKEN=${ghToken}\n\n`;
    } else {
      envContent += `# GITHUB_TOKEN=\n\n`;
    }

    envContent += `# Automatische Backups\n`;
    envContent += `ENABLE_BACKUPS=${backups ? 'true' : 'false'}\n`;
    envContent += `BACKUP_INTERVAL_HOURS=${interval}\n`;

    elements.envPreview.textContent = envContent;
    elements.appUrlLink.href = `http://localhost:${port}`;
    elements.appUrlLink.textContent = `http://localhost:${port}`;
  }

  // Toggle backup interval input visibility
  elements.enableBackups.addEventListener('change', () => {
    elements.backupIntervalGroup.style.display = elements.enableBackups.checked ? 'block' : 'none';
    renderEnv();
  });

  // Re-render preview on input change
  const inputs = [
    elements.mongoUser, elements.mongoPassword, elements.mongoDbName,
    elements.flaskSecretKey, elements.adminDefaultPassword, elements.appPort,
    elements.curseforgeApiKey, elements.githubToken, elements.backupIntervalHours
  ];
  inputs.forEach(input => input.addEventListener('input', renderEnv));

  // Individual secret generators
  document.querySelectorAll('.btn-gen-secret').forEach(button => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-target');
      const targetInput = document.getElementById(targetId);
      if (targetInput) {
        targetInput.value = targetId === 'flaskSecretKey' ? generateRandomSecret(36) : generateAlphanumericSecret(20);
        renderEnv();
        showToast('Nieuwe willekeurige sleutel gegenereerd!');
      }
    });
  });

  // Generate all secrets at once
  elements.btnGenerateAllSecrets.addEventListener('click', () => {
    elements.mongoPassword.value = generateAlphanumericSecret(24);
    elements.flaskSecretKey.value = generateRandomSecret(40);
    elements.adminDefaultPassword.value = generateAlphanumericSecret(16);
    renderEnv();
    showToast('Alle wachtwoorden en Flask sleutels zijn vernieuwd!');
  });

  // Copy .env preview
  elements.btnCopyEnv.addEventListener('click', () => {
    navigator.clipboard.writeText(elements.envPreview.textContent)
      .then(() => showToast('.env inhoud gekopieerd naar klembord!'))
      .catch(() => showToast('Kopiëren mislukt', false));
  });

  // Download .env file
  elements.btnDownloadEnv.addEventListener('click', () => {
    const blob = new Blob([elements.envPreview.textContent], { type: 'text/plain;charset=utf-8' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = '.env';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    showToast('.env bestand gedownload!');
  });

  // Copy command buttons
  document.querySelectorAll('.btn-copy-cmd').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.getAttribute('data-cmd');
      navigator.clipboard.writeText(cmd)
        .then(() => showToast('Commando gekopieerd!'))
        .catch(() => showToast('Kopiëren mislukt', false));
    });
  });

  // Initial render
  renderEnv();
});
