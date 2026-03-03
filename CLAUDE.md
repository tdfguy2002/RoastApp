# RoastApp — Coffee Roast Tracker

A browser-based app to log and visualize coffee bean roasting sessions.

## Project Goal

Track coffee roasts over time, recording key data per session and visualizing weight loss trends in an interactive graph.

## Features

### Dashboard (`/dashboard`)
- Summary stats: total roasts, avg weight loss %, total weight roasted, inventory value
- Recent 10 roasts table (left column)
- Bean inventory with progress bars (right column) — bars turn yellow when below threshold
- Low inventory alert banner
- `/` redirects here

### Roast Log (`/roast`)
- Log each roast with:
  - **Date**, **Bean type**, **Start weight** (g), **End weight** (g)
  - **Weight loss** calculated automatically (`start - end`)
  - Start weight is deducted from bean inventory on save
- **Roast Timing** section (optional, Behmor roaster):
  - First crack time (M:SS countdown remaining on roaster)
  - C button checkbox (pressed at first crack, resets timer to 3:10)
  - \+ presses (+10s each) and − presses (−10s each) after C
  - Live total roast time preview: `(18:00 − first_crack) + (3:10 + plus×10 − minus×10)`
  - If C not used: total = 18:00

### Bean Management (`/beans`)
- Add, edit, delete bean types
- Fields: name, processing type (Washed/Natural/Honey/Wet-Hulled), inventory (g or lbs), purchase price (per lb/kg/g)
- Cost/g and stock value calculated and displayed
- Total inventory weight and total stock value in table footer
- Delete blocked if bean has roasts logged
- Low inventory alert configurable (default 200g); banner + row highlight for low beans

### Roast History (`/history`)
- Scrollable table of all roasts with First Crack and Total Time columns
- Edit/delete each roast (edit modal includes timing fields)
- CSV import (two-step: preview then confirm)
  - Column mapping: col 1=date (MM/DD/YYYY), col 2=start weight, col 3=end weight, col 7=bean name
  - Default bean if col 7 empty: `Espresso Monkey`
  - Bean matched case-insensitively; must exist in DB before import

### Interactive Chart (`/history`)
- Scatter + line chart per bean type (Chart.js 4)
- Running average dashed line per bean (same color)
- Toggle pills to show/hide individual beans (hides both raw and avg lines)
- % / g mode toggle (Y-axis switches between weight loss % and grams)
- Scroll/pinch zoom + pan (chartjs-plugin-zoom + hammerjs)
- Reset Zoom button
- Tooltips show full roast details for data points, running avg for avg points

## Port

Use port **3000** (ports 5000, 5001, and 8080 are already in use).
Always verify a port is free before assigning it.

## Tech Stack

- **Backend:** Python / Flask (`app.py`)
- **Database:** SQLite via Python's built-in `sqlite3` (`roastapp.db`)
- **Frontend:** Jinja2 templates + Bootstrap 5 (CDN) + Inter font (Google Fonts)
- **Theme:** Tabler dark palette (see Color Palette below)
- **Charting:** Chart.js 4 + chartjs-adapter-date-fns + chartjs-plugin-zoom + hammerjs (all CDN)

## Data Model

### `beans` table
| Field | Type | Notes |
|-------|------|-------|
| id | integer | primary key |
| name | text | unique |
| process_type | text | Washed/Natural/Honey/Wet-Hulled |
| inventory_g | real | current stock in grams |
| cost_per_g | real | stored as $/g regardless of input unit |

### `roasts` table
| Field | Type | Notes |
|-------|------|-------|
| id | integer | primary key |
| date | text | roast date (YYYY-MM-DD) |
| bean_id | integer | foreign key → beans.id |
| start_weight_g | real | grams |
| end_weight_g | real | grams |
| weight_loss_g | real | calculated: start − end |
| first_crack_secs | integer | countdown seconds remaining at first crack (nullable) |
| c_button_used | integer | 0 or 1 |
| plus_presses | integer | number of + presses after C |
| minus_presses | integer | number of − presses after C |

### `settings` table
| Field | Type | Notes |
|-------|------|-------|
| key | text | primary key |
| value | text | |

Current settings keys: `low_inventory_g` (default: `200`)

## Color Palette (Tabler Dark)

| Token | Hex | Usage |
|-------|-----|-------|
| Page bg | `#040a11` | `--bs-body-bg` |
| Card/surface | `#182433` | `--bs-card-bg`, modal content |
| Sidebar/input bg | `#0e1722` | sidebar, inputs, modal headers |
| Border | `#25384f` | all borders, chart grid |
| Text | `#dce1e7` | body text, labels |
| Muted text | `rgba(220,225,231,0.6)` | section labels, placeholders |
| Primary blue | `#6aa9e3` | `btn-coffee`, active nav, badges, chart accent |

Chart palette (in order): `#6aa9e3`, `#4fc9da`, `#5a7fd4`, `#88bae9`, `#3b8fd4`, `#a78bfa`

## Key App Helpers (`app.py`)

- `parse_inventory(form)` — converts lbs→g if unit field is `lbs`
- `parse_cost(form)` — converts price+unit to cost_per_g
- `parse_crack_time(str)` — parses `M:SS` → seconds, returns None if blank/invalid
- `calc_roast_time(first_crack_secs, c_used, plus, minus)` → total seconds (1080 if no C)
- `fmt_time(seconds)` → `M:SS` string
- `get_setting(key, default)` / `set_setting(key, value)` — key-value settings store
- `init_db()` handles schema creation + column migrations (safe to re-run)

## Development Notes

- Always check that the target port is open before starting the server
- `weight_loss_g` is stored (derived) for simpler queries and charting
- Bean inventory is adjusted automatically on roast add/edit/delete
- Schema migrations use `PRAGMA table_info` — add new columns with `ALTER TABLE` if missing
- `LBS_TO_G = 453.592`, `KG_TO_G = 1000.0`
