from PySide6.QtWidgets import (
    QLabel, QWidget,
    QHBoxLayout, QVBoxLayout,
    QCheckBox, QDoubleSpinBox
)
from PySide6.QtCore import Qt, Signal
from dataclasses import dataclass
from numpy import inf


@dataclass(frozen=True)
class TabState:
    """
    A class to hold data representing a state of a ConstraintTab.
    """

    integral: bool
    minimized: bool
    maximized: bool
    default_lower_bound: bool
    default_upper_bound: bool
    lower_bound: float
    upper_bound: float


class ConstraintTab(QWidget):
    """
    An extending class of QWidget that allows a user to define the constraints on a variable when
    attempting to find a solution to the system.
    """

    state_changed = Signal(TabState)

    def __init__(self, is_all_tab: bool = False) -> None:
        """
        Initializes a new ConstraintTab by initializing its QWidgets and QLayouts, and connecting
        its Signals and Slots.

        :param is_all_tab: A bool which, when True, treats this ConstraintTab as an `all tab`,
            which, when changed, changes all other ConstraintTabs to have the same state
        """

        super().__init__()
        self._init_ui()
        self._init_signals(is_all_tab)

    def _init_ui(self) -> None:
        """
        Initializes the QWidgets and QLayouts of this ConstraintTab.
        """

        main_layout = QHBoxLayout(self)
        optimize_layout = QVBoxLayout()
        lower_bound_layout = QVBoxLayout()
        upper_bound_layout = QVBoxLayout()

        self._integer = QCheckBox("Integer")

        self._minimize = QCheckBox("Minimize")
        self._maximize = QCheckBox("Maximize")
        optimize_layout.addWidget(self._minimize)
        optimize_layout.addWidget(self._maximize)

        self._default_lower_bound = QCheckBox("Default (-inf)")
        self._lower_bound = QDoubleSpinBox()
        self._lower_bound.setRange(-inf, inf)
        self._lower_bound.setValue(0)
        lower_bound_layout.addWidget(self._default_lower_bound)
        lower_bound_layout.addWidget(self._lower_bound)

        self._default_upper_bound = QCheckBox("Default (inf)")
        self._upper_bound = QDoubleSpinBox()
        self._upper_bound.setRange(-inf, inf)
        self._upper_bound.setValue(0)
        upper_bound_layout.addWidget(self._default_upper_bound)
        upper_bound_layout.addWidget(self._upper_bound)

        main_layout.addWidget(self._integer)
        main_layout.addLayout(optimize_layout)
        main_layout.addWidget(QLabel("Lower Bound",
                                     alignment=Qt.AlignmentFlag.AlignRight |
                                               Qt.AlignmentFlag.AlignVCenter))
        main_layout.addLayout(lower_bound_layout)
        main_layout.addWidget(QLabel("Upper Bound",
                                     alignment=Qt.AlignmentFlag.AlignRight |
                                               Qt.AlignmentFlag.AlignVCenter))
        main_layout.addLayout(upper_bound_layout)

    def _init_signals(self, is_all_tab: bool) -> None:
        """
        Connects the Signals and Slots of this ConstraintTab.

        :param is_all_tab: A bool which, when True, connects the extra Signal and Slot needed to
            treat this ConstraintTab as an `all tab`
        """

        if is_all_tab:
            on_state_changed = lambda: self.state_changed.emit(self.get_state())

            for widget in (self._integer, self._minimize, self._maximize, self._default_lower_bound,
                           self._default_upper_bound):
                widget.toggled.connect(on_state_changed)

            self._lower_bound.valueChanged.connect(on_state_changed)
            self._upper_bound.valueChanged.connect(on_state_changed)

        self._minimize.toggled.connect(self._on_minimize_toggled)
        self._maximize.toggled.connect(self._on_maximize_toggled)

        self._default_lower_bound.toggled.connect(self._on_default_lower_bound_toggled)
        self._default_lower_bound.toggle()

        self._default_upper_bound.toggled.connect(self._on_default_upper_bound_toggled)
        self._default_upper_bound.toggle()

    def _on_minimize_toggled(self, checked: bool) -> None:
        """
        Ensures that the two optimization QCheckboxes are never simultaneously enabled.

        :param checked: The boolean state of the `minimize` QCheckbox
        """

        self._maximize.setEnabled(not checked)

    def _on_maximize_toggled(self, checked: bool) -> None:
        """
        Ensures that the two optimization QCheckboxes are never simultaneously enabled.

        :param checked: The boolean state of the `maximize` QCheckbox
        """

        self._minimize.setEnabled(not checked)

    def _on_default_lower_bound_toggled(self, checked: bool) -> None:
        """
        Ensures that the two lower-bounds QWidgets are never simultaneously enabled.

        :param checked: The boolean state of the `default_lower_bound` QCheckbox
        """

        self._lower_bound.setEnabled(not checked)

    def _on_default_upper_bound_toggled(self, checked: bool) -> None:
        """
        Ensures that the two upper-bounds QWidgets are never simultaneously enabled.

        :param checked: The boolean state of the `default_upper_bound` QCheckbox
        """

        self._upper_bound.setEnabled(not checked)

    def get_state(self) -> TabState:
        """
        Returns the current state of this ConstraintTab.

        :return: This ConstraintTab's current state
        """

        return TabState(self._integer.isChecked(), self._minimize.isChecked(),
                        self._maximize.isChecked(), self._default_lower_bound.isChecked(),
                        self._default_upper_bound.isChecked(), self._lower_bound.value(),
                        self._upper_bound.value())

    def set_state(self, tab_state: TabState) -> None:
        """
        Sets the current state of this ConstraintTab to the provided one.

        :param tab_state: The state to set this ConstraintTab to
        """

        self._integer.setChecked(tab_state.integral)
        self._minimize.setChecked(tab_state.minimized)
        self._maximize.setChecked(tab_state.maximized)
        self._default_lower_bound.setChecked(tab_state.default_lower_bound)
        self._default_upper_bound.setChecked(tab_state.default_upper_bound)
        self._lower_bound.setValue(tab_state.lower_bound)
        self._upper_bound.setValue(tab_state.upper_bound)