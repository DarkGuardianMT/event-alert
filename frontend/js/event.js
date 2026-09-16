const ui = window.EventAlertUI;
const languageButtons = [...document.querySelectorAll('[data-language]')];
const statusPanel = document.getElementById('detail-status');
const statusTitle = document.getElementById('detail-status-title');
const statusMessage = document.getElementById('detail-status-message');
const detail = document.getElementById('event-detail');
const detailDate = document.getElementById('detail-date');
const detailTitle = document.getElementById('detail-title');
const detailCategories = document.getElementById('detail-categories');
const detailCity = document.getElementById('detail-city');
const detailLocation = document.getElementById('detail-location');
const detailSource = document.getElementById('detail-source');
const originalSource = document.getElementById('original-source');

const translations = {
  nl: {
    pageTitle: 'Evenement bekijken — Event Alert',
    pageDescription: 'Bekijk een lokaal evenement bij Event Alert.',
    brandLabel: 'Event Alert startpagina',
    navLabel: 'Hoofdnavigatie',
    nav: 'Evenementen',
    back: 'Terug naar evenementen',
    eventKicker: 'Lokaal evenement',
    cityLabel: 'Plaats',
    locationLabel: 'Locatie',
    sourceLabel: 'Bron',
    originalSource: 'Bekijk originele bron',
    sourceLinkLabel: 'Bekijk originele bron (opent in een nieuw tabblad)',
    footerTagline: 'Lokale evenementen op één plek.',
    footerNote: 'Gegevens komen uit openbare evenementbronnen.',
    missingLocation: 'Locatie beschikbaar op evenementpagina',
    missingDate: 'Datum nog niet bekend',
    missingCity: 'Plaats niet vermeld',
    missingSource: 'Bron niet vermeld',
    states: {
      loading: ['Evenement laden...', 'Even geduld, we halen het evenement op.'],
      invalid: ['Ongeldige evenementlink', 'Ga terug naar de evenementen en kies een evenement.'],
      notFound: ['Evenement niet gevonden', 'Dit evenement is niet meer beschikbaar.'],
      error: ['Evenement niet beschikbaar', 'Probeer het straks opnieuw.'],
    },
  },
  en: {
    pageTitle: 'View event — Event Alert',
    pageDescription: 'View a local event at Event Alert.',
    brandLabel: 'Event Alert home',
    navLabel: 'Main navigation',
    nav: 'Events',
    back: 'Back to events',
    eventKicker: 'Local event',
    cityLabel: 'City',
    locationLabel: 'Location',
    sourceLabel: 'Source',
    originalSource: 'View original source',
    sourceLinkLabel: 'View original source (opens in a new tab)',
    footerTagline: 'Local events in one place.',
    footerNote: 'Data is collected from public event sources.',
    missingLocation: 'Location available on event page',
    missingDate: 'Date to be confirmed',
    missingCity: 'City not listed',
    missingSource: 'Source not listed',
    states: {
      loading: ['Loading event...', 'Just a moment while we load this event.'],
      invalid: ['Invalid event link', 'Go back to the event list and choose an event.'],
      notFound: ['Event not found', 'This event is no longer available.'],
      error: ['Event unavailable', 'Please try again in a moment.'],
    },
  },
};

let currentLanguage = 'nl';
let currentState = 'loading';
let currentEvent = null;

function showState(state) {
  currentState = state;
  [statusTitle.textContent, statusMessage.textContent] = translations[currentLanguage].states[state];
  statusPanel.hidden = false;
  detail.hidden = true;
}

function renderEvent() {
  const event = currentEvent;
  const text = translations[currentLanguage];
  detailDate.textContent = ui.formatEventDate(event.start_date, event.end_date, currentLanguage)
    || event.date_text || text.missingDate;
  if (event.start_date) {
    detailDate.dateTime = event.start_date;
  }
  detailTitle.textContent = event.title;
  const categories = ui.createCategoryChips(event.categories, currentLanguage);
  detailCategories.replaceChildren(...categories.childNodes);
  detailCategories.hidden = !detailCategories.childElementCount;
  document.title = `${event.title} — Event Alert`;
  detailCity.textContent = event.city || text.missingCity;
  detailLocation.textContent = event.location || text.missingLocation;
  detailSource.textContent = event.source || text.missingSource;

  const sourceUrl = ui.safeSourceUrl(event.source_url);
  originalSource.hidden = !sourceUrl;
  if (sourceUrl) {
    originalSource.href = sourceUrl;
  } else {
    originalSource.removeAttribute('href');
  }

  detail.hidden = false;
  statusPanel.hidden = true;
  currentState = null;
}

function setLanguage(language, persist = true) {
  if (!translations[language]) {
    return;
  }
  currentLanguage = language;
  ui.applyTranslations(language, translations[language]);
  if (persist) {
    ui.saveLanguage(language);
  }
  if (currentEvent) {
    renderEvent();
  } else if (currentState) {
    showState(currentState);
  }
}

function getEventId() {
  const ids = new URLSearchParams(window.location.search).getAll('id');
  if (ids.length !== 1 || !/^[1-9][0-9]*$/.test(ids[0])) {
    return null;
  }
  const number = Number(ids[0]);
  return Number.isSafeInteger(number) && number <= 2147483647 ? ids[0] : null;
}

async function loadEvent(id) {
  const url = new URL('../api/event/', window.location.href);
  url.searchParams.set('id', id);
  try {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (response.status === 404) {
      showState('notFound');
      return;
    }
    if (!response.ok) {
      showState('error');
      return;
    }
    const payload = await response.json();
    if (!payload.success || !payload.event || String(payload.event.id) !== id) {
      showState('error');
      return;
    }
    currentEvent = payload.event;
    renderEvent();
  } catch {
    showState('error');
  }
}

languageButtons.forEach((button) => {
  button.addEventListener('click', () => setLanguage(button.dataset.language));
});

setLanguage(ui.getSavedLanguage(), false);
const id = getEventId();
if (id) {
  loadEvent(id);
} else {
  showState('invalid');
}
