// i18n.js - Internationalization module for VibeCodeTask
class I18n {
    constructor() {
        // Check URL path first, then localStorage, then default to 'en'
        this.currentLang = this.getLangFromURL() || localStorage.getItem('vct-language') || 'en';
        this.translations = {};
        this.loadedLanguages = new Set();
    }
    
    getLangFromURL() {
        // Check if URL contains language code
        const path = window.location.pathname;
        const match = path.match(/^\/(en|zh)(\/|$)/);
        return match ? match[1] : null;
    }

    async init() {
        await this.loadLanguage(this.currentLang);
    }

    async loadLanguage(lang) {
        if (this.loadedLanguages.has(lang)) {
            return this.translations[lang];
        }

        try {
            const response = await fetch(`/i18n/${lang}.json`);
            if (!response.ok) {
                throw new Error(`Failed to load language: ${lang}`);
            }
            this.translations[lang] = await response.json();
            this.loadedLanguages.add(lang);
            return this.translations[lang];
        } catch (error) {
            console.error(`Error loading language ${lang}:`, error);
            // Fallback to English if loading fails
            if (lang !== 'en') {
                return await this.loadLanguage('en');
            }
            throw error;
        }
    }

    async setLanguage(lang, updateURL = true) {
        await this.loadLanguage(lang);
        this.currentLang = lang;
        localStorage.setItem('vct-language', lang);
        
        // Optionally update URL
        if (updateURL && window.history) {
            const currentPath = window.location.pathname;
            let newPath = currentPath;
            
            // Remove existing language from path
            newPath = newPath.replace(/^\/(en|zh)(\/|$)/, '/');
            
            // Add new language to path
            if (lang !== 'en') { // Only add language code if not English (default)
                newPath = `/${lang}${newPath}`;
            }
            
            // Update URL without reloading page
            if (currentPath !== newPath) {
                window.history.pushState({lang: lang}, '', newPath);
            }
        }
        
        this.updateDOM();
    }

    t(key, params = {}) {
        const keys = key.split('.');
        let value = this.translations[this.currentLang];
        
        for (const k of keys) {
            if (value && typeof value === 'object') {
                value = value[k];
            } else {
                console.warn(`Translation key not found: ${key}`);
                return key;
            }
        }

        // Replace parameters like {n} with actual values
        if (typeof value === 'string' && Object.keys(params).length > 0) {
            let result = value;
            for (const [param, val] of Object.entries(params)) {
                result = result.replace(new RegExp(`\\{${param}\\}`, 'g'), val);
            }
            return result;
        }

        return value || key;
    }

    updateDOM() {
        // Update all elements with data-i18n attribute
        document.querySelectorAll('[data-i18n]').forEach(element => {
            const key = element.getAttribute('data-i18n');
            const text = this.t(key);
            
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
                const attr = element.getAttribute('data-i18n-attr') || 'placeholder';
                element.setAttribute(attr, text);
            } else {
                element.textContent = text;
            }
        });

        // Update document title
        document.title = this.t('app.title');

        // Dispatch event for custom handlers
        window.dispatchEvent(new CustomEvent('languageChanged', { 
            detail: { language: this.currentLang } 
        }));
    }

    getCurrentLanguage() {
        return this.currentLang;
    }

    getAvailableLanguages() {
        return [
            { code: 'en', name: 'English', flag: '🇬🇧' },
            { code: 'zh', name: '中文', flag: '🇨🇳' }
        ];
    }
}

// Create global instance
window.i18n = new I18n();