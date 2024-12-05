import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout, QDialog, QDialogButtonBox, QHeaderView
)
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtCore import Qt
import requests

API_URL = "http://127.0.0.1:8000"  # Backend-API-Adresse


class PrivateKeyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set Private Key")
        self.setGeometry(200, 200, 400, 150)
        self.layout = QVBoxLayout()

        self.label = QLabel("Enter your private key:")
        self.input_field = QLineEdit()
        self.input_field.setEchoMode(QLineEdit.Password)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input_field)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def get_private_key(self):
        return self.input_field.text()


class CopyTradingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Solana CopyTrading Bot")
        self.setGeometry(100, 100, 900, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        input_layout = QHBoxLayout()
        wallet_layout = QVBoxLayout()

        self.wallet_input = QLineEdit()
        self.wallet_input.setPlaceholderText("Enter Wallet Address")
        self.add_wallet_button = QPushButton("Add Wallet")
        self.add_wallet_button.clicked.connect(self.add_wallet)
        input_layout.addWidget(self.wallet_input)
        input_layout.addWidget(self.add_wallet_button)

        self.wallet_table = QTableWidget()
        self.wallet_table.setColumnCount(5)
        self.wallet_table.setHorizontalHeaderLabels(
            ["Wallet Address", "PNL", "Active Trades", "% per trade", "Actions"])
        self.wallet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.total_pnl_label = QLabel("Total PNL: 0.0")
        self.refresh_button = QPushButton("Refresh Wallets")
        self.refresh_button.clicked.connect(self.refresh_wallets)

        self.private_key_button = QPushButton("Set Private Key")
        self.private_key_button.clicked.connect(self.open_private_key_dialog)

        wallet_layout.addWidget(self.wallet_table)
        wallet_layout.addWidget(self.total_pnl_label)
        wallet_layout.addWidget(self.refresh_button)
        wallet_layout.addWidget(self.private_key_button)

        layout.addLayout(input_layout)
        layout.addLayout(wallet_layout)

        self.refresh_wallets()

    def open_private_key_dialog(self):
        dialog = PrivateKeyDialog()
        if dialog.exec_():
            private_key = dialog.get_private_key()
            response = requests.post(f"{API_URL}/set_private_key/", json={"key": private_key})
            if response.status_code == 200:
                self.statusBar().showMessage("Private Key set successfully.", 5000)
            else:
                self.statusBar().showMessage("Failed to set Private Key.", 5000)

    def add_wallet(self):
        wallet_address = self.wallet_input.text()
        if wallet_address:
            response = requests.post(f"{API_URL}/wallets/", json={"wallet_address": wallet_address})
            if response.status_code == 200:
                self.wallet_input.setText("")
                self.refresh_wallets()
            else:
                self.statusBar().showMessage("Failed to add wallet.", 5000)

    def refresh_wallets(self):
        response = requests.get(f"{API_URL}/wallets/")
        if response.status_code == 200:
            wallets = response.json()
            self.wallet_table.setRowCount(len(wallets))
            total_pnl = 0.0
            for i, wallet in enumerate(wallets):
                # Wallet Address (nicht bearbeitbar)
                wallet_address_item = QTableWidgetItem(wallet["wallet_address"])
                wallet_address_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 0, wallet_address_item)

                # PNL (nicht bearbeitbar)
                pnl_item = QTableWidgetItem(str(wallet["pnl"]))
                pnl_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 1, pnl_item)
                total_pnl += wallet["pnl"]

                # Active Trades (nicht bearbeitbar)
                active_trades_item = QTableWidgetItem(str(wallet.get("active_trades", 0)))
                active_trades_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 2, active_trades_item)

                # Allocation (bearbeitbar durch Klick)
                allocation_item = QTableWidgetItem(f"{wallet.get('allocation_percentage', 10.0):.2f}")
                allocation_item.setTextAlignment(Qt.AlignCenter)
                allocation_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 3, allocation_item)

                # Remove Button
                remove_button = QPushButton("Remove")
                remove_button.clicked.connect(lambda _, w_id=wallet["id"]: self.remove_wallet(w_id))
                self.wallet_table.setCellWidget(i, 4, remove_button)

            self.wallet_table.cellClicked.connect(self.handle_cell_click)
            self.total_pnl_label.setText(f"Total PNL: {total_pnl:.2f}")
        else:
            self.statusBar().showMessage("Failed to refresh wallets.", 5000)

    def handle_cell_click(self, row, column):
        if column == 3:  # Nur '% per trade' ist bearbeitbar
            self.activate_allocation_edit(row)

    def activate_allocation_edit(self, row):
        current_value = self.wallet_table.item(row, 3).text()
        allocation_input = QLineEdit(current_value)
        allocation_input.setValidator(QDoubleValidator(0.0, 100.0, 2))
        allocation_input.setAlignment(Qt.AlignCenter)
        self.wallet_table.setCellWidget(row, 3, allocation_input)
        allocation_input.setFocus()
        allocation_input.returnPressed.connect(lambda: self.update_allocation(row, allocation_input))

    def update_allocation(self, row, input_field):
        try:
            allocation = float(input_field.text())
            wallet_id = self.get_wallet_id_from_row(row)
            if not wallet_id:
                self.statusBar().showMessage(f"Failed to find wallet ID for row {row}.", 5000)
                return
            response = requests.put(f"{API_URL}/wallets/{wallet_id}/set_allocation/", json={"percentage": allocation})
            if response.status_code == 200:
                allocation_item = QTableWidgetItem(f"{allocation:.2f}")
                allocation_item.setTextAlignment(Qt.AlignCenter)
                allocation_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(row, 3, allocation_item)
                self.statusBar().showMessage("Allocation updated successfully.", 5000)
            else:
                error_message = response.json().get("detail", "Unknown error")
                self.statusBar().showMessage(f"Failed to update allocation. Error: {error_message}", 5000)
        except ValueError:
            self.statusBar().showMessage("Invalid allocation value.", 5000)

    def get_wallet_id_from_row(self, row):
        wallet_address = self.wallet_table.item(row, 0).text()
        response = requests.get(f"{API_URL}/wallets/")
        if response.status_code == 200:
            wallets = response.json()
            for wallet in wallets:
                if wallet["wallet_address"] == wallet_address:
                    return wallet["id"]
        return None

    def remove_wallet(self, wallet_id):
        response = requests.delete(f"{API_URL}/wallets/{wallet_id}")
        if response.status_code == 200:
            self.refresh_wallets()
            self.statusBar().showMessage("Wallet removed successfully.", 5000)
        else:
            self.statusBar().showMessage("Failed to remove wallet.", 5000)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CopyTradingGUI()
    window.show()
    sys.exit(app.exec_())
