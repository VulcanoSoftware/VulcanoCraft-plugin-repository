import API from './api.js';
import i18n from './i18n.js';
import { showConfirmModal, showAlertModal } from './modals.js';

class NotificationsPage {
    constructor() {
        this.container = document.getElementById('notificationsContainer');
        this.clearBtn = document.getElementById('clearAllNotificationsBtn');
        this.unreadBadge = document.getElementById('unreadNotifCountBadge');
        this.totalBadge = document.getElementById('totalNotifCountBadge');
        this.filterAllBtn = document.getElementById('filterNotifAll');
        this.filterUnreadBtn = document.getElementById('filterNotifUnread');

        this.notifications = [];
        this.currentFilter = 'all';

        this.init();
    }

    async init() {
        await i18n.init();
        this.setupEventListeners();
        await this.loadNotifications();
    }

    setupEventListeners() {
        if (this.clearBtn) {
            this.clearBtn.addEventListener('click', () => this.handleClearAll());
        }

        if (this.filterAllBtn) {
            this.filterAllBtn.addEventListener('click', () => {
                this.setActiveFilter('all');
            });
        }

        if (this.filterUnreadBtn) {
            this.filterUnreadBtn.addEventListener('click', () => {
                this.setActiveFilter('unread');
            });
        }
    }

    setActiveFilter(filter) {
        this.currentFilter = filter;
        if (filter === 'all') {
            this.filterAllBtn.classList.add('active');
            this.filterUnreadBtn.classList.remove('active');
        } else {
            this.filterUnreadBtn.classList.add('active');
            this.filterAllBtn.classList.remove('active');
        }
        this.renderNotifications();
    }

    async loadNotifications() {
        this.container.innerHTML = `
            <div class="text-center text-light py-5">
                <div class="spinner-border text-info mb-3" role="status"></div>
                <p data-i18n="common.loading">Laden...</p>
            </div>`;

        try {
            const data = await API.getNotifications();
            this.notifications = (data && data.notifications) || [];
            this.updateBadges(data.unread_count || 0, this.notifications.length);
            this.renderNotifications();
        } catch (err) {
            console.error('Failed to load notifications:', err);
            this.container.innerHTML = `
                <div class="alert alert-danger text-center shadow" role="alert">
                    <i class="fas fa-exclamation-triangle me-2"></i> ${i18n.t('error.load_notifications') || 'Fout bij het laden van notificaties.'}
                </div>`;
        }
    }

    updateBadges(unreadCount, totalCount) {
        if (this.unreadBadge) {
            this.unreadBadge.textContent = `${unreadCount} ${i18n.t('notifications.unread') || 'ongelezen'}`;
        }
        if (this.totalBadge) {
            this.totalBadge.textContent = `${totalCount} ${i18n.t('notifications.total') || 'totaal'}`;
        }
    }

    renderNotifications() {
        let filtered = this.notifications;
        if (this.currentFilter === 'unread') {
            filtered = this.notifications.filter(n => !n.read);
        }

        if (filtered.length === 0) {
            this.container.innerHTML = `
                <div class="card shadow-lg border-0 dark-glass-card p-5 text-center">
                    <i class="fas fa-bell-slash text-warning mb-3" style="font-size: 3rem;"></i>
                    <h5 class="text-light fw-bold mb-2">${i18n.t('notifications.no_notifications') || 'Geen notificaties gevonden'}</h5>
                    <p class="text-light opacity-90 mb-0 fs-6">${i18n.t('notifications.no_notifications_desc') || 'Er zijn geen notificaties in deze weergave.'}</p>
                </div>`;
            return;
        }

        let html = '<div class="d-flex flex-column gap-3">';
        filtered.forEach((n, idx) => {
            const isUnread = !n.read;
            const dateStr = n.timestamp ? new Date(n.timestamp).toLocaleString(i18n.currentLang || 'nl') : '';
            const borderClass = isUnread ? 'border-start border-4 border-warning' : 'border-start border-4 border-secondary';

            html += `
                <div class="card bg-dark text-light border-0 shadow ${borderClass} overflow-hidden" style="background-color: rgba(15, 23, 42, 0.85) !important;">
                    <div class="card-body p-4 d-flex align-items-start justify-content-between flex-wrap gap-3">
                        <div class="d-flex gap-3 align-items-start">
                            <div class="mt-1">
                                <i class="fas fa-arrow-circle-up text-warning fs-3"></i>
                            </div>
                            <div>
                                <div class="d-flex align-items-center gap-2 flex-wrap mb-1">
                                    <h5 class="card-title text-light mb-0 fw-bold">${this.escapeHtml(n.plugin_title || 'Plugin Update')}</h5>
                                    ${isUnread ? `<span class="badge bg-warning text-dark">${i18n.t('notifications.unread') || 'Nieuw'}</span>` : ''}
                                </div>
                                <p class="card-text text-light opacity-90 mb-2">${this.escapeHtml(n.message || '')}</p>
                                <div class="d-flex align-items-center gap-3 text-muted small">
                                    <span><i class="far fa-clock me-1"></i>${dateStr}</span>
                                    ${n.url ? `<a href="${this.escapeHtml(n.url)}" target="_blank" rel="noopener noreferrer" class="text-info text-decoration-none"><i class="fas fa-external-link-alt me-1"></i>Bekijk Plugin</a>` : ''}
                                </div>
                            </div>
                        </div>
                    </div>
                </div>`;
        });
        html += '</div>';

        this.container.innerHTML = html;
    }

    async handleClearAll() {
        const confirmed = await showConfirmModal({
            title: i18n.t('notifications.clear_all') || 'Notificaties Wissen',
            message: i18n.t('notifications.confirm_clear') || 'Weet je zeker dat je alle notificaties wilt wissen?',
            confirmText: i18n.t('notifications.clear_all') || 'Wissen',
            confirmClass: 'btn-danger',
            iconClass: 'fas fa-trash-alt text-danger'
        });

        if (!confirmed) {
            return;
        }

        try {
            await API.clearNotifications();
            this.notifications = [];
            this.updateBadges(0, 0);
            this.renderNotifications();
        } catch (err) {
            console.error('Failed to clear notifications:', err);
            await showAlertModal(i18n.t('error.clear_notifications') || 'Fout bij het wissen van notificaties.', i18n.t('common.error') || 'Fout', 'fas fa-exclamation-triangle text-danger');
        }
    }

    escapeHtml(str) {
        return String(str || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    window.notificationsPage = new NotificationsPage();
});
