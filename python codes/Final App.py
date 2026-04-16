# pip install qrcode[pil] pillow

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import mysql.connector
from datetime import datetime
import sys
import json
import os
import csv

# ------------------- DATABASE CONNECTION -------------------
def connect_db():
    """Establishes connection to the MySQL database."""
    try:
        # !!! IMPORTANT: UPDATE YOUR CREDENTIALS HERE !!!
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="12345678",
            database="AssetDB"
        )
    except mysql.connector.Error as e:
        print(f"Database Connection Error: {e}")
        messagebox.showerror("DB Error", f"Could not connect to database: {e}")
        return None

conn = connect_db()
if not conn:
    sys.exit()

# ------------------- PROFESSIONAL THEME (NEW DESIGN) -------------------
# Modern neutral palette and spacing tokens for a professional look
PRIMARY = "#0A66C2"        # primary blue
SECONDARY = "#0B7285"      # teal accent
SUCCESS = "#198754"
DANGER = "#DC3545"
BG = "#F3F6F9"             # app background
CARD = "#FFFFFF"           # cards and panels
TEXT = "#1F2937"           # primary text
MUTED = "#6B7280"          # muted text
BORDER = "#E6EEF6"         # borders / light separators
FONT_FAMILY = "Segoe UI"
PADDING_SMALL = (6, 4)
PADDING = (10, 8)
LARGE_PADDING = (14, 10)

# ------------------- GLOBAL DATA & UTILITY -------------------
employees_list = []
departments_list = []
vendors_list = []
assets_list = []
assets_table_rows = []  # Raw rows fetched from DB for client-side filtering
LOGGED_IN_USER = None
GLOBAL_SELECTED_ASSET_ID = None
GLOBAL_SELECTED_EMP_ID = None
GLOBAL_SELECTED_MAINT_ID = None
GLOBAL_SELECTED_DEPT_ID = None
GLOBAL_SELECTED_VENDOR_ID = None
SESSION_FILE = 'ams_session.json'

# ------------------- SESSION MANAGEMENT FUNCTIONS -------------------


def save_session(user):
    """Saves the logged-in user state to a file."""
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump({'user': user}, f)
        print(f"Session saved for user: {user}")
    except Exception as e:
        print(f"Error saving session: {e}")


def load_session():
    """Loads the logged-in user state from a file."""
    global LOGGED_IN_USER
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, 'r') as f:
                data = json.load(f)
                LOGGED_IN_USER = data.get('user')
                print(f"Session loaded for user: {LOGGED_IN_USER}")
                return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    return False


def clear_session():
    """Removes the session file."""
    global LOGGED_IN_USER
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)
    LOGGED_IN_USER = None
    print("Session cleared.")


# ------------------- ASSET CODE FORMATTING UTIL -------------------


def format_asset_code(asset_id):
    """Return asset code in AMS-000 format. Accepts int or numeric string."""
    try:
        return f"AMS-{int(asset_id):03d}"
    except Exception:
        return str(asset_id)


def extract_numeric_id_from_code(code_str):
    """Extract numeric id from a formatted code like 'AMS-001' or from plain '123'.
    Returns int or None."""
    if code_str is None:
        return None
    first = code_str.split(':')[0].strip()
    digits = ''.join(ch for ch in first if ch.isdigit())
    if digits:
        try:
            return int(digits)
        except ValueError:
            return None
    try:
        return int(first)
    except Exception:
        return None


def parse_combo_selection(selection, data_list):
    """Extracts the ID from a combobox selection string or by matching against data_list.
       Supports formatted asset codes like 'AMS-001: Name (...)'."""
    if not selection:
        return None
    numeric = extract_numeric_id_from_code(selection)
    if numeric is not None:
        return numeric
    return next((d[0] for d in data_list if d[1] == selection), None)


# ------------------- AUDIT AND STATUS UTILITY -------------------


def log_audit(asset_id, action, user, notes):
    """
    Inserts a record into the AuditHistory table.
    """
    cursor = conn.cursor()
    asset_id_val = asset_id if asset_id is not None else None

    try:
        cursor.execute("INSERT INTO AuditHistory (asset_id, action, performed_by, notes) VALUES (%s,%s,%s,%s)",
                       (asset_id_val, action, user, notes))
        conn.commit()
    except mysql.connector.Error as e:
        # Don't block core flow for audit logging failures
        print(f"Audit Log Error: {e}")


def update_asset_status(asset_id, new_status):
    """Updates the status of an asset in the Assets table."""
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE Assets SET status = %s WHERE asset_id = %s", (new_status, asset_id))
        conn.commit()
        return True
    except mysql.connector.Error as e:
        messagebox.showerror("DB Error", f"Failed to update asset status: {e}")
        return False


def fetch_dropdowns():
    """Fetches data for all dropdown menus (comboboxes)."""
    global employees_list, departments_list, vendors_list, assets_list
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT employee_id, full_name, department FROM Employees")
        employees_list = cursor.fetchall()  # (id, name, department_name)
    except Exception:
        employees_list = []

    try:
        cursor.execute("SELECT dept_id, dept_name FROM Departments")
        departments_list = cursor.fetchall()
    except Exception:
        departments_list = []

    try:
        cursor.execute("SELECT vendor_id, name FROM Vendors")
        vendors_list = cursor.fetchall()
    except Exception:
        vendors_list = []

    try:
        cursor.execute("SELECT asset_id, name, status FROM Assets")
        assets_list = [(a[0], f"{format_asset_code(a[0])}: {a[1]} ({a[2]})") for a in cursor.fetchall()]
    except Exception:
        assets_list = []


# ------------------- STYLING (Professional Theme Implementation) -------------------


def apply_styles(root):
    """Applies a consistent, modern professional theme using ttk styles."""
    style = ttk.Style(root)
    # Try to use a clean theme where available
    for th in ('clam', 'alt', 'default'):
        try:
            style.theme_use(th)
            break
        except Exception:
            continue

    # Root background
    root.configure(background=BG)

    base_font = (FONT_FAMILY, 10)
    header_font = (FONT_FAMILY, 16, 'bold')
    subheader_font = (FONT_FAMILY, 12, 'bold')
    small_font = (FONT_FAMILY, 9)

    # General widgets
    style.configure('TLabel', background=BG, foreground=TEXT, font=base_font)
    style.configure('Header.TLabel', background=BG, foreground=PRIMARY, font=header_font)
    style.configure('SubHeader.TLabel', background=BG, foreground=TEXT, font=subheader_font)
    style.configure('Muted.TLabel', background=BG, foreground=MUTED, font=small_font)

    style.configure('TFrame', background=BG)
    style.configure('Card.TFrame', background=CARD, relief='flat', borderwidth=1)
    style.configure('Card.TLabelframe', background=CARD)
    style.configure('TLabelframe.Label', background=CARD, foreground=TEXT, font=subheader_font)

    # Entries and Comboboxes
    style.configure('TEntry', relief='flat', padding=6, font=base_font, fieldbackground='white')
    style.configure('TCombobox', relief='flat', padding=6, font=base_font)
    style.map('TCombobox', fieldbackground=[('readonly', 'white')])

    # Buttons
    style.configure('TButton', font=(FONT_FAMILY, 10, 'bold'), padding=(8, 6), foreground=TEXT)
    style.configure('Primary.TButton', background=PRIMARY, foreground='white')
    style.map('Primary.TButton', background=[('active', PRIMARY), ('!disabled', PRIMARY)])
    style.configure('Accent.TButton', background=SECONDARY, foreground='white')
    style.map('Accent.TButton', background=[('active', SECONDARY)])
    style.configure('Danger.TButton', background=DANGER, foreground='white')
    style.map('Danger.TButton', background=[('active', DANGER)])
    style.configure('Clear.TButton', background=BORDER, foreground=TEXT)
    style.map('Clear.TButton', background=[('active', BORDER)])

    # Notebook / Tabs
    style.configure('TNotebook', background=BG, tabmargins=[2, 5, 2, 0])
    style.configure('TNotebook.Tab', font=(FONT_FAMILY, 10, 'bold'), padding=(10, 8), background=BORDER, foreground=TEXT)
    style.map('TNotebook.Tab', background=[('selected', PRIMARY)], foreground=[('selected', 'white')])

    # Treeview styling (table)
    style.configure('Treeview', font=base_font, rowheight=26, background='white', fieldbackground='white', foreground=TEXT)
    style.configure('Treeview.Heading', font=(FONT_FAMILY, 10, 'bold'), background=PRIMARY, foreground='white', relief='flat')
    style.map('Treeview.Heading', background=[('active', PRIMARY)])

    # Small tweaks to separators
    style.configure('Separator.TSeparator', background=BORDER)

    # Watermark style (small, muted, italic)
    style.configure('Watermark.TLabel', background=BG, foreground='#9AA3AA', font=(FONT_FAMILY, 9, 'italic'))

    # Make sure widgets that use 'Card.TFrame' have consistent padding via custom wrapper classes in code


# ------------------- MAIN APPLICATION WINDOW -------------------


def main_application_window():
    """Initializes the main application window with a tabbed interface (professional layout)."""
    fetch_dropdowns()

    root = tk.Tk()
    root.title(f"Assets Management System — Logged in as: {LOGGED_IN_USER}")
    root.geometry("1360x760")
    apply_styles(root)

    # Top bar
    topbar = ttk.Frame(root, padding=(12, 8), style='TFrame')
    topbar.pack(side='top', fill='x')

    title_label = ttk.Label(topbar, text="Assets Management System", style='Header.TLabel')
    title_label.pack(side='left')

    user_label = ttk.Label(topbar, text=f"Signed in as: {LOGGED_IN_USER}", style='Muted.TLabel')
    user_label.pack(side='right')

    # Notebook container with consistent padding
    container = ttk.Frame(root, padding=12, style='TFrame')
    container.pack(fill='both', expand=True)

    notebook = ttk.Notebook(container)
    notebook.pack(expand=True, fill='both')

    # Tabs (kept same features, visually refined)
    asset_tab = ttk.Frame(notebook, padding=12, style='Tab.TFrame')
    employee_tab = ttk.Frame(notebook, padding=12, style='Tab.TFrame')
    assignment_tab = ttk.Frame(notebook, padding=12, style='Tab.TFrame')
    maintenance_tab = ttk.Frame(notebook, padding=12, style='Tab.TFrame')
    reports_tab = ttk.Frame(notebook, padding=12, style='Tab.TFrame')
    admin_tab = ttk.Frame(notebook, padding=12, style='Tab.TFrame')

    notebook.add(asset_tab, text='Asset Inventory')
    notebook.add(employee_tab, text='Personnel')
    notebook.add(assignment_tab, text='Assignments & Returns')
    notebook.add(maintenance_tab, text='Maintenance Log')
    notebook.add(reports_tab, text='Reports')
    notebook.add(admin_tab, text='Configuration')

    # Populate tabs using existing setup functions (logic unchanged)
    setup_assets_tab(asset_tab)
    setup_employees_tab(employee_tab)
    setup_assignments_tab(assignment_tab)
    setup_maintenance_tab(maintenance_tab)
    setup_reports_tab(reports_tab)
    setup_admin_tab(admin_tab)

    # Status footer
    footer = ttk.Frame(root, padding=(10, 6), style='TFrame')
    footer.pack(side='bottom', fill='x')
    ttk.Separator(footer, orient='horizontal', style='Separator.TSeparator').pack(fill='x', pady=(0, 6))
    footer_inner = ttk.Frame(footer, style='TFrame')
    footer_inner.pack(fill='x')
    ttk.Label(footer_inner, text=f"Logged in as: {LOGGED_IN_USER}", style='Muted.TLabel').pack(side='left')
    ttk.Button(footer_inner, text="Logout", command=lambda: [clear_session(), root.destroy()], style='Clear.TButton').pack(side='right')

    # Watermark (bottom-right). Non-interactive decorative label.
    watermark = ttk.Label(root, text="Made By Noman Daudpota (24F-AI-202)", style='Watermark.TLabel')
    # Place at bottom-right corner with small offset
    watermark.place(relx=1.0, rely=1.0, x=-8, y=-8, anchor='se')
    watermark.lift()

    root.mainloop()


# ------------------- TAB SETUP FUNCTIONS -------------------

# --- ASSETS TAB (refined visual structure; logic preserved) ---
def setup_assets_tab(tab_frame):
    global GLOBAL_SELECTED_ASSET_ID, assets_table_rows

    tab_frame.configure(style='Tab.TFrame')
    tab_frame.columnconfigure(0, weight=1, uniform='a')
    tab_frame.columnconfigure(1, weight=3, uniform='a')
    tab_frame.rowconfigure(0, weight=1)

    fetch_dropdowns()

    # ---------------- Data functions ----------------
    def fetch_assets_table_raw():
        """Populate assets_table_rows (module-level) with current DB rows."""
        global assets_table_rows
        assets_table_rows = []
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    a.asset_id, a.name, a.category, a.cost, a.purchase_date, a.status, d.dept_name, a.location
                FROM Assets a 
                LEFT JOIN Departments d ON a.department_id=d.dept_id
                ORDER BY a.asset_id
            """)
            assets_table_rows = cursor.fetchall()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to fetch assets: {e}")

    def populate_assets_tree(rows, tree):
        tree.delete(*tree.get_children())
        for idx, r in enumerate(rows):
            values = list(r)
            values[0] = format_asset_code(values[0])
            # We keep department out of the table values for internal alignment — show consistent columns
            tag = 'archived' if str(r[5]).lower() == 'archived' else ('odd' if idx % 2 else 'even')
            tree.insert('', 'end', values=values[:-1], tags=(tag,))
        tree.tag_configure('even', background='#FFFFFF')
        tree.tag_configure('odd', background='#F9FAFB')
        tree.tag_configure('archived', background='#F3F4F6', foreground='#8B95A1')

    def update_summary_counts(rows=None):
        rows = rows if rows is not None else [r for r in assets_table_rows]
        total = len([r for r in rows if str(r[5]).lower() != 'archived'])
        assigned = sum(1 for r in rows if str(r[5]).lower() == 'assigned')
        in_maint = sum(1 for r in rows if 'maintenance' in str(r[5]).lower())
        archived = sum(1 for r in assets_table_rows if str(r[5]).lower() == 'archived')
        total_val.config(text=str(total))
        assigned_val.config(text=str(assigned))
        maint_val.config(text=str(in_maint))
        archived_val.config(text=str(archived))

    # ---------------- Left: Card form ----------------
    left_card = ttk.Frame(tab_frame, style='Card.TFrame', padding=12)
    left_card.grid(row=0, column=0, sticky='nsew', padx=(6, 8), pady=6)
    left_card.columnconfigure(0, weight=1)

    title = ttk.Label(left_card, text="Asset Registration & Edit", style='SubHeader.TLabel')
    title.grid(row=0, column=0, sticky='w', pady=(0, 12))

    # Form variables
    asset_code_var = tk.StringVar()
    asset_name_var = tk.StringVar()
    asset_category_var = tk.StringVar()
    purchase_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    cost_var = tk.StringVar()
    dept_combo_var = tk.StringVar()
    location_var = tk.StringVar()
    asset_status_var = tk.StringVar(value='Available')

    # Form grid - labels right-aligned, clean spacing
    form = ttk.Frame(left_card, style='Card.TFrame')
    form.grid(row=1, column=0, sticky='nsew')
    for c in (0, 1):
        form.columnconfigure(c, weight=1)

    def make_row(label_text, var, row, readonly=False):
        lbl = ttk.Label(form, text=label_text)
        lbl.grid(row=row, column=0, sticky='e', padx=6, pady=6)
        ent = ttk.Entry(form, textvariable=var)
        if readonly:
            ent.state(['readonly'])
        ent.grid(row=row, column=1, sticky='ew', padx=6, pady=6)
        return ent

    make_row("Asset Code:", asset_code_var, 0, readonly=True)
    make_row("Name:", asset_name_var, 1)
    make_row("Category:", asset_category_var, 2)
    make_row("Purchase Date (YYYY-MM-DD):", purchase_date_var, 3)
    make_row("Cost ($):", cost_var, 4)
    make_row("Location:", location_var, 5)
    ttk.Label(form, text="Department:").grid(row=6, column=0, sticky='e', padx=6, pady=6)
    dept_cb = ttk.Combobox(form, textvariable=dept_combo_var, values=[d[1] for d in departments_list], state='readonly')
    dept_cb.grid(row=6, column=1, sticky='ew', padx=6, pady=6)
    ttk.Label(form, text="Status:").grid(row=7, column=0, sticky='e', padx=6, pady=6)
    status_cb = ttk.Combobox(form, textvariable=asset_status_var, values=['Available', 'Assigned', 'In Maintenance', 'Disposed', 'Archived'], state='readonly')
    status_cb.grid(row=7, column=1, sticky='ew', padx=6, pady=6)

    # Button row
    btn_row = ttk.Frame(left_card, style='Card.TFrame')
    btn_row.grid(row=2, column=0, sticky='ew', pady=(12, 0))
    btn_row.columnconfigure(0, weight=1)
    btn_row.columnconfigure(1, weight=1)
    btn_row.columnconfigure(2, weight=1)

    primary_btn = ttk.Button(btn_row, text="Add / Update", style='Primary.TButton')
    primary_btn.grid(row=0, column=0, sticky='ew', padx=4)
    archive_btn = ttk.Button(btn_row, text="Archive", style='Danger.TButton', state='disabled')
    archive_btn.grid(row=0, column=1, sticky='ew', padx=4)
    clear_btn = ttk.Button(btn_row, text="Clear", style='Clear.TButton')
    clear_btn.grid(row=0, column=2, sticky='ew', padx=4)

    notes = ttk.Label(left_card, text="Fields marked * are required.", style='Muted.TLabel')
    notes.grid(row=3, column=0, sticky='w', pady=(8, 0))

    # ---------------- Right: Inventory card (header + KPIs + table) ----------------
    right_card = ttk.Frame(tab_frame, style='Card.TFrame', padding=12)
    right_card.grid(row=0, column=1, sticky='nsew', padx=(8, 6), pady=6)
    right_card.columnconfigure(0, weight=1)
    right_card.rowconfigure(2, weight=1)

    header = ttk.Frame(right_card, style='Card.TFrame')
    header.grid(row=0, column=0, sticky='ew')
    header.columnconfigure(0, weight=1)

    ttk.Label(header, text="Asset Inventory List", style='SubHeader.TLabel').grid(row=0, column=0, sticky='w')

    search_frame = ttk.Frame(header)
    search_frame.grid(row=0, column=1, sticky='e')

    search_var = tk.StringVar()
    ttk.Entry(search_frame, textvariable=search_var, width=28).pack(side='left', padx=(0, 8))
    action_frame = ttk.Frame(search_frame)
    action_frame.pack(side='left')
    csv_btn = ttk.Button(action_frame, text="Export CSV", style='TButton')
    csv_btn.pack(side='left', padx=4)
    export_btn = ttk.Button(action_frame, text="Export All", style='TButton', state='disabled')
    export_btn.pack(side='left', padx=4)
    copy_btn = ttk.Button(action_frame, text="Copy ID", style='TButton', state='disabled')
    copy_btn.pack(side='left', padx=4)
    qr_btn = ttk.Button(action_frame, text="QR + Receipt", style='TButton')
    qr_btn.pack(side='left', padx=4)

    kpi_frame = ttk.Frame(right_card, style='Card.TFrame')
    kpi_frame.grid(row=1, column=0, sticky='ew', pady=(10, 12))
    for i in range(4):
        kpi_frame.columnconfigure(i, weight=1)

    total_chip = ttk.Frame(kpi_frame, style='Card.TFrame', padding=(8, 6))
    total_chip.grid(row=0, column=0, sticky='w', padx=(0, 8))
    ttk.Label(total_chip, text="Total", style='Muted.TLabel').pack(anchor='w')
    total_val = ttk.Label(total_chip, text="0", font=(FONT_FAMILY, 12, 'bold'), foreground=PRIMARY)
    total_val.pack(anchor='w')

    assigned_chip = ttk.Frame(kpi_frame, style='Card.TFrame', padding=(8, 6))
    assigned_chip.grid(row=0, column=1, sticky='w', padx=(0, 8))
    ttk.Label(assigned_chip, text="Assigned", style='Muted.TLabel').pack(anchor='w')
    assigned_val = ttk.Label(assigned_chip, text="0", font=(FONT_FAMILY, 12, 'bold'), foreground=SECONDARY)
    assigned_val.pack(anchor='w')

    maint_chip = ttk.Frame(kpi_frame, style='Card.TFrame', padding=(8, 6))
    maint_chip.grid(row=0, column=2, sticky='w', padx=(0, 8))
    ttk.Label(maint_chip, text="In Maintenance", style='Muted.TLabel').pack(anchor='w')
    maint_val = ttk.Label(maint_chip, text="0", font=(FONT_FAMILY, 12, 'bold'), foreground=SUCCESS)
    maint_val.pack(anchor='w')

    archived_chip = ttk.Frame(kpi_frame, style='Card.TFrame', padding=(8, 6))
    archived_chip.grid(row=0, column=3, sticky='w')
    ttk.Label(archived_chip, text="Archived", style='Muted.TLabel').pack(anchor='w')
    archived_val = ttk.Label(archived_chip, text="0", font=(FONT_FAMILY, 12, 'bold'), foreground=MUTED)
    archived_val.pack(anchor='w')

    table_container = ttk.Frame(right_card)
    table_container.grid(row=2, column=0, sticky='nsew')
    table_container.columnconfigure(0, weight=1)
    table_container.rowconfigure(0, weight=1)

    cols = ("ID", "Name", "Category", "Cost", "Purchase Date", "Status", "Department")
    tree = ttk.Treeview(table_container, columns=cols, show='headings', selectmode='browse')
    for c in cols:
        tree.heading(c, text=c)
    tree.column("ID", width=110, anchor='center')
    tree.column("Name", width=260, anchor='w')
    tree.column("Category", width=160, anchor='w')
    tree.column("Cost", width=100, anchor='e')
    tree.column("Purchase Date", width=120, anchor='center')
    tree.column("Status", width=140, anchor='center')
    tree.column("Department", width=160, anchor='w')

    tree.grid(row=0, column=0, sticky='nsew')
    vscroll = ttk.Scrollbar(table_container, orient='vertical', command=tree.yview)
    tree.configure(yscrollcommand=vscroll.set)
    vscroll.grid(row=0, column=1, sticky='ns')

    # Filters under header
    filter_row = ttk.Frame(right_card)
    filter_row.grid(row=3, column=0, sticky='ew', pady=(10, 0))
    filter_row.columnconfigure(0, weight=1)

    status_filter_var = tk.StringVar(value="All")
    dept_filter_var = tk.StringVar(value="All")
    show_archived_var = tk.BooleanVar(value=False)

    ttk.Label(filter_row, text="").grid(row=0, column=0)  # spacer
    ttk.Label(filter_row, text="Status:").grid(row=0, column=1, sticky='e', padx=(6, 4))
    status_cb = ttk.Combobox(filter_row, textvariable=status_filter_var, values=["All", "Available", "Assigned", "In Maintenance", "Disposed", "Archived"], width=18, state='readonly')
    status_cb.grid(row=0, column=2, sticky='w', padx=(0, 8))
    status_cb.bind('<<ComboboxSelected>>', lambda e: apply_filters_local())

    ttk.Label(filter_row, text="Department:").grid(row=0, column=3, sticky='e', padx=(6, 4))
    dept_cb2 = ttk.Combobox(filter_row, textvariable=dept_filter_var, values=["All"] + [d[1] for d in departments_list], width=18, state='readonly')
    dept_cb2.grid(row=0, column=4, sticky='w', padx=(0, 8))
    dept_cb2.bind('<<ComboboxSelected>>', lambda e: apply_filters_local())

    ttk.Checkbutton(filter_row, text="Show Archived", variable=show_archived_var, command=lambda: apply_filters_local()).grid(row=0, column=5, padx=(8, 0))

    # ---------------- Actions & logic wiring ----------------

    def apply_filters_local():
        q = search_var.get().strip().lower()
        sfilter = status_filter_var.get()
        dfilter = dept_filter_var.get()
        show_arch = show_archived_var.get()
        filtered = []
        for r in assets_table_rows:
            asset_id, name, category, cost, purchase_date, status, dept_name, location = r
            if not show_arch and str(status).lower() == 'archived':
                continue
            if sfilter != "All" and status != sfilter:
                continue
            if dfilter != "All" and (dept_name is None or dept_name != dfilter):
                continue
            if q:
                searchable = " ".join([str(name or ""), str(category or ""), str(location or ""), str(dept_name or ""), str(format_asset_code(asset_id))]).lower()
                if q not in searchable:
                    continue
            filtered.append(r)
        populate_assets_tree(filtered, tree)
        update_summary_counts(filtered)

    def refresh_assets_view():
        fetch_dropdowns()
        fetch_assets_table_raw()
        populate_assets_tree(assets_table_rows, tree)
        update_summary_counts(None)
        clear_asset_form()
        dept_cb['values'] = [d[1] for d in departments_list]
        dept_cb2['values'] = ["All"] + [d[1] for d in departments_list]

    def on_asset_select(event):
        global GLOBAL_SELECTED_ASSET_ID
        sel = tree.focus()
        if not sel:
            clear_asset_form()
            return
        vals = tree.item(sel, 'values')
        selected_id = extract_numeric_id_from_code(vals[0])
        GLOBAL_SELECTED_ASSET_ID = selected_id
        asset_code_var.set(vals[0])
        asset_name_var.set(vals[1])
        asset_category_var.set(vals[2])
        cost_var.set(vals[3])
        purchase_date_var.set(vals[4])
        asset_status_var.set(vals[5])
        dept_combo_var.set(vals[6] if len(vals) > 6 else "")
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT location FROM Assets WHERE asset_id = %s", (GLOBAL_SELECTED_ASSET_ID,))
            res = cursor.fetchone()
            if res:
                location_var.set(res[0] or "")
        except Exception:
            pass
        archive_btn.config(state='normal' if str(asset_status_var.get()).lower() != 'archived' else 'disabled')
        export_btn.config(state='normal')
        copy_btn.config(state='normal')
        primary_btn.config(text="Update", style='Primary.TButton')

    tree.bind('<<TreeviewSelect>>', on_asset_select)

    def add_update_asset():
        global GLOBAL_SELECTED_ASSET_ID
        name = asset_name_var.get().strip()
        category = asset_category_var.get().strip()
        purchase_date_str = purchase_date_var.get().strip()
        cost_str = cost_var.get().strip()
        location = location_var.get().strip() or None
        dept_name = dept_combo_var.get().strip()
        new_status = asset_status_var.get().strip()
        dept_id = next((d[0] for d in departments_list if d[1] == dept_name), None)

        if not all([name, category, purchase_date_str, cost_str]):
            messagebox.showwarning("Validation Error", "Name, Category, Purchase Date, and Cost are required.")
            return
        try:
            purchase_date = datetime.strptime(purchase_date_str, "%Y-%m-%d").date()
            cost_value = float(cost_str)
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid date or cost value.")
            return

        cursor = conn.cursor()
        try:
            if GLOBAL_SELECTED_ASSET_ID is None:
                cursor.execute("INSERT INTO Assets (name, category, purchase_date, cost, location, department_id, status) VALUES (%s,%s,%s,%s,%s,%s,%s)",
                               (name, category, purchase_date, cost_value, location, dept_id, new_status))
                conn.commit()
                new_id = cursor.lastrowid
                log_audit(new_id, "Added", LOGGED_IN_USER, f"Asset added: {name}")
                messagebox.showinfo("Success", "Asset added successfully.")
            else:
                cursor.execute("""UPDATE Assets SET name=%s, category=%s, purchase_date=%s, cost=%s, location=%s, department_id=%s, status=%s
                                  WHERE asset_id=%s""",
                               (name, category, purchase_date, cost_value, location, dept_id, new_status, GLOBAL_SELECTED_ASSET_ID))
                conn.commit()
                log_audit(GLOBAL_SELECTED_ASSET_ID, "Updated", LOGGED_IN_USER, f"Asset updated: {GLOBAL_SELECTED_ASSET_ID}")
                messagebox.showinfo("Success", "Asset updated successfully.")
            refresh_assets_view()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to save asset: {e}")

    primary_btn.config(command=add_update_asset)

    def archive_selected():
        global GLOBAL_SELECTED_ASSET_ID
        if GLOBAL_SELECTED_ASSET_ID is None:
            messagebox.showwarning("Select", "Select an asset first.")
            return
        if not messagebox.askyesno("Confirm", f"Archive {format_asset_code(GLOBAL_SELECTED_ASSET_ID)}?"):
            return
        cursor = conn.cursor()
        try:
            cursor.execute("UPDATE Assets SET status=%s WHERE asset_id=%s", ('Archived', GLOBAL_SELECTED_ASSET_ID))
            conn.commit()
            log_audit(GLOBAL_SELECTED_ASSET_ID, "Archived", LOGGED_IN_USER, "Archived via UI")
            messagebox.showinfo("Archived", "Asset archived.")
            refresh_assets_view()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to archive: {e}")

    archive_btn.config(command=archive_selected)

    def clear_asset_form():
        global GLOBAL_SELECTED_ASSET_ID
        GLOBAL_SELECTED_ASSET_ID = None
        asset_code_var.set("")
        asset_name_var.set("")
        asset_category_var.set("")
        purchase_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        cost_var.set("")
        location_var.set("")
        dept_combo_var.set("")
        asset_status_var.set('Available')
        archive_btn.config(state='disabled')
        export_btn.config(state='disabled')
        copy_btn.config(state='disabled')
        primary_btn.config(text="Add / Update", style='Primary.TButton')

    clear_btn.config(command=clear_asset_form)

    def copy_id():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select an asset first.")
            return
        vals = tree.item(sel, 'values')
        root = tab_frame.winfo_toplevel()
        try:
            root.clipboard_clear()
            root.clipboard_append(vals[0])
            messagebox.showinfo("Copied", f"{vals[0]} copied to clipboard.")
        except Exception as e:
            messagebox.showerror("Clipboard", f"Failed to copy: {e}")

    copy_btn.config(command=copy_id)

    def download_csv():
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV", "*.csv")], initialfile="asset_inventory.csv")
        if not filepath:
            return
        rows = []
        for iid in tree.get_children():
            rows.append(tree.item(iid, 'values'))
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(cols)
                for r in rows:
                    writer.writerow(r)
            messagebox.showinfo("Saved", f"CSV saved to {filepath}")
        except Exception as e:
            messagebox.showerror("File", f"Could not save CSV: {e}")

    csv_btn.config(command=download_csv)
    export_btn.config(command=lambda: download_csv())

    def generate_receipt_with_qr_local():
        sel = tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Select an asset first.")
            return
        vals = tree.item(sel, 'values')
        try:
            import qrcode
            from PIL import Image, ImageDraw, ImageFont
        except Exception:
            messagebox.showerror("Missing", "Install qrcode[pil] and pillow: pip install qrcode[pil] pillow")
            return
        asset_code = vals[0]
        asset_name = vals[1]
        category = vals[2]
        cost = vals[3]
        purchase_date = vals[4]
        status = vals[5]
        dept = vals[6] if len(vals) > 6 else ""
        qr = qrcode.make(f"{asset_code} | {asset_name}")
        width, height = 900, 520
        canvas = Image.new('RGB', (width, height), 'white')
        draw = ImageDraw.Draw(canvas)
        try:
            font_title = ImageFont.truetype("arial.ttf", 28)
            font_label = ImageFont.truetype("arial.ttf", 16)
        except Exception:
            font_title = ImageFont.load_default()
            font_label = ImageFont.load_default()
        draw.text((28, 24), "ASSET RECEIPT", font=font_title, fill='black')
        y = 84
        spacing = 34
        draw.text((28, y), f"Asset Code: {asset_code}", font=font_label, fill='black'); y += spacing
        draw.text((28, y), f"Name: {asset_name}", font=font_label, fill='black'); y += spacing
        draw.text((28, y), f"Category: {category}", font=font_label, fill='black'); y += spacing
        draw.text((28, y), f"Cost: {cost}", font=font_label, fill='black'); y += spacing
        draw.text((28, y), f"Purchase Date: {purchase_date}", font=font_label, fill='black'); y += spacing
        draw.text((28, y), f"Department: {dept}", font=font_label, fill='black')
        qr = qr.resize((260, 260))
        canvas.paste(qr, (width - 300, 120))
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], initialfile=f"Receipt_{asset_code}.png")
        if not path:
            return
        try:
            canvas.save(path)
            messagebox.showinfo("Saved", f"Receipt saved to {path}")
        except Exception as e:
            messagebox.showerror("Save", f"Failed to save: {e}")

    qr_btn.config(command=generate_receipt_with_qr_local)

    # Initial load
    refresh_assets_view()


# --- EMPLOYEES TAB (kept unchanged in behavior; visual refined) ---
def setup_employees_tab(tab_frame):
    global GLOBAL_SELECTED_EMP_ID

    tab_frame.configure(style='Tab.TFrame')
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.columnconfigure(1, weight=2)
    tab_frame.rowconfigure(0, weight=1)

    input_frame_container = ttk.Frame(tab_frame, padding="10", style='Tab.TFrame')
    input_frame_container.grid(row=0, column=0, sticky='nsew')
    input_frame_container.columnconfigure(0, weight=1)

    input_frame = ttk.LabelFrame(input_frame_container, text="Employee Details (Add / Edit)", padding="15")
    input_frame.pack(fill='x', padx=5, pady=5)
    input_frame.columnconfigure(1, weight=1)

    emp_full_name_var = tk.StringVar()
    emp_department_var = tk.StringVar()
    job_title_var = tk.StringVar()
    email_var = tk.StringVar()
    phone_var = tk.StringVar()
    date_joined_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

    def fetch_employees_table(tree_view):
        tree_view.delete(*tree_view.get_children())
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    employee_id, full_name, department, job_title, email, phone, date_joined 
                FROM Employees
            """)
            rows = cursor.fetchall()
            for r in rows:
                display_row = list(r)
                if display_row[6]:
                    display_row[6] = str(display_row[6])
                tree_view.insert("", "end", values=display_row)
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to fetch employees: {e}")

    def clear_employee_form():
        global GLOBAL_SELECTED_EMP_ID
        GLOBAL_SELECTED_EMP_ID = None
        emp_full_name_var.set("")
        emp_department_var.set("")
        job_title_var.set("")
        email_var.set("")
        phone_var.set("")
        date_joined_var.set(datetime.now().strftime("%Y-%m-%d"))
        add_button.config(text="Add New Employee", style='Primary.TButton')
        delete_button.config(state='disabled')

    def refresh_employees_view():
        fetch_dropdowns()
        fetch_employees_table(tree)
        clear_employee_form()

    row_idx = 0
    ttk.Label(input_frame, text="Full Name:").grid(row=row_idx, column=0, sticky='w', padx=5, pady=5); row_idx += 1
    ttk.Entry(input_frame, textvariable=emp_full_name_var, width=30).grid(row=row_idx - 1, column=1, padx=5, pady=5, sticky='ew')

    ttk.Label(input_frame, text="Job Title:").grid(row=row_idx, column=0, sticky='w', padx=5, pady=5); row_idx += 1
    ttk.Entry(input_frame, textvariable=job_title_var, width=30).grid(row=row_idx - 1, column=1, padx=5, pady=5, sticky='ew')

    ttk.Label(input_frame, text="Department (Text):").grid(row=row_idx, column=0, sticky='w', padx=5, pady=5); row_idx += 1
    ttk.Entry(input_frame, textvariable=emp_department_var, width=30).grid(row=row_idx - 1, column=1, padx=5, pady=5, sticky='ew')

    ttk.Label(input_frame, text="Email:").grid(row=row_idx, column=0, sticky='w', padx=5, pady=5); row_idx += 1
    ttk.Entry(input_frame, textvariable=email_var, width=30).grid(row=row_idx - 1, column=1, padx=5, pady=5, sticky='ew')

    ttk.Label(input_frame, text="Phone:").grid(row=row_idx, column=0, sticky='w', padx=5, pady=5); row_idx += 1
    ttk.Entry(input_frame, textvariable=phone_var, width=30).grid(row=row_idx - 1, column=1, padx=5, pady=5, sticky='ew')

    ttk.Label(input_frame, text="Date Joined (YYYY-MM-DD):").grid(row=row_idx, column=0, sticky='w', padx=5, pady=5); row_idx += 1
    ttk.Entry(input_frame, textvariable=date_joined_var, width=30).grid(row=row_idx - 1, column=1, padx=5, pady=5, sticky='ew')

    def add_update_employee():
        global GLOBAL_SELECTED_EMP_ID
        full_name = emp_full_name_var.get().strip()
        department = emp_department_var.get().strip() or None
        job_title = job_title_var.get().strip() or None
        email = email_var.get().strip() or None
        phone = phone_var.get().strip() or None
        date_joined_str = date_joined_var.get().strip()

        if not full_name:
            messagebox.showwarning("Validation Error", "Employee full name required.")
            return

        try:
            date_joined = datetime.strptime(date_joined_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid date format. Use YYYY-MM-DD for Date Joined.")
            return

        cursor = conn.cursor()
        try:
            if GLOBAL_SELECTED_EMP_ID is None:
                sql = "INSERT INTO Employees (full_name, department, job_title, email, phone, date_joined) VALUES (%s,%s,%s,%s,%s,%s)"
                data = (full_name, department, job_title, email, phone, date_joined)
                cursor.execute(sql, data)
                conn.commit()
                log_audit(None, "Added", LOGGED_IN_USER, f"New employee '{full_name}' added.")
                messagebox.showinfo("Success", f"Employee '{full_name}' added successfully.")
            else:
                sql = """
                    UPDATE Employees SET 
                    full_name = %s, department = %s, job_title = %s, email = %s, phone = %s, date_joined = %s 
                    WHERE employee_id = %s
                """
                data = (full_name, department, job_title, email, phone, date_joined, GLOBAL_SELECTED_EMP_ID)
                cursor.execute(sql, data)
                conn.commit()
                log_audit(None, "Updated", LOGGED_IN_USER, f"Employee ID {GLOBAL_SELECTED_EMP_ID} updated to '{full_name}'.")
                messagebox.showinfo("Success", f"Employee '{full_name}' updated successfully.")
            refresh_employees_view()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to perform employee operation: {e}")

    def delete_employee():
        global GLOBAL_SELECTED_EMP_ID
        if GLOBAL_SELECTED_EMP_ID is None:
            messagebox.showwarning("Selection Error", "Please select an employee to delete.")
            return

        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM AssetAssignments WHERE employee_id = %s AND return_date IS NULL", (GLOBAL_SELECTED_EMP_ID,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Error", "Cannot delete. This employee has currently assigned assets.")
            return

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Employee ID {GLOBAL_SELECTED_EMP_ID} ('{emp_full_name_var.get()}')?"):
            return

        try:
            cursor.execute("DELETE FROM AssetAssignments WHERE employee_id = %s", (GLOBAL_SELECTED_EMP_ID,))
            cursor.execute("DELETE FROM Employees WHERE employee_id = %s", (GLOBAL_SELECTED_EMP_ID,))
            conn.commit()
            log_audit(None, "Deleted", LOGGED_IN_USER, f"Employee ID {GLOBAL_SELECTED_EMP_ID} deleted.")
            messagebox.showinfo("Success", f"Employee ID {GLOBAL_SELECTED_EMP_ID} deleted successfully.")
            refresh_employees_view()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to delete employee: {e}")

    def on_employee_select(event):
        global GLOBAL_SELECTED_EMP_ID
        selected_item = tree.focus()
        if not selected_item:
            clear_employee_form()
            return
        values = tree.item(selected_item, 'values')
        GLOBAL_SELECTED_EMP_ID = values[0]
        emp_full_name_var.set(values[1])
        emp_department_var.set(values[2] or "")
        job_title_var.set(values[3] or "")
        email_var.set(values[4] or "")
        phone_var.set(values[5] or "")
        date_joined_var.set(values[6] if len(values) > 6 and values[6] else datetime.now().strftime("%Y-%m-%d"))
        add_button.config(text="Update Employee", style='TButton')
        delete_button.config(state='enabled')

    button_frame = ttk.Frame(input_frame)
    button_frame.grid(row=row_idx, column=0, columnspan=2, pady=15, sticky='ew')
    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.columnconfigure(2, weight=1)

    add_button = ttk.Button(button_frame, text="Add New Employee", command=add_update_employee, style='Primary.TButton')
    add_button.grid(row=0, column=0, padx=5, sticky='ew')
    delete_button = ttk.Button(button_frame, text="Delete", command=delete_employee, style='Danger.TButton', state='disabled')
    delete_button.grid(row=0, column=1, padx=5, sticky='ew')
    ttk.Button(button_frame, text="Clear", command=clear_employee_form, style='Clear.TButton').grid(row=0, column=2, padx=5, sticky='ew')

    table_frame = ttk.Frame(tab_frame)
    table_frame.grid(row=0, column=1, sticky='nsew')
    table_frame.rowconfigure(1, weight=1)
    table_frame.columnconfigure(0, weight=1)

    header_frame = ttk.Frame(table_frame)
    header_frame.grid(row=0, column=0, sticky='ew')
    header_frame.columnconfigure(0, weight=1)

    ttk.Label(header_frame, text="Employee List", style='SubHeader.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=5)

    refresh_btn = ttk.Button(header_frame, text="Refresh", command=refresh_employees_view, style='Clear.TButton')
    refresh_btn.grid(row=0, column=1, sticky='ne', padx=5, pady=5)

    table_container = ttk.Frame(table_frame)
    table_container.grid(row=1, column=0, sticky='nsew')
    table_container.rowconfigure(0, weight=1)
    table_container.columnconfigure(0, weight=1)

    columns = ("ID", "Name", "Department", "Job Title", "Email", "Phone", "Joined Date")
    tree = ttk.Treeview(table_container, columns=columns, show="headings")
    for col in columns:
        tree.heading(col, text=col)
    tree.column("ID", width=40, anchor='center')
    tree.column("Name", anchor='w', width=140)
    tree.column("Department", anchor='w', width=120)
    tree.column("Job Title", anchor='w', width=110)
    tree.column("Email", anchor='w', width=180)
    tree.column("Phone", anchor='w', width=110)
    tree.column("Joined Date", anchor='w', width=100)

    vscroll = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vscroll.set)
    tree.grid(row=0, column=0, sticky='nsew')
    vscroll.grid(row=0, column=1, sticky='ns')

    tree.bind('<<TreeviewSelect>>', on_employee_select)
    refresh_employees_view()


# --- ASSIGNMENTS TAB (visual refinements only) ---
def setup_assignments_tab(tab_frame):
    GLOBAL_SELECTED_ASSIGNMENT_ID = None

    fetch_dropdowns()

    tab_frame.configure(style='Tab.TFrame')
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.columnconfigure(1, weight=2)
    tab_frame.rowconfigure(0, weight=1)
    tab_frame.rowconfigure(1, weight=1)

    asset_combo_var = tk.StringVar()
    employee_combo_var = tk.StringVar()
    assign_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    assigned_asset_var = tk.StringVar()
    return_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))

    def fetch_assignments_table(tree_view):
        tree_view.delete(*tree_view.get_children())
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    a.assignment_id, ast.name, e.full_name, a.assign_date, a.return_date, a.asset_id
                FROM AssetAssignments a
                JOIN Assets ast ON a.asset_id = ast.asset_id
                JOIN Employees e ON a.employee_id = e.employee_id
                ORDER BY a.assignment_id DESC
            """)
            rows = cursor.fetchall()
            for r in rows:
                tag = 'active_assignment' if r[4] is None or str(r[4]).strip() == '' else ''
                tree_view.insert("", "end", values=r[:-1], tags=(tag, r[0], r[5]))
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to fetch assignments: {e}")

    def refresh_assignment_comboboxes(tree_view):
        fetch_dropdowns()
        fetch_assignments_table(tree_view)
        available_assets = [a[1] for a in assets_list if '(Available)' in a[1]]
        asset_combo['values'] = available_assets
        asset_combo_var.set("")
        assigned_assets = [a[1] for a in assets_list if '(Assigned)' in a[1]]
        assigned_asset_combo['values'] = assigned_assets
        assigned_asset_combo.set("")
        employee_combo['values'] = [e[1] for e in employees_list]
        employee_combo_var.set("")

    def assign_asset():
        asset_info = asset_combo_var.get()
        emp_name = employee_combo_var.get()
        assign_date_str = assign_date_var.get().strip()

        asset_id = parse_combo_selection(asset_info, assets_list)
        employee_id = parse_combo_selection(emp_name, employees_list)

        if not all([asset_id, employee_id, assign_date_str]):
            messagebox.showwarning("Validation Error", "All fields are required.")
            return

        if '(Assigned)' in asset_info or '(In Maintenance)' in asset_info:
            messagebox.showwarning("Status Error", "This asset is not Available for assignment.")
            return

        try:
            assign_date = datetime.strptime(assign_date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO AssetAssignments (asset_id, employee_id, assign_date) VALUES (%s,%s,%s)",
                           (asset_id, employee_id, assign_date))
            conn.commit()
            if update_asset_status(asset_id, 'Assigned'):
                log_audit(asset_id, "Assigned", LOGGED_IN_USER, f"Asset ID {asset_id} assigned to employee ID {employee_id}.")
                messagebox.showinfo("Success", "Asset assigned successfully.")
                refresh_assignment_comboboxes(tree)
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to assign asset: {e}")

    def record_return():
        asset_info = assigned_asset_var.get()
        return_date_str = return_date_var.get().strip()
        asset_id = parse_combo_selection(asset_info, assets_list)

        if not all([asset_id, return_date_str]):
            messagebox.showwarning("Validation Error", "Asset and Return Date are required.")
            return

        if '(Available)' in asset_info:
            messagebox.showwarning("Status Error", "This asset is already Available. No return record needed.")
            return

        try:
            return_date = datetime.strptime(return_date_str, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid date format. Use YYYY-MM-DD.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE AssetAssignments 
                SET return_date = %s 
                WHERE asset_id = %s AND return_date IS NULL
                ORDER BY assign_date DESC 
                LIMIT 1
            """, (return_date, asset_id))
            conn.commit()

            if cursor.rowcount == 0:
                messagebox.showwarning("Validation Warning", "No open assignment record found for this asset. Status remains unchanged.")
                return

            if update_asset_status(asset_id, 'Available'):
                log_audit(asset_id, "Returned", LOGGED_IN_USER, f"Asset ID {asset_id} returned on {return_date_str}. Status set to Available.")
                messagebox.showinfo("Success", "Asset return recorded and status updated.")
                assigned_asset_var.set("")
                refresh_assignment_comboboxes(tree)

        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to record return: {e}")

    def delete_assignment():
        nonlocal GLOBAL_SELECTED_ASSIGNMENT_ID
        if GLOBAL_SELECTED_ASSIGNMENT_ID is None:
            messagebox.showwarning("Selection Error", "Please select an assignment record to delete/cancel.")
            return

        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Assignment ID {GLOBAL_SELECTED_ASSIGNMENT_ID}?\n\nIf this was an open assignment, the asset status will be set to 'Available'."):
            return

        cursor = conn.cursor()
        try:
            selected_item = tree.focus()
            tags = tree.item(selected_item, 'tags')
            asset_id_to_check = tags[2]
            was_open = 'active_assignment' in tags
            cursor.execute("DELETE FROM AssetAssignments WHERE assignment_id = %s", (GLOBAL_SELECTED_ASSIGNMENT_ID,))
            conn.commit()
            if was_open:
                cursor.execute("SELECT COUNT(*) FROM AssetAssignments WHERE asset_id = %s AND return_date IS NULL", (asset_id_to_check,))
                if cursor.fetchone()[0] == 0:
                    update_asset_status(asset_id_to_check, 'Available')
                    log_audit(asset_id_to_check, "Assignment Cancelled/Deleted", LOGGED_IN_USER, f"Assignment ID {GLOBAL_SELECTED_ASSIGNMENT_ID} deleted. Asset status set to Available.")
                else:
                    log_audit(asset_id_to_check, "Assignment Deleted", LOGGED_IN_USER, f"Assignment ID {GLOBAL_SELECTED_ASSIGNMENT_ID} deleted. Asset remains assigned to another user.")
            else:
                log_audit(asset_id_to_check, "Historical Assignment Deleted", LOGGED_IN_USER, f"Historical Assignment ID {GLOBAL_SELECTED_ASSIGNMENT_ID} deleted.")
            messagebox.showinfo("Success", f"Assignment ID {GLOBAL_SELECTED_ASSIGNMENT_ID} deleted successfully.")
            GLOBAL_SELECTED_ASSIGNMENT_ID = None
            delete_button.config(state='disabled')
            refresh_assignment_comboboxes(tree)
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to delete assignment: {e}")
        except IndexError:
            messagebox.showerror("Error", "Could not retrieve necessary IDs for deletion.")

    def on_assignment_select(event):
        nonlocal GLOBAL_SELECTED_ASSIGNMENT_ID
        selected_item = tree.focus()
        if not selected_item:
            GLOBAL_SELECTED_ASSIGNMENT_ID = None
            delete_button.config(state='disabled')
            return
        tags = tree.item(selected_item, 'tags')
        GLOBAL_SELECTED_ASSIGNMENT_ID = tags[1]
        delete_button.config(state='enabled')

    input_panel = ttk.Frame(tab_frame, padding="10", style='Tab.TFrame')
    input_panel.grid(row=0, column=0, sticky='nsew')
    input_panel.columnconfigure(0, weight=1)

    assign_group = ttk.LabelFrame(input_panel, text="New Asset Assignment", padding="15")
    assign_group.pack(fill='x', padx=5, pady=10)
    assign_group.columnconfigure(1, weight=1)

    fields = [
        ("Asset (Available Only):", asset_combo_var, [a[1] for a in assets_list if '(Available)' in a[1]]),
        ("Employee:", employee_combo_var, [e[1] for e in employees_list]),
        ("Assignment Date:", assign_date_var, None)
    ]
    for i, (label_text, var, values) in enumerate(fields):
        ttk.Label(assign_group, text=label_text).grid(row=i, column=0, sticky='w', padx=5, pady=8)
        if values is not None:
            if label_text.startswith("Asset"):
                asset_combo = ttk.Combobox(assign_group, textvariable=var, values=values, width=40, state='readonly')
                asset_combo.grid(row=i, column=1, padx=5, pady=8, sticky='ew')
            elif label_text.startswith("Employee"):
                employee_combo = ttk.Combobox(assign_group, textvariable=var, values=values, width=40, state='readonly')
                employee_combo.grid(row=i, column=1, padx=5, pady=8, sticky='ew')
        else:
            ttk.Entry(assign_group, textvariable=var, width=40).grid(row=i, column=1, padx=5, pady=8, sticky='ew')

    ttk.Button(assign_group, text="Perform Assignment", command=assign_asset, style='Primary.TButton').grid(row=len(fields), column=0, columnspan=2, pady=15, sticky='ew')

    return_group = ttk.LabelFrame(input_panel, text="Record Asset Return", padding="15")
    return_group.pack(fill='x', padx=5, pady=10)
    return_group.columnconfigure(1, weight=1)

    ttk.Label(return_group, text="Assigned Asset:").grid(row=0, column=0, sticky='w', padx=5, pady=8)
    assigned_assets = [a[1] for a in assets_list if '(Assigned)' in a[1]]
    assigned_asset_combo = ttk.Combobox(return_group, textvariable=assigned_asset_var,
                                        values=assigned_assets,
                                        width=40, state='readonly')
    assigned_asset_combo.grid(row=0, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(return_group, text="Return Date (YYYY-MM-DD):").grid(row=1, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(return_group, textvariable=return_date_var, width=40).grid(row=1, column=1, padx=5, pady=8, sticky='ew')

    ttk.Button(return_group, text="Record Return", command=record_return, style='TButton').grid(row=2, column=0, columnspan=2, pady=15, sticky='ew')

    ttk.Button(input_panel, text="Refresh Data", command=lambda: refresh_assignment_comboboxes(tree), style='Clear.TButton').pack(pady=10, fill='x')

    table_frame = ttk.Frame(tab_frame, padding="10", style='Tab.TFrame')
    table_frame.grid(row=0, column=1, sticky='nsew', rowspan=2)
    table_frame.rowconfigure(1, weight=1)
    table_frame.columnconfigure(0, weight=1)

    header_frame = ttk.Frame(table_frame)
    header_frame.grid(row=0, column=0, sticky='ew')
    header_frame.columnconfigure(0, weight=1)

    ttk.Label(header_frame, text="Assignment History", style='SubHeader.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=5)

    refresh_btn = ttk.Button(header_frame, text="Refresh", command=lambda: refresh_assignment_comboboxes(tree), style='Clear.TButton')
    refresh_btn.grid(row=0, column=1, sticky='ne', padx=5, pady=5)

    table_container = ttk.Frame(table_frame)
    table_container.grid(row=1, column=0, sticky='nsew')
    table_container.rowconfigure(0, weight=1)
    table_container.columnconfigure(0, weight=1)

    columns = ("ID", "Asset", "Employee", "Assigned Date", "Return Date")
    tree = ttk.Treeview(table_container, columns=columns, show="headings")

    tree.tag_configure('active_assignment', background='#FFF3CD', foreground='#664D03')

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, anchor='center', width=120)
    tree.column("ID", width=40)
    tree.column("Asset", anchor='w', width=180)
    tree.column("Employee", anchor='w', width=150)

    vscroll = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vscroll.set)
    tree.grid(row=0, column=0, sticky='nsew')
    vscroll.grid(row=0, column=1, sticky='ns')

    delete_button = ttk.Button(table_frame, text="Delete Selected Assignment", command=delete_assignment, style='Danger.TButton', state='disabled')
    delete_button.grid(row=2, column=0, pady=10, sticky='ew')

    tree.bind('<<TreeviewSelect>>', on_assignment_select)
    refresh_assignment_comboboxes(tree)


# --- MAINTENANCE TAB (visual only) ---
def setup_maintenance_tab(tab_frame):
    global GLOBAL_SELECTED_MAINT_ID

    fetch_dropdowns()

    tab_frame.configure(style='Tab.TFrame')
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.rowconfigure(1, weight=3)

    new_asset_combo_var = tk.StringVar()
    vendor_combo_var = tk.StringVar()
    issue_desc_var = tk.StringVar()
    start_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    cost_var = tk.StringVar()
    maint_asset_combo_var = tk.StringVar()
    end_date_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
    final_cost_var = tk.StringVar()

    def fetch_maintenance_table(tree_view):
        tree_view.delete(*tree_view.get_children())
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    m.maintenance_id, a.name, v.name, m.issue_desc, m.start_date, m.end_date, m.cost, m.asset_id, m.vendor_id
                FROM Maintenance m
                JOIN Assets a ON m.asset_id = a.asset_id
                LEFT JOIN Vendors v ON m.vendor_id = v.vendor_id
                ORDER BY m.maintenance_id DESC
            """)
            rows = cursor.fetchall()
            for r in rows:
                tag = 'open_maint' if r[5] is None or str(r[5]).strip() == '' else ''
                tree_view.insert("", "end", values=r[:-2], tags=(tag, r[7], r[8]))
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to fetch maintenance records: {e}")

    def clear_maint_start_form():
        global GLOBAL_SELECTED_MAINT_ID
        GLOBAL_SELECTED_MAINT_ID = None
        new_asset_combo_var.set("")
        vendor_combo_var.set("")
        issue_desc_var.set("")
        cost_var.set("")
        start_date_var.set(datetime.now().strftime("%Y-%m-%d"))
        maint_add_button.config(text="Record Maintenance Start", style='Primary.TButton')
        maint_delete_button.config(state='disabled')

    def refresh_maintenance_views():
        fetch_dropdowns()
        fetch_maintenance_table(tree)
        new_asset_combo['values'] = [a[1] for a in assets_list]
        vendor_combo['values'] = [v[1] for v in vendors_list]
        new_asset_combo_var.set("")
        vendor_combo_var.set("")
        assets_in_maint = [a[1] for a in assets_list if '(In Maintenance)' in a[1]]
        maint_asset_combo['values'] = assets_in_maint
        maint_asset_combo_var.set("")
        clear_maint_start_form()

    def record_maintenance():
        global GLOBAL_SELECTED_MAINT_ID
        asset_info = new_asset_combo_var.get()
        vendor_name = vendor_combo_var.get()
        issue_desc = issue_desc_var.get().strip()
        start_date_str = start_date_var.get().strip()
        cost_str = cost_var.get().strip()

        asset_id = parse_combo_selection(asset_info, assets_list)
        vendor_id = parse_combo_selection(vendor_name, vendors_list)

        if not all([asset_id, vendor_id, issue_desc, start_date_str, cost_str]):
            messagebox.showwarning("Validation Error", "All fields are required.")
            return

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            cost_value = float(cost_str)
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid date (YYYY-MM-DD) or Cost format.")
            return

        cursor = conn.cursor()
        try:
            if GLOBAL_SELECTED_MAINT_ID is None:
                sql = "INSERT INTO Maintenance (asset_id, vendor_id, issue_desc, start_date, cost) VALUES (%s,%s,%s,%s,%s)"
                data = (asset_id, vendor_id, issue_desc, start_date, cost_value)
                cursor.execute(sql, data)
                conn.commit()
                update_asset_status(asset_id, 'In Maintenance')
                log_audit(asset_id, "Maintenance Started", LOGGED_IN_USER, f"Maintenance started on Asset ID {asset_id}. Est. Cost: ${cost_value}.")
                messagebox.showinfo("Success", "Maintenance start record added successfully. Asset status set to 'In Maintenance'.")
            else:
                sql = """
                    UPDATE Maintenance 
                    SET asset_id = %s, vendor_id = %s, issue_desc = %s, start_date = %s, cost = %s
                    WHERE maintenance_id = %s AND end_date IS NULL
                """
                data = (asset_id, vendor_id, issue_desc, start_date, cost_value, GLOBAL_SELECTED_MAINT_ID)
                cursor.execute(sql, data)
                conn.commit()
                log_audit(asset_id, "Maintenance Info Updated", LOGGED_IN_USER, f"Maintenance record ID {GLOBAL_SELECTED_MAINT_ID} updated. Est. Cost: ${cost_value}.")
                messagebox.showinfo("Success", f"Maintenance record ID {GLOBAL_SELECTED_MAINT_ID} updated successfully.")
            refresh_maintenance_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to record maintenance: {e}")

    def delete_maintenance_record():
        global GLOBAL_SELECTED_MAINT_ID
        if GLOBAL_SELECTED_MAINT_ID is None:
            messagebox.showwarning("Selection Error", "Please select a maintenance record to delete.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Maintenance Record ID {GLOBAL_SELECTED_MAINT_ID}?"):
            return
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT asset_id, end_date FROM Maintenance WHERE maintenance_id = %s", (GLOBAL_SELECTED_MAINT_ID,))
            result = cursor.fetchone()
            asset_id = result[0]
            end_date = result[1]
            cursor.execute("DELETE FROM Maintenance WHERE maintenance_id = %s", (GLOBAL_SELECTED_MAINT_ID,))
            conn.commit()
            if end_date is None:
                cursor.execute("SELECT COUNT(*) FROM Maintenance WHERE asset_id = %s AND end_date IS NULL", (asset_id,))
                if cursor.fetchone()[0] == 0:
                    update_asset_status(asset_id, 'Available')
            log_audit(asset_id, "Maintenance Deleted", LOGGED_IN_USER, f"Maintenance record ID {GLOBAL_SELECTED_MAINT_ID} deleted.")
            messagebox.showinfo("Success", f"Maintenance record ID {GLOBAL_SELECTED_MAINT_ID} deleted.")
            refresh_maintenance_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to delete maintenance record: {e}")

    def finish_maintenance():
        asset_info = maint_asset_combo_var.get()
        end_date_str = end_date_var.get().strip()
        final_cost_str = final_cost_var.get().strip()
        asset_id = parse_combo_selection(asset_info, assets_list)
        if not all([asset_id, end_date_str, final_cost_str]):
            messagebox.showwarning("Validation Error", "Asset, Completion Date, and Final Cost are required.")
            return
        if '(In Maintenance)' not in asset_info:
            messagebox.showwarning("Status Error", "Selected asset is not currently in maintenance.")
            return
        try:
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
            final_cost = float(final_cost_str)
        except ValueError:
            messagebox.showwarning("Validation Error", "Invalid date (YYYY-MM-DD) or Cost format.")
            return

        cursor = conn.cursor()
        try:
            cursor.execute("""
                UPDATE Maintenance 
                SET end_date = %s, cost = %s 
                WHERE asset_id = %s AND end_date IS NULL
                ORDER BY start_date DESC 
                LIMIT 1
            """, (end_date, final_cost, asset_id))
            conn.commit()
            if update_asset_status(asset_id, 'Available'):
                log_audit(asset_id, "Maintenance Finished", LOGGED_IN_USER, f"Maintenance completed on Asset ID {asset_id}. Final Cost: ${final_cost}.")
                messagebox.showinfo("Success", "Maintenance finished, asset status updated to 'Available'.")
                maint_asset_combo_var.set("")
                final_cost_var.set("")
                refresh_maintenance_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to record maintenance completion: {e}")

    def on_maintenance_select(event):
        global GLOBAL_SELECTED_MAINT_ID
        selected_item = tree.focus()
        if not selected_item:
            clear_maint_start_form()
            return
        values = tree.item(selected_item, 'values')
        tags = tree.item(selected_item, 'tags')
        GLOBAL_SELECTED_MAINT_ID = values[0]
        if 'open_maint' not in tags:
            messagebox.showinfo("Read-Only", "Completed maintenance records can only be viewed, not edited.")
            clear_maint_start_form()
            return
        asset_id_from_tag = tags[1]
        vendor_id_from_tag = tags[2]
        asset_string = next((a[1] for a in assets_list if a[0] == asset_id_from_tag), values[1])
        vendor_string = next((v[1] for v in vendors_list if v[0] == vendor_id_from_tag), values[2])
        new_asset_combo_var.set(asset_string)
        vendor_combo_var.set(vendor_string)
        issue_desc_var.set(values[3])
        start_date_var.set(values[4])
        cost_var.set(values[6] if values[6] is not None and str(values[6]).strip() != '' else "")
        maint_add_button.config(text="Update Maintenance Record", style='TButton')
        maint_delete_button.config(state='enabled')

    forms_section = ttk.Frame(tab_frame, padding="10", style='Tab.TFrame')
    forms_section.grid(row=0, column=0, sticky='new')
    forms_section.columnconfigure(0, weight=1)
    forms_section.columnconfigure(1, weight=1)

    left_form_container = ttk.Frame(forms_section, padding="5")
    left_form_container.grid(row=0, column=0, sticky='nsw', padx=5)
    left_form_container.columnconfigure(0, weight=1)

    input_frame = ttk.LabelFrame(left_form_container, text="Record New/Edit Open Maintenance", padding="15")
    input_frame.pack(fill='x', padx=5, pady=5)
    input_frame.columnconfigure(1, weight=1)

    ttk.Label(input_frame, text="Asset (ID: Name):").grid(row=0, column=0, sticky='w', padx=5, pady=8)
    new_asset_combo = ttk.Combobox(input_frame, textvariable=new_asset_combo_var, values=[a[1] for a in assets_list], width=40, state='readonly')
    new_asset_combo.grid(row=0, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(input_frame, text="Vendor:").grid(row=1, column=0, sticky='w', padx=5, pady=8)
    vendor_combo = ttk.Combobox(input_frame, textvariable=vendor_combo_var, values=[v[1] for v in vendors_list], width=40, state='readonly')
    vendor_combo.grid(row=1, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(input_frame, text="Issue Description:").grid(row=2, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(input_frame, textvariable=issue_desc_var, width=40).grid(row=2, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(input_frame, text="Start Date:").grid(row=3, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(input_frame, textvariable=start_date_var, width=40).grid(row=3, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(input_frame, text="Estimated Cost ($):").grid(row=4, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(input_frame, textvariable=cost_var, width=40).grid(row=4, column=1, padx=5, pady=8, sticky='ew')

    maint_action_frame = ttk.Frame(input_frame)
    maint_action_frame.grid(row=5, column=0, columnspan=2, pady=15, sticky='ew')
    maint_action_frame.columnconfigure(0, weight=1)
    maint_action_frame.columnconfigure(1, weight=1)
    maint_action_frame.columnconfigure(2, weight=1)

    maint_add_button = ttk.Button(maint_action_frame, text="Record Maintenance Start", command=record_maintenance, style='Primary.TButton')
    maint_add_button.grid(row=0, column=0, padx=5, sticky='ew')
    maint_delete_button = ttk.Button(maint_action_frame, text="Delete Record", command=delete_maintenance_record, style='Danger.TButton', state='disabled')
    maint_delete_button.grid(row=0, column=1, padx=5, sticky='ew')
    ttk.Button(maint_action_frame, text="Clear", command=clear_maint_start_form, style='Clear.TButton').grid(row=0, column=2, padx=5, sticky='ew')

    right_form_container = ttk.Frame(forms_section, padding="5")
    right_form_container.grid(row=0, column=1, sticky='nsw', padx=5)
    right_form_container.columnconfigure(0, weight=1)

    finish_frame = ttk.LabelFrame(right_form_container, text="Record Maintenance Completion", padding="15")
    finish_frame.pack(fill='x', padx=5, pady=5)
    finish_frame.columnconfigure(1, weight=1)

    ttk.Label(finish_frame, text="Asset (In Maint.):").grid(row=0, column=0, sticky='w', padx=5, pady=8)
    assets_in_maint = [a[1] for a in assets_list if '(In Maintenance)' in a[1]]
    maint_asset_combo = ttk.Combobox(finish_frame, textvariable=maint_asset_combo_var,
                                     values=assets_in_maint,
                                     width=40, state='readonly')
    maint_asset_combo.grid(row=0, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(finish_frame, text="Completion Date:").grid(row=1, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(finish_frame, textvariable=end_date_var, width=40).grid(row=1, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(finish_frame, text="Final Cost ($):").grid(row=2, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(finish_frame, textvariable=final_cost_var, width=40).grid(row=2, column=1, padx=5, pady=8, sticky='ew')

    ttk.Button(finish_frame, text="Finish Maintenance", command=finish_maintenance, style='TButton').grid(row=3, column=0, columnspan=2, pady=15, sticky='ew')

    table_frame = ttk.Frame(tab_frame, padding="10")
    table_frame.grid(row=1, column=0, padx=10, pady=10, sticky='nsew')
    table_frame.rowconfigure(1, weight=1)
    table_frame.columnconfigure(0, weight=1)

    header_frame = ttk.Frame(table_frame)
    header_frame.grid(row=0, column=0, sticky='ew')
    header_frame.columnconfigure(0, weight=1)

    ttk.Label(header_frame, text="Maintenance History", style='SubHeader.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=5)

    refresh_btn = ttk.Button(header_frame, text="Refresh", command=refresh_maintenance_views, style='Clear.TButton')
    refresh_btn.grid(row=0, column=1, sticky='ne', padx=5, pady=5)

    table_container = ttk.Frame(table_frame)
    table_container.grid(row=1, column=0, sticky='nsew')
    table_container.rowconfigure(0, weight=1)
    table_container.columnconfigure(0, weight=1)

    columns = ("ID", "Asset", "Vendor", "Issue", "Start Date", "End Date", "Cost")
    tree = ttk.Treeview(table_container, columns=columns, show="headings")

    tree.tag_configure('open_maint', background='#ADD8E6')

    for col in columns:
        tree.heading(col, text=col)
    tree.column("ID", width=40, anchor='center')
    tree.column("Asset", width=140, anchor='w')
    tree.column("Vendor", width=120, anchor='w')
    tree.column("Issue", anchor='w', width=220)
    tree.column("Cost", width=100, anchor='e')

    vscroll = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
    hscroll = ttk.Scrollbar(table_container, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    tree.grid(row=0, column=0, sticky='nsew')
    vscroll.grid(row=0, column=1, sticky='ns')
    hscroll.grid(row=1, column=0, sticky='ew')

    tree.bind('<<TreeviewSelect>>', on_maintenance_select)
    refresh_maintenance_views()


# --- REPORTS TAB (mask asset id display) ---
def setup_reports_tab(tab_frame):
    tab_frame.configure(style='Tab.TFrame')
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.rowconfigure(1, weight=1)

    def fetch_audit_log(tree_view):
        """
        Populate Audit Log table but mask/hide the Asset ID column for display.
        Stored audit entries in DB remain unchanged; we only replace the displayed value with '***'.
        """
        tree_view.delete(*tree_view.get_children())
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT 
                    audit_id, timestamp, asset_id, action, performed_by, notes
                FROM AuditHistory 
                ORDER BY timestamp DESC
            """)
            rows = cursor.fetchall()
            for r in rows:
                display = list(r)
                # Mask the asset_id in the display (index 2). Keep empty or None as-is.
                if display[2] is not None and str(display[2]).strip() != "":
                    display[2] = '***'  # replace with masked value
                tree_view.insert("", "end", values=display)
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to fetch audit logs: {e}")

    def refresh_log_view():
        fetch_audit_log(tree)

    header_frame = ttk.Frame(tab_frame)
    header_frame.grid(row=0, column=0, sticky='ew')
    header_frame.columnconfigure(0, weight=1)

    ttk.Label(header_frame, text="System Audit Log", style='SubHeader.TLabel').grid(row=0, column=0, sticky='w', pady=5, padx=5)
    refresh_btn = ttk.Button(header_frame, text="Refresh", command=refresh_log_view, style='Clear.TButton')
    refresh_btn.grid(row=0, column=1, sticky='ne', padx=5, pady=5)

    table_container = ttk.Frame(tab_frame, padding="10 5 10 10")
    table_container.grid(row=1, column=0, sticky='nsew')
    table_container.rowconfigure(0, weight=1)
    table_container.columnconfigure(0, weight=1)

    columns = ("ID", "Timestamp", "Asset ID", "Action", "Performed By", "Notes")
    tree = ttk.Treeview(table_container, columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col)

    tree.column("ID", width=60, anchor='center')
    tree.column("Timestamp", width=180, anchor='center')
    tree.column("Asset ID", width=100, anchor='center')
    tree.column("Action", width=140, anchor='w')
    tree.column("Performed By", width=140, anchor='w')
    tree.column("Notes", width=420, anchor='w')

    vscroll = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
    hscroll = ttk.Scrollbar(table_container, orient="horizontal", command=tree.xview)

    tree.configure(yscrollcommand=vscroll.set, xscrollcommand=hscroll.set)

    tree.grid(row=0, column=0, sticky='nsew')
    vscroll.grid(row=0, column=1, sticky='ns')
    hscroll.grid(row=1, column=0, sticky='ew')

    refresh_log_view()


# --- ADMIN TAB (unchanged in behavior; refined visuals) ---
def setup_admin_tab(tab_frame):
    global GLOBAL_SELECTED_DEPT_ID, GLOBAL_SELECTED_VENDOR_ID

    tab_frame.configure(style='Tab.TFrame')
    tab_frame.columnconfigure(0, weight=1)
    tab_frame.columnconfigure(1, weight=1)
    tab_frame.rowconfigure(0, weight=1)

    dept_name_var = tk.StringVar()
    vendor_name_var = tk.StringVar()
    vendor_contact_var = tk.StringVar()

    def fetch_departments_table(tree_view):
        tree_view.delete(*tree_view.get_children())
        cursor = conn.cursor()
        cursor.execute("SELECT dept_id, dept_name FROM Departments")
        for r in cursor.fetchall():
            tree_view.insert("", "end", values=r)

    def clear_dept_form():
        global GLOBAL_SELECTED_DEPT_ID
        GLOBAL_SELECTED_DEPT_ID = None
        dept_name_var.set("")
        dept_add_button.config(text="Add New Department", style='Primary.TButton')
        dept_delete_button.config(state='disabled')

    def refresh_admin_views():
        fetch_dropdowns()
        fetch_departments_table(dept_tree)
        fetch_vendors_table(vendor_tree)
        clear_dept_form()
        clear_vendor_form()

    def add_update_department():
        global GLOBAL_SELECTED_DEPT_ID
        name = dept_name_var.get().strip()
        if not name:
            messagebox.showwarning("Error", "Department name required")
            return
        cursor = conn.cursor()
        try:
            if GLOBAL_SELECTED_DEPT_ID is None:
                cursor.execute("INSERT INTO Departments (dept_name) VALUES (%s)", (name,))
                messagebox.showinfo("Success", "Department added")
            else:
                cursor.execute("UPDATE Departments SET dept_name = %s WHERE dept_id = %s", (name, GLOBAL_SELECTED_DEPT_ID))
                messagebox.showinfo("Success", "Department updated")
            conn.commit()
            refresh_admin_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to perform department operation: {e}")

    def delete_department():
        global GLOBAL_SELECTED_DEPT_ID
        if GLOBAL_SELECTED_DEPT_ID is None:
            messagebox.showwarning("Selection Error", "Please select a department to delete.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Assets WHERE department_id = %s", (GLOBAL_SELECTED_DEPT_ID,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Error", "Cannot delete. Assets are linked to this department.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Department ID {GLOBAL_SELECTED_DEPT_ID}?"):
            return
        try:
            cursor.execute("DELETE FROM Departments WHERE dept_id = %s", (GLOBAL_SELECTED_DEPT_ID,))
            conn.commit()
            messagebox.showinfo("Success", f"Department ID {GLOBAL_SELECTED_DEPT_ID} deleted.")
            refresh_admin_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to delete department: {e}")

    def on_dept_select(event):
        global GLOBAL_SELECTED_DEPT_ID
        selected_item = dept_tree.focus()
        if not selected_item:
            clear_dept_form()
            return
        values = dept_tree.item(selected_item, 'values')
        GLOBAL_SELECTED_DEPT_ID = values[0]
        dept_name_var.set(values[1])
        dept_add_button.config(text="Update Department", style='TButton')
        dept_delete_button.config(state='enabled')

    def fetch_vendors_table(tree_view):
        tree_view.delete(*tree_view.get_children())
        cursor = conn.cursor()
        cursor.execute("SELECT vendor_id, name, contact FROM Vendors")
        for r in cursor.fetchall():
            tree_view.insert("", "end", values=r)

    def clear_vendor_form():
        global GLOBAL_SELECTED_VENDOR_ID
        GLOBAL_SELECTED_VENDOR_ID = None
        vendor_name_var.set("")
        vendor_contact_var.set("")
        vendor_add_button.config(text="Add New Vendor", style='Primary.TButton')
        vendor_delete_button.config(state='disabled')

    def add_update_vendor():
        global GLOBAL_SELECTED_VENDOR_ID
        name = vendor_name_var.get().strip()
        contact = vendor_contact_var.get().strip()
        if not name:
            messagebox.showwarning("Error", "Vendor name required")
            return
        cursor = conn.cursor()
        try:
            if GLOBAL_SELECTED_VENDOR_ID is None:
                cursor.execute("INSERT INTO Vendors (name, contact) VALUES (%s,%s)", (name, contact))
                messagebox.showinfo("Success", "Vendor added")
            else:
                cursor.execute("UPDATE Vendors SET name = %s, contact = %s WHERE vendor_id = %s", (name, contact, GLOBAL_SELECTED_VENDOR_ID))
                messagebox.showinfo("Success", "Vendor updated")
            conn.commit()
            refresh_admin_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to perform vendor operation: {e}")

    def delete_vendor():
        global GLOBAL_SELECTED_VENDOR_ID
        if GLOBAL_SELECTED_VENDOR_ID is None:
            messagebox.showwarning("Selection Error", "Please select a vendor to delete.")
            return
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM Maintenance WHERE vendor_id = %s", (GLOBAL_SELECTED_VENDOR_ID,))
        if cursor.fetchone()[0] > 0:
            messagebox.showwarning("Error", "Cannot delete. Maintenance records are linked to this vendor.")
            return
        if not messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete Vendor ID {GLOBAL_SELECTED_VENDOR_ID}?"):
            return
        try:
            cursor.execute("DELETE FROM Vendors WHERE vendor_id = %s", (GLOBAL_SELECTED_VENDOR_ID,))
            conn.commit()
            messagebox.showinfo("Success", f"Vendor ID {GLOBAL_SELECTED_VENDOR_ID} deleted.")
            refresh_admin_views()
        except mysql.connector.Error as e:
            messagebox.showerror("DB Error", f"Failed to delete vendor: {e}")

    def on_vendor_select(event):
        global GLOBAL_SELECTED_VENDOR_ID
        selected_item = vendor_tree.focus()
        if not selected_item:
            clear_vendor_form()
            return
        values = vendor_tree.item(selected_item, 'values')
        GLOBAL_SELECTED_VENDOR_ID = values[0]
        vendor_name_var.set(values[1])
        vendor_contact_var.set(values[2] or "")
        vendor_add_button.config(text="Update Vendor", style='TButton')
        vendor_delete_button.config(state='enabled')

    dept_frame = ttk.LabelFrame(tab_frame, text="Manage Departments (Used by Assets Tab)", padding="15")
    dept_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
    dept_frame.columnconfigure(1, weight=1)
    dept_frame.rowconfigure(2, weight=1)

    ttk.Label(dept_frame, text="Department Name:").grid(row=0, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(dept_frame, textvariable=dept_name_var, width=30).grid(row=0, column=1, padx=5, pady=8, sticky='ew')

    dept_action_frame = ttk.Frame(dept_frame)
    dept_action_frame.grid(row=1, column=0, columnspan=2, pady=10, sticky='ew')
    dept_action_frame.columnconfigure(0, weight=1)
    dept_action_frame.columnconfigure(1, weight=1)
    dept_action_frame.columnconfigure(2, weight=1)

    dept_add_button = ttk.Button(dept_action_frame, text="Add New Department", command=add_update_department, style='Primary.TButton')
    dept_add_button.grid(row=0, column=0, padx=5, sticky='ew')
    dept_delete_button = ttk.Button(dept_action_frame, text="Delete", command=delete_department, style='Danger.TButton', state='disabled')
    dept_delete_button.grid(row=0, column=1, padx=5, sticky='ew')
    ttk.Button(dept_action_frame, text="Clear", command=clear_dept_form, style='Clear.TButton').grid(row=0, column=2, padx=5, sticky='ew')

    dept_tree_container = ttk.Frame(dept_frame)
    dept_tree_container.grid(row=2, column=0, columnspan=2, sticky='nsew', pady=10)
    dept_tree_container.rowconfigure(0, weight=1)
    dept_tree_container.columnconfigure(0, weight=1)

    dept_tree = ttk.Treeview(dept_tree_container, columns=("ID", "Name"), show="headings", height=8)
    dept_tree.grid(row=0, column=0, sticky='nsew')

    dept_tree.heading("ID", text="ID"); dept_tree.column("ID", width=60, anchor='center')
    dept_tree.heading("Name", text="Department Name"); dept_tree.column("Name", width=300, anchor='w')

    dept_vscroll = ttk.Scrollbar(dept_tree_container, orient="vertical", command=dept_tree.yview)
    dept_tree.configure(yscrollcommand=dept_vscroll.set)
    dept_vscroll.grid(row=0, column=1, sticky='ns')

    dept_tree.bind('<<TreeviewSelect>>', on_dept_select)
    fetch_departments_table(dept_tree)

    vendor_frame = ttk.LabelFrame(tab_frame, text="Manage Vendors", padding="15")
    vendor_frame.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
    vendor_frame.columnconfigure(1, weight=1)
    vendor_frame.rowconfigure(3, weight=1)

    ttk.Label(vendor_frame, text="Vendor Name:").grid(row=0, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(vendor_frame, textvariable=vendor_name_var, width=30).grid(row=0, column=1, padx=5, pady=8, sticky='ew')

    ttk.Label(vendor_frame, text="Contact:").grid(row=1, column=0, sticky='w', padx=5, pady=8)
    ttk.Entry(vendor_frame, textvariable=vendor_contact_var, width=30).grid(row=1, column=1, padx=5, pady=8, sticky='ew')

    vendor_action_frame = ttk.Frame(vendor_frame)
    vendor_action_frame.grid(row=2, column=0, columnspan=2, pady=10, sticky='ew')
    vendor_action_frame.columnconfigure(0, weight=1)
    vendor_action_frame.columnconfigure(1, weight=1)
    vendor_action_frame.columnconfigure(2, weight=1)

    vendor_add_button = ttk.Button(vendor_action_frame, text="Add New Vendor", command=add_update_vendor, style='Primary.TButton')
    vendor_add_button.grid(row=0, column=0, padx=5, sticky='ew')
    vendor_delete_button = ttk.Button(vendor_action_frame, text="Delete", command=delete_vendor, style='Danger.TButton', state='disabled')
    vendor_delete_button.grid(row=0, column=1, padx=5, sticky='ew')
    ttk.Button(vendor_action_frame, text="Clear", command=clear_vendor_form, style='Clear.TButton').grid(row=0, column=2, padx=5, sticky='ew')

    vendor_tree_container = ttk.Frame(vendor_frame)
    vendor_tree_container.grid(row=3, column=0, columnspan=2, sticky='nsew', pady=10)
    vendor_tree_container.rowconfigure(0, weight=1)
    vendor_tree_container.columnconfigure(0, weight=1)

    vendor_tree = ttk.Treeview(vendor_tree_container, columns=("ID", "Name", "Contact"), show="headings", height=8)
    vendor_tree.grid(row=0, column=0, sticky='nsew')

    vendor_tree.heading("ID", text="ID"); vendor_tree.column("ID", width=60, anchor='center')
    vendor_tree.heading("Name", text="Name"); vendor_tree.column("Name", width=220, anchor='w')
    vendor_tree.heading("Contact", text="Contact"); vendor_tree.column("Contact", width=220, anchor='w')

    vendor_vscroll = ttk.Scrollbar(vendor_tree_container, orient="vertical", command=vendor_tree.yview)
    vendor_tree.configure(yscrollcommand=vendor_vscroll.set)
    vendor_vscroll.grid(row=0, column=1, sticky='ns')

    vendor_tree.bind('<<TreeviewSelect>>', on_vendor_select)
    fetch_vendors_table(vendor_tree)

    ttk.Button(tab_frame, text="Refresh Data", command=refresh_admin_views, style='Clear.TButton').grid(row=1, column=0, columnspan=2, pady=10, sticky='ew')


# ------------------- LOGIN & START -------------------
def login():
    """Authenticates user and launches the tabbed application window."""
    global LOGGED_IN_USER
    username = username_entry.get()
    password = password_entry.get()

    if conn is None:
        messagebox.showerror("Login Failed", "Database connection failed. Cannot proceed.")
        return

    cursor = conn.cursor()
    try:
        if username == "admin" and password == "adminpass":
            LOGGED_IN_USER = "System Admin"
            save_session(LOGGED_IN_USER)
            login_window.destroy()
            main_application_window()
            return
        cursor.execute("SELECT username FROM Users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        if result:
            LOGGED_IN_USER = result[0]
            save_session(LOGGED_IN_USER)
            login_window.destroy()
            main_application_window()
        else:
            messagebox.showerror("Login Failed", "Invalid credentials. Please try again.")
    except mysql.connector.Error as e:
        if "Table 'AssetDB.Users' doesn't exist" in str(e):
            LOGGED_IN_USER = "Default Admin"
            save_session(LOGGED_IN_USER)
            login_window.destroy()
            main_application_window()
        else:
            messagebox.showerror("DB Error", f"Login database error: {e}")


# ------------------- LOGIN WINDOW -------------------
if __name__ == '__main__':
    if load_session():
        main_application_window()
        sys.exit()

    login_window = tk.Tk()
    login_window.title("Login - Assets Management System")
    login_window.geometry("420x320")
    login_window.resizable(False, False)
    apply_styles(login_window)

    login_frame = ttk.Frame(login_window, padding="24 20 24 20")
    login_frame.pack(expand=True)

    ttk.Label(login_frame, text="Assets Management Login", style='Header.TLabel').pack(pady=(6, 16))

    ttk.Label(login_frame, text="Username:").pack(pady=(6, 2))
    username_entry = ttk.Entry(login_frame, width=36)
    username_entry.pack(pady=6)
    username_entry.focus_set()

    ttk.Label(login_frame, text="Password:").pack(pady=(6, 2))
    password_entry = ttk.Entry(login_frame, show="*", width=36)
    password_entry.pack(pady=6)

    login_window.bind('<Return>', lambda event: login())

    ttk.Button(login_frame, text="Login", command=login, style='Primary.TButton').pack(pady=20, fill='x')
    ttk.Button(login_frame, text="Quit", command=login_window.destroy, style='Clear.TButton').pack(fill='x')

    login_window.mainloop()