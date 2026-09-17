import requests
from bs4 import BeautifulSoup


SOURCE_URL = "https://www.gouda.nl/evenementenkalender/"


def fetch_events():
    response = requests.get(SOURCE_URL, timeout=30)
    response.raise_for_status()
    soup = BeautifulSoup(response.content, "html.parser")
    events = []

    for table in soup.find_all("table"):
        headers = [cell.get_text(strip=True) for cell in table.find_all("th")]
        if headers != ["Wanneer", "Wat", "Waar"]:
            continue

        for row in table.find_all("tr"):
            cells = row.find_all("td", recursive=False)
            if len(cells) not in (2, 3):
                continue

            date_text = cells[0].get_text(" ", strip=True)
            title = cells[1].get_text(" ", strip=True)
            if not date_text or not title:
                continue

            location = cells[2].get_text(" ", strip=True) if len(cells) == 3 else ""
            events.append({
                "title": title,
                "date_text": date_text,
                "time_text": None,
                "description": None,
                "location": location,
                "city": "Gouda",
                "source": "Gemeente Gouda",
                "source_url": SOURCE_URL,
            })

    return events
