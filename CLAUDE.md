# RoastApp — Coffee Roast Tracker

A browser-based app to log and visualize coffee bean roasting sessions.

## Project Goal

Track coffee roasts over time, recording key data per session and visualizing weight loss trends in an interactive graph.

## Features

### Roast Log
- Log each roast with:
  - **Date** of the roast
  - **Bean type** selected from a dropdown list
  - **Start weight** (grams)
  - **End weight** (grams)
  - **Weight loss** (calculated automatically: `start - end`)
- All roasts saved to a database

### Bean Management
- Separate UI section (or page) to add/edit/delete coffee bean types
- Bean list populates the dropdown in the roast logging form

### Interactive Graph
- X-axis: roast date
- Y-axis: weight loss (grams or %)
- Hover tooltips showing full roast details (date, bean type, start weight, end weight, weight loss)

## Port

Use port **3000** (ports 5000, 5001, and 8080 are already in use).
Always verify a port is free before assigning it.

## Tech Stack

- **Backend:** Python / Flask (`app.py`)
- **Database:** SQLite via Python's built-in `sqlite3` (`roastapp.db`)
- **Frontend:** Jinja2 templates + Bootstrap 5 (CDN)
- **Charting:** Chart.js 4 + chartjs-adapter-date-fns (both CDN)

## Data Model

### `beans` table
| Field | Type | Notes |
|-------|------|-------|
| id | integer | primary key |
| name | text | e.g. "Ethiopia Yirgacheffe" |

### `roasts` table
| Field | Type | Notes |
|-------|------|-------|
| id | integer | primary key |
| date | date | roast date |
| bean_id | integer | foreign key → beans.id |
| start_weight_g | decimal | grams |
| end_weight_g | decimal | grams |
| weight_loss_g | decimal | calculated: start − end |

## Color Palette

Derived from the app icon (roasting coffee bean illustration). Use these consistently across all UI elements.

| Name          |  Hex      | Usage                                                       |
|---------------|-----------|-------------------------------------------------------------|
| Espresso Dark | `#1a0800` | Sidebar background, modal headers                           |
| Ember Brown   | `#7a3008` | Chart line 3                                                |
| Fire Orange   | `#c05808` | Buttons (`btn-coffee`), active nav link, badges             |
| Amber Gold    | `#e8a020` | Sidebar nav links                                           |
| Bright Gold   | `#f5b010` | Sidebar brand/logo text, chart line 2                       |
| Parchment     | `#f7eddf` | Page background                                             |
| Dark Roast    | `#3d1800` | Page titles (`h4.page-title`)                               |

Chart palette (in order): `#c05808`, `#f5b010`, `#7a3008`, `#e8a020`, `#ffd040`, `#3d1800`

## Development Notes

- Always check that the target port is open before starting the server
- Weight loss is derived, but storing it makes queries and charting simpler
- Bean dropdown should always reflect the current contents of the `beans` table
