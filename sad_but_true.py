import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium", app_title="Sad but true")


@app.cell
def _():
    # Sad but true
    # Das Durcheinander des Saarbahn-Fahrplans - einfach dargestellt

    # Idee https://stb.brightel.uk/ und https://v6.db.transport.rest/

    # September 2025, marcus@dankesuper.de

    import marimo as mo

    # Haltestellen finden
    # curl 'https://v6.db.transport.rest/locations?poi=false&addresses=false&query=hauptbahnhof,saarbruecken' -s | jq | less

    show_departures = 6
    return mo, show_departures


@app.cell
def _(mo):
    mo.md(r"""## Abfahrtszeiten der Saarbahn""")
    return


@app.cell
def _(mo):
    # haltstellen
    # mit name, api-id

    stops = {
        "Auersmacher Bahnhof": "839419",
        "Brebach Bahnhof": "839427",
        "Bübingen Bahnhof": "839428",
        "Cottbuser Platz": "839433",
        "Eiweiler": "836587",
        "Eiweiler Nord": "836588",
        "Gisorsstraße": "839548",
        "Güchenbach": "836533",
        "Güdingen Bahnhof": "839421",
        "Hanweiler Bahnhof": "839426",
        #"Hauptbahnhof": "836075",
        "Hauptbahnhof": "8000323",
        "Heinrichshaus": "838333",
        "Hellwigstraße": "837196",
        "In der Hommersbach": "837275",
        "Johanneskirche": "838107",
        "Kaiserstraße": "835228",
        "Kieselhumes": "837234",
        "Kirchstraße": "836341",
        "Kirschhof": "836586",
        "Kleinblittersdorf Bahnhof": "8003318",
        "Landsweiler Nord": "836590",
        "Landsweiler Süd": "836589",
        "Landwehrplatz": "838367",
        "Lebach": "8000563",
        "Lebach Süd": "836591",
        "Lebach-Jabach": "8007868",
        "Lugwigstraße": "835814",
        "Markt": "836472",
        "Mühlenstraße": "836475",
        "Pariser Platz": "836174",
        "Rastphul": "837878",
        "Rathaus": "837116",
        "Riegelsberg Süd": "839562",
        "Römerkastell": "836945",
        "Sarreguemines": "8700439",
        "Schulzentrum": "835885",
        "Siedlerheim": "835558",
        "Trierer Straße": "836375",
        "Uhlandstraße": "836104",
        "Walpershofen Mitte": "836412",
        "Walpershofen/Etzenhofen": "836348",
        "Wolfskaulstraße": "836831"
    }

    dropdown = mo.ui.dropdown(
        options=stops,
        label="Haltestelle",
        searchable=True
    )
    dropdown
    return (dropdown,)


@app.cell
def _(mo):
    # fan von fibonacci-zahlen?
    # https://oeis.org/A000045
    refresh = mo.ui.refresh(
        options=["2m", "3m", "5m", "8m"],
        default_interval="5m"
    )
    refresh
    return (refresh,)


@app.cell
def _(dropdown, mo, refresh, show_departures):
    # v6.db.transport.rest-api abfragen
    # nach abfahrtszeiten fuer die ausgewaehlte haltstelle

    import requests

    mo.stop(not dropdown.value)

    refresh

    base_url = "https://v6.db.transport.rest/stops"
    url = f"{base_url}/{dropdown.value}/departures"

    response = requests.get(url)
    fehler = None

    if response.status_code == 200:
        data = response.json()

        trams = []
        next_departures = data['departures'][:show_departures]

        for departure in next_departures:
            # uns interessiert nur die Saarbahn stb-1
            if departure['line']['id'] == "stb-1":
                trams.append({
                    'tripId': departure['tripId'],
                    'plannedWhen': departure['plannedWhen'],
                    'direction': departure['direction'],
                    'delay': departure.get('delay') or 0,
                    'cancelled': departure.get('cancelled', False)
                })
    else:
        fehler = mo.md(
            f"HTTP-Fehler: {response.status_code}"
        )

    fehler
    return (trams,)


@app.cell
def _(mo, refresh, trams):
    from datetime import datetime
    import pytz

    refresh

    # tabelle erstellen
    table_html = """
    <style>
        .tram-table {
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            color: var(--text-color, #000);
            background-color: var(--bg-color, #fff);
        }
        .tram-table th {
            background-color: var(--header-bg, #f2f2f2);
            border: 1px solid var(--border-color, #ddd);
            padding: 12px;
            text-align: left;
            color: var(--header-text, #000);
        }
        .tram-table td {
            border: 1px solid var(--border-color, #ddd);
            padding: 12px;
        }
        .row-even {
            background-color: var(--row-even-bg, #f9f9f9);
        }
        .row-odd {
            background-color: var(--row-odd-bg, #ffffff);
        }
        .cancelled {
            color: var(--cancelled-color, red);
            text-decoration: line-through;
        }

        /* Dark mode */
        @media (prefers-color-scheme: dark) {
            .tram-table {
                --text-color: #e0e0e0;
                --bg-color: #1a1a1a;
                --header-bg: #2a2a2a;
                --header-text: #e0e0e0;
                --border-color: #404040;
                --row-even-bg: #222222;
                --row-odd-bg: #1a1a1a;
                --cancelled-color: #ff6b6b;
            }
        }
    </style>
    <table class="tram-table">
        <thead>
            <tr>
                <th>Uhrzeit</th>
                <th>Richtung</th>
                <th>Verspätung</th>
            </tr>
        </thead>
        <tbody>
    """

    for i, tram in enumerate(trams):
        # uhrzeit extrahieren und formatieren
        planned_dt = datetime.fromisoformat(tram['plannedWhen'].replace('Z', '+00:00'))
        german_tz = pytz.timezone('Europe/Berlin')
        german_time = planned_dt.astimezone(german_tz)
        time_str = german_time.strftime('%H:%M')

        # richtung mit Pfeil
        direction_str = f"→ {tram['direction']}"

        # verspaetung
        delay_str = ""
        if tram['delay'] > 0:
            delay_str = f"{tram['delay'] // 60} min"

        # css-klasse für abwechselnde farben in tabellenzeilen
        row_class = "row-even" if i % 2 == 0 else "row-odd"

        # durchstreichen wenn cancelled
        cell_class = "cancelled" if tram['cancelled'] else ""

        table_html += f"""
            <tr class="{row_class}">
                <td class="{cell_class}">{time_str}</td>
                <td class="{cell_class}">{direction_str}</td>
                <td class="{cell_class}">{delay_str}</td>
            </tr>
        """

    table_html += """
        </tbody>
    </table>
    """

    mo.Html(table_html)
    return


@app.cell(hide_code=True)
def _(dropdown, mo):
    mo.stop(not dropdown.value)

    mo.md(
        f"""
        Ohne Gewähr - muss nicht stimmen.  
        Erstellt mit [Marimo](https://marimo.io/).
        """
    )
    return


if __name__ == "__main__":
    app.run()
