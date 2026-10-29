import API from './api.js';
import i18n from './i18n.js';

class ChangesPage {
    constructor() {
        this.startDateInput = document.getElementById('startDate');
        this.endDateInput = document.getElementById('endDate');
        this.fetchBtn = document.getElementById('fetchChangesBtn');
        this.resetBtn = document.getElementById('resetDateFilterBtn');
        this.changesContainer = document.getElementById('changesContainer');
        this.summaryBar = document.getElementById('changesSummaryBar');
        this.countBadge = document.getElementById('changesCountBadge');
        this.rangeText = document.getElementById('changesDateRangeText');
    }

    async init() {
        await i18n.init();
        await i18n.applyTranslations();

        // Default to last 30 days
        this.setQuickDateRange(30);

        this.setupEventListeners();
        await this.loadChanges();
    }

    setupEventListeners() {
        if (this.fetchBtn) {
            this.fetchBtn.addEventListener('click', () => this.loadChanges());
        }

        if (this.resetBtn) {
            this.resetBtn.addEventListener('click', () => {
                this.startDateInput.value = '';
                this.endDateInput.value = '';
                this.loadChanges();
            });
        }

        document.querySelectorAll('.quick-date-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const days = e.target.dataset.days;
                if (days === 'ALL') {
                    this.startDateInput.value = '';
                    this.endDateInput.value = '';
                } else {
                    this.setQuickDateRange(parseInt(days, 10));
                }
                this.loadChanges();
            });
        });
    }

    setQuickDateRange(days) {
        const today = new Date();
        const endDateStr = today.toISOString().split('T')[0];

        let startDateStr = '';
        if (days === 0) {
            startDateStr = endDateStr;
        } else {
            const startDate = new Date();
            startDate.setDate(today.getDate() - days);
            startDateStr = startDate.toISOString().split('T')[0];
        }

        if (this.startDateInput) this.startDateInput.value = startDateStr;
        if (this.endDateInput) this.endDateInput.value = endDateStr;
    }

    async loadChanges() {
        const startDate = this.startDateInput ? this.startDateInput.value : '';
        const endDate = this.endDateInput ? this.endDateInput.value : '';

        this.changesContainer.innerHTML = `
            <div class="text-center text-light py-5">
                <div class="spinner-border text-info mb-3" role="status"></div>
                <p data-i18n="common.loading">${i18n.t('common.loading')}</p>
            </div>`;

        try {
            const data = await API.getChanges(startDate, endDate);
            const changes = (data && data.changes) || [];
            this.renderChanges(changes, startDate, endDate);
        } catch (err) {
            console.error('Failed to load changes:', err);
            this.changesContainer.innerHTML = `
                <div class="alert alert-danger text-center">
                    <i class="fas fa-exclamation-triangle me-2"></i> ${i18n.t('error.load_changes') || 'Fout bij het laden van wijzigingen.'}
                </div>`;
        }
    }

    renderChanges(changes, startDate, endDate) {
        this._updateSummaryBar(changes.length, startDate, endDate);

        if (changes.length === 0) {
            this.changesContainer.innerHTML = `
                <div class="card shadow-sm border-0 text-center p-5">
                    <i class="fas fa-search text-muted fa-3x mb-3"></i>
                    <h5 class="text-light" data-i18n="changes.no_changes">Geen wijzigingen gevonden voor deze periode</h5>
                    <p class="text-muted mb-0" data-i18n="changes.no_changes_desc">Probeer een andere datumreeks of bekijk alle resultaten.</p>
                </div>`;
            return;
        }

        const grouped = this._groupChangesByDate(changes);
        let html = '';
        for (const [dateStr, items] of grouped.entries()) {
            html += `
                <div class="mb-4">
                    <div class="d-flex align-items-center mb-3">
                        <span class="badge bg-primary fs-6 me-2"><i class="far fa-calendar-alt me-1"></i> ${dateStr}</span>
                        <hr class="flex-grow-1 my-0 opacity-25">
                    </div>
                    <div class="row g-3">
                        ${items.map(item => this._createChangeCard(item)).join('')}
                    </div>
                </div>`;
        }

        this.changesContainer.innerHTML = html;
    }

    _updateSummaryBar(count, startDate, endDate) {
        if (this.summaryBar) this.summaryBar.style.setProperty('display', 'flex', 'important');
        if (this.countBadge) {
            const changesLabel = count === 1 ? (i18n.t('changes.singular_found') || 'wijziging gevonden') : (i18n.t('changes.plural_found') || 'wijzigingen gevonden');
            this.countBadge.textContent = `${count} ${changesLabel}`;
        }

        if (this.rangeText) {
            if (startDate && endDate) {
                this.rangeText.textContent = i18n.t('changes.period_range', { start: startDate, end: endDate }) || `Periode: ${startDate} t/m ${endDate}`;
            } else if (startDate) {
                this.rangeText.textContent = i18n.t('changes.from_date', { start: startDate }) || `Vanaf: ${startDate}`;
            } else if (endDate) {
                this.rangeText.textContent = i18n.t('changes.to_date', { end: endDate }) || `Tot: ${endDate}`;
            } else {
                this.rangeText.textContent = i18n.t('changes.all_changes_range') || 'Alle bekende wijzigingen';
            }
        }
    }

    _groupChangesByDate(changes) {
        const grouped = new Map();
        changes.forEach(c => {
            const dateStr = c.date || (c.timestamp ? c.timestamp.split('T')[0] : 'Onbekend');
            if (!grouped.has(dateStr)) {
                grouped.set(dateStr, []);
            }
            grouped.get(dateStr).push(c);
        });
        return grouped;
    }

    _getChangeActionBadge(action) {
        if (action === 'version_update') {
            return `<span class="badge bg-success"><i class="fas fa-arrow-up me-1"></i>${i18n.t('changes.action_new_version') || 'Nieuwe Versie'}</span>`;
        }
        if (action === 'added') {
            return `<span class="badge bg-primary"><i class="fas fa-plus me-1"></i>${i18n.t('changes.action_added') || 'Toegevoegd'}</span>`;
        }
        if (action === 'deleted') {
            return `<span class="badge bg-danger"><i class="fas fa-trash me-1"></i>${i18n.t('changes.action_deleted') || 'Verwijderd'}</span>`;
        }
        return `<span class="badge bg-info text-dark"><i class="fas fa-sync-alt me-1"></i>${i18n.t('changes.action_update') || 'Update'}</span>`;
    }

    _renderVersionBadges(oldVer, newVer) {
        if (!oldVer && !newVer) return '';
        return `
            <div class="d-flex align-items-center gap-2 mt-2 p-2 rounded bg-dark bg-opacity-50 border border-secondary small">
                <span class="badge bg-secondary text-truncate" style="max-width: 110px;">${oldVer || '-'}</span>
                <i class="fas fa-arrow-right text-info"></i>
                <span class="badge bg-success text-truncate" style="max-width: 110px;">${newVer || '-'}</span>
            </div>`;
    }

    _createChangeCard(item) {
        const timeStr = item.timestamp ? new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : '';
        const title = item.plugin_title || 'Plugin';
        const owner = item.owner ? `<small class="text-muted ms-2"><i class="fas fa-user me-1"></i>${item.owner}</small>` : '';
        const actionBadge = this._getChangeActionBadge(item.action);
        const versionBadges = this._renderVersionBadges(item.old_version, item.new_version);

        return `
            <div class="col-md-6 col-lg-4">
                <div class="card h-100 shadow-sm border-0" style="background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1) !important;">
                    <div class="card-header bg-transparent d-flex justify-content-between align-items-center border-bottom border-secondary">
                        <div class="d-flex align-items-center min-w-0 me-2">
                            <h6 class="card-title text-light mb-0 text-truncate fw-bold">${title}</h6>
                            ${owner}
                        </div>
                        ${actionBadge}
                    </div>
                    <div class="card-body">
                        <div class="small text-light mb-2">${item.details || ''}</div>
                        ${versionBadges}
                    </div>
                    <div class="card-footer bg-transparent d-flex justify-content-between align-items-center border-top border-secondary small text-muted">
                        <span><i class="far fa-clock me-1"></i>${timeStr}</span>
                        ${item.url ? `<a href="${item.url}" target="_blank" class="text-info text-decoration-none"><i class="fas fa-external-link-alt me-1"></i>${i18n.t('common.view') || 'Bekijk'}</a>` : ''}
                    </div>
                </div>
            </div>`;
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const page = new ChangesPage();
    page.init();
});