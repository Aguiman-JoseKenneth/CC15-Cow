import sys
import mysql.connector
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTabWidget, QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QFormLayout, QLineEdit, QComboBox, QHeaderView, QGroupBox, QAbstractItemView,
    QMessageBox, QStackedWidget, QFrame
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QColor


def connect_to_database():
    try:
        return mysql.connector.connect(
            host="localhost",
            user="root",
            password="1234",
            database="inventorydb"
        )
    except mysql.connector.Error as err:
        print(f"Database Connection Error: {err}")
        return None


class FarmManagementSystem(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Agro-Industrial Livestock Enterprise OS")
        self.setGeometry(50, 50, 1350, 850)

        self.current_user = "None"
        self.current_role = "None"

        self.cattle_ledger = []
        self.product_inventory = []
        self.sales = []

        self.audit_logs = [
            "SYSTEM: Core security subsystem initialized.",
            "DATABASE: Inventory registers verified against production metrics."
        ]

        self.main_stack = QStackedWidget()
        self.setCentralWidget(self.main_stack)

        self.main_dashboard()
        self.login_screen()

        self.main_stack.setCurrentIndex(1)

    def login_screen(self):
        page = QWidget()
        page.setObjectName("LoginPage")
        layout = QVBoxLayout(page)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        box = QGroupBox("AGRO-SYSTEM FIREWALL: IDENTITY AUTHENTICATION")
        box.setFixedSize(450, 320)
        box_layout = QFormLayout(box)
        box_layout.setContentsMargins(30, 40, 30, 30)
        box_layout.setVerticalSpacing(15)

        self.login_user = QComboBox()
        self.login_user.addItems([
            "Farmer John (Staff)",
            "Supervisor Sarah (Manager)",
            "Director Alex (Admin)"
        ])

        self.login_pass = QLineEdit()
        self.login_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self.login_pass.setPlaceholderText("Enter secure pin/password")

        box_layout.addRow("Authorized Identity:", self.login_user)
        box_layout.addRow("Access Security Token:", self.login_pass)

        btn_login = QPushButton("Verify & Open Workspace")
        btn_login.clicked.connect(self.execute_login_handshake)
        box_layout.addRow("", btn_login)

        layout.addWidget(box)
        self.main_stack.addWidget(page)

    def execute_login_handshake(self):
        user_selection = self.login_user.currentText()
        password = self.login_pass.text()

        if not password:
            QMessageBox.critical(self, "Access Denied", "Token cannot be empty.")
            return

        if "Farmer" in user_selection:
            username = "farmer_john"
        elif "Manager" in user_selection:
            username = "supervisor_sarah"
        else:
            username = "director_alex"

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT * FROM users WHERE username=%s and password=%s"
                cursor.execute(query, (username, password))
                result = cursor.fetchone()

                if result:
                    QMessageBox.information(self, "Login Success", f"Welcome {username}!")
                    self.current_user = result["username"]
                    self.current_role = result["role"].capitalize()

                    self.lbl_session_identity.setText(f"Session: {self.current_user} ({self.current_role})")
                    self.log_action("Auth Engine", f"Successfully authenticated workspace access.")

                    is_staff = (self.current_role == "Staff")
                    is_admin = (self.current_role == "Admin")

                    self.btn_commit_cattle.setDisabled(is_staff)
                    self.btn_commit_product.setDisabled(is_staff)
                    self.btn_medical_intervention.setDisabled(is_staff)
                    self.btn_post_sale.setDisabled(is_staff)
                    self.btn_remove_cow.setDisabled(is_staff)

                    self.in_tag_id.setDisabled(is_staff)
                    self.in_cow_type.setDisabled(is_staff)
                    self.in_gender.setDisabled(is_staff)
                    self.in_milk.setDisabled(is_staff)
                    self.combo_med_action.setDisabled(is_staff)

                    if is_staff:
                        self.kpi_sales.hide()
                    else:
                        self.kpi_sales.show()

                    self.tabs.setTabVisible(3, True)
                    self.tabs.setTabVisible(4, not is_staff)
                    self.tabs.setTabVisible(5, is_admin)

                    self.load_cattle_from_db()
                    self.load_products_from_db()
                    self.load_sales_from_db()

                    self.recalculate_system_metrics()
                    self.refresh_cattle_table_render()
                    self.refresh_cold_chain_table_render()
                    self.refresh_sales_table_render()

                    self.main_stack.setCurrentIndex(0)
                    self.login_pass.clear()
                else:
                    QMessageBox.critical(self, "Access Denied", "Invalid access tokens.")
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Query Error", f"Database error:\n{err}")
            finally:
                connection.close()
        else:
            QMessageBox.critical(self, "Database Error", "Unable to reach database server.")

    def main_dashboard(self):
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(15, 15, 15, 15)

        workspace.setStyleSheet("""
            QWidget { background-color: #0F172A; color: #F1F5F9; font-family: 'Segoe UI', sans-serif; font-size: 13px; }
            QTabWidget::pane { border: 1px solid #334155; background: #1E293B; border-radius: 6px; }
            QTabBar::tab { background: #334155; color: #94A3B8; padding: 12px 20px; font-weight: bold; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
            QTabBar::tab:selected { background: #1E293B; border-bottom: 3px solid #38BDF8; color: #38BDF8; }
            QTableWidget { background-color: #1E293B; gridline-color: #334155; border: none; alternate-background-color: #111827; selection-background-color: #0369A1; }
            QHeaderView::section { background-color: #334155; color: #38BDF8; padding: 8px; border: 1px solid #1E293B; font-weight: bold; text-transform: uppercase; font-size: 11px; }
            QGroupBox { border: 1px solid #334155; border-radius: 6px; margin-top: 15px; font-weight: bold; color: #38BDF8; padding-top: 15px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 5px; background-color: #0F172A; }
            QLineEdit, QComboBox { background-color: #334155; border: 1px solid #475569; padding: 8px; border-radius: 4px; color: #FFFFFF; }
            QPushButton { background-color: #38BDF8; color: #0F172A; font-weight: bold; border: none; padding: 10px 20px; border-radius: 4px; text-transform: uppercase; }
            QPushButton:hover { background-color: #7DD3FC; }
        """)

        banner = QHBoxLayout()
        title = QLabel("LIVESTOCK ASSET, PROCESSING & HARVEST SALES INTEGRATED OS")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setStyleSheet("color: #38BDF8;")

        self.lbl_session_identity = QLabel("Session: None")
        self.lbl_session_identity.setStyleSheet("color: #F59E0B; font-weight: bold; padding-right: 15px;")

        btn_logout = QPushButton("Lock Terminal")
        btn_logout.setStyleSheet("background-color: #EF4444; color: white; padding: 5px 12px;")
        btn_logout.clicked.connect(lambda: self.main_stack.setCurrentIndex(1))

        banner.addWidget(title)
        banner.addStretch()
        banner.addWidget(self.lbl_session_identity)
        banner.addWidget(btn_logout)
        layout.addLayout(banner)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.main_overview_tab()
        self.livestock_tab()
        self.harvesting_tab()
        self.inventory_tab()
        self.sales_tab()
        self.audit_records_tab()

        self.main_stack.addWidget(workspace)

    def main_overview_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        kpi_row = QHBoxLayout()
        self.kpi_female = self.build_kpi_widget("TOTAL FEMALE CATTLE", "0 Head", "#1E293B")
        self.kpi_milk = self.build_kpi_widget("MILK STORAGE VOLUME", "0 L", "#1E293B")
        self.kpi_meat = self.build_kpi_widget("STORAGE MASS", "0 kg", "#1E293B")
        self.kpi_sales = self.build_kpi_widget("TOTAL SALES REVENUE", "₱0.00", "#38BDF8", text_color="#0F172A")

        kpi_row.addWidget(self.kpi_female)
        kpi_row.addWidget(self.kpi_milk)
        kpi_row.addWidget(self.kpi_meat)
        kpi_row.addWidget(self.kpi_sales)
        layout.addLayout(kpi_row)

        box = QGroupBox("Global Strategic Inventory Asset & Valuation Matrix")
        box_layout = QVBoxLayout(box)

        self.table_overview = QTableWidget(0, 4)
        self.table_overview.setAlternatingRowColors(True)
        self.table_overview.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_overview.setHorizontalHeaderLabels(
            ["SKU Item Designation", "Inventory Category Class", "Available Stock Quantities", "Unit Valuation Base"])
        self.table_overview.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        box_layout.addWidget(self.table_overview)

        layout.addWidget(box)
        self.tabs.addTab(tab, "Overview Dashboard")

    def livestock_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        left_box = QGroupBox("Live Animal Herd Directory Status Ledger")
        left_layout = QVBoxLayout(left_box)

        self.table_cattle = QTableWidget(0, 5)
        self.table_cattle.setAlternatingRowColors(True)
        self.table_cattle.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_cattle.setHorizontalHeaderLabels(
            ["Tag ID", "Cattle Type Profile", "Biological Sex", "Health Index", "Daily Milk Yield"])
        self.table_cattle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table_cattle)

        self.btn_remove_cow = QPushButton("Remove Selected Cow")
        self.btn_remove_cow.setStyleSheet("background-color: #DC2626; color: white; font-weight: bold;")
        self.btn_remove_cow.clicked.connect(self.remove_cattle)
        left_layout.addWidget(self.btn_remove_cow)

        box_med = QGroupBox("Medical Action Suite")
        med_layout = QHBoxLayout(box_med)
        self.combo_med_action = QComboBox()
        self.combo_med_action.addItems(["Cure / Administer Care", "Cull / Discard From Herd"])
        self.btn_medical_intervention = QPushButton("Execute Medical Order")
        self.btn_medical_intervention.clicked.connect(self.execute_medical_intervention)
        med_layout.addWidget(self.combo_med_action)
        med_layout.addWidget(self.btn_medical_intervention)
        left_layout.addWidget(box_med)
        layout.addWidget(left_box, 2)

        right_box = QGroupBox("Log New Animal Entry Node")
        form = QFormLayout(right_box)
        form.setVerticalSpacing(12)

        self.in_tag_id = QLineEdit()
        self.in_tag_id.setPlaceholderText("e.g. CTL-405")

        self.in_cow_type = QComboBox()
        self.in_cow_type.addItems(["Adult", "Adult(Sick)", "Young", "Young(Sick)"])

        self.in_gender = QComboBox()
        self.in_gender.addItems(["Female", "Male"])

        self.in_milk = QLineEdit("0L")

        form.addRow("Bovine Ear Tag ID:", self.in_tag_id)
        form.addRow("Cattle Type Profile:", self.in_cow_type)
        form.addRow("Biological Sex:", self.in_gender)
        form.addRow("Milk Volume in Liters (If Female):", self.in_milk)

        self.btn_commit_cattle = QPushButton("Add Cattle")
        self.btn_commit_cattle.clicked.connect(self.add_new_cattle)
        form.addRow("", self.btn_commit_cattle)

        self.in_gender.currentTextChanged.connect(
            lambda gender: self.in_milk.setEnabled(gender == "Female" and "Sick" not in self.in_cow_type.currentText())
        )
        self.in_cow_type.currentTextChanged.connect(
            lambda type_val: self.in_milk.setDisabled("Sick" in type_val or self.in_gender.currentText() == "Male")
        )

        layout.addWidget(right_box, 1)
        self.tabs.addTab(tab, "Livestock Management")

    def harvesting_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        left_box = QGroupBox("Live Animal Herd Directory Status Ledger (Select row to Harvest)")
        left_layout = QVBoxLayout(left_box)

        self.table_harvest_cattle = QTableWidget(0, 5)
        self.table_harvest_cattle.setAlternatingRowColors(True)
        self.table_harvest_cattle.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_harvest_cattle.setHorizontalHeaderLabels(
            ["Tag ID", "Cattle Type Profile", "Biological Sex", "Health Index", "Daily Milk Yield"])
        self.table_harvest_cattle.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table_harvest_cattle)
        layout.addWidget(left_box, 2)

        right_box = QGroupBox("Log Production Line Processing Yield")
        form = QFormLayout(right_box)
        form.setVerticalSpacing(12)

        self.in_sku_name = QLineEdit()
        self.in_sku_name.setPlaceholderText("e.g. Export Porterhouse Steak Cut")

        self.in_product_cat = QComboBox()
        self.in_product_cat.addItems([
            "Hide", "Milk", "Beef Tallow",
            "Chuck Cut", "Rib Cut", "Loin Cut", "Round Cut",
            "Flank Cut", "Brisket Cut", "Plate Cut", "Shank Cut"
        ])

        self.in_sku_qty = QLineEdit()
        self.in_sku_qty.setPlaceholderText("e.g. 45")

        self.in_sku_price = QLineEdit()
        self.in_sku_price.setPlaceholderText("e.g. 450.00")

        form.addRow("Stock Description SKU:", self.in_sku_name)
        form.addRow("Inventory Product Class:", self.in_product_cat)
        form.addRow("Batch Stock Output Quantity (Numeric):", self.in_sku_qty)
        form.addRow("Target Unit Price Value (PHP):", self.in_sku_price)

        self.btn_commit_product = QPushButton("Harvest Cattle from Livestock")
        self.btn_commit_product.clicked.connect(self.get_new_product)
        form.addRow("", self.btn_commit_product)

        layout.addWidget(right_box, 1)
        self.tabs.addTab(tab, "Harvesting and Processing")

    def inventory_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        left_box = QGroupBox("Cold Chain Inventory Storage Allocation Registry")
        left_layout = QVBoxLayout(left_box)

        self.table_processing = QTableWidget(0, 4)
        self.table_processing.setAlternatingRowColors(True)
        self.table_processing.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_processing.setHorizontalHeaderLabels(
            ["SKU Stock Label", "Target Product Category", "Current On-Hand Balance", "Unit Price"])
        self.table_processing.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table_processing)

        layout.addWidget(left_box)
        self.tabs.addTab(tab, "Inventory")

    def sales_tab(self):
        tab = QWidget()
        layout = QHBoxLayout(tab)

        left_box = QGroupBox("Archived Commercial Sales Transaction History Logs")
        left_layout = QVBoxLayout(left_box)

        self.table_sales = QTableWidget(0, 4)
        self.table_sales.setAlternatingRowColors(True)
        self.table_sales.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_sales.setHorizontalHeaderLabels(
            ["Receipt TX ID", "Product SKU Sold", "Sold Quantity Volume", "Gross Revenue Realized"])
        self.table_sales.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        left_layout.addWidget(self.table_sales)
        layout.addWidget(left_box, 2)

        right_box = QGroupBox("Post Commercial Sales Order Receipt")
        form = QFormLayout(right_box)
        form.setVerticalSpacing(12)

        self.in_sales_sku = QComboBox()
        self.in_sales_qty = QLineEdit()
        self.in_sales_qty.setPlaceholderText("Enter numeric units count")

        form.addRow("Select Target Stock SKU:", self.in_sales_sku)
        form.addRow("Transaction Sales Qty:", self.in_sales_qty)

        # ✨ ADDED: Standard Conversion Helper Label Interface
        self.lbl_conversion_info = QLabel("Metric Rules:  1 Liter = 1 Unit  |  1 Kg = 1 Unit")
        self.lbl_conversion_info.setStyleSheet("color: #F59E0B; font-weight: bold; margin-top: 5px; font-size: 11px;")
        form.addRow("", self.lbl_conversion_info)

        self.btn_post_sale = QPushButton("Process Transaction Receipt")
        self.btn_post_sale.clicked.connect(self.submit_sales_transaction)
        form.addRow("", self.btn_post_sale)

        layout.addWidget(right_box, 1)
        self.tabs.addTab(tab, "Sell Product/Sales")

    def audit_records_tab(self):
        tab = QWidget()
        layout = QVBoxLayout(tab)

        box = QGroupBox("Secured Core System Action & Audit Trail")
        box_layout = QVBoxLayout(box)

        self.table_audit = QTableWidget(0, 1)
        self.table_audit.setHorizontalHeaderLabels(["System Broadcast Operations Messages History"])
        self.table_audit.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_audit.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        box_layout.addWidget(self.table_audit)

        layout.addWidget(box)
        self.tabs.addTab(tab, "System Security Audit")

    def build_kpi_widget(self, label, val, bg_color, text_color="#FFFFFF"):
        card = QFrame()
        card.setStyleSheet(f"background-color: {bg_color}; border-radius: 6px;")
        card.setMinimumHeight(110)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(15, 15, 15, 15)

        title_lbl = QLabel(label.upper())
        title_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        title_lbl.setStyleSheet(f"color: {text_color}; opacity: 0.75; letter-spacing: 0.5px;")

        val_lbl = QLabel(val)
        val_lbl.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        val_lbl.setStyleSheet(f"color: {text_color};")

        card_layout.addWidget(title_lbl)
        card_layout.addWidget(val_lbl)
        return card

    def log_action(self, process, message):
        self.audit_logs.append(f"[{process.upper()}] by User '{self.current_user}' -> {message}")
        if hasattr(self, 'table_audit'):
            self.table_audit.setRowCount(len(self.audit_logs))
            for idx, log in enumerate(reversed(self.audit_logs)):
                self.table_audit.setItem(idx, 0, QTableWidgetItem(log))

    def load_cattle_from_db(self):
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                query = "SELECT tag_id, cattle_type, gender, health, milk_yield FROM cattle"
                cursor.execute(query)
                self.cattle_ledger = cursor.fetchall()
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Database Error", str(err))
            finally:
                connection.close()

    def load_products_from_db(self):
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT sku, category, stock, price FROM product_inventory")
                self.product_inventory = cursor.fetchall()
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Database Error", f"Failed to load products: {err}")
            finally:
                connection.close()

    def load_sales_from_db(self):
        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                cursor.execute("SELECT tx_id, sku, qty, total FROM sales")
                self.sales = cursor.fetchall()
            except mysql.connector.Error as err:
                QMessageBox.critical(self, "Database Error", f"Failed to load sales: {err}")
            finally:
                connection.close()

    def recalculate_system_metrics(self):
        female_count = sum(1 for c in self.cattle_ledger if c["gender"] == "Female")
        self.kpi_female.findChildren(QLabel)[1].setText(f"{female_count} Head")

        milk_sum = 0
        for c in self.cattle_ledger:
            val_str = c["milk_yield"].lower().replace('l', '').strip()
            if val_str.isdigit(): milk_sum += int(val_str)
        self.kpi_milk.findChildren(QLabel)[1].setText(f"{milk_sum} Units")  # Enforced standardized units naming

        meat_sum = 0
        for p in self.product_inventory:
            if p["category"] not in ["Milk", "Hide", "Beef Tallow"]:
                mass_val = "".join(char for char in p["stock"] if char.isdigit())
                if mass_val.isdigit():
                    meat_sum += int(mass_val)

        self.kpi_meat.findChildren(QLabel)[1].setText(f"{meat_sum} Units")  # Enforced standardized units naming

        gross_sales = 0.0
        for sale in self.sales:
            gross_sales += float(sale["total"].replace('₱', '').replace('$', '').replace(',', '').strip())
        self.cumulative_sales = gross_sales
        self.kpi_sales.findChildren(QLabel)[1].setText(f"₱{self.cumulative_sales:,.2f}")

        self.table_overview.setRowCount(len(self.product_inventory))
        for index, item in enumerate(self.product_inventory):
            self.table_overview.setItem(index, 0, QTableWidgetItem(item["sku"]))
            self.table_overview.setItem(index, 1, QTableWidgetItem(item["category"]))
            self.table_overview.setItem(index, 2, QTableWidgetItem(item["stock"]))
            self.table_overview.setItem(index, 3, QTableWidgetItem(item["price"]))

        self.in_sales_sku.clear()
        for item in self.product_inventory:
            self.in_sales_sku.addItem(item["sku"])

    def refresh_cattle_table_render(self):
        for target_table in [self.table_cattle, self.table_harvest_cattle]:
            target_table.setRowCount(0)
            for data in self.cattle_ledger:
                if self.current_role == "Staff" and data["health"] == "Sick":
                    continue

                row = target_table.rowCount()
                target_table.insertRow(row)

                target_table.setItem(row, 0, QTableWidgetItem(data["tag_id"]))
                target_table.setItem(row, 1, QTableWidgetItem(data["cattle_type"]))
                target_table.setItem(row, 2, QTableWidgetItem(data["gender"]))

                health_cell = QTableWidgetItem(data["health"])
                if data["health"] == "Sick":
                    health_cell.setBackground(QColor("#991B1B"))
                target_table.setItem(row, 3, health_cell)
                target_table.setItem(row, 4, QTableWidgetItem(data["milk_yield"]))

    def refresh_cold_chain_table_render(self):
        self.table_processing.setRowCount(len(self.product_inventory))
        for row, data in enumerate(self.product_inventory):
            self.table_processing.setItem(row, 0, QTableWidgetItem(data["sku"]))
            self.table_processing.setItem(row, 1, QTableWidgetItem(data["category"]))
            self.table_processing.setItem(row, 2, QTableWidgetItem(data["stock"]))
            self.table_processing.setItem(row, 3, QTableWidgetItem(data["price"]))

    def refresh_sales_table_render(self):
        self.table_sales.setRowCount(len(self.sales))
        for row, data in enumerate(self.sales):
            self.table_sales.setItem(row, 0, QTableWidgetItem(data["tx_id"]))
            self.table_sales.setItem(row, 1, QTableWidgetItem(data["sku"]))
            self.table_sales.setItem(row, 2, QTableWidgetItem(data["qty"]))
            self.table_sales.setItem(row, 3, QTableWidgetItem(data["total"]))

    def execute_medical_intervention(self):
        ranges = self.table_cattle.selectedRanges()
        if not ranges:
            QMessageBox.warning(self, "Invalid Request", "Please select a row from the database.")
            return

        row_index = ranges[0].topRow()
        tag_id = self.table_cattle.item(row_index, 0).text()
        medical_choice = self.combo_med_action.currentText()

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor(dictionary=True)
                fetch_query = "SELECT * FROM cattle WHERE tag_id = %s"
                cursor.execute(fetch_query, (tag_id,))
                target_bovine = cursor.fetchone()

                if not target_bovine:
                    return

                if "Sick" not in target_bovine["cattle_type"]:
                    QMessageBox.information(self, "Action Prevented", "This livestock element is already healthy.")
                    return

                if "Cure" in medical_choice:
                    update_query = "UPDATE cattle SET health = %s WHERE tag_id = %s"
                    cursor.execute(update_query, ("Healthy", tag_id))
                    self.log_action("Vet Subsystem", f"Administered cure vector onto animal profile {tag_id}.")
                    connection.commit()
                else:
                    delete_query = "DELETE FROM cattle WHERE tag_id = %s"
                    cursor.execute(delete_query, (tag_id,))
                    self.log_action("Cull System", f"Culled livestock {tag_id}.")
                    connection.commit()

                self.load_cattle_from_db()
                self.refresh_cattle_table_render()
                self.recalculate_system_metrics()
            finally:
                connection.close()

    def remove_cattle(self):
        ranges = self.table_cattle.selectedRanges()
        if not ranges:
            QMessageBox.warning(self, "Selection Required", "Please select a row of cattle you want to remove.")
            return

        row_index = ranges[0].topRow()
        tag_id = self.table_cattle.item(row_index, 0).text()

        confirm = QMessageBox.question(
            self, "Confirm Delete",
            f"Are you sure you want to permanently remove the cattle {tag_id} from the list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            connection = connect_to_database()
            if connection:
                try:
                    cursor = connection.cursor(dictionary=True)
                    query = "DELETE FROM cattle WHERE tag_id = %s"
                    cursor.execute(query, (tag_id,))
                    connection.commit()

                    self.log_action("Asset Eraser", f"Permanently removed and purged livestock node: {tag_id}")
                    QMessageBox.information(self, "Removed", f"The Cattle {tag_id} is successfully removed.")

                    self.load_cattle_from_db()
                    self.refresh_cattle_table_render()
                    self.recalculate_system_metrics()
                finally:
                    connection.close()

    def add_new_cattle(self):
        tag_id = self.in_tag_id.text().strip()
        type_val = self.in_cow_type.currentText()
        gender = self.in_gender.currentText()
        milk = self.in_milk.text().strip()

        if not tag_id:
            QMessageBox.warning(self, "Missing Data", "Ear Tag ID fields cannot be blank.")
            return

        if any(c["tag_id"] == tag_id for c in self.cattle_ledger):
            QMessageBox.warning(self, "Duplicate Error", f"Tag ID {tag_id} already exists.")
            return

        health_status = "Sick" if "Sick" in type_val else "Healthy"
        milk_final = f"{milk.upper().replace('L', '')}L" if (
                gender == "Female" and health_status == "Healthy") else "0L"
        if gender == "Male": milk_final = "N/A"

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                check_query = "SELECT * FROM cattle WHERE tag_id = %s"
                cursor.execute(check_query, (tag_id,))
                if cursor.fetchone():
                    QMessageBox.warning(self, "Duplicate Error", f"Tag {tag_id} already exists.")
                    return

                query = "INSERT INTO cattle (tag_id, cattle_type, gender, health, milk_yield) VALUES (%s, %s, %s, %s, %s)"
                values = (tag_id, type_val, gender, health_status, milk_final)
                cursor.execute(query, values)
                connection.commit()

                self.log_action("Herd Registry", f"Registered cattle profile {tag_id} under classification {type_val}.")
                self.load_cattle_from_db()
                self.refresh_cattle_table_render()
                self.recalculate_system_metrics()
                self.in_tag_id.clear()
            finally:
                connection.close()

    def get_new_product(self):
        ranges = self.table_harvest_cattle.selectedRanges()
        if not ranges:
            QMessageBox.warning(self, "Selection Required",
                                "Please select a live animal row from the harvest table view.")
            return

        row_index = ranges[0].topRow()
        tag_id = self.table_harvest_cattle.item(row_index, 0).text()

        # ✨ Extract explicit attributes to evaluate validation rule thresholds
        selected_cow_milk_yield = self.table_harvest_cattle.item(row_index, 4).text().strip().upper()

        sku = self.in_sku_name.text().strip()
        category = self.in_product_cat.currentText()
        qty = self.in_sku_qty.text().strip()
        price = self.in_sku_price.text().strip()

        if not sku or not qty or not price:
            QMessageBox.warning(self, "Incomplete Form", "Please fill in all product form entry fields.")
            return

        if category == "Milk":
            # Strip out letters like 'L' or 'N/A' to get a pure number
            clean_yield_str = "".join(char for char in selected_cow_milk_yield if char.isdigit())

            # Convert to integer if digits exist, otherwise default to 0
            actual_yield_int = int(clean_yield_str) if clean_yield_str else 0

            if actual_yield_int <= 0 or "N/A" in selected_cow_milk_yield:
                QMessageBox.warning(
                    self, "Harvest Denied",
                    f"Selected cattle {tag_id} cannot produce milk inventory because its active yield register status is '{selected_cow_milk_yield}'."
                )
                return
            try:
                requested_qty = int(qty)
                if requested_qty > actual_yield_int:
                    QMessageBox.warning(
                        self, "Excessive Quantity Requested",
                        f"Cannot harvest {requested_qty} units. Selected cow only yields up to {actual_yield_int} units."
                    )
                    return
            except ValueError:
                QMessageBox.warning(self, "Validation Failure", "Please enter a valid numeric harvest quantity.")
                return

        price = price.replace('₱', '').replace('$', '').strip()
        try:
            price_val = float(price)
            price = f"₱{price_val:,.2f}"
        except ValueError:
            price = f"₱{price}"

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                connection.start_transaction()

                if category != "Milk":
                    delete_query = "DELETE FROM cattle WHERE tag_id = %s"
                    cursor.execute(delete_query, (tag_id,))
                else:
                    # Calculate remaining milk capacity for this cow
                    rem_yield = actual_yield_int - requested_qty
                    new_yield_str = f"{rem_yield}L" if rem_yield > 0 else "0L"

                    # Update the live cow's yield record in the database
                    update_cow_query = "UPDATE cattle SET milk_yield = %s WHERE tag_id = %s"
                    cursor.execute(update_cow_query, (new_yield_str, tag_id))

                    self.log_action("Harvest Line",f"Extracted {requested_qty} units of milk from {tag_id}. Remaining yield capacity: {new_yield_str}")

                check_product_query = "SELECT stock FROM product_inventory WHERE sku = %s"
                cursor.execute(check_product_query, (sku,))
                existing_product = cursor.fetchone()

                if existing_product:
                    existing_qty = "".join(char for char in existing_product[0] if char.isdigit())
                    new_qty_total = int(existing_qty if existing_qty else 0) + int(qty)

                    update_stock_query = "UPDATE product_inventory SET stock = %s, price = %s WHERE sku = %s"
                    cursor.execute(update_stock_query, (f"{new_qty_total} units", price, sku))
                else:
                    insert_query = "INSERT INTO product_inventory (sku, category, stock, price) VALUES (%s, %s, %s, %s)"
                    cursor.execute(insert_query, (sku, category, f"{qty} units", price))

                connection.commit()
                self.log_action("Harvest Line", f"Harvested animal {tag_id} into retail inventory SKU stock: {sku}.")

                self.load_cattle_from_db()
                self.load_products_from_db()
                self.refresh_cattle_table_render()
                self.refresh_cold_chain_table_render()
                self.recalculate_system_metrics()

                self.in_sku_name.clear()
                self.in_sku_qty.clear()
                self.in_sku_price.clear()

                QMessageBox.information(self, "Success",
                                        f"Animal {tag_id} successfully processed into retail inventory.")
            except (mysql.connector.Error, ValueError) as err:
                connection.rollback()
                QMessageBox.critical(self, "Database Error", f"Harvest transaction roll-back initiated: {err}")
            finally:
                connection.close()

    def submit_sales_transaction(self):
        sku_target = self.in_sales_sku.currentText()
        quantity_input = self.in_sales_qty.text().strip()

        if not sku_target:
            QMessageBox.warning(self, "Validation Failure",
                                "No products available in inventory ledger storage to sell.")
            return

        if not quantity_input or not quantity_input.isdigit() or int(quantity_input) <= 0:
            QMessageBox.warning(self, "Validation Failure", "Please enter a valid positive numeric sales quantity.")
            return

        sell_qty = int(quantity_input)
        product = next((p for p in self.product_inventory if p["sku"] == sku_target), None)
        if not product: return

        clean_stock_str = "".join(char for char in product["stock"] if char.isdigit())
        current_stock_qty = int(clean_stock_str) if clean_stock_str else 0

        if sell_qty > current_stock_qty:
            QMessageBox.warning(self, "Stock Out Error",
                                f"Inadequate inventory volume balances. Stock available: {current_stock_qty}")
            return

        unit_price = float(product["price"].replace('₱', '').replace('$', '').replace(',', '').strip())
        calculated_gross = unit_price * sell_qty
        new_tx_id = f"TX-{len(self.sales) + 1001}"

        connection = connect_to_database()
        if connection:
            try:
                cursor = connection.cursor()
                connection.start_transaction()

                rem_qty = current_stock_qty - sell_qty
                if rem_qty <= 0:
                    cursor.execute("DELETE FROM product_inventory WHERE sku = %s", (sku_target,))
                else:
                    cursor.execute("UPDATE product_inventory SET stock = %s WHERE sku = %s",
                                   (f"{rem_qty} units", sku_target))

                query = "INSERT INTO sales (tx_id, sku, qty, total) VALUES (%s, %s, %s, %s)"
                cursor.execute(query, (new_tx_id, sku_target, f"{sell_qty} units", f"₱{calculated_gross:,.2f}"))

                connection.commit()
                self.log_action("Sales Engine",
                                f"Executed order receipt {new_tx_id}. Gross value: ₱{calculated_gross:,.2f}")

                self.load_products_from_db()
                self.load_sales_from_db()
                self.refresh_cold_chain_table_render()
                self.refresh_sales_table_render()
                self.recalculate_system_metrics()

                self.in_sales_qty.clear()
                QMessageBox.information(self, "Order Dispatched",
                                        f"Receipt {new_tx_id} successfully recorded and billed.")
            except mysql.connector.Error as err:
                connection.rollback()
                QMessageBox.critical(self, "Database Error", f"Sales operation database fallback: {err}")
            finally:
                connection.close()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = FarmManagementSystem()
    window.show()
    sys.exit(app.exec())