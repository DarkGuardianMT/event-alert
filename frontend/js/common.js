window.EventAlertUI = (() => {
  const languageStorageKey = 'event-alert-language';
  const monthFormatters = {
    nl: new Intl.DateTimeFormat('nl-NL', { month: 'short', timeZone: 'UTC' }),
    en: new Intl.DateTimeFormat('en-US', { month: 'short', timeZone: 'UTC' }),
  };

  function getSavedLanguage() {
    try {
      const language = window.localStorage.getItem(languageStorageKey);
      return language === 'en' ? 'en' : 'nl';
    } catch {
      // Zonder opslag blijft Nederlands de standaardtaal.
      return 'nl';
    }
  }

  function saveLanguage(language) {
    try {
      window.localStorage.setItem(languageStorageKey, language);
    } catch {
      // De taalwissel blijft werken als opslag niet beschikbaar is.
    }
  }

  function applyTranslations(language, text) {
    document.documentElement.lang = language;
    document.querySelectorAll('[data-i18n]').forEach((element) => {
      element.textContent = text[element.dataset.i18n];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((element) => {
      element.placeholder = text[element.dataset.i18nPlaceholder];
    });
    document.querySelectorAll('[data-i18n-aria-label]').forEach((element) => {
      element.setAttribute('aria-label', text[element.dataset.i18nAriaLabel]);
    });
    document.title = text.pageTitle;
    document.querySelector('meta[name="description"]').content = text.pageDescription;
    document.querySelectorAll('[data-language]').forEach((button) => {
      button.setAttribute('aria-pressed', String(button.dataset.language === language));
    });
  }

  function parseApiDate(value) {
    if (typeof value !== 'string' || !/^\d{4}-\d{2}-\d{2}$/.test(value)) {
      return null;
    }

    const [year, month, day] = value.split('-').map(Number);
    const date = new Date(Date.UTC(year, month - 1, day));
    if (date.getUTCFullYear() !== year || date.getUTCMonth() + 1 !== month || date.getUTCDate() !== day) {
      return null;
    }
    return date;
  }

  function formatEventDate(startValue, endValue, language) {
    const start = parseApiDate(startValue);
    if (!start) {
      return '';
    }

    const end = parseApiDate(endValue);
    const startDay = start.getUTCDate();
    const startMonth = monthFormatters[language].format(start);
    const startYear = start.getUTCFullYear();

    if (!end || end <= start) {
      return `${startDay} ${startMonth} ${startYear}`;
    }

    const endDay = end.getUTCDate();
    const endMonth = monthFormatters[language].format(end);
    const endYear = end.getUTCFullYear();

    if (startYear === endYear && start.getUTCMonth() === end.getUTCMonth()) {
      return `${startDay} – ${endDay} ${startMonth} ${startYear}`;
    }
    if (startYear === endYear) {
      return `${startDay} ${startMonth} – ${endDay} ${endMonth} ${startYear}`;
    }
    return `${startDay} ${startMonth} ${startYear} – ${endDay} ${endMonth} ${endYear}`;
  }

  function safeSourceUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === 'http:' || url.protocol === 'https:' ? url.href : null;
    } catch {
      return null;
    }
  }

  return { getSavedLanguage, saveLanguage, applyTranslations, formatEventDate, safeSourceUrl };
})();
