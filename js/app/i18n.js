class I18n {
    constructor() {
        this.currentLang = localStorage.getItem('user_language') || 'nl';
        this.translations = {};
        this._fetchPromise = null;
        this.initPromise = this.init();
    }

    async init() {
        if (!this._fetchPromise) {
            this._fetchPromise = (async () => {
                try {
                    const langs = ['nl', 'en', 'de', 'fr', 'el', 'es', 'it', 'pt', 'pl', 'tr'];
                    const results = await Promise.all(
                        langs.map(l => fetch(`/lang/${l}.json`).then(r => r.ok ? r.json() : {}))
                    );
                    this.translations = {};
                    langs.forEach((l, idx) => {
                        this.translations[l] = results[idx];
                    });
                } catch (err) {
                    console.error('Failed to load translations from JSON:', err);
                }
            })();
        }
        await this._fetchPromise;
        return this.translations;
    }

    get lang() {
        return this.currentLang;
    }

    async setLanguage(lang, saveToAccount = false) {
        await this.init();
        if (!this.translations[lang] || Object.keys(this.translations[lang]).length === 0) {
            lang = 'nl';
        }
        this.currentLang = lang;
        localStorage.setItem('user_language', lang);
        document.documentElement.lang = lang;

        if (saveToAccount) {
            fetch('/api/user/language', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ language: lang })
            }).catch(err => console.error('Failed to save language to account:', err));
        }

        await this.applyTranslations();
    }

    _getValue(obj, key) {
        if (!obj || typeof obj !== 'object') return undefined;
        if (Object.prototype.hasOwnProperty.call(obj, key) && obj[key] !== undefined) {
            return obj[key];
        }
        const parts = key.split('.');
        let curr = obj;
        for (const part of parts) {
            if (curr && typeof curr === 'object' && Object.prototype.hasOwnProperty.call(curr, part)) {
                curr = curr[part];
            } else {
                return undefined;
            }
        }
        return typeof curr === 'string' ? curr : undefined;
    }

    t(key, params = {}) {
        let text = this._getValue(this.translations[this.currentLang], key);
        if (text === undefined) {
            text = this._getValue(this.translations['nl'], key);
        }
        if (text === undefined) {
            text = this._getValue(this.translations['en'], key);
        }
        if (text === undefined) {
            text = key;
        }
        Object.keys(params).forEach(p => {
            text = text.replace(new RegExp(`\\{${p}\\}`, 'g'), params[p]);
        });
        return text;
    }

    async applyTranslations() {
        await this.init();

        document.documentElement.lang = this.currentLang;

        document.querySelectorAll('input[type="file"]').forEach(el => {
            el.lang = this.currentLang;
        });

        document.querySelectorAll('[data-i18n]').forEach(el => {
            const key = el.getAttribute('data-i18n');
            el.textContent = this.t(key);
        });

        document.querySelectorAll('[data-i18n-html]').forEach(el => {
            const key = el.getAttribute('data-i18n-html');
            el.innerHTML = this.t(key);
        });

        document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
            const key = el.getAttribute('data-i18n-placeholder');
            el.placeholder = this.t(key);
        });

        document.querySelectorAll('[data-i18n-title]').forEach(el => {
            const key = el.getAttribute('data-i18n-title');
            el.title = this.t(key);
        });

        const currentFlag = document.getElementById('currentLanguageFlag');
        const currentText = document.getElementById('currentLanguageText');
        if (currentFlag) {
            currentFlag.src = `images/flags/${this.currentLang}.png`;
            currentFlag.alt = this.currentLang.toUpperCase();
        }
        if (currentText) {
            const langWords = {
                nl: 'taal', en: 'language', de: 'Sprache', fr: 'langue',
                el: 'γλώσσα', es: 'idioma', it: 'lingua', pt: 'idioma',
                pl: 'język', tr: 'dil'
            };
            const translatedWord = langWords[this.currentLang] || 'language';
            currentText.textContent = `language / ${translatedWord}`;
        }

        this.sortLanguageMenu();

        document.querySelectorAll('#languageDropdownMenu .cyber-lang-item').forEach(item => {
            const isSelected = item.getAttribute('data-lang') === this.currentLang;
            const dot = item.querySelector('.active-pulse-dot');
            if (isSelected) {
                item.classList.add('active');
                if (dot) dot.style.display = 'inline-block';
            } else {
                item.classList.remove('active');
                if (dot) dot.style.display = 'none';
            }
        });
    }

    sortLanguageMenu() {
        const menu = document.getElementById('languageDropdownMenu');
        if (!menu) return;

        const items = Array.from(menu.children);
        items.sort((a, b) => {
            const titleA = a.querySelector('.lang-title')?.textContent?.trim() || a.textContent.trim();
            const titleB = b.querySelector('.lang-title')?.textContent?.trim() || b.textContent.trim();
            return titleA.localeCompare(titleB);
        });

        items.forEach(item => menu.appendChild(item));
    }
}

export const i18n = new I18n();
export default i18n;
