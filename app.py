from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
import sqlite3
import csv
import io
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = 'roastapp-secret-key'
DATABASE = 'roastapp.db'

PROCESS_TYPES = ['Washed', 'Natural', 'Honey', 'Wet-Hulled']
LBS_TO_G = 453.592


def parse_inventory(form):
    """Return inventory in grams, converting from lbs if the unit field says 'lbs'."""
    try:
        value = float(form.get('inventory_g', 0))
    except ValueError:
        value = 0
    if form.get('inventory_unit') == 'lbs':
        value = round(value * LBS_TO_G, 1)
    return value


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS beans (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            name         TEXT    NOT NULL UNIQUE,
            process_type TEXT    NOT NULL DEFAULT 'Washed',
            inventory_g  REAL    NOT NULL DEFAULT 0
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS roasts (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            date            TEXT    NOT NULL,
            bean_id         INTEGER NOT NULL,
            start_weight_g  REAL    NOT NULL,
            end_weight_g    REAL    NOT NULL,
            weight_loss_g   REAL    NOT NULL,
            FOREIGN KEY (bean_id) REFERENCES beans(id)
        )
    ''')
    conn.commit()

    # Migrate existing beans table if new columns are missing
    existing_cols = {row[1] for row in conn.execute('PRAGMA table_info(beans)').fetchall()}
    if 'process_type' not in existing_cols:
        conn.execute("ALTER TABLE beans ADD COLUMN process_type TEXT NOT NULL DEFAULT 'Washed'")
        conn.commit()
    if 'inventory_g' not in existing_cols:
        conn.execute("ALTER TABLE beans ADD COLUMN inventory_g REAL NOT NULL DEFAULT 0")
        conn.commit()

    conn.close()


@app.route('/')
def index():
    return redirect(url_for('roast_page'))


@app.route('/roast')
def roast_page():
    db = get_db()
    beans = db.execute('SELECT * FROM beans ORDER BY name').fetchall()
    db.close()
    return render_template('roast.html', beans=beans, today=date.today().isoformat())


@app.route('/roasts', methods=['POST'])
def add_roast():
    date_val = request.form['date']
    bean_id  = request.form['bean_id']
    try:
        start = float(request.form['start_weight_g'])
        end   = float(request.form['end_weight_g'])
    except ValueError:
        flash('Invalid weight values.', 'danger')
        return redirect(url_for('roast_page'))

    if start <= 0 or end <= 0:
        flash('Weights must be greater than zero.', 'danger')
        return redirect(url_for('roast_page'))
    if end >= start:
        flash('End weight must be less than start weight.', 'danger')
        return redirect(url_for('roast_page'))

    loss = round(start - end, 1)
    conn = get_db()
    conn.execute(
        'INSERT INTO roasts (date, bean_id, start_weight_g, end_weight_g, weight_loss_g) '
        'VALUES (?, ?, ?, ?, ?)',
        (date_val, bean_id, start, end, loss)
    )
    # Deduct start weight from bean inventory
    conn.execute(
        'UPDATE beans SET inventory_g = ROUND(inventory_g - ?, 1) WHERE id = ?',
        (start, bean_id)
    )
    conn.commit()
    conn.close()
    flash('Roast logged successfully.', 'success')
    return redirect(url_for('roast_page'))


@app.route('/roasts/<int:roast_id>/delete', methods=['POST'])
def delete_roast(roast_id):
    conn = get_db()
    roast = conn.execute(
        'SELECT bean_id, start_weight_g FROM roasts WHERE id = ?', (roast_id,)
    ).fetchone()
    if roast:
        # Restore inventory when deleting a roast
        conn.execute(
            'UPDATE beans SET inventory_g = ROUND(inventory_g + ?, 1) WHERE id = ?',
            (roast['start_weight_g'], roast['bean_id'])
        )
    conn.execute('DELETE FROM roasts WHERE id = ?', (roast_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('history_page'))


@app.route('/history')
def history_page():
    db = get_db()
    roasts = db.execute('''
        SELECT r.id, r.date, r.bean_id, b.name AS bean_name,
               r.start_weight_g, r.end_weight_g, r.weight_loss_g,
               ROUND(r.weight_loss_g / r.start_weight_g * 100.0, 1) AS weight_loss_pct
        FROM roasts r
        JOIN beans b ON r.bean_id = b.id
        ORDER BY r.date DESC, r.id DESC
    ''').fetchall()
    beans = db.execute('SELECT * FROM beans ORDER BY name').fetchall()
    db.close()
    return render_template('history.html', roasts=roasts, beans=beans)


@app.route('/roasts/<int:roast_id>/edit', methods=['POST'])
def edit_roast(roast_id):
    date_val = request.form['date']
    new_bean_id = int(request.form['bean_id'])
    try:
        new_start = float(request.form['start_weight_g'])
        new_end   = float(request.form['end_weight_g'])
    except ValueError:
        flash('Invalid weight values.', 'danger')
        return redirect(url_for('history_page'))

    if new_start <= 0 or new_end <= 0:
        flash('Weights must be greater than zero.', 'danger')
        return redirect(url_for('history_page'))
    if new_end >= new_start:
        flash('End weight must be less than start weight.', 'danger')
        return redirect(url_for('history_page'))

    new_loss = round(new_start - new_end, 1)
    conn = get_db()
    old = conn.execute(
        'SELECT bean_id, start_weight_g FROM roasts WHERE id = ?', (roast_id,)
    ).fetchone()
    if old:
        # Restore old start weight to the old bean's inventory
        conn.execute(
            'UPDATE beans SET inventory_g = ROUND(inventory_g + ?, 1) WHERE id = ?',
            (old['start_weight_g'], old['bean_id'])
        )
    # Deduct new start weight from the new bean's inventory
    conn.execute(
        'UPDATE beans SET inventory_g = ROUND(inventory_g - ?, 1) WHERE id = ?',
        (new_start, new_bean_id)
    )
    conn.execute(
        'UPDATE roasts SET date=?, bean_id=?, start_weight_g=?, end_weight_g=?, weight_loss_g=? WHERE id=?',
        (date_val, new_bean_id, new_start, new_end, new_loss, roast_id)
    )
    conn.commit()
    conn.close()
    flash('Roast updated.', 'success')
    return redirect(url_for('history_page'))


@app.route('/beans', methods=['GET', 'POST'])
def beans_page():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        process_type = request.form.get('process_type', 'Washed')
        inventory_g = parse_inventory(request.form)

        if not name:
            flash('Bean name cannot be empty.', 'danger')
        elif process_type not in PROCESS_TYPES:
            flash('Invalid processing type.', 'danger')
        else:
            conn = get_db()
            try:
                conn.execute(
                    'INSERT INTO beans (name, process_type, inventory_g) VALUES (?, ?, ?)',
                    (name, process_type, inventory_g)
                )
                conn.commit()
            except sqlite3.IntegrityError:
                flash(f'"{name}" already exists.', 'warning')
            finally:
                conn.close()
        return redirect(url_for('beans_page'))

    db = get_db()
    beans_list = db.execute('''
        SELECT b.id, b.name, b.process_type, b.inventory_g, COUNT(r.id) AS roast_count
        FROM beans b
        LEFT JOIN roasts r ON r.bean_id = b.id
        GROUP BY b.id, b.name, b.process_type, b.inventory_g
        ORDER BY b.name
    ''').fetchall()
    db.close()
    return render_template('beans.html', beans=beans_list, process_types=PROCESS_TYPES)


@app.route('/beans/<int:bean_id>/edit', methods=['POST'])
def edit_bean(bean_id):
    name = request.form.get('name', '').strip()
    process_type = request.form.get('process_type', 'Washed')
    inventory_g = parse_inventory(request.form)

    if not name:
        flash('Bean name cannot be empty.', 'danger')
    elif process_type not in PROCESS_TYPES:
        flash('Invalid processing type.', 'danger')
    else:
        conn = get_db()
        try:
            conn.execute(
                'UPDATE beans SET name = ?, process_type = ?, inventory_g = ? WHERE id = ?',
                (name, process_type, inventory_g, bean_id)
            )
            conn.commit()
        except sqlite3.IntegrityError:
            flash(f'"{name}" already exists.', 'warning')
        finally:
            conn.close()
    return redirect(url_for('beans_page'))


@app.route('/beans/<int:bean_id>/delete', methods=['POST'])
def delete_bean(bean_id):
    db = get_db()
    count = db.execute(
        'SELECT COUNT(*) FROM roasts WHERE bean_id = ?', (bean_id,)
    ).fetchone()[0]
    db.close()
    if count > 0:
        flash(f'Cannot delete: this bean has {count} roast(s) logged.', 'danger')
        return redirect(url_for('beans_page'))
    conn = get_db()
    conn.execute('DELETE FROM beans WHERE id = ?', (bean_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('beans_page'))


DEFAULT_IMPORT_BEAN = 'Espresso Monkey'


@app.route('/roasts/import/preview', methods=['POST'])
def import_preview():
    file = request.files.get('csv_file')
    if not file or file.filename == '':
        flash('Please select a CSV file.', 'danger')
        return redirect(url_for('history_page'))

    db = get_db()
    beans_list = db.execute('SELECT * FROM beans ORDER BY name').fetchall()
    db.close()

    # Build case-insensitive name → bean lookup
    bean_lookup = {b['name'].strip().lower(): dict(b) for b in beans_list}

    content = file.read().decode('utf-8', errors='replace')
    rows = []
    for line_num, row in enumerate(csv.reader(io.StringIO(content)), start=1):
        if not any(cell.strip() for cell in row):
            continue  # skip blank lines

        entry = {'line': line_num, 'raw': ','.join(row), 'errors': [],
                 'date': '', 'start': None, 'end': None, 'loss': None, 'loss_pct': None,
                 'bean_name': '', 'bean_id': None}

        # Column 7 → bean name; default to DEFAULT_IMPORT_BEAN if absent/empty
        raw_bean = row[7].strip() if len(row) > 7 else ''
        bean_name = raw_bean if raw_bean else DEFAULT_IMPORT_BEAN
        entry['bean_name'] = bean_name
        matched = bean_lookup.get(bean_name.lower())
        if matched:
            entry['bean_id'] = matched['id']
        else:
            entry['errors'].append(f'Bean "{bean_name}" not found — add it in Beans first')

        # Column 1 → date (MM/DD/YYYY)
        try:
            entry['date'] = datetime.strptime(row[1].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
        except (ValueError, IndexError):
            entry['errors'].append(f'Invalid date "{row[1].strip() if len(row) > 1 else ""}" — expected MM/DD/YYYY')

        # Column 2 → start weight
        try:
            start = float(row[2].strip())
            if start <= 0:
                entry['errors'].append('Start weight must be > 0')
            else:
                entry['start'] = start
        except (ValueError, IndexError):
            entry['errors'].append(f'Invalid start weight "{row[2].strip() if len(row) > 2 else ""}"')

        # Column 3 → end weight
        try:
            end = float(row[3].strip())
            if end <= 0:
                entry['errors'].append('End weight must be > 0')
            else:
                entry['end'] = end
        except (ValueError, IndexError):
            entry['errors'].append(f'Invalid end weight "{row[3].strip() if len(row) > 3 else ""}"')

        if entry['start'] and entry['end']:
            if entry['end'] >= entry['start']:
                entry['errors'].append('End weight must be less than start weight')
            elif not entry['errors']:
                entry['loss'] = round(entry['start'] - entry['end'], 1)
                entry['loss_pct'] = round(entry['loss'] / entry['start'] * 100, 1)

        rows.append(entry)

    valid = [r for r in rows if not r['errors']]
    invalid = [r for r in rows if r['errors']]
    return render_template('import_preview.html',
                           rows=rows, valid=valid, invalid=invalid,
                           beans=beans_list)


@app.route('/roasts/import/confirm', methods=['POST'])
def import_confirm():
    dates    = request.form.getlist('date')
    starts   = request.form.getlist('start')
    ends     = request.form.getlist('end')
    bean_ids = request.form.getlist('bean_id')

    if not dates:
        flash('No valid rows to import.', 'warning')
        return redirect(url_for('history_page'))

    conn = get_db()
    count = 0
    for date_val, start_val, end_val, bean_id in zip(dates, starts, ends, bean_ids):
        try:
            start = float(start_val)
            end   = float(end_val)
            loss  = round(start - end, 1)
            conn.execute(
                'INSERT INTO roasts (date, bean_id, start_weight_g, end_weight_g, weight_loss_g) '
                'VALUES (?, ?, ?, ?, ?)',
                (date_val, bean_id, start, end, loss)
            )
            count += 1
        except (ValueError, Exception):
            continue
    conn.commit()
    conn.close()
    flash(f'Imported {count} roast(s) successfully.', 'success')
    return redirect(url_for('history_page'))


@app.route('/api/chart-data')
def chart_data():
    db = get_db()
    roasts = db.execute('''
        SELECT r.date, b.name AS bean_name,
               r.start_weight_g, r.end_weight_g, r.weight_loss_g,
               ROUND(r.weight_loss_g / r.start_weight_g * 100.0, 1) AS weight_loss_pct
        FROM roasts r
        JOIN beans b ON r.bean_id = b.id
        ORDER BY r.date ASC, r.id ASC
    ''').fetchall()
    db.close()
    return jsonify([dict(r) for r in roasts])


if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=3000, debug=True)
