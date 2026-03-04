# RoastApp

A browser-based coffee roast tracker. Log roasting sessions, manage bean inventory, and visualize weight loss trends over time.

![Python](https://img.shields.io/badge/Python-Flask-6aa9e3) ![SQLite](https://img.shields.io/badge/Database-SQLite-6aa9e3) ![Bootstrap](https://img.shields.io/badge/UI-Bootstrap%205-6aa9e3)

## Features

- **Dashboard** — at-a-glance stats (total roasts, avg weight loss, total weight roasted, inventory value), recent roasts, and bean inventory progress bars with low-stock alerts
- **Roast logging** — record date, bean type, start weight, and end weight; weight loss calculated automatically; start weight deducted from inventory
- **Behmor roast timing** — optionally log first crack time, C button usage, and +/− presses to calculate total roast time
- **Roast history** — scrollable table with First Crack and Total Time columns; edit and delete support
- **Interactive chart** — weight loss (% or g) over time with per-bean toggle pills, running average lines, scroll/pinch zoom, pan, and mode toggle
- **Bean management** — add, edit, and delete bean types with process type, inventory (g or lbs), and purchase price (per lb, kg, or g); stock value calculated automatically
- **Low inventory alerts** — configurable threshold (default 200 g); banner and row highlighting when stock runs low
- **CSV import** — import historical roasts from a CSV file with a row-by-row preview before committing
- **Roast Color Card** — Sweet Maria's roast color reference card for judging roast degree by eye
- **Resizable layouts** — all pages use GridStack so panels can be dragged and resized; a global grid lock toggle in the sidebar Settings section freezes/unfreezes the layout

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python / Flask |
| Database | SQLite (`roastapp.db`) |
| Frontend | Jinja2 + Bootstrap 5 + Inter font |
| Charting | Chart.js 4 + chartjs-plugin-zoom |

## Getting Started

### Run locally

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

### Run with Docker (Synology NAS or any Docker host)

**Prerequisites:** Docker + Docker Compose

```bash
git clone https://github.com/tdfguy2002/RoastApp.git
cd RoastApp
docker compose up -d
```

Then open [http://your-host:3000](http://your-host:3000) in your browser.

The SQLite database is stored in a `./data/` directory on the host so your data survives container restarts and upgrades.

**Synology tip:** In `docker-compose.yml`, change the volume path to an absolute location on your NAS, e.g.:
```yaml
volumes:
  - /volume1/docker/roastapp:/data
```

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
| cost_per_g | real | purchase cost in $/g |

**`roasts`** — individual roast sessions

| Column | Type | Notes |
|--------|------|-------|
| id | integer | primary key |
| date | text | ISO format (YYYY-MM-DD) |
| bean_id | integer | foreign key → beans.id |
| start_weight_g | real | grams |
| end_weight_g | real | grams |
| weight_loss_g | real | calculated: start − end |
| first_crack_secs | integer | countdown seconds remaining at first crack (nullable) |
| c_button_used | integer | 0 or 1 |
| plus_presses | integer | number of + presses after C |
| minus_presses | integer | number of − presses after C |

**`settings`** — key-value configuration store

| Key | Default | Description |
|-----|---------|-------------|
| `low_inventory_g` | `200` | Inventory alert threshold in grams |
