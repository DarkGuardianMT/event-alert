const form = document.getElementById('filter-form');
const searchInput = document.getElementById('search-filter');
const cityInput = document.getElementById('city-filter');
const categoryInput = document.getElementById('category-filter');
const fromInput = document.getElementById('from-filter');
const toInput = document.getElementById('to-filter');
const clearButton = document.getElementById('clear-filters');
const grid = document.getElementById('event-grid');
const resultCount = document.getElementById('result-count');
const statusPanel = document.getElementById('event-status');
const statusTitle = document.getElementById('status-title');
const statusMessage = document.getElementById('status-message');
const languageButtons = [...document.querySelectorAll('[data-language]')];
const ui = window.EventAlertUI;

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
    categoryLabel: 'Categorie',
    allCategories: 'Alle categorieën',
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
    categoryLabel: 'Category',
    allCategories: 'All categories',
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
let categoriesLoaded = false;
let availableCategories = [];
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
  const text = translations[language];
  ui.applyTranslations(language, text);
  updateCategoryFilterLabels();

  if (persist) {
    ui.saveLanguage(language);
  }

  if (isReady && !isLoading) {
    renderEvents();
  } else if (currentState) {
    showState(currentState);
  }
}

function createEventCard(event) {
  const text = translations[currentLanguage];
  const card = document.createElement('a');
  card.className = 'event-card';
  card.href = `event.html?id=${encodeURIComponent(event.id)}`;
  card.setAttribute('aria-label', `${text.viewEvent}: ${event.title || text.missingTitle}`);

  const date = document.createElement('time');
  date.className = 'event-date';
  if (event.start_date) {
    date.dateTime = event.start_time
      ? `${event.start_date}T${event.start_time}`
      : event.start_date;
  }
  date.textContent = ui.formatEventDate(
    event.start_date,
    event.end_date,
    currentLanguage,
    event.start_time,
    event.end_time
  ) || event.date_text || text.missingDate;
  card.append(date);

  const title = document.createElement('h3');
  title.textContent = event.title || text.missingTitle;
  card.append(title);

  const categories = ui.createCategoryChips(event.categories, currentLanguage, 3);
  if (categories.childElementCount) {
    card.append(categories);
  }

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

  const linkLabel = document.createElement('span');
  linkLabel.className = 'event-link';
  linkLabel.textContent = text.viewEvent;
  const arrow = document.createElement('span');
  arrow.setAttribute('aria-hidden', 'true');
  arrow.textContent = '→';
  linkLabel.append(arrow);
  footer.append(linkLabel);
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

function updateCategoryFilterLabels() {
  const defaultOption = categoryInput.querySelector('option[value=""]');
  if (defaultOption) {
    defaultOption.textContent = translations[currentLanguage].allCategories;
  }
  const nameField = currentLanguage === 'en' ? 'name_en' : 'name_nl';
  availableCategories.forEach((category) => {
    const option = [...categoryInput.options].find((item) => item.value === category.slug);
    if (option) {
      option.textContent = category[nameField];
    }
  });
}

function populateCategoryFilter(events) {
  const uniqueCategories = new Map();
  events.forEach((event) => {
    const categories = Array.isArray(event.categories) ? event.categories : [];
    categories.forEach((category) => {
      if (category?.slug && !uniqueCategories.has(category.slug)) {
        uniqueCategories.set(category.slug, category);
      }
    });
  });
  availableCategories = [...uniqueCategories.values()];
  availableCategories.forEach((category) => {
    const option = document.createElement('option');
    option.value = category.slug;
    categoryInput.append(option);
  });
  updateCategoryFilterLabels();
  categoriesLoaded = true;
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
    if (!categoriesLoaded) {
      populateCategoryFilter(payload.events);
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
  return fetchEvents({
    city: cityInput.value,
    category: categoryInput.value,
    from: fromInput.value,
    to: toInput.value,
  });
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

setLanguage(ui.getSavedLanguage(), false);
fetchEvents();
