from PySide6.QtWidgets import (
    QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem,
    QPushButton, QTabWidget, QTextEdit
)
from solver import Constraints, System, get_solution
from constraint_tab import ConstraintTab, TabState
from PySide6.QtGui import QIcon
from PySide6.QtCore import Qt
from pathlib import Path
from csv import reader
import numpy as np

a = [1,2]



def _new_centered_item(text: str) -> QTableWidgetItem:
    """
    Initializes and returns new QTableWidgetItem that is centered.

    :param text: The text that thew new QTableWidgetItem will display
    :return: A new centered QTableWidgetItem that displays the provided text
    """

    item = QTableWidgetItem(text)
    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)

    return item


class SolverWindow(QMainWindow):
    """
    An extending class of QMainWindow that defines the main, and only window, of this GUI. It allows
    a user to input a linear system of equations into a QTableWidget and define constraints for each
    variable in the system.
    """

    def __init__(self, table_path: Path | None, icon_path: str, default_rows: int = 3,
                 default_cols: int = 4) -> None:
        """
        Initializes a new SolverWindow by initializing its QWidgets and QLayouts, and connecting its
        Signals and Slots.

        :param table_path: The optional path to a file which could be used to initialize the
            QTableWidget
        :param icon_path: The filename of this SolverWindow's icon
        :param default_rows: The number of rows to initialize the QTableWidget with, if `table_path`
            is not provided
        :param default_cols: The number of columns to initialize the QTableWidget with, if
            `table_path` is not provided
        """

        super().__init__()
        self.setWindowTitle("Constraint Satisfaction Solver")
        self.setWindowIcon(QIcon(icon_path))

        table = _load_csv(table_path) if table_path else None

        if table is not None:
            self._rows = table.shape[0]
            self._cols = table.shape[1]
        else:
            self._rows = default_rows
            self._cols = default_cols

        self._init_ui(table)

    def _init_ui(self, table: np.ndarray[tuple[int, int], np.float64] | None) -> None:
        """
        Initializes the QWidgets and QLayouts for this SolverWindow.

        :param table: The optional array which could be used to initialize the QTableWidget
        """

        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self._init_table(table)
        main_layout.addWidget(self._table)

        main_layout.addLayout(self._new_table_controls())
        self._table.selectionModel().selectionChanged.connect(self._update_removal_buttons)

        self._init_tabs()
        main_layout.addWidget(self._tabs)

        solve_btn = QPushButton("Solve")
        solve_btn.clicked.connect(self._solve)
        main_layout.addWidget(solve_btn)

        self._output_field = QTextEdit(readOnly=True)
        main_layout.addWidget(self._output_field)

    def _init_table(self, table: np.ndarray[tuple[int, int], np.float64] | None) -> None:
        """
        Initializes the QTableWidget for this SolverWindow.

        :param table: The optional array which could be used to initialize the QTableWidget
        """

        self._table = QTableWidget(self._rows, self._cols)
        self._update_headers()

        if table is not None:
            for (row, col), value in np.ndenumerate(table):
                self._table.setItem(row, col, _new_centered_item(str(value)))
        else:
            for row in range(self._rows):
                self._fill_empty_row(row)

    def _update_headers(self) -> None:
        """
        Updates the headers of this SolverWindow's QTableWidget.
        """

        self._table.setHorizontalHeaderLabels([f"x{i}" for i in range(self._cols - 1)] + ["b"])

    def _fill_empty_row(self, row: int) -> None:
        """
        Fills the provided row of this SolverWindow's QTableWidget with '0'.

        :param row: The row to fill
        """

        for col in range(self._cols):
            self._table.setItem(row, col, _new_centered_item("0"))

    def _new_table_controls(self) -> QHBoxLayout:
        """
        Initializes and returns the QLayout, and QWidgets and QLayouts within it, that support the
        user in managing this SolverWindow's QTableWidget.

        :return: The QLayout which supports the user in managing this SolverWindow's QTableWidget
        """

        layout = QHBoxLayout()

        add_row_btn = QPushButton("+ Row")
        add_row_btn.clicked.connect(self._on_add_row)
        layout.addWidget(add_row_btn)

        self._remove_row_btn = QPushButton("- Row")
        self._remove_row_btn.clicked.connect(self._on_remove_row)
        self._remove_row_btn.setDisabled(True)
        layout.addWidget(self._remove_row_btn)

        add_col_btn = QPushButton("+ Column")
        add_col_btn.clicked.connect(self._on_add_column)
        layout.addWidget(add_col_btn)

        self._remove_col_btn = QPushButton("- Column")
        self._remove_col_btn.clicked.connect(self._on_remove_column)
        self._remove_col_btn.setDisabled(True)
        layout.addWidget(self._remove_col_btn)

        return layout

    def _on_add_row(self) -> None:
        """
        Adds a new empty row to this SolverWindow's QTableWidget.
        """

        self._table.insertRow(self._rows)
        self._fill_empty_row(self._rows)
        self._rows += 1

    def _on_remove_row(self) -> None:
        """
        Removes the selected rows from this SolverWindow's QTableWidget.
        """

        selected_rows = self._table.selectionModel().selectedRows()
        num_selected = len(selected_rows)

        for row_idx in sorted((row.row() for row in selected_rows), reverse=True):
            self._table.removeRow(row_idx)

        self._rows -= num_selected

    def _on_add_column(self) -> None:
        """
        Adds a new empty column to this SolverWindow's QTableWidget and a new related ConstraintTab.
        """

        self._table.insertColumn(self._cols - 1)
        self._fill_empty_col(self._cols - 1)

        self._cols += 1
        self._update_headers()

        new_tab = ConstraintTab()
        self._tabs.insertTab(self._cols - 1, new_tab, f'x{self._cols - 2}')
        new_tab.set_state(self._all_tab.get_state())

    def _fill_empty_col(self, col: int) -> None:
        """
        Fills the provided column of this SolverWindow's QTableWidget with '0'.

        :param col: The column to fill
        """

        for row in range(self._rows):
            self._table.setItem(row, col, _new_centered_item("0"))

    def _on_remove_column(self) -> None:
        """
        Removes the selected columns from this SolverWindow's QTableWidget and the related
        ConstraintTabs.
        """

        cols = sorted([col.column() for col in self._table.selectionModel().selectedColumns()],
                      reverse=True)
        num_selected = len(cols)

        for col_idx in cols:
            self._table.removeColumn(col_idx)
            self._tabs.removeTab(col_idx + 1)

        self._cols -= num_selected
        self._update_headers()
        for i in range(1, self._cols):
            self._tabs.setTabText(i, f"x{i - 1}")

    def _update_removal_buttons(self) -> None:
        """
        Determines the appropriate status of the `remove_row_btn` and `remove_col_btn` QPushButtons
        based off what is currently selected in this SolverWindow's QTableWidget.
        """

        selection = self._table.selectionModel()

        valid_row_quantity = 0 < len(selection.selectedRows()) < self._rows
        self._remove_row_btn.setEnabled(valid_row_quantity)

        valid_col_quantity = 0 < len(selection.selectedColumns()) < self._cols - 1
        selected_target = self._cols - 1 in (col.column() for col in selection.selectedColumns())
        self._remove_col_btn.setEnabled(valid_col_quantity and not selected_target)

    def _init_tabs(self) -> None:
        """
        Initializes this SolverWindow's QTabWidget, and ConstraintTabs within it, to be used to
        constrain the solution space for certain variables.
        """

        self._tabs = QTabWidget()

        self._all_tab = ConstraintTab(is_all_tab=True)
        self._all_tab.state_changed.connect(self._on_all_tab_changed)
        self._tabs.addTab(self._all_tab, "all")

        for i in range(self._cols - 1):
            self._tabs.addTab(ConstraintTab(), f"x{i}")

    def _on_all_tab_changed(self, tab_state: TabState) -> None:
        """
        Updates all ConstraintTabs within this SolverWindow's QTabWidget to have the same state as
        the newly changed `all tab`.

        :param tab_state: The state that the `all tab` just entered
        """

        for i in range(1, self._cols):
            self._tabs.widget(i).set_state(tab_state)

    def _solve(self) -> None:
        """
        Collects the information from this SolverWindow's QTableWidget and ConstraintTabs to then
        send out to the solver. The result the solver returns will then be printed to the output
        field.
        """

        try:
            system = self._get_system()
        except ValueError:
            self._output_field.setText("Please input only numbers into the table.")
        else:
            constraints = self._get_all_constraints()

            if any(lower > upper for lower, upper in
                   zip(constraints.lower_bounds, constraints.upper_bounds)):
                self._output_field.setText("Cannot have a lower bound higher than an upper bound.")
            else:
                solution = get_solution(system, constraints)

                if solution.array is not None:
                    self._output_field.setText(solution.message)
                    self._output_field.append(
                        ", ".join(f'x{i} = {val:.2f}' for i, val in enumerate(solution.array)))
                else:
                    self._output_field.setText(solution.message)

    def _get_system(self) -> System:
        """
        Collects the information from this SolverWindow's QTableWidget into two arrays, the
        variables and the targets, comprising the system for which to find a solution.

        :return: The system of variables and targets
        :except ValueError: Thrown if a non-numeric text is found within the QTableWidget
        """

        variables = np.empty((self._rows, self._cols - 1), dtype=np.float64)
        targets = np.empty(self._rows, dtype=np.float64)

        for row in range(self._rows):
            for col in range(self._cols - 1):
                variables[row, col] = np.float64(self._table.item(row, col).text())
            targets[row] = np.float64(self._table.item(row, self._cols - 1).text())

        return System(variables, targets)

    def _get_all_constraints(self) -> Constraints:
        """
        Collects the constraints from all of this SolverWindow's variable-representing
        ConstraintTabs into multiple arrays, comprising the constraints used to limit the solution
        space.

        :return: The collection of constraints from this SolverWindow's ConstraintTabs
        """

        integrality = np.empty(self._cols - 1, dtype=np.bool)
        minimization = np.empty_like(integrality)
        maximization = np.empty_like(integrality)
        lower_bounds = np.empty_like(integrality, dtype=np.float64)
        upper_bounds = np.empty_like(lower_bounds)

        for i in range(self._cols - 1):
            tab_state = self._tabs.widget(i + 1).get_state()
            integrality[i] = tab_state.integral
            minimization[i] = tab_state.minimized
            maximization[i] = tab_state.maximized
            lower_bounds[i] = -np.inf if tab_state.default_lower_bound else tab_state.lower_bound
            upper_bounds[i] = np.inf if tab_state.default_upper_bound else tab_state.upper_bound

        return Constraints(integrality, minimization, maximization, lower_bounds, upper_bounds)