# RoastApp

A browser-based coffee roast tracker. Log roasting sessions, manage bean inventory, and visualize weight loss trends over time.

![Python](https://img.shields.io/badge/Python-Flask-c05808) ![SQLite](https://img.shields.io/badge/Database-SQLite-e8a020) ![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205-f5b010)

## Features

- **Roast logging** — record date, bean type, start weight, and end weight; weight loss is calculated automatically
- **Roast history** — scrollable table of all roasts with edit and delete support
- **Interactive chart** — weight loss (%) over time with per-bean toggle pills, scroll/pinch zoom, and pan
- **Bean management** — add, edit, and delete bean types with process type and inventory tracking
- **CSV import** — import historical roasts from a CSV file with a row-by-row preview before committing

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| Database | SQLite (`roastapp.db`) |
| Frontend | Jinja2 + Bootstrap 5 |
| Charting | Chart.js 4 + chartjs-plugin-zoom |

## Getting Started

**Prerequisites:** Python 3.8+

```bash
# Clone the repo
git clone https://github.com/tdfguy2002/RoastApp.git
cd RoastApp

# Install dependencies
pip install flask

# Run the app
python app.py
```

Then open [http://localhost:3000](http://localhost:3000) in your browser.

## CSV Import Format

Roasts can be imported from a CSV file. The expected column layout is:

| Index | Content |
|-------|---------|
| 0 | Ignored |
| 1 | Date (`MM/DD/YYYY`) |
| 2 | Start weight (grams) |
| 3 | End weight (grams) |
| 4–6 | Ignored |
| 7 | Bean name (optional — defaults to *Espresso Monkey*) |

- Rows with unrecognised bean names are flagged in the preview; add the bean first and re-import
- A full preview of valid and invalid rows is shown before anything is saved

## Data Model

**`beans`** — bean types available for roasting

| Column | Type | Notes |
|--------|------|-------|
| id | integer | primary key |
| name | text | unique |
| process_type | text | Washed / Natural / Honey / Wet-Hulled |
| inventory_g | real | current stock in grams |

**`roasts`** — individual roast sessions

| Column | Type | Notes |
|--------|------|-------|
| id | integer | primary key |
| date | text | ISO format (YYYY-MM-DD) |
| bean_id | integer | foreign key → beans.id |
| start_weight_g | real | grams |
| end_weight_g | real | grams |
| weight_loss_g | real | calculated: start − end |
