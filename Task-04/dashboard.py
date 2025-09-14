import sys
import csv
import mysql.connector
from mysql.connector import Error
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QGridLayout, 
    QTextEdit, QSizePolicy, QLineEdit, QMessageBox, QCheckBox,
    QDialog, QDialogButtonBox, QFileDialog
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt
from datetime import datetime

class ColumnSelectionDialog(QDialog):
    def __init__(self, available_columns, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Columns to Display")
        self.setMinimumSize(300, 400)
        
        layout = QVBoxLayout(self)
        
        self.checkboxes = {}
        for column in available_columns:
            checkbox = QCheckBox(column.capitalize())
            checkbox.setChecked(True)
            self.checkboxes[column] = checkbox
            layout.addWidget(checkbox)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def get_selected_columns(self):
        return [col for col, cb in self.checkboxes.items() if cb.isChecked()]

class Dashboard(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CineScope – Dashboard")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet("background-color: #121212; color: white;")
        
        self.connection = None
        self.connect_to_db()
        
        self.search_mode = "title"
        self.selected_columns = ["title", "year", "genre", "rating", "director", "stars"]
        
        self.current_data = []
        self.current_columns = []
        
        self.search_buttons = {}
        
        self.init_ui()

    def connect_to_db(self):
        try:
            self.connection = mysql.connector.connect(
                host='localhost',
                database='movies_db',
                user='movie_user',
                password='Gsk@6363'
            )
            if self.connection.is_connected():
                print("Successfully connected to database")
                cursor = self.connection.cursor()
                cursor.execute("SELECT DATABASE()")
                db_name = cursor.fetchone()
                print(f"Connected to database: {db_name[0]}")
                cursor.close()
        except Error as e:
            print(f"Failed to connect to database: {e}")
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to connect to database: {e}\n\nPlease check:\n"
                "1. MySQL server is running\n"
                "2. Database 'movies_db' exists\n"
                "3. User 'movie_user' has privileges\n"
                "4. Password is correct"
            )

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(10)

        header = QLabel("🎬 CineScope Dashboard")
        header.setFont(QFont("Arial", 24, QFont.Bold))
        header.setAlignment(Qt.AlignCenter)
        header.setFixedHeight(80)
        main_layout.addWidget(header)

        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)

        left_widget = QWidget()
        left_widget.setFixedWidth(300)
        left_container = QVBoxLayout(left_widget)
        left_container.setSpacing(15)
        left_container.setAlignment(Qt.AlignTop)

        search_heading = QLabel("Search By")
        search_heading.setFont(QFont("Arial", 18, QFont.Bold))
        left_container.addWidget(search_heading)

        search_buttons = [
            ("Genre", "genre"),
            ("Year", "year"),
            ("Rating", "rating"),
            ("Director", "director"),
            ("Title", "title"),
        ]

        search_grid = QGridLayout()
        for index, (label, mode) in enumerate(search_buttons):
            btn = QPushButton(label)
            btn.setStyleSheet(self.get_button_style(mode == self.search_mode))
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(lambda checked, m=mode: self.set_search_mode(m))
            row, col = divmod(index, 2)
            search_grid.addWidget(btn, row, col)
            self.search_buttons[mode] = btn
        left_container.addLayout(search_grid)

        column_heading = QLabel("Select Columns")
        column_heading.setFont(QFont("Arial", 18, QFont.Bold))
        left_container.addWidget(column_heading)

        column_btn = QPushButton("Choose Columns...")
        column_btn.setStyleSheet(self.get_button_style(False))
        column_btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        column_btn.clicked.connect(self.show_column_dialog)
        left_container.addWidget(column_btn)

        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search term")
        self.query_input.setStyleSheet("background-color: #1e1e1e; color: white; padding: 5px; border: 1px solid #444;")
        left_container.addWidget(self.query_input)

        action_layout = QHBoxLayout()
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("background-color: #e50914; color: white; padding: 6px; border-radius: 5px;")
        search_btn.clicked.connect(self.execute_search)
        action_layout.addWidget(search_btn)

        export_btn = QPushButton("Export CSV")
        export_btn.setStyleSheet("background-color: #1f1f1f; color: white; padding: 6px; border-radius: 5px;")
        export_btn.clicked.connect(self.export_csv)
        action_layout.addWidget(export_btn)
        left_container.addLayout(action_layout)

        split_layout.addWidget(left_widget)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setSpacing(10)

        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                color: white;
                font-family: Arial, sans-serif;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: white;
                color: black;
                padding: 4px;
            }
        """)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.output_console = QTextEdit()
        self.output_console.setPlaceholderText("Results will appear here...")
        self.output_console.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: white;
                border: 1px solid #444;
                padding: 5px;
            }
        """)
        self.output_console.setFixedHeight(100)

        right_layout.addWidget(self.table)
        right_layout.addWidget(self.output_console)

        split_layout.addWidget(right_widget)
        main_layout.addLayout(split_layout)

    def get_button_style(self, is_selected):
        if is_selected:
            return """
                QPushButton {
                    background-color: #ffcc00;
                    color: black;
                    border: 1px solid #ff9900;
                    border-radius: 3px;
                    padding: 6px;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #1f1f1f;
                    color: white;
                    border: 1px solid #333;
                    border-radius: 3px;
                    padding: 6px;
                }
                QPushButton:hover {
                    background-color: #333;
                }
            """

    def set_search_mode(self, mode):
        self.search_mode = mode
        self.output_console.append(f"Search mode set to: {mode}")
        for m, btn in self.search_buttons.items():
            btn.setStyleSheet(self.get_button_style(m == mode))

    def show_column_dialog(self):
        available_columns = ["title", "year", "genre", "rating", "director", "stars", "duration", "votes"]
        dialog = ColumnSelectionDialog(available_columns, self)
        if dialog.exec() == QDialog.Accepted:
            self.selected_columns = dialog.get_selected_columns()
            self.output_console.append(f"Selected columns: {', '.join(self.selected_columns)}")
            self.execute_search()

    def build_query(self):
        search_text = self.query_input.text().strip()
        if self.selected_columns:
            columns = ", ".join(self.selected_columns)
            query = f"SELECT {columns} FROM movies"
        else:
            query = "SELECT * FROM movies"
        if search_text:
            if self.search_mode == "year":
                query += f" WHERE {self.search_mode} = %s"
                params = (int(search_text),)
            elif self.search_mode == "rating":
                query += f" WHERE {self.search_mode} >= %s"
                params = (float(search_text),)
            else:
                query += f" WHERE {self.search_mode} LIKE %s"
                params = (f"%{search_text}%",)
        else:
            params = ()
        query += " ORDER BY title"
        return query, params

    def execute_search(self):
        if not self.connection or not self.connection.is_connected():
            self.connect_to_db()
            if not self.connection:
                self.output_console.append("Error: Not connected to database")
                return
        try:
            cursor = self.connection.cursor()
            query, params = self.build_query()
            self.output_console.append(f"Executing: {query} with params: {params}")
            cursor.execute(query, params)
            results = cursor.fetchall()
            column_names = [desc[0] for desc in cursor.description]
            self.current_data = results
            self.current_columns = column_names
            self.table.setRowCount(len(results))
            self.table.setColumnCount(len(column_names))
            self.table.setHorizontalHeaderLabels([name.capitalize() for name in column_names])
            for row_idx, row_data in enumerate(results):
                for col_idx, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data) if col_data is not None else "")
                    item.setTextAlignment(Qt.AlignCenter)
                    self.table.setItem(row_idx, col_idx, item)
            cursor.close()
            self.output_console.append(f"Found {len(results)} results")
        except Error as e:
            self.output_console.append(f"Database error: {e}")
        except ValueError as e:
            self.output_console.append(f"Input error: {e}. Please check your search term.")

    def export_csv(self):
        if not self.current_data:
            self.output_console.append("No data to export. Please perform a search first.")
            return
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save CSV File", f"movies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", 
            "CSV Files (*.csv)"
        )
        if not file_path:
            return
        try:
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([col.capitalize() for col in self.current_columns])
                for row in self.current_data:
                    writer.writerow(row)
            self.output_console.append(f"Data exported successfully to {file_path}")
        except Exception as e:
            self.output_console.append(f"Error exporting CSV: {e}")

    def closeEvent(self, event):
        if self.connection and self.connection.is_connected():
            self.connection.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    dashboard = Dashboard()
    dashboard.show()
    sys.exit(app.exec())
