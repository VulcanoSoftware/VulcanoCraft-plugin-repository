// VulcanoCraft Production Configuration Generator Logic

document.addEventListener('DOMContentLoaded', () => {
  const elements = {
    mongoHost: document.getElementById('mongoHost'),
    mongoPort: document.getElementById('mongoPort'),
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
    btnCopyEnv: document.getElementById('btnCopyEnv'),
    btnDownloadEnv: document.getElementById('btnDownloadEnv'),
    btnGenerateAllSecrets: document.getElementById('btnGenerateAllSecrets'),
    btnUploadEnv: document.getElementById('btnUploadEnv'),
    envFileInput: document.getElementById('envFileInput'),
    dropZone: document.getElementById('dropZone'),
    uploadStatusBadge: document.getElementById('uploadStatusBadge'),
    uploadedFileName: document.getElementById('uploadedFileName'),
    uploadedStats: document.getElementById('uploadedStats'),
    btnClearUpload: document.getElementById('btnClearUpload'),
    customVarsBadge: document.getElementById('customVarsBadge'),
    customVarsCount: document.getElementById('customVarsCount'),
    deploymentInstructions: document.getElementById('deploymentInstructions'),
    appToast: document.getElementById('appToast'),
    toastMessage: document.getElementById('toastMessage')
  };

  const bsToast = new bootstrap.Toast(elements.appToast, { delay: 3500 });

  // Current deployment method: 'docker', 'local', or 'arm64'
  let currentDeployMethod = 'docker';

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

  function generateHexSecret(length = 64) {
    const chars = '0123456789abcdef';
    const array = new Uint8Array(length);
    window.crypto.getRandomValues(array);
    let result = '';
    for (let i = 0; i < length; i++) {
      result += chars[array[i] % chars.length];
    }
    return result;
  }

  function generateAlphanumericSecret(length = 24) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+-=';
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

      if ((val.startsWith('"') && val.endsWith('"')) || (val.startsWith("'") && val.endsWith("'"))) {
        val = val.substring(1, val.length - 1);
      }

      parsedKV[key] = val;
      if (!standardKeys.has(key)) customKV[key] = val;
    });

    return { parsedKV, customKV };
  }

  function applyMongoCredentials(parsedKV) {
    if (parsedKV['MONGO_URI'] && parsedKV['MONGO_URI'].startsWith('mongodb://')) {
      const match = parsedKV['MONGO_URI'].match(/^mongodb:\/\/([^:]+):([^@]+)@([^:\/]+)(?::(\d+))?\/([^?]+)/);
      if (match) {
        elements.mongoUser.value = decodeURIComponent(match[1]);
        elements.mongoPassword.value = decodeURIComponent(match[2]);
        elements.mongoHost.value = match[3];
        if (match[4]) elements.mongoPort.value = match[4];
        elements.mongoDbName.value = match[5];
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

  function applyEnvToForm(fileName, parsedKV, customKV) {
    customEnvVars = { ...customKV };
    applyMongoCredentials(parsedKV);
    applyServerAndApiCredentials(parsedKV);
    applyBackupSettings(parsedKV);
    updateCustomVarsBadge();

    const totalCount = Object.keys(parsedKV).length;
    const customCount = Object.keys(customKV).length;
    elements.uploadedFileName.textContent = fileName || '.env';
    elements.uploadedStats.textContent = `${totalCount} variable(s) imported${customCount > 0 ? ` (${customCount} custom preserved)` : ''}`;
    elements.uploadStatusBadge.classList.remove('d-none');

    renderEnv();
  }

  function handleFileRead(file) {
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const text = e.target.result;
        const { parsedKV, customKV } = parseEnvContent(text);
        applyEnvToForm(file.name, parsedKV, customKV);
        showToast(`Successfully loaded configuration from ${file.name}!`);
      } catch (err) {
        showToast('Error reading .env file format', false);
      }
    };
    reader.readAsText(file);
  }

  function getDockerInstructions(port) {
    return `
      <ol class="mb-0 ps-3">
        <li class="mb-3">
          <strong>Save Configuration:</strong> Click <code class="text-success">Download .env</code> above and place the <code>.env</code> file in the root directory of your project.
        </li>
        <li class="mb-3">
          <strong>Build &amp; Start Stack:</strong> Run Docker Compose to launch Flask WSGI (${port}), MongoDB, cron, and optional backups:
          <div class="bg-black text-white p-2 rounded mt-2 font-monospace fs-7 d-flex justify-content-between align-items-center border border-secondary">
            <code>docker compose build app &amp;&amp; docker compose up -d</code>
            <button class="btn btn-sm btn-outline-warning border-0 btn-copy-cmd" data-cmd="docker compose build app &amp;&amp; docker compose up -d" title="Copy command">
              <i class="fa-solid fa-copy"></i>
            </button>
          </div>
        </li>
        <li class="mb-3">
          <strong>Create Initial Admin Account:</strong>
          <div class="bg-black text-white p-2 rounded mt-2 font-monospace fs-7 d-flex justify-content-between align-items-center border border-secondary">
            <code>docker compose exec app python create_admin.py</code>
            <button class="btn btn-sm btn-outline-warning border-0 btn-copy-cmd" data-cmd="docker compose exec app python create_admin.py" title="Copy command">
              <i class="fa-solid fa-copy"></i>
            </button>
          </div>
        </li>
        <li>
          <strong>Access Application:</strong> Open browser at <a href="http://localhost:${port}" target="_blank" class="text-info fw-bold text-decoration-none">http://localhost:${port}</a>.
        </li>
      </ol>`;
  }

  function getLocalInstructions(port) {
    return `
      <ol class="mb-0 ps-3">
        <li class="mb-3">
          <strong>Install Dependencies:</strong> Use <code>uv</code> or <code>pip</code> with Python 3.11:
          <div class="bg-black text-white p-2 rounded mt-2 font-monospace fs-7 d-flex justify-content-between align-items-center border border-secondary">
            <code>uv pip install -r requirements.txt &amp;&amp; playwright install</code>
            <button class="btn btn-sm btn-outline-warning border-0 btn-copy-cmd" data-cmd="uv pip install -r requirements.txt &amp;&amp; playwright install" title="Copy command">
              <i class="fa-solid fa-copy"></i>
            </button>
          </div>
        </li>
        <li class="mb-3">
          <strong>Start Local Server:</strong> Run Flask webserver:
          <div class="bg-black text-white p-2 rounded mt-2 font-monospace fs-7 d-flex justify-content-between align-items-center border border-secondary">
            <code>uv run webserver.py</code>
            <button class="btn btn-sm btn-outline-warning border-0 btn-copy-cmd" data-cmd="uv run webserver.py" title="Copy command">
              <i class="fa-solid fa-copy"></i>
            </button>
          </div>
        </li>
        <li>
          <strong>Access Application:</strong> Open browser at <a href="http://localhost:${port}" target="_blank" class="text-info fw-bold text-decoration-none">http://localhost:${port}</a>.
        </li>
      </ol>`;
  }

  function getArm64Instructions(port) {
    return `
      <ol class="mb-0 ps-3">
        <li class="mb-3">
          <strong>Requirements &amp; Architecture:</strong> Requires a 64-bit OS (e.g., Raspberry Pi OS 64-bit or Ubuntu Server 64-bit). The Docker stack pins <code>mongo:4.4.18</code> to guarantee ARMv8 CPU compatibility.
        </li>
        <li class="mb-3">
          <strong>Build &amp; Launch Stack:</strong>
          <div class="bg-black text-white p-2 rounded mt-2 font-monospace fs-7 d-flex justify-content-between align-items-center border border-secondary">
            <code>docker compose build app &amp;&amp; docker compose up -d</code>
            <button class="btn btn-sm btn-outline-warning border-0 btn-copy-cmd" data-cmd="docker compose build app &amp;&amp; docker compose up -d" title="Copy command">
              <i class="fa-solid fa-copy"></i>
            </button>
          </div>
        </li>
        <li>
          <strong>Access Application:</strong> Open browser at <a href="http://localhost:${port}" target="_blank" class="text-info fw-bold text-decoration-none">http://localhost:${port}</a>.
        </li>
      </ol>`;
  }

  function renderDeploymentInstructions() {
    const port = elements.appPort.value.trim() || (currentDeployMethod === 'local' ? '5000' : '8000');
    const instructionMap = {
      docker: getDockerInstructions(port),
      local: getLocalInstructions(port),
      arm64: getArm64Instructions(port)
    };

    elements.deploymentInstructions.innerHTML = instructionMap[currentDeployMethod] || getDockerInstructions(port);

    elements.deploymentInstructions.querySelectorAll('.btn-copy-cmd').forEach(btn => {
      btn.addEventListener('click', () => {
        const cmd = btn.getAttribute('data-cmd');
        navigator.clipboard.writeText(cmd)
          .then(() => showToast('Command copied to clipboard!'))
          .catch(() => showToast('Failed to copy command', false));
      });
    });
  }

  function buildMongoSection(user, pass, dbName, mongoUri) {
    return `# MongoDB Database Config\n` +
      `MONGO_ROOT_USERNAME=${user}\n` +
      `MONGO_ROOT_PASSWORD=${pass}\n` +
      `MONGO_DB_NAME=${dbName}\n` +
      `MONGO_URI=${mongoUri}\n` +
      `MONGO_BACKUP_URI=${mongoUri}\n\n`;
  }

  function buildWebserverSection(flaskKey, adminPass) {
    return `# Webserver & Security\n` +
      `FLASK_SECRET_KEY=${flaskKey}\n` +
      `ADMIN_DEFAULT_PASSWORD=${adminPass}\n\n`;
  }

  function buildApiSection(cfKey, ghToken) {
    let text = cfKey ?
      `# API Integration Key\nCURSEFORGE_API_KEY=${cfKey}\n\n` :
      `# CURSEFORGE_API_KEY=\n\n`;

    text += ghToken ?
      `# GitHub Access Token (Prevents rate-limiting for update checks)\nGITHUB_TOKEN=${ghToken}\n\n` :
      `# GITHUB_TOKEN=\n\n`;

    return text;
  }

  function buildBackupSection(backups, interval) {
    return `# Automatic Backups\n` +
      `ENABLE_BACKUPS=${backups ? 'true' : 'false'}\n` +
      `BACKUP_INTERVAL_HOURS=${interval}\n`;
  }

  function buildCustomSection() {
    const customKeys = Object.keys(customEnvVars);
    if (customKeys.length === 0) return '';
    let text = `\n# Additional / Custom Variables (Preserved from imported .env)\n`;
    customKeys.forEach(k => {
      text += `${k}=${customEnvVars[k]}\n`;
    });
    return text;
  }

  function renderEnv() {
    const defaultHost = (currentDeployMethod === 'docker' || currentDeployMethod === 'arm64') ? 'mongo' : 'localhost';
    const host = elements.mongoHost.value.trim() || defaultHost;
    const port = elements.mongoPort.value.trim() || '27017';
    const user = elements.mongoUser.value.trim() || 'vulcano_root';
    const pass = elements.mongoPassword.value.trim() || 'change-me-strong-mongo-password';
    const dbName = elements.mongoDbName.value.trim() || 'vulcanocraft';
    const flaskKey = elements.flaskSecretKey.value.trim() || 'a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890a1b2c3d4e5f67890';
    const adminPass = elements.adminDefaultPassword.value.trim() || 'change-me-strong-admin-password';
    const cfKey = elements.curseforgeApiKey.value.trim();
    const ghToken = elements.githubToken.value.trim();
    const backups = elements.enableBackups.checked;
    const interval = elements.backupIntervalHours.value.trim() || '24';

    const mongoUri = `mongodb://${encodeURIComponent(user)}:${encodeURIComponent(pass)}@${host}:${port}/${dbName}?authSource=admin`;

    let envContent = `# ==========================================\n` +
      `# VulcanoCraft Configuration File (.env)\n` +
      `# Target Deployment Method: ${currentDeployMethod.toUpperCase()}\n` +
      `# Generated via VulcanoCraft Configurator\n` +
      `# ==========================================\n\n`;

    envContent += buildMongoSection(user, pass, dbName, mongoUri);
    envContent += buildWebserverSection(flaskKey, adminPass);
    envContent += buildApiSection(cfKey, ghToken);
    envContent += buildBackupSection(backups, interval);
    envContent += buildCustomSection();

    elements.envPreview.textContent = envContent;
    renderDeploymentInstructions();
  }

  // Handle deployment method switching
  document.querySelectorAll('#deployMethodCards .deploy-card').forEach(card => {
    card.addEventListener('click', () => {
      document.querySelectorAll('#deployMethodCards .deploy-card').forEach(c => {
        c.classList.remove('active', 'border-warning');
        c.classList.add('border-secondary');
      });

      card.classList.add('active', 'border-warning');
      card.classList.remove('border-secondary');

      currentDeployMethod = card.getAttribute('data-method');

      if (currentDeployMethod === 'docker' || currentDeployMethod === 'arm64') {
        elements.mongoHost.value = 'mongo';
        elements.appPort.value = '8000';
      } else if (currentDeployMethod === 'local') {
        elements.mongoHost.value = 'localhost';
        elements.appPort.value = '5000';
      }

      renderEnv();
      showToast(`Switched deployment method to ${card.querySelector('h6').textContent}`);
    });
  });

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

  // Clear imported configuration
  elements.btnClearUpload.addEventListener('click', (e) => {
    e.stopPropagation();
    customEnvVars = {};
    elements.uploadStatusBadge.classList.add('d-none');
    updateCustomVarsBadge();
    elements.envFileInput.value = '';
    renderEnv();
    showToast('Imported configuration reset.');
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
    elements.mongoHost, elements.mongoPort, elements.mongoUser, elements.mongoPassword,
    elements.mongoDbName, elements.flaskSecretKey, elements.adminDefaultPassword,
    elements.appPort, elements.curseforgeApiKey, elements.githubToken, elements.backupIntervalHours
  ];
  inputs.forEach(input => input.addEventListener('input', renderEnv));

  // Individual secret generators
  document.querySelectorAll('.btn-gen-secret').forEach(button => {
    button.addEventListener('click', () => {
      const targetId = button.getAttribute('data-target');
      const targetInput = document.getElementById(targetId);
      if (targetInput) {
        if (targetId === 'flaskSecretKey') {
          targetInput.value = generateHexSecret(64);
        } else {
          targetInput.value = generateAlphanumericSecret(24);
        }
        renderEnv();
        showToast('New secure secret key generated!');
      }
    });
  });

  // Generate all secrets at once
  elements.btnGenerateAllSecrets.addEventListener('click', () => {
    elements.mongoPassword.value = generateAlphanumericSecret(24);
    elements.flaskSecretKey.value = generateHexSecret(64);
    elements.adminDefaultPassword.value = generateAlphanumericSecret(20);
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

  // Initial render
  renderEnv();
});
