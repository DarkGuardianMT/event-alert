# Development Rules

These rules apply to the entire Event Alert repository.

## Technology stack

- Use PHP for the website and application logic.
- Use MySQL for persistent data storage.
- Use vanilla JavaScript for browser-side behavior.
- Use Python for collecting and scraping event data.
- Do not introduce React, Vue, Node.js, or other frameworks without prior approval.

## Development approach

- Keep the code simple, readable, and understandable.
- Prefer small, incremental changes over broad rewrites.
- Create a separate Python scraper module for each event source.
- Do not add AI-based functionality unless it is explicitly requested.
- Explain important architectural changes before making large refactors.

## Language and version control

- Write commit messages in English and follow the Conventional Commits format.
- Write code comments in Dutch where comments are useful.

## Security

- Never commit API keys, passwords, secrets, or environment-specific credentials.
- Keep sensitive configuration outside version control.
