const form = document.getElementById('filter-form');
const searchInput = document.getElementById('search-filter');
const cityInput = document.getElementById('city-filter');
const fromInput = document.getElementById('from-filter');
const toInput = document.getElementById('to-filter');
const clearButton = document.getElementById('clear-filters');
const grid = document.getElementById('event-grid');
const resultCount = document.getElementById('result-count');
const statusPanel = document.getElementById('event-status');
const statusTitle = document.getElementById('status-title');
const statusMessage = document.getElementById('status-message');
const languageButtons = [...document.querySelectorAll('[data-language]')];
const metaDescription = document.querySelector('meta[name="description"]');
const languageStorageKey = 'event-alert-language';
const monthFormatters = {
  nl: new Intl.DateTimeFormat('nl-NL', { month: 'short', timeZone: 'UTC' }),
  en: new Intl.DateTimeFormat('en-US', { month: 'short', timeZone: 'UTC' }),
};

const translations = {
  nl: {
    pageTitle: 'Event Alert — Evenementen bij jou in de buurt',
    pageDescription: 'Vind lokale evenementen en activiteiten in Gouda en omliggende plaatsen.',
    brandLabel: 'Event Alert startpagina',
    navLabel: 'Hoofdnavigatie',
    filterLabel: 'Evenementen zoeken',
    nav: 'Evenementen',
    heroEyebrow: 'Lokaal ontdekken, eenvoudig gemaakt',
    heroHeading: 'Ontdek wat er gebeurt',
    heroAccent: 'bij jou in de buurt.',
    heroCopy: 'Vind lokale evenementen, activiteiten en ontmoetingen in Gouda en omliggende plaatsen.',
    searchLabel: 'Zoeken',
    searchPlaceholder: 'Zoek evenementen...',
    cityLabel: 'Plaats',
    allCities: 'Alle plaatsen',
    fromDate: 'Vanaf',
    toDate: 'Tot en met',
    findEvents: 'Zoek evenementen',
    clearFilters: 'Filters wissen',
    sectionEyebrow: 'Dichter bij huis',
    sectionHeading: 'Ontdek lokale evenementen',
    footerTagline: 'Lokale evenementen op één plek.',
    footerNote: 'Gegevens komen uit openbare evenementbronnen.',
    eventSingular: 'evenement',
    eventPlural: 'evenementen',
    viewEvent: 'Bekijk evenement',
    opensNewTab: 'opent in een nieuw tabblad',
    missingLocation: 'Locatie beschikbaar op evenementpagina',
    missingDate: 'Datum nog niet bekend',
    missingTitle: 'Evenement zonder titel',
    missingCity: 'Plaats niet vermeld',
    missingSource: 'Bron niet vermeld',
    states: {
      loading: ['Evenementen laden...', 'We zoeken activiteiten bij jou in de buurt.', 'Evenementen zoeken…'],
      empty: ['Geen evenementen gevonden', 'Probeer een andere plaats of periode.', '0 evenementen'],
      error: ['We konden de evenementen niet laden.', 'Probeer het straks opnieuw.', 'Evenementen niet beschikbaar'],
      dates: ['Controleer je datums', 'De begindatum mag niet na de einddatum liggen.', 'Controleer datums'],
    },
  },
  en: {
    pageTitle: 'Event Alert — Local events near you',
    pageDescription: 'Find local events and community activities in Gouda and nearby cities.',
    brandLabel: 'Event Alert home',
    navLabel: 'Main navigation',
    filterLabel: 'Find events',
    nav: 'Events',
    heroEyebrow: 'Local discovery, made simple',
    heroHeading: 'Discover what’s happening',
    heroAccent: 'near you.',
    heroCopy: 'Find local events, activities and community experiences in Gouda and surrounding cities.',
    searchLabel: 'Search',
    searchPlaceholder: 'Search events...',
    cityLabel: 'City',
    allCities: 'All cities',
    fromDate: 'From date',
    toDate: 'To date',
    findEvents: 'Find events',
    clearFilters: 'Clear filters',
    sectionEyebrow: 'A little closer to home',
    sectionHeading: 'Explore local events',
    footerTagline: 'Local events in one place.',
    footerNote: 'Data is collected from public event sources.',
    eventSingular: 'event',
    eventPlural: 'events',
    viewEvent: 'View event',
    opensNewTab: 'opens in a new tab',
    missingLocation: 'Location available on event page',
    missingDate: 'Date to be confirmed',
    missingTitle: 'Untitled event',
    missingCity: 'City not listed',
    missingSource: 'Event source',
    states: {
      loading: ['Loading events...', 'Finding things to do near you.', 'Finding events…'],
      empty: ['No events found', 'Try changing your city or date filters.', '0 events'],
      error: ['We couldn’t load the events.', 'Please try again in a moment.', 'Events unavailable'],
      dates: ['Check your dates', 'The from date must be on or before the to date.', 'Check your dates'],
    },
  },
};

let currentEvents = [];
let citiesLoaded = false;
let isReady = false;
let isLoading = false;
let latestRequest = 0;
let currentLanguage = 'nl';
let currentState = 'loading';

function eventCountLabel(count) {
  const text = translations[currentLanguage];
  return `${count} ${count === 1 ? text.eventSingular : text.eventPlural}`;
}

function setLanguage(language, persist = true) {
  if (!translations[language]) {
    return;
  }
  currentLanguage = language;
  document.documentElement.lang = language;
  const text = translations[language];

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
  metaDescription.content = text.pageDescription;
  languageButtons.forEach((button) => {
    button.setAttribute('aria-pressed', String(button.dataset.language === language));
  });

  if (persist) {
    try {
      window.localStorage.setItem(languageStorageKey, language);
    } catch {
      // De interface blijft werken als opslag niet beschikbaar is.
    }
  }

  if (isReady && !isLoading) {
    renderEvents();
  } else if (currentState) {
    showState(currentState);
  }
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

function formatEventDate(startValue, endValue) {
  const start = parseApiDate(startValue);
  if (!start) {
    return '';
  }

  const end = parseApiDate(endValue);
  const startDay = start.getUTCDate();
  const startMonth = monthFormatters[currentLanguage].format(start);
  const startYear = start.getUTCFullYear();

  if (!end || end <= start) {
    return `${startDay} ${startMonth} ${startYear}`;
  }

  const endDay = end.getUTCDate();
  const endMonth = monthFormatters[currentLanguage].format(end);
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

function createEventCard(event) {
  const text = translations[currentLanguage];
  const card = document.createElement('article');
  card.className = 'event-card';

  const date = document.createElement('time');
  date.className = 'event-date';
  if (event.start_date) {
    date.dateTime = event.start_date;
  }
  date.textContent = formatEventDate(event.start_date, event.end_date) || event.date_text || text.missingDate;
  card.append(date);

  const title = document.createElement('h3');
  title.textContent = event.title || text.missingTitle;
  card.append(title);

  const details = document.createElement('div');
  details.className = 'event-details';
  const location = document.createElement('p');
  location.className = 'event-location';
  location.textContent = event.location || text.missingLocation;
  const city = document.createElement('p');
  city.className = 'event-city';
  city.textContent = event.city || text.missingCity;
  details.append(location, city);
  card.append(details);

  const footer = document.createElement('div');
  footer.className = 'event-card-footer';
  const source = document.createElement('span');
  source.className = 'event-source';
  source.textContent = event.source || text.missingSource;
  footer.append(source);

  const sourceUrl = safeSourceUrl(event.source_url);
  if (sourceUrl) {
    const link = document.createElement('a');
    link.className = 'event-link';
    link.href = sourceUrl;
    link.target = '_blank';
    link.rel = 'noopener noreferrer';
    link.setAttribute('aria-label', `${text.viewEvent}: ${event.title || text.missingTitle} (${text.opensNewTab})`);
    link.textContent = text.viewEvent;
    const arrow = document.createElement('span');
    arrow.setAttribute('aria-hidden', 'true');
    arrow.textContent = '↗';
    link.append(arrow);
    footer.append(link);
  }
  card.append(footer);

  return card;
}

function showState(state) {
  currentState = state;
  const [title, message, countLabel] = translations[currentLanguage].states[state];
  statusTitle.textContent = title;
  statusMessage.textContent = message;
  resultCount.textContent = countLabel;
  statusPanel.hidden = false;
  grid.hidden = true;
  grid.replaceChildren();
}

function applySearch(events) {
  const query = searchInput.value.trim().toLocaleLowerCase();
  if (!query) {
    return events;
  }
  return events.filter((event) =>
    `${event.title || ''} ${event.location || ''}`.toLocaleLowerCase().includes(query)
  );
}

function renderEvents() {
  const events = applySearch(currentEvents);
  resultCount.textContent = eventCountLabel(events.length);
  if (!events.length) {
    showState('empty');
    return;
  }

  const cards = document.createDocumentFragment();
  events.forEach((event) => cards.append(createEventCard(event)));
  grid.replaceChildren(cards);
  grid.hidden = false;
  statusPanel.hidden = true;
  currentState = null;
}

function populateCityFilter(events) {
  const cities = [...new Set(events.map((event) => event.city).filter(Boolean))]
    .sort((first, second) => first.localeCompare(second));
  cities.forEach((city) => {
    const option = document.createElement('option');
    option.value = city;
    option.textContent = city;
    cityInput.append(option);
  });
  citiesLoaded = true;
}

async function fetchEvents(filters = {}) {
  const requestNumber = ++latestRequest;
  isLoading = true;
  isReady = false;
  showState('loading');

  const url = new URL('../api/events/', window.location.href);
  for (const [name, value] of Object.entries(filters)) {
    if (value) {
      url.searchParams.set(name, value);
    }
  }

  try {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) {
      throw new Error(`Events API returned HTTP ${response.status}`);
    }
    const payload = await response.json();
    if (!payload.success || !Array.isArray(payload.events)) {
      throw new Error('Events API returned an invalid response');
    }
    if (requestNumber !== latestRequest) {
      return;
    }

    currentEvents = payload.events;
    if (!citiesLoaded) {
      populateCityFilter(payload.events);
    }
    isLoading = false;
    isReady = true;
    renderEvents();
  } catch (error) {
    if (requestNumber !== latestRequest) {
      return;
    }
    console.error('Could not load events:', error);
    isLoading = false;
    isReady = false;
    showState('error');
  }
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  if (fromInput.value && toInput.value && fromInput.value > toInput.value) {
    latestRequest++;
    isLoading = false;
    isReady = false;
    showState('dates');
    return;
  }
  return fetchEvents({ city: cityInput.value, from: fromInput.value, to: toInput.value });
});

searchInput.addEventListener('input', () => {
  if (isReady && !isLoading) {
    renderEvents();
  }
});

clearButton.addEventListener('click', () => {
  form.reset();
  return fetchEvents();
});

languageButtons.forEach((button) => {
  button.addEventListener('click', () => setLanguage(button.dataset.language));
});

let savedLanguage = 'nl';
try {
  const storedLanguage = window.localStorage.getItem(languageStorageKey);
  if (translations[storedLanguage]) {
    savedLanguage = storedLanguage;
  }
} catch {
  // De eerste taalkeuze blijft Nederlands als opslag niet beschikbaar is.
}
setLanguage(savedLanguage, false);
fetchEvents();
