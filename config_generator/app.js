// VulcanoCraft Production Configuration Generator Logic

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
    btnUploadEnv: document.getElementById('btnUploadEnv'),
    envFileInput: document.getElementById('envFileInput'),
    dropZone: document.getElementById('dropZone'),
    customVarsBadge: document.getElementById('customVarsBadge'),
    customVarsCount: document.getElementById('customVarsCount'),
    appToast: document.getElementById('appToast'),
    toastMessage: document.getElementById('toastMessage')
  };

  const bsToast = new bootstrap.Toast(elements.appToast, { delay: 3500 });

  // Store non-standard / additional custom variables loaded from uploaded .env files
  let customEnvVars = {};

  // Standard keys known to the generator form
  const standardKeys = new Set([
    'MONGO_ROOT_USERNAME',
    'MONGO_ROOT_PASSWORD',
    'MONGO_DB_NAME',
    'MONGO_URI',
    'MONGO_BACKUP_URI',
    'FLASK_SECRET_KEY',
    'ADMIN_DEFAULT_PASSWORD',
    'CURSEFORGE_API_KEY',
    'GITHUB_TOKEN',
    'ENABLE_BACKUPS',
    'BACKUP_INTERVAL_HOURS'
  ]);

  function showToast(message, isSuccess = true) {
    elements.appToast.className = `toast text-white border-0 shadow-lg ${isSuccess ? 'bg-success' : 'bg-danger'}`;
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

  function parseEnvContent(text) {
    const lines = text.split(/\r?\n/);
    const parsedKV = {};
    const customKV = {};

    lines.forEach(line => {
      let trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) return;

      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) return;

      const key = trimmed.substring(0, eqIdx).trim();
      let val = trimmed.substring(eqIdx + 1).trim();

      // Remove surrounding quotes if present
      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.substring(1, val.length - 1);
      }

      parsedKV[key] = val;

      if (!standardKeys.has(key)) {
        customKV[key] = val;
      }
    });

    return { parsedKV, customKV };
  }

  function applyMongoCredentials(parsedKV) {
    if (parsedKV['MONGO_URI'] && parsedKV['MONGO_URI'].startsWith('mongodb://')) {
      const match = parsedKV['MONGO_URI'].match(/^mongodb:\/\/([^:]+):([^@]+)@/);
      if (match) {
        elements.mongoUser.value = decodeURIComponent(match[1]);
        elements.mongoPassword.value = decodeURIComponent(match[2]);
      }
    }
    if (parsedKV['MONGO_ROOT_USERNAME']) elements.mongoUser.value = parsedKV['MONGO_ROOT_USERNAME'];
    if (parsedKV['MONGO_ROOT_PASSWORD']) elements.mongoPassword.value = parsedKV['MONGO_ROOT_PASSWORD'];
    if (parsedKV['MONGO_DB_NAME']) elements.mongoDbName.value = parsedKV['MONGO_DB_NAME'];
  }

  function applyServerAndApiCredentials(parsedKV) {
    if (parsedKV['FLASK_SECRET_KEY']) elements.flaskSecretKey.value = parsedKV['FLASK_SECRET_KEY'];
    if (parsedKV['ADMIN_DEFAULT_PASSWORD']) elements.adminDefaultPassword.value = parsedKV['ADMIN_DEFAULT_PASSWORD'];
    if (parsedKV['CURSEFORGE_API_KEY'] !== undefined) elements.curseforgeApiKey.value = parsedKV['CURSEFORGE_API_KEY'];
    if (parsedKV['GITHUB_TOKEN'] !== undefined) elements.githubToken.value = parsedKV['GITHUB_TOKEN'];
  }

  function applyBackupSettings(parsedKV) {
    if (parsedKV['ENABLE_BACKUPS'] !== undefined) {
      const isEnabled = parsedKV['ENABLE_BACKUPS'].toLowerCase() === 'true';
      elements.enableBackups.checked = isEnabled;
      elements.backupIntervalGroup.style.display = isEnabled ? 'block' : 'none';
    }
    if (parsedKV['BACKUP_INTERVAL_HOURS']) elements.backupIntervalHours.value = parsedKV['BACKUP_INTERVAL_HOURS'];
  }

  function updateCustomVarsBadge() {
    const customKeysCount = Object.keys(customEnvVars).length;
    if (customKeysCount > 0) {
      elements.customVarsCount.textContent = customKeysCount;
      elements.customVarsBadge.classList.remove('d-none');
    } else {
      elements.customVarsBadge.classList.add('d-none');
    }
  }

  function applyEnvToForm(parsedKV, customKV) {
    customEnvVars = { ...customKV };
    applyMongoCredentials(parsedKV);
    applyServerAndApiCredentials(parsedKV);
    applyBackupSettings(parsedKV);
    updateCustomVarsBadge();
    renderEnv();
  }

  function handleFileRead(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const { parsedKV, customKV } = parseEnvContent(text);
        applyEnvToForm(parsedKV, customKV);
        const count = Object.keys(parsedKV).length;
        showToast(`Successfully loaded ${count} setting(s) from .env file!`);
      } catch (err) {
        showToast('Error reading .env file format', false);
      }
    };
    reader.readAsText(file);
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
    envContent += `# VulcanoCraft Production Configuration File (.env)\n`;
    envContent += `# Generated via VulcanoCraft Configurator\n`;
    envContent += `# ==========================================\n\n`;

    envContent += `# MongoDB Database Config\n`;
    envContent += `MONGO_ROOT_USERNAME=${user}\n`;
    envContent += `MONGO_ROOT_PASSWORD=${pass}\n`;
    envContent += `MONGO_DB_NAME=${dbName}\n`;
    envContent += `MONGO_URI=${mongoUri}\n`;
    envContent += `MONGO_BACKUP_URI=${mongoUri}\n\n`;

    envContent += `# Webserver & Security\n`;
    envContent += `FLASK_SECRET_KEY=${flaskKey}\n`;
    envContent += `ADMIN_DEFAULT_PASSWORD=${adminPass}\n\n`;

    if (cfKey) {
      envContent += `# API Integration Key\n`;
      envContent += `CURSEFORGE_API_KEY=${cfKey}\n\n`;
    } else {
      envContent += `# CURSEFORGE_API_KEY=\n\n`;
    }

    if (ghToken) {
      envContent += `# GitHub Access Token (Prevents rate-limiting for update checks)\n`;
      envContent += `GITHUB_TOKEN=${ghToken}\n\n`;
    } else {
      envContent += `# GITHUB_TOKEN=\n\n`;
    }

    envContent += `# Automatic Backups\n`;
    envContent += `ENABLE_BACKUPS=${backups ? 'true' : 'false'}\n`;
    envContent += `BACKUP_INTERVAL_HOURS=${interval}\n`;

    // Append preserved custom/additional variables
    const customKeys = Object.keys(customEnvVars);
    if (customKeys.length > 0) {
      envContent += `\n# Additional / Custom Variables (Preserved from imported .env)\n`;
      customKeys.forEach(k => {
        envContent += `${k}=${customEnvVars[k]}\n`;
      });
    }

    elements.envPreview.textContent = envContent;
    elements.appUrlLink.href = `http://localhost:${port}`;
    elements.appUrlLink.textContent = `http://localhost:${port}`;
  }

  // Toggle backup interval input visibility
  elements.enableBackups.addEventListener('change', () => {
    elements.backupIntervalGroup.style.display = elements.enableBackups.checked ? 'block' : 'none';
    renderEnv();
  });

  // Upload button & File Input events
  elements.btnUploadEnv.addEventListener('click', () => {
    elements.envFileInput.click();
  });

  elements.dropZone.addEventListener('click', () => {
    elements.envFileInput.click();
  });

  elements.envFileInput.addEventListener('change', (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileRead(e.target.files[0]);
    }
  });

  // Drag and Drop events
  ['dragenter', 'dragover'].forEach(eventName => {
    elements.dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.dropZone.classList.add('dragover');
    }, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    elements.dropZone.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      elements.dropZone.classList.remove('dragover');
    }, false);
  });

  elements.dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    if (dt && dt.files && dt.files.length > 0) {
      handleFileRead(dt.files[0]);
    }
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
        showToast('New random key generated!');
      }
    });
  });

  // Generate all secrets at once
  elements.btnGenerateAllSecrets.addEventListener('click', () => {
    elements.mongoPassword.value = generateAlphanumericSecret(24);
    elements.flaskSecretKey.value = generateRandomSecret(40);
    elements.adminDefaultPassword.value = generateAlphanumericSecret(16);
    renderEnv();
    showToast('All passwords and secret keys renewed!');
  });

  // Copy .env preview
  elements.btnCopyEnv.addEventListener('click', () => {
    navigator.clipboard.writeText(elements.envPreview.textContent)
      .then(() => showToast('.env content copied to clipboard!'))
      .catch(() => showToast('Failed to copy content', false));
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
    showToast('.env file downloaded!');
  });

  // Copy command buttons
  document.querySelectorAll('.btn-copy-cmd').forEach(btn => {
    btn.addEventListener('click', () => {
      const cmd = btn.getAttribute('data-cmd');
      navigator.clipboard.writeText(cmd)
        .then(() => showToast('Command copied!'))
        .catch(() => showToast('Failed to copy command', false));
    });
  });

  // Initial render
  renderEnv();
});
