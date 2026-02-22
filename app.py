
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from tkinter.font import Font
import sqlite3
import json
import os
from datetime import datetime, date
from PIL import Image, ImageTk
import webbrowser
import threading

# Database Setup
class Database:
    def __init__(self):
        self.conn = sqlite3.connect('seize_billing.db')
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                role TEXT DEFAULT 'user',
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Company settings
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS company (
                id INTEGER PRIMARY KEY,
                name TEXT DEFAULT 'SEIZE',
                address TEXT,
                phone TEXT,
                email TEXT,
                gstin TEXT,
                logo_path TEXT
            )
        ''')

        # Products
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                hsn_code TEXT,
                price REAL DEFAULT 0,
                gst_rate REAL DEFAULT 18,
                stock INTEGER DEFAULT 0,
                min_stock INTEGER DEFAULT 10,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Invoices
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_no TEXT UNIQUE NOT NULL,
                customer_name TEXT,
                customer_phone TEXT,
                customer_gstin TEXT,
                date DATE DEFAULT CURRENT_DATE,
                subtotal REAL DEFAULT 0,
                gst_amount REAL DEFAULT 0,
                total REAL DEFAULT 0,
                status TEXT DEFAULT 'pending',
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Invoice Items
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoice_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                quantity INTEGER DEFAULT 1,
                price REAL,
                gst_rate REAL,
                total REAL,
                FOREIGN KEY (invoice_id) REFERENCES invoices (id)
            )
        ''')

        # Expenses
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT,
                amount REAL,
                description TEXT,
                date DATE DEFAULT CURRENT_DATE,
                created_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Insert default admin user
        self.cursor.execute('''
            INSERT OR IGNORE INTO users (id, username, password, role, email)
            VALUES (1, 'admin', 'admin123', 'admin', 'admin@seize.com')
        ''')

        # Insert default company
        self.cursor.execute('''
            INSERT OR IGNORE INTO company (id, name, address, phone, email)
            VALUES (1, 'SEIZE', 'Your Business Address', 'Phone Number', 'email@seize.com')
        ''')

        self.conn.commit()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()
        return self.cursor

    def fetchall(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def fetchone(self, query, params=()):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

# Main Application
class SeizeBillingApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SEIZE - Billing & Inventory Management")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f2f5')

        # Initialize database
        self.db = Database()
        self.current_user = None
        self.current_role = None

        # Colors
        self.colors = {
            'primary': '#2c3e50',
            'secondary': '#34495e',
            'accent': '#3498db',
            'success': '#27ae60',
            'danger': '#e74c3c',
            'warning': '#f39c12',
            'light': '#ecf0f1',
            'white': '#ffffff',
            'border': '#bdc3c7'
        }

        # Fonts
        self.fonts = {
            'title': Font(family="Helvetica", size=24, weight="bold"),
            'header': Font(family="Helvetica", size=16, weight="bold"),
            'normal': Font(family="Helvetica", size=11),
            'small': Font(family="Helvetica", size=9)
        }

        self.show_login_screen()

    def show_login_screen(self):
        self.clear_window()

        # Main container with border
        container = tk.Frame(self.root, bg=self.colors['white'], 
                           highlightbackground=self.colors['accent'], 
                           highlightthickness=3)
        container.place(relx=0.5, rely=0.5, anchor='center', width=500, height=600)

        # Logo/Title Section
        title_frame = tk.Frame(container, bg=self.colors['primary'], height=150)
        title_frame.pack(fill='x', pady=0)
        title_frame.pack_propagate(False)

        tk.Label(title_frame, text="SEIZE", font=Font(family="Helvetica", size=36, weight="bold"),
                bg=self.colors['primary'], fg=self.colors['white']).pack(pady=20)
        tk.Label(title_frame, text="Billing & Inventory System", 
                font=self.fonts['header'], bg=self.colors['primary'], 
                fg=self.colors['light']).pack()

        # Login Form
        form_frame = tk.Frame(container, bg=self.colors['white'], padx=50, pady=40)
        form_frame.pack(fill='both', expand=True)

        # Username
        tk.Label(form_frame, text="Username", font=self.fonts['header'], 
                bg=self.colors['white'], fg=self.colors['primary']).pack(anchor='w', pady=(0,5))

        username_frame = tk.Frame(form_frame, bg=self.colors['white'], 
                                 highlightbackground=self.colors['border'], 
                                 highlightthickness=2)
        username_frame.pack(fill='x', pady=(0,20))

        self.username_entry = tk.Entry(username_frame, font=self.fonts['normal'], 
                                      bg=self.colors['white'], fg=self.colors['primary'],
                                      insertbackground=self.colors['primary'],
                                      relief='flat', bd=10)
        self.username_entry.pack(fill='x')
        self.username_entry.insert(0, "admin")

        # Password
        tk.Label(form_frame, text="Password", font=self.fonts['header'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(anchor='w', pady=(0,5))

        password_frame = tk.Frame(form_frame, bg=self.colors['white'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=2)
        password_frame.pack(fill='x', pady=(0,30))

        self.password_entry = tk.Entry(password_frame, font=self.fonts['normal'],
                                      bg=self.colors['white'], fg=self.colors['primary'],
                                      insertbackground=self.colors['primary'],
                                      relief='flat', bd=10, show='•')
        self.password_entry.pack(fill='x')
        self.password_entry.insert(0, "admin123")

        # Login Button
        login_btn = tk.Button(form_frame, text="LOGIN", font=Font(family="Helvetica", size=14, weight="bold"),
                             bg=self.colors['accent'], fg=self.colors['white'],
                             activebackground=self.colors['primary'],
                             activeforeground=self.colors['white'],
                             cursor='hand2', relief='flat', bd=0,
                             command=self.login)
        login_btn.pack(fill='x', ipady=12)

        # Bind Enter key
        self.password_entry.bind('<Return>', lambda e: self.login())

        # Footer
        footer_frame = tk.Frame(container, bg=self.colors['light'], height=50)
        footer_frame.pack(fill='x', side='bottom')
        footer_frame.pack_propagate(False)

        tk.Label(footer_frame, text="© 2024 SEIZE Software", 
                font=self.fonts['small'], bg=self.colors['light'],
                fg=self.colors['secondary']).pack(pady=15)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password")
            return

        user = self.db.fetchone("SELECT * FROM users WHERE username=? AND password=?", 
                               (username, password))

        if user:
            self.current_user = username
            self.current_role = user[3]
            self.show_dashboard()
        else:
            messagebox.showerror("Error", "Invalid username or password")

    def show_dashboard(self):
        self.clear_window()

        # Main layout
        self.root.configure(bg=self.colors['light'])

        # Sidebar
        self.sidebar = tk.Frame(self.root, bg=self.colors['primary'], width=250)
        self.sidebar.pack(side='left', fill='y')
        self.sidebar.pack_propagate(False)

        # Logo in sidebar
        logo_frame = tk.Frame(self.sidebar, bg=self.colors['secondary'], height=100)
        logo_frame.pack(fill='x', pady=0)
        logo_frame.pack_propagate(False)

        tk.Label(logo_frame, text="SEIZE", font=Font(family="Helvetica", size=28, weight="bold"),
                bg=self.colors['secondary'], fg=self.colors['white']).pack(pady=20)

        # Menu Items
        menu_items = [
            ("Dashboard", self.show_dashboard_content),
            ("New Invoice", self.show_invoice_screen),
            ("Invoices", self.show_invoices_list),
            ("Products", self.show_products),
            ("Stock", self.show_stock),
            ("Expenses", self.show_expenses),
            ("Reports", self.show_reports),
            ("Settings", self.show_settings)
        ]

        if self.current_role == 'admin':
            menu_items.insert(-1, ("Users", self.show_users))

        for text, command in menu_items:
            btn = tk.Button(self.sidebar, text=text, font=self.fonts['normal'],
                          bg=self.colors['primary'], fg=self.colors['white'],
                          activebackground=self.colors['accent'],
                          activeforeground=self.colors['white'],
                          relief='flat', bd=0, cursor='hand2',
                          command=command)
            btn.pack(fill='x', pady=2, ipady=10)

        # Logout button at bottom
        logout_btn = tk.Button(self.sidebar, text="Logout", font=self.fonts['normal'],
                              bg=self.colors['danger'], fg=self.colors['white'],
                              activebackground='#c0392b',
                              relief='flat', bd=0, cursor='hand2',
                              command=self.logout)
        logout_btn.pack(fill='x', side='bottom', pady=10, ipady=10)

        # User info
        user_frame = tk.Frame(self.sidebar, bg=self.colors['secondary'], height=60)
        user_frame.pack(fill='x', side='bottom')
        user_frame.pack_propagate(False)

        tk.Label(user_frame, text=f"Logged in as: {self.current_user}",
                font=self.fonts['small'], bg=self.colors['secondary'],
                fg=self.colors['light']).pack(pady=20)

        # Main content area
        self.main_content = tk.Frame(self.root, bg=self.colors['light'])
        self.main_content.pack(side='right', fill='both', expand=True, padx=20, pady=20)

        self.show_dashboard_content()

    def show_dashboard_content(self):
        self.clear_main_content()

        # Header
        header = tk.Frame(self.main_content, bg=self.colors['white'], 
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Dashboard", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        # Date
        tk.Label(header, text=datetime.now().strftime("%d %B, %Y"),
                font=self.fonts['normal'], bg=self.colors['white'],
                fg=self.colors['secondary']).pack(side='right', padx=30, pady=20)

        # Stats Cards
        stats_frame = tk.Frame(self.main_content, bg=self.colors['light'])
        stats_frame.pack(fill='x', pady=10)

        # Get stats from database
        today_sales = self.db.fetchone("""
            SELECT COALESCE(SUM(total), 0) FROM invoices 
            WHERE date = ? AND status != 'cancelled'
        """, (date.today(),))[0]

        total_invoices = self.db.fetchone("""
            SELECT COUNT(*) FROM invoices WHERE status != 'cancelled'
        """)[0]

        low_stock = self.db.fetchone("""
            SELECT COUNT(*) FROM products WHERE stock <= min_stock
        """)[0]

        today_expenses = self.db.fetchone("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses WHERE date = ?
        """, (date.today(),))[0]

        stats = [
            ("Today's Sales", f"₹{today_sales:,.2f}", self.colors['success']),
            ("Total Invoices", total_invoices, self.colors['accent']),
            ("Low Stock Items", low_stock, self.colors['warning'] if low_stock > 0 else self.colors['success']),
            ("Today's Expenses", f"₹{today_expenses:,.2f}", self.colors['danger'])
        ]

        for title, value, color in stats:
            card = tk.Frame(stats_frame, bg=self.colors['white'],
                          highlightbackground=color,
                          highlightthickness=2, width=300, height=150)
            card.pack(side='left', padx=10, pady=10)
            card.pack_propagate(False)

            tk.Label(card, text=title, font=self.fonts['normal'],
                    bg=self.colors['white'], fg=self.colors['secondary']).pack(pady=(20,5))
            tk.Label(card, text=str(value), font=Font(family="Helvetica", size=24, weight="bold"),
                    bg=self.colors['white'], fg=color).pack()

        # Recent Activity
        activity_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                                 highlightbackground=self.colors['border'],
                                 highlightthickness=1)
        activity_frame.pack(fill='both', expand=True, pady=20)

        tk.Label(activity_frame, text="Recent Invoices", font=self.fonts['header'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(anchor='w', padx=20, pady=15)

        # Treeview for recent invoices
        columns = ('Invoice No', 'Customer', 'Date', 'Amount', 'Status')
        tree = ttk.Treeview(activity_frame, columns=columns, show='headings', height=10)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(activity_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=20, pady=(0,20))

        # Load recent invoices
        invoices = self.db.fetchall("""
            SELECT invoice_no, customer_name, date, total, status 
            FROM invoices ORDER BY created_at DESC LIMIT 10
        """)

        for inv in invoices:
            status_color = self.colors['success'] if inv[4] == 'paid' else self.colors['warning']
            tree.insert('', 'end', values=inv, tags=(inv[4],))

        tree.tag_configure('paid', foreground=self.colors['success'])
        tree.tag_configure('pending', foreground=self.colors['warning'])

    def show_invoice_screen(self, edit_invoice_id=None):
        self.clear_main_content()

        # Header
        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        title_text = "Edit Invoice" if edit_invoice_id else "New Invoice"
        tk.Label(header, text=title_text, font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        # Invoice Form Container
        form_container = tk.Frame(self.main_content, bg=self.colors['light'])
        form_container.pack(fill='both', expand=True)

        # Left side - Invoice Details
        left_frame = tk.Frame(form_container, bg=self.colors['white'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=1)
        left_frame.pack(side='left', fill='both', expand=True, padx=(0,10))

        # Customer Details Section
        cust_frame = tk.LabelFrame(left_frame, text="Customer Details", 
                                  font=self.fonts['header'],
                                  bg=self.colors['white'], fg=self.colors['primary'],
                                  padx=20, pady=15)
        cust_frame.pack(fill='x', padx=20, pady=20)

        # Invoice Number
        tk.Label(cust_frame, text="Invoice No:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=0, column=0, sticky='w', pady=5)
        self.inv_no_var = tk.StringVar()
        if not edit_invoice_id:
            last_inv = self.db.fetchone("SELECT MAX(CAST(SUBSTR(invoice_no, 4) AS INTEGER)) FROM invoices")
            next_no = (last_inv[0] or 0) + 1
            self.inv_no_var.set(f"SEZ{next_no:04d}")
        inv_no_entry = tk.Entry(cust_frame, font=self.fonts['normal'],
                               textvariable=self.inv_no_var, state='readonly',
                               bg=self.colors['light'])
        inv_no_entry.grid(row=0, column=1, sticky='ew', padx=10)

        # Date
        tk.Label(cust_frame, text="Date:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=0, column=2, sticky='w', padx=(20,0))
        self.inv_date_var = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        date_entry = tk.Entry(cust_frame, font=self.fonts['normal'],
                             textvariable=self.inv_date_var)
        date_entry.grid(row=0, column=3, sticky='ew', padx=10)

        # Customer Name
        tk.Label(cust_frame, text="Customer Name:*", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=1, column=0, sticky='w', pady=5)
        self.cust_name_var = tk.StringVar()
        tk.Entry(cust_frame, font=self.fonts['normal'],
                textvariable=self.cust_name_var).grid(row=1, column=1, sticky='ew', padx=10)

        # Customer Phone
        tk.Label(cust_frame, text="Phone:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=1, column=2, sticky='w', padx=(20,0))
        self.cust_phone_var = tk.StringVar()
        tk.Entry(cust_frame, font=self.fonts['normal'],
                textvariable=self.cust_phone_var).grid(row=1, column=3, sticky='ew', padx=10)

        # Customer GSTIN
        tk.Label(cust_frame, text="GSTIN:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=2, column=0, sticky='w', pady=5)
        self.cust_gstin_var = tk.StringVar()
        tk.Entry(cust_frame, font=self.fonts['normal'],
                textvariable=self.cust_gstin_var).grid(row=2, column=1, sticky='ew', padx=10)

        cust_frame.columnconfigure(1, weight=1)
        cust_frame.columnconfigure(3, weight=1)

        # Items Section - AUTO EXPANDING
        items_frame = tk.LabelFrame(left_frame, text="Invoice Items",
                                   font=self.fonts['header'],
                                   bg=self.colors['white'], fg=self.colors['primary'],
                                   padx=20, pady=15)
        items_frame.pack(fill='both', expand=True, padx=20, pady=10)

        # Items Treeview with auto-expand
        columns = ('Item', 'HSN', 'Qty', 'Rate', 'GST%', 'Amount')
        self.items_tree = ttk.Treeview(items_frame, columns=columns, show='headings', height=8)

        for col in columns:
            self.items_tree.heading(col, text=col)
            self.items_tree.column(col, width=100)

        self.items_tree.column('Item', width=250)

        scrollbar = ttk.Scrollbar(items_frame, orient='vertical', command=self.items_tree.yview)
        self.items_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        self.items_tree.pack(fill='both', expand=True)

        # Add Item Button
        btn_frame = tk.Frame(items_frame, bg=self.colors['white'])
        btn_frame.pack(fill='x', pady=10)

        tk.Button(btn_frame, text="+ Add Item", font=self.fonts['normal'],
                 bg=self.colors['accent'], fg=self.colors['white'],
                 relief='flat', cursor='hand2',
                 command=self.add_item_dialog).pack(side='left', padx=5)

        tk.Button(btn_frame, text="- Remove Item", font=self.fonts['normal'],
                 bg=self.colors['danger'], fg=self.colors['white'],
                 relief='flat', cursor='hand2',
                 command=self.remove_item).pack(side='left', padx=5)

        # Totals Section
        totals_frame = tk.Frame(left_frame, bg=self.colors['white'],
                               highlightbackground=self.colors['border'],
                               highlightthickness=1, padx=20, pady=15)
        totals_frame.pack(fill='x', padx=20, pady=20)

        self.subtotal_var = tk.StringVar(value="0.00")
        self.gst_var = tk.StringVar(value="0.00")
        self.total_var = tk.StringVar(value="0.00")

        tk.Label(totals_frame, text="Subtotal:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=0, column=0, sticky='e', padx=10)
        tk.Label(totals_frame, textvariable=self.subtotal_var,
                font=self.fonts['header'], bg=self.colors['white'],
                fg=self.colors['primary']).grid(row=0, column=1, sticky='w')

        tk.Label(totals_frame, text="GST Amount:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=1, column=0, sticky='e', padx=10)
        tk.Label(totals_frame, textvariable=self.gst_var,
                font=self.fonts['header'], bg=self.colors['white'],
                fg=self.colors['primary']).grid(row=1, column=1, sticky='w')

        tk.Label(totals_frame, text="Total:", font=Font(family="Helvetica", size=14, weight="bold"),
                bg=self.colors['white']).grid(row=2, column=0, sticky='e', padx=10, pady=10)
        tk.Label(totals_frame, textvariable=self.total_var,
                font=Font(family="Helvetica", size=18, weight="bold"),
                bg=self.colors['white'], fg=self.colors['success']).grid(row=2, column=1, sticky='w')

        # Action Buttons
        action_frame = tk.Frame(left_frame, bg=self.colors['white'])
        action_frame.pack(fill='x', padx=20, pady=20)

        tk.Button(action_frame, text="Save Invoice", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=self.save_invoice).pack(side='left', padx=5)

        tk.Button(action_frame, text="Print", font=self.fonts['normal'],
                 bg=self.colors['primary'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=self.print_invoice).pack(side='left', padx=5)

        tk.Button(action_frame, text="Cancel", font=self.fonts['normal'],
                 bg=self.colors['danger'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=self.show_dashboard_content).pack(side='left', padx=5)

        # Right side - Quick Products
        right_frame = tk.Frame(form_container, bg=self.colors['white'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1, width=300)
        right_frame.pack(side='right', fill='y')
        right_frame.pack_propagate(False)

        tk.Label(right_frame, text="Quick Add Products",
                font=self.fonts['header'], bg=self.colors['white'],
                fg=self.colors['primary']).pack(pady=20)

        # Product list
        products = self.db.fetchall("SELECT name, price, gst_rate FROM products LIMIT 20")

        prod_canvas = tk.Canvas(right_frame, bg=self.colors['white'], highlightthickness=0)
        prod_scrollbar = ttk.Scrollbar(right_frame, orient='vertical', command=prod_canvas.yview)
        prod_frame = tk.Frame(prod_canvas, bg=self.colors['white'])

        prod_canvas.configure(yscrollcommand=prod_scrollbar.set)
        prod_scrollbar.pack(side='right', fill='y')
        prod_canvas.pack(side='left', fill='both', expand=True, padx=10)
        prod_canvas.create_window((0,0), window=prod_frame, anchor='nw', width=260)

        for prod in products:
            prod_btn = tk.Button(prod_frame, 
                               text=f"{prod[0]}\n₹{prod[1]} ({prod[2]}% GST)",
                               font=self.fonts['small'],
                               bg=self.colors['light'], fg=self.colors['primary'],
                               relief='flat', cursor='hand2',
                               command=lambda p=prod: self.quick_add_product(p))
            prod_btn.pack(fill='x', pady=2, ipady=5)

        prod_frame.update_idletasks()
        prod_canvas.configure(scrollregion=prod_canvas.bbox('all'))

        # If editing, load invoice data
        if edit_invoice_id:
            self.load_invoice_for_edit(edit_invoice_id)

    def add_item_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Item")
        dialog.geometry("500x400")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Product selection
        tk.Label(dialog, text="Select Product:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(20,5))

        products = self.db.fetchall("SELECT id, name, price, gst_rate FROM products")
        prod_names = [f"{p[1]} - ₹{p[2]}" for p in products]
        prod_dict = {f"{p[1]} - ₹{p[2]}": p for p in products}

        prod_var = tk.StringVar()
        prod_combo = ttk.Combobox(dialog, textvariable=prod_var, values=prod_names,
                                 font=self.fonts['normal'], state='readonly')
        prod_combo.pack(fill='x', padx=20, pady=5)

        # Quantity
        tk.Label(dialog, text="Quantity:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(10,5))
        qty_var = tk.IntVar(value=1)
        tk.Spinbox(dialog, from_=1, to=1000, textvariable=qty_var,
                  font=self.fonts['normal']).pack(fill='x', padx=20, pady=5)

        def add_item():
            if not prod_var.get():
                messagebox.showerror("Error", "Please select a product")
                return

            prod = prod_dict[prod_var.get()]
            qty = qty_var.get()
            price = prod[2]
            gst_rate = prod[3]
            amount = qty * price
            gst_amount = amount * (gst_rate / 100)
            total = amount + gst_amount

            self.items_tree.insert('', 'end', values=(
                prod[1], '', qty, price, gst_rate, total
            ))

            self.calculate_totals()
            dialog.destroy()

        tk.Button(dialog, text="Add", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=add_item).pack(pady=30)

    def quick_add_product(self, product):
        self.items_tree.insert('', 'end', values=(
            product[0], '', 1, product[1], product[2], 
            product[1] * (1 + product[2]/100)
        ))
        self.calculate_totals()

    def remove_item(self):
        selected = self.items_tree.selection()
        if selected:
            self.items_tree.delete(selected[0])
            self.calculate_totals()

    def calculate_totals(self):
        subtotal = 0
        gst_total = 0

        for item in self.items_tree.get_children():
            values = self.items_tree.item(item, 'values')
            if values:
                qty = float(values[2])
                rate = float(values[3])
                gst_rate = float(values[4])

                amount = qty * rate
                gst_amount = amount * (gst_rate / 100)

                subtotal += amount
                gst_total += gst_amount

        total = subtotal + gst_total

        self.subtotal_var.set(f"₹{subtotal:,.2f}")
        self.gst_var.set(f"₹{gst_total:,.2f}")
        self.total_var.set(f"₹{total:,.2f}")

    def save_invoice(self):
        if not self.cust_name_var.get().strip():
            messagebox.showerror("Error", "Customer name is required")
            return

        if not self.items_tree.get_children():
            messagebox.showerror("Error", "Please add at least one item")
            return

        try:
            # Save invoice
            self.db.execute("""
                INSERT INTO invoices (invoice_no, customer_name, customer_phone, 
                                    customer_gstin, date, subtotal, gst_amount, total, 
                                    status, created_by)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?)
            """, (
                self.inv_no_var.get(),
                self.cust_name_var.get(),
                self.cust_phone_var.get(),
                self.cust_gstin_var.get(),
                self.inv_date_var.get(),
                float(self.subtotal_var.get().replace('₹', '').replace(',', '')),
                float(self.gst_var.get().replace('₹', '').replace(',', '')),
                float(self.total_var.get().replace('₹', '').replace(',', '')),
                self.current_user
            ))

            invoice_id = self.db.cursor.lastrowid

            # Save items
            for item in self.items_tree.get_children():
                values = self.items_tree.item(item, 'values')
                self.db.execute("""
                    INSERT INTO invoice_items (invoice_id, product_name, quantity, 
                                             price, gst_rate, total)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (invoice_id, values[0], values[2], values[3], values[4], values[5]))

                # Update stock
                self.db.execute("""
                    UPDATE products SET stock = stock - ? WHERE name = ?
                """, (values[2], values[0]))

            messagebox.showinfo("Success", f"Invoice {self.inv_no_var.get()} saved successfully!")
            self.show_invoices_list()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to save invoice: {str(e)}")

    def show_invoices_list(self):
        self.clear_main_content()

        # Header
        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Invoices", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        tk.Button(header, text="+ New Invoice", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2',
                 command=self.show_invoice_screen).pack(side='right', padx=30, pady=20)

        # Filter Frame
        filter_frame = tk.Frame(self.main_content, bg=self.colors['light'])
        filter_frame.pack(fill='x', pady=10)

        tk.Label(filter_frame, text="Search:", font=self.fonts['normal'],
                bg=self.colors['light']).pack(side='left', padx=5)

        search_var = tk.StringVar()
        tk.Entry(filter_frame, textvariable=search_var,
                font=self.fonts['normal'], width=30).pack(side='left', padx=5)

        tk.Label(filter_frame, text="From:", font=self.fonts['normal'],
                bg=self.colors['light']).pack(side='left', padx=(20,5))

        from_date = tk.StringVar(value=date.today().strftime("%Y-%m-01"))
        tk.Entry(filter_frame, textvariable=from_date,
                font=self.fonts['normal'], width=12).pack(side='left')

        tk.Label(filter_frame, text="To:", font=self.fonts['normal'],
                bg=self.colors['light']).pack(side='left', padx=(10,5))

        to_date = tk.StringVar(value=date.today().strftime("%Y-%m-%d"))
        tk.Entry(filter_frame, textvariable=to_date,
                font=self.fonts['normal'], width=12).pack(side='left')

        tk.Button(filter_frame, text="Filter", font=self.fonts['normal'],
                 bg=self.colors['accent'], fg=self.colors['white'],
                 relief='flat', cursor='hand2',
                 command=lambda: self.load_invoices(tree, from_date.get(), to_date.get(), search_var.get())).pack(side='left', padx=20)

        # Invoices Table
        table_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        table_frame.pack(fill='both', expand=True, pady=10)

        columns = ('Invoice No', 'Customer', 'Date', 'Amount', 'Status', 'Actions')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.column('Invoice No', width=120)
        tree.column('Customer', width=200)
        tree.column('Actions', width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=20, pady=20)

        # Action buttons frame
        def on_select(event):
            item = tree.selection()[0]
            values = tree.item(item, 'values')
            if values:
                self.show_invoice_actions(values[0])

        tree.bind('<Double-1>', on_select)

        self.load_invoices(tree, from_date.get(), to_date.get())

    def load_invoices(self, tree, from_date, to_date, search=''):
        # Clear existing
        for item in tree.get_children():
            tree.delete(item)

        query = """
            SELECT invoice_no, customer_name, date, total, status 
            FROM invoices 
            WHERE date BETWEEN ? AND ?
        """
        params = [from_date, to_date]

        if search:
            query += " AND (invoice_no LIKE ? OR customer_name LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%'])

        query += " ORDER BY date DESC"

        invoices = self.db.fetchall(query, params)

        for inv in invoices:
            status_tag = 'paid' if inv[4] == 'paid' else 'pending'
            tree.insert('', 'end', values=inv, tags=(status_tag,))

        tree.tag_configure('paid', foreground=self.colors['success'])
        tree.tag_configure('pending', foreground=self.colors['warning'])

    def show_reports(self):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Reports", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        # Report buttons
        reports_frame = tk.Frame(self.main_content, bg=self.colors['light'])
        reports_frame.pack(fill='both', expand=True)

        reports = [
            ("Sales Report", self.show_sales_report),
            ("Purchase Report", self.show_purchase_report),
            ("Stock Report", self.show_stock_report),
            ("Profit & Loss", self.show_profit_loss),
            ("GST Report", self.show_gst_report),
            ("Expense Report", self.show_expense_report)
        ]

        for name, command in reports:
            btn = tk.Button(reports_frame, text=name, font=self.fonts['header'],
                          bg=self.colors['white'], fg=self.colors['primary'],
                          activebackground=self.colors['accent'],
                          activeforeground=self.colors['white'],
                          relief='flat', bd=2, cursor='hand2',
                          command=command, width=30, height=5)
            btn.pack(pady=10)

    def show_sales_report(self):
        self.generate_report("Sales Report", """
            SELECT date, COUNT(*) as invoices, SUM(total) as total
            FROM invoices WHERE status != 'cancelled'
            GROUP BY date ORDER BY date DESC
        """)

    def show_profit_loss(self):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Profit & Loss Statement", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        # Get data
        total_sales = self.db.fetchone("""
            SELECT COALESCE(SUM(total), 0) FROM invoices WHERE status != 'cancelled'
        """)[0]

        total_expenses = self.db.fetchone("""
            SELECT COALESCE(SUM(amount), 0) FROM expenses
        """)[0]

        profit = total_sales - total_expenses

        # Display
        content = tk.Frame(self.main_content, bg=self.colors['white'],
                          highlightbackground=self.colors['border'],
                          highlightthickness=1, padx=50, pady=50)
        content.pack(fill='both', expand=True, pady=20)

        tk.Label(content, text="Total Sales:", font=self.fonts['header'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(anchor='w')
        tk.Label(content, text=f"₹{total_sales:,.2f}", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['success']).pack(anchor='w', pady=(0,20))

        tk.Label(content, text="Total Expenses:", font=self.fonts['header'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(anchor='w')
        tk.Label(content, text=f"₹{total_expenses:,.2f}", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['danger']).pack(anchor='w', pady=(0,20))

        tk.Label(content, text="Net Profit:", font=self.fonts['header'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(anchor='w')

        color = self.colors['success'] if profit >= 0 else self.colors['danger']
        tk.Label(content, text=f"₹{profit:,.2f}", font=Font(family="Helvetica", size=32, weight="bold"),
                bg=self.colors['white'], fg=color).pack(anchor='w')

    def generate_report(self, title, query):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text=title, font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        tk.Button(header, text="Export to Excel", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2').pack(side='right', padx=30, pady=20)

        # Report table
        table_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        table_frame.pack(fill='both', expand=True, pady=10)

        # Get columns from query
        self.db.cursor.execute(query)
        columns = [description[0] for description in self.db.cursor.description]

        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        for col in columns:
            tree.heading(col, text=col.replace('_', ' ').title())
            tree.column(col, width=150)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=20, pady=20)

        # Load data
        data = self.db.fetchall(query)
        for row in data:
            tree.insert('', 'end', values=row)

    def show_users(self):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="User Management", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        tk.Button(header, text="+ Add User", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2',
                 command=self.add_user_dialog).pack(side='right', padx=30, pady=20)

        # Users table
        table_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        table_frame.pack(fill='both', expand=True, pady=10)

        columns = ('Username', 'Role', 'Email', 'Created At')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=200)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=20, pady=20)

        # Load users
        users = self.db.fetchall("SELECT username, role, email, created_at FROM users")
        for user in users:
            tree.insert('', 'end', values=user)

    def add_user_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add User")
        dialog.geometry("400x400")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Username:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(20,5))
        username_var = tk.StringVar()
        tk.Entry(dialog, textvariable=username_var, font=self.fonts['normal']).pack(fill='x', padx=20)

        tk.Label(dialog, text="Password:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(15,5))
        password_var = tk.StringVar()
        tk.Entry(dialog, textvariable=password_var, show='•', font=self.fonts['normal']).pack(fill='x', padx=20)

        tk.Label(dialog, text="Role:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(15,5))
        role_var = tk.StringVar(value='user')
        ttk.Combobox(dialog, textvariable=role_var, values=['admin', 'user', 'salesman'],
                    font=self.fonts['normal'], state='readonly').pack(fill='x', padx=20)

        tk.Label(dialog, text="Email:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(15,5))
        email_var = tk.StringVar()
        tk.Entry(dialog, textvariable=email_var, font=self.fonts['normal']).pack(fill='x', padx=20)

        def save():
            try:
                self.db.execute("""
                    INSERT INTO users (username, password, role, email)
                    VALUES (?, ?, ?, ?)
                """, (username_var.get(), password_var.get(), role_var.get(), email_var.get()))
                messagebox.showinfo("Success", "User added!")
                dialog.destroy()
                self.show_users()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(dialog, text="Save", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=save).pack(pady=30)

    def show_settings(self):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Settings", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        # Settings form
        form_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                             highlightbackground=self.colors['border'],
                             highlightthickness=1, padx=50, pady=30)
        form_frame.pack(fill='both', expand=True, pady=20)

        # Company settings
        company = self.db.fetchone("SELECT * FROM company LIMIT 1")

        tk.Label(form_frame, text="Company Name:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=0, column=0, sticky='w', pady=10)
        name_var = tk.StringVar(value=company[1] if company else 'SEIZE')
        tk.Entry(form_frame, textvariable=name_var, font=self.fonts['normal'], width=40).grid(row=0, column=1, padx=10)

        tk.Label(form_frame, text="Address:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=1, column=0, sticky='w', pady=10)
        address_var = tk.StringVar(value=company[2] if company else '')
        tk.Entry(form_frame, textvariable=address_var, font=self.fonts['normal'], width=40).grid(row=1, column=1, padx=10)

        tk.Label(form_frame, text="Phone:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=2, column=0, sticky='w', pady=10)
        phone_var = tk.StringVar(value=company[3] if company else '')
        tk.Entry(form_frame, textvariable=phone_var, font=self.fonts['normal'], width=40).grid(row=2, column=1, padx=10)

        tk.Label(form_frame, text="Email:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=3, column=0, sticky='w', pady=10)
        email_var = tk.StringVar(value=company[4] if company else '')
        tk.Entry(form_frame, textvariable=email_var, font=self.fonts['normal'], width=40).grid(row=3, column=1, padx=10)

        tk.Label(form_frame, text="GSTIN:", font=self.fonts['normal'],
                bg=self.colors['white']).grid(row=4, column=0, sticky='w', pady=10)
        gstin_var = tk.StringVar(value=company[5] if company else '')
        tk.Entry(form_frame, textvariable=gstin_var, font=self.fonts['normal'], width=40).grid(row=4, column=1, padx=10)

        def save_settings():
            self.db.execute("""
                UPDATE company SET name=?, address=?, phone=?, email=?, gstin=?
                WHERE id=1
            """, (name_var.get(), address_var.get(), phone_var.get(), 
                 email_var.get(), gstin_var.get()))
            messagebox.showinfo("Success", "Settings saved!")

        tk.Button(form_frame, text="Save Settings", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=save_settings).grid(row=5, column=1, pady=30, sticky='e')

    def logout(self):
        self.current_user = None
        self.current_role = None
        self.show_login_screen()

    def clear_window(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    def clear_main_content(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

# Run Application
if __name__ == "__main__":
    root = tk.Tk()
    app = SeizeBillingApp(root)
    root.mainloop()

    def show_invoice_actions(self, invoice_no):
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Invoice {invoice_no}")
        dialog.geometry("300x250")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text=f"Invoice: {invoice_no}",
                font=self.fonts['header'], bg=self.colors['white'],
                fg=self.colors['primary']).pack(pady=20)

        tk.Button(dialog, text="View/Edit", font=self.fonts['normal'],
                 bg=self.colors['accent'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', width=20, pady=10,
                 command=lambda: [dialog.destroy(), self.edit_invoice(invoice_no)]).pack(pady=5)

        tk.Button(dialog, text="Print", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', width=20, pady=10,
                 command=lambda: [dialog.destroy(), self.print_invoice(invoice_no)]).pack(pady=5)

        if self.current_role == 'admin':
            tk.Button(dialog, text="Delete", font=self.fonts['normal'],
                     bg=self.colors['danger'], fg=self.colors['white'],
                     relief='flat', cursor='hand2', width=20, pady=10,
                     command=lambda: [dialog.destroy(), self.delete_invoice(invoice_no)]).pack(pady=5)

    def edit_invoice(self, invoice_no):
        inv = self.db.fetchone("SELECT id FROM invoices WHERE invoice_no=?", (invoice_no,))
        if inv:
            self.show_invoice_screen(edit_invoice_id=inv[0])

    def load_invoice_for_edit(self, invoice_id):
        inv = self.db.fetchone("""
            SELECT invoice_no, customer_name, customer_phone, customer_gstin, date
            FROM invoices WHERE id=?
        """, (invoice_id,))

        if inv:
            self.inv_no_var.set(inv[0])
            self.cust_name_var.set(inv[1])
            self.cust_phone_var.set(inv[2])
            self.cust_gstin_var.set(inv[3])
            self.inv_date_var.set(inv[4])

            # Load items
            items = self.db.fetchall("""
                SELECT product_name, quantity, price, gst_rate, total
                FROM invoice_items WHERE invoice_id=?
            """, (invoice_id,))

            for item in items:
                self.items_tree.insert('', 'end', values=item)

            self.calculate_totals()

    def delete_invoice(self, invoice_no):
        if messagebox.askyesno("Confirm", f"Delete invoice {invoice_no}?"):
            self.db.execute("DELETE FROM invoices WHERE invoice_no=?", (invoice_no,))
            messagebox.showinfo("Success", "Invoice deleted")
            self.show_invoices_list()

    def print_invoice(self, invoice_no=None):
        if not invoice_no:
            invoice_no = self.inv_no_var.get()

        messagebox.showinfo("Print", f"Printing invoice {invoice_no}...\n(Print functionality would generate PDF)")

    def show_products(self):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Products", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        if self.current_role == 'admin':
            tk.Button(header, text="+ Add Product", font=self.fonts['normal'],
                     bg=self.colors['success'], fg=self.colors['white'],
                     relief='flat', cursor='hand2',
                     command=self.add_product_dialog).pack(side='right', padx=30, pady=20)

        # Products table
        table_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        table_frame.pack(fill='both', expand=True, pady=10)

        columns = ('Name', 'HSN', 'Price', 'GST%', 'Stock', 'Min Stock')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        tree.column('Name', width=250)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=20, pady=20)

        # Load products
        products = self.db.fetchall("SELECT name, hsn_code, price, gst_rate, stock, min_stock FROM products")

        for prod in products:
            tag = 'low' if prod[4] <= prod[5] else 'normal'
            tree.insert('', 'end', values=prod, tags=(tag,))

        tree.tag_configure('low', foreground=self.colors['danger'])
        tree.tag_configure('normal', foreground=self.colors['success'])

    def add_product_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Product")
        dialog.geometry("400x500")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()

        fields = [
            ('Product Name:', 'name'),
            ('HSN Code:', 'hsn'),
            ('Price:', 'price'),
            ('GST Rate (%):', 'gst'),
            ('Opening Stock:', 'stock'),
            ('Min Stock Level:', 'min_stock')
        ]

        entries = {}
        for label, key in fields:
            tk.Label(dialog, text=label, font=self.fonts['normal'],
                    bg=self.colors['white']).pack(pady=(15,5))
            entry = tk.Entry(dialog, font=self.fonts['normal'])
            entry.pack(fill='x', padx=20)
            entries[key] = entry

        def save():
            try:
                self.db.execute("""
                    INSERT INTO products (name, hsn_code, price, gst_rate, stock, min_stock)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entries['name'].get(),
                    entries['hsn'].get(),
                    float(entries['price'].get() or 0),
                    float(entries['gst'].get() or 18),
                    int(entries['stock'].get() or 0),
                    int(entries['min_stock'].get() or 10)
                ))
                messagebox.showinfo("Success", "Product added!")
                dialog.destroy()
                self.show_products()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(dialog, text="Save", font=self.fonts['normal'],
                 bg=self.colors['success'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=save).pack(pady=30)

    def show_stock(self):
        self.show_products()  # Same as products for now

    def show_expenses(self):
        self.clear_main_content()

        header = tk.Frame(self.main_content, bg=self.colors['white'],
                         highlightbackground=self.colors['border'],
                         highlightthickness=1, height=80)
        header.pack(fill='x', pady=(0,20))
        header.pack_propagate(False)

        tk.Label(header, text="Expenses", font=self.fonts['title'],
                bg=self.colors['white'], fg=self.colors['primary']).pack(side='left', padx=30, pady=20)

        tk.Button(header, text="+ Add Expense", font=self.fonts['normal'],
                 bg=self.colors['danger'], fg=self.colors['white'],
                 relief='flat', cursor='hand2',
                 command=self.add_expense_dialog).pack(side='right', padx=30, pady=20)

        # Expenses table
        table_frame = tk.Frame(self.main_content, bg=self.colors['white'],
                              highlightbackground=self.colors['border'],
                              highlightthickness=1)
        table_frame.pack(fill='both', expand=True, pady=10)

        columns = ('Date', 'Category', 'Amount', 'Description', 'Added By')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', height=20)

        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)

        tree.column('Description', width=300)

        scrollbar = ttk.Scrollbar(table_frame, orient='vertical', command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side='right', fill='y')
        tree.pack(fill='both', expand=True, padx=20, pady=20)

        # Load expenses
        expenses = self.db.fetchall("""
            SELECT date, category, amount, description, created_by 
            FROM expenses ORDER BY date DESC
        """)

        for exp in expenses:
            tree.insert('', 'end', values=exp)

    def add_expense_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Add Expense")
        dialog.geometry("400x400")
        dialog.configure(bg=self.colors['white'])
        dialog.transient(self.root)
        dialog.grab_set()

        tk.Label(dialog, text="Category:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(20,5))

        categories = ['Rent', 'Salary', 'Electricity', 'Transport', 'Marketing', 'Other']
        cat_var = tk.StringVar()
        ttk.Combobox(dialog, textvariable=cat_var, values=categories,
                    font=self.fonts['normal'], state='readonly').pack(fill='x', padx=20)

        tk.Label(dialog, text="Amount:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(15,5))
        amount_var = tk.StringVar()
        tk.Entry(dialog, textvariable=amount_var, font=self.fonts['normal']).pack(fill='x', padx=20)

        tk.Label(dialog, text="Description:", font=self.fonts['normal'],
                bg=self.colors['white']).pack(pady=(15,5))
        desc_text = tk.Text(dialog, font=self.fonts['normal'], height=5)
        desc_text.pack(fill='x', padx=20)

        def save():
            try:
                self.db.execute("""
                    INSERT INTO expenses (category, amount, description, created_by)
                    VALUES (?, ?, ?, ?)
                """, (cat_var.get(), float(amount_var.get()), 
                     desc_text.get('1.0', 'end'), self.current_user))
                messagebox.showinfo("Success", "Expense added!")
                dialog.destroy()
                self.show_expenses()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        tk.Button(dialog, text="Save", font=self.fonts['normal'],
                 bg=self.colors['danger'], fg=self.colors['white'],
                 relief='flat', cursor='hand2', padx=30, pady=10,
                 command=save).pack(pady=30)