import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QVBoxLayout, QWidget, QHBoxLayout, QLabel, QDialog, QDialogButtonBox, QHeaderView
)
from PyQt5.QtGui import QIntValidator
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
        """Gibt den eingegebenen Private Key zurück."""
        return self.input_field.text()


class PublicKeyDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set Public Key")
        self.setGeometry(200, 200, 400, 150)
        self.layout = QVBoxLayout()

        self.label = QLabel("Enter your public key:")
        self.input_field = QLineEdit()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.input_field)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel, self)
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        self.layout.addWidget(self.buttons)

        self.setLayout(self.layout)

    def get_public_key(self):
        """Gibt den eingegebenen Public Key zurück."""
        return self.input_field.text()


class CopyTradingGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.public_key = None  # Speichert den Public Key des Benutzers
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Solana CopyTrading Bot")
        self.setGeometry(100, 100, 900, 600)

        # Hauptlayout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        input_layout = QHBoxLayout()
        wallet_layout = QVBoxLayout()

        # Eingabe für neue Wallet-Adresse
        self.wallet_input = QLineEdit()
        self.wallet_input.setPlaceholderText("Enter Wallet Address")
        self.add_wallet_button = QPushButton("Add Wallet")
        self.add_wallet_button.clicked.connect(self.add_wallet)
        input_layout.addWidget(self.wallet_input)
        input_layout.addWidget(self.add_wallet_button)

        # Wallet-Tabelle
        self.wallet_table = QTableWidget()
        self.wallet_table.setColumnCount(4)
        self.wallet_table.setHorizontalHeaderLabels(
            ["Wallet Address", "PNL", "% per trade", "Actions"])
        self.wallet_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.wallet_table.cellClicked.connect(self.handle_cell_click)

        # Refresh Button
        self.refresh_button = QPushButton("Refresh Wallets")
        self.refresh_button.clicked.connect(self.refresh_wallets)

        # Private Key Button
        self.private_key_button = QPushButton("Set Private Key")
        self.private_key_button.clicked.connect(self.open_private_key_dialog)

        # Public Key Button
        self.public_key_button = QPushButton("Set Public Key")
        self.public_key_button.clicked.connect(self.open_public_key_dialog)

        # Labels
        self.total_pnl_label = QLabel("Total PNL: 0.0")
        self.total_sol_label = QLabel("Total SOL: 0.0")  # Neues Label für Total SOL

        # Layout zusammenfügen
        wallet_layout.addWidget(self.wallet_table)
        wallet_layout.addWidget(self.total_pnl_label)
        wallet_layout.addWidget(self.total_sol_label)
        wallet_layout.addWidget(self.refresh_button)
        wallet_layout.addWidget(self.private_key_button)
        wallet_layout.addWidget(self.public_key_button)

        layout.addLayout(input_layout)
        layout.addLayout(wallet_layout)

        self.refresh_wallets()

    def open_private_key_dialog(self):
        """Öffnet den Dialog zur Eingabe des Private Keys."""
        dialog = PrivateKeyDialog()
        if dialog.exec_():
            private_key = dialog.get_private_key()
            response = requests.post(f"{API_URL}/set_private_key/", json={"key": private_key})
            if response.status_code == 200:
                self.statusBar().showMessage("Private Key set successfully.", 5000)
            else:
                self.statusBar().showMessage("Failed to set Private Key.", 5000)

    def open_public_key_dialog(self):
        """Öffnet den Dialog zur Eingabe des Public Keys."""
        dialog = PublicKeyDialog()
        if dialog.exec_():
            self.public_key = dialog.get_public_key()
            if self.public_key:
                self.statusBar().showMessage("Public Key set successfully.", 5000)
                self.update_total_sol()
            else:
                self.statusBar().showMessage("Public Key not set.", 5000)

    def add_wallet(self):
        """Fügt eine neue Wallet hinzu."""
        wallet_address = self.wallet_input.text()
        if wallet_address:
            response = requests.post(f"{API_URL}/wallets/", json={"wallet_address": wallet_address})
            if response.status_code == 200:
                self.wallet_input.setText("")
                self.refresh_wallets()
            else:
                self.statusBar().showMessage("Failed to add wallet.", 5000)

    def refresh_wallets(self):
        """Aktualisiert die Tabelle mit den Wallet-Daten."""
        response = requests.get(f"{API_URL}/wallets/")
        if response.status_code == 200:
            wallets = response.json()
            self.wallet_table.setRowCount(len(wallets))
            total_pnl = 0.0
            for i, wallet in enumerate(wallets):
                # Wallet-Adresse
                wallet_address_item = QTableWidgetItem(wallet["wallet_address"])
                wallet_address_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 0, wallet_address_item)

                # PNL
                pnl_item = QTableWidgetItem(str(wallet["pnl"]))
                pnl_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 1, pnl_item)
                total_pnl += wallet["pnl"]

                # Allocation
                allocation_item = QTableWidgetItem(f"{int(wallet.get('allocation_percentage', 10))}")
                allocation_item.setTextAlignment(Qt.AlignCenter)
                allocation_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(i, 2, allocation_item)

                # Remove-Button
                remove_button = QPushButton("Remove")
                remove_button.clicked.connect(lambda _, w_id=wallet["id"]: self.remove_wallet(w_id))
                self.wallet_table.setCellWidget(i, 3, remove_button)

            self.total_pnl_label.setText(f"Total PNL: {total_pnl:.2f}")
            self.update_total_sol()  # Aktualisiert den Total SOL Wert
        else:
            self.statusBar().showMessage("Failed to refresh wallets.", 5000)

    def update_total_sol(self):
        """Aktualisiert den Total SOL-Wert für das eigene Wallet."""
        if not self.public_key:
            self.total_sol_label.setText("Total SOL: Public Key not set.")
            return

        response = requests.get(f"{API_URL}/wallets/{self.public_key}/balance/")
        if response.status_code == 200:
            # Defaultwert verwenden, falls `balance` nicht verfügbar ist
            balance = response.json().get("balance", 0.0)
            balance = balance if balance is not None else 0.0
            self.total_sol_label.setText(f"Total SOL: {balance:.2f}")
        else:
            self.total_sol_label.setText("Total SOL: Error fetching balance.")
            self.statusBar().showMessage("Failed to fetch Total SOL.", 5000)

    def handle_cell_click(self, row, column):
        """Wenn auf eine Zelle geklickt wird."""
        if column == 2:  # Nur '% per trade' ist bearbeitbar
            self.activate_allocation_edit(row)

    def activate_allocation_edit(self, row):
        """Aktiviert die Bearbeitung der '% per trade'-Spalte."""
        current_value = self.wallet_table.item(row, 2).text()
        allocation_input = QLineEdit(current_value)
        allocation_input.setValidator(QIntValidator(0, 100))  # Nur ganze Zahlen
        allocation_input.setAlignment(Qt.AlignCenter)
        self.wallet_table.setCellWidget(row, 2, allocation_input)
        allocation_input.setFocus()
        allocation_input.returnPressed.connect(lambda: self.update_allocation(row, allocation_input))

    def update_allocation(self, row, input_field):
        """Aktualisiert die Allokation für eine Wallet."""
        try:
            allocation = int(input_field.text())  # Nur ganze Zahlen
            wallet_id = self.get_wallet_id_from_row(row)
            if not wallet_id:
                self.statusBar().showMessage(f"Failed to find wallet ID for row {row}.", 5000)
                return

            response = requests.put(f"{API_URL}/wallets/{wallet_id}/set_allocation/", json={"percentage": allocation})
            if response.status_code == 200:
                allocation_item = QTableWidgetItem(str(allocation))
                allocation_item.setTextAlignment(Qt.AlignCenter)
                allocation_item.setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.wallet_table.setItem(row, 2, allocation_item)
                self.statusBar().showMessage("Allocation updated successfully.", 5000)
            else:
                error_message = response.json().get("detail", "Unknown error")
                self.statusBar().showMessage(f"Failed to update allocation. Error: {error_message}", 5000)
        except ValueError:
            self.statusBar().showMessage("Invalid allocation value. Use whole numbers only.", 5000)

    def get_wallet_id_from_row(self, row):
        """Holt die Wallet-ID basierend auf der Tabellenzeile."""
        wallet_address = self.wallet_table.item(row, 0).text()
        response = requests.get(f"{API_URL}/wallets/")
        if response.status_code == 200:
            wallets = response.json()
            for wallet in wallets:
                if wallet["wallet_address"] == wallet_address:
                    return wallet["id"]
        return None

    def remove_wallet(self, wallet_id):
        """Entfernt eine Wallet."""
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
