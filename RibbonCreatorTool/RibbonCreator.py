import os
from importlib import reload
from typing import List, Optional

from PySide2 import QtCore, QtWidgets, QtGui
from PySide2.QtUiTools import QUiLoader
from shiboken2 import wrapInstance

from maya import OpenMayaUI

filePath = __file__

try:
    import RibbonCreatorTool.RibbonCreatorOperations as RibbonGenOp
except ModuleNotFoundError:
    import sys

    currentParent = os.path.abspath(os.path.join(os.path.dirname(filePath), os.pardir))
    sys.path.append(currentParent)
    import RibbonCreatorTool.RibbonCreatorOperations as RibbonGenOp

reload(RibbonGenOp)


def maya_main_window() -> QtWidgets.QWidget:
    main_window = OpenMayaUI.MQtUtil.mainWindow()
    return wrapInstance(int(main_window), QtWidgets.QWidget)


def get_top_widget_by_name(pClass) -> Optional[QtWidgets.QWidget]:
    for widget in maya_window.children():
        if widget.__class__.__name__ == pClass.__name__:
            return widget
    return None


maya_window = maya_main_window()

uiPath = os.path.join(os.path.dirname(filePath), "RibbonCreator.ui")
ToolName = "Ribbon Creator Tool"


class RibbonInterface(QtWidgets.QMainWindow):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, parent=None):
        super(RibbonInterface, self).__init__(parent)
        self.setParent(maya_window)
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle(ToolName)
        self.setObjectName(ToolName)
        self.setContentsMargins(0, 0, 0, 0)

        # setup menu
        menubar = self.menuBar()
        menu = QtWidgets.QMenu('&Help', self)  # title and parent
        qa_about = QtWidgets.QAction("About", self)  # title and parent
        qa_about.triggered.connect(self.help)
        menu.addAction(qa_about)
        menubar.addMenu(menu)

        # setup status bar
        self.info = self.statusBar()
        self.send_message("Ready")

        # setup UI
        ui_file = QtCore.QFile(uiPath)
        ui_file.open(QtCore.QFile.ReadOnly)
        loader = QUiLoader()
        self.ui = loader.load(ui_file, parentWidget=self.centralWidget())
        ui_file.close()
        self.setCentralWidget(self.ui)

        self.rop = RibbonGenOp.RibbonOperations
        self.rop.init_params()
        self.ui.qle_name.setText(self.rop.generate_new_name(self.ribbon_name))
        self.ui.qrb_forward_x.setChecked(True)
        self.ui.qrb_up_y.setChecked(True)
        # self.ui.qgb_name.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        # self.ui.qgb_forward.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        # self.ui.qgb_up.setStyle(QtWidgets.QStyleFactory.create("plastique"))
        self.ui.qtw_tabs.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)

        self.ui.setStyleSheet("""
                    QGroupBox {
                        /*font-weight:bold;*/
                        font-size:12px;
                        color:#EEEEEE;
                    }
                    QTabBar::tab {
                        min-width: 100px;
                        min-height: 10px;
                        border-radius: 0px;
                        padding: 8px;
                        background-color: #373737;
                        color:#EEEEEE;
                    }
                    QTabBar::tab:selected {
                        background-color: #5d5d5d;
                    }
                    QTabBar::tab:hover {
                        background-color: #707070;
                    }
                    QTabWidget::tab-bar {
                        alignment: center;
                    }
                    QTabWidget {
                        /*font-weight:bold;*/
                        font-size:12px;

                    }
                    QTabWidget::pane { 
                        background-color: transparent; 
                    }
                    QPushButton {
                        min-height:20px;
                    }
                    """)

        # Install the event filter to detect mouse enter events
        self.installEventFilter(self)

        # self.update_layout()
        self.connect_buttons()
        self.connect_tooltips()

    @classmethod
    def instance(cls) -> _instance:
        return cls._instance

    @classmethod
    def delete_instance(cls) -> None:
        if cls._instance:
            del cls._instance
            cls._instance = None

    def eventFilter(self, source, event) -> object:
        if event.type() == QtCore.QEvent.Enter:
            self.rop.selection = self.rop.get_selection("joint", True)
            if self.rop.check_ribbon(pCheckAll=True):
                if self.rop.previs_step and self.align:
                    self.update_layout_align()
            else:
                if self.rop.previs_step:
                    self.switch_previs(False, False)
                    self.rop.init_params()
                self.check_ribbon_name()
        return super().eventFilter(source, event)

    def help(self) -> None:
        message = "This tool is provided for free, and helps to build limbs, tentacles, tails...\n" \
                  "Hover checkbox of the interface to get more info about available features.\n\n" \
                  "If you find any bug, please message me at: contact[at]remicuxac.com\n" \
                  "Author: Rémi CUXAC\n" \
                  "https://github.com/RemiCuxac/Ribbon-Creator\n"
        self.show_popup(message, True)

    def send_message(self, pMessage) -> None:
        self.info.showMessage(pMessage)

    @staticmethod
    def show_popup(pMessage, pShowLogo=False) -> None:
        msgBox = QtWidgets.QMessageBox()
        msgBox.setText(pMessage)
        if pShowLogo:
            msgBox.setIconPixmap(QtGui.QPixmap(filePath.replace(".py", ".png")))
        msgBox.setWindowTitle("Result")
        msgBox.exec()

    @property
    def ribbon_name(self) -> str:
        return self.ui.qle_name.text()

    @property
    def forward_vector(self) -> List[int]:
        x = int(self.ui.qrb_forward_x.isChecked())
        y = int(self.ui.qrb_forward_y.isChecked())
        z = int(self.ui.qrb_forward_z.isChecked())
        return [x, y, z]

    @property
    def up_vector(self) -> List[int]:
        x = int(self.ui.qrb_up_x.isChecked())
        y = int(self.ui.qrb_up_y.isChecked())
        z = int(self.ui.qrb_up_z.isChecked())
        return [x, y, z]

    @property
    def main_joint_count(self) -> int:
        return self.ui.qsb_main_joints.value()

    @property
    def roll_joint_count(self) -> int:
        return self.ui.qsb_roll_joints.value()

    @property
    def length(self) -> float:
        return self.ui.qsb_length.value()

    @property
    def create_chain(self) -> bool:
        return self.ui.qcb_chain.isChecked()

    @property
    def create_ik(self) -> bool:
        return self.ui.qcb_ik.isChecked()

    @property
    def create_switch(self) -> bool:
        return self.ui.qcb_switch.isChecked()

    @property
    def create_sine(self) -> bool:
        return self.ui.qcb_sine.isChecked()

    @property
    def create_twist(self) -> bool:
        return self.ui.qcb_twist.isChecked()

    @property
    def create_flare(self) -> bool:
        return self.ui.qcb_flare.isChecked()

    @property
    def create_bend(self) -> bool:
        return self.ui.qcb_bend.isChecked()

    @property
    def create_stretch(self) -> bool:
        return self.ui.qcb_stretch.isChecked()

    @property
    def align(self) -> bool:
        return self.ui.qcb_align.isChecked()

    @property
    def control_joints(self) -> bool:
        return self.ui.qcb_control_joints.isChecked()

    @property
    def skin(self) -> bool:
        return self.ui.qcb_skin.isChecked()

    @property
    def pinch(self) -> bool:
        return self.ui.qcb_pinch.isChecked()

    def check_ribbon_name(self) -> None:
        if self.rop.check_ribbon(self.ribbon_name) and not self.rop.previs_step:
            self.ui.ql_name.setText("\N{Warning Sign} Name")
            self.ui.ql_name.setStyleSheet("background-color: brown")
            self.send_message("Please choose another name.")
            self.ui.ql_name.setToolTip("A ribbon has already this name in the scene.")
            self.ui.qpb_previs.setEnabled(False)
            self.ui.qpb_build.setEnabled(False)
        else:
            self.ui.ql_name.setText("Name")
            self.ui.ql_name.setStyleSheet("")
            self.send_message("Ready")
            self.ui.ql_name.setToolTip(f"{self.ribbon_name} is available.")
            self.ui.qpb_previs.setEnabled(True)
            self.ui.qpb_build.setEnabled(True)

    def update_layout_align(self) -> None:
        self.ui.qs_main_joints.setEnabled(not self.align)
        self.ui.qsb_main_joints.setReadOnly(self.align)
        self.ui.qs_length.setEnabled(not self.align)
        self.ui.qsb_length.setReadOnly(self.align)
        self.ui.qcb_chain.setEnabled(self.control_joints and not self.align)
        self.ui.qcb_control_joints.setEnabled(not self.align)
        self.ui.qcb_ik.setEnabled(self.create_chain and self.control_joints and not self.align)
        self.ui.qcb_switch.setEnabled(self.create_chain and self.control_joints and not self.align)
        self.ui.qcb_stretch.setEnabled(self.create_chain and self.control_joints and not self.align)
        self.ui.qcb_skin.setEnabled(self.control_joints and not self.align)
        if self.align:
            self.rop.align = True
            if self.rop.selection:
                self.rop.distances = self.rop.generate_distance_list(self.rop.selection)
                self.rop.length = self.rop.get_length_from_list(self.rop.distances)
                self.ui.qsb_length.setValue(self.rop.length)
                self.ui.qs_length.setValue(self.rop.length)
                self.ui.qsb_main_joints.setValue(len(self.rop.selection) - 1)
                self.ui.qs_main_joints.setValue(len(self.rop.selection) - 1)
                if self.rop.previs_step and self.rop.check_ribbon():
                    self.update_main_iso()
        else:
            self.rop.align = False
            self.rop.distances = self.length
            if self.rop.previs_step and self.rop.check_ribbon():
                self.update_main_iso()
                # self.rop.reset_control_joints_transform()
        self.rop.end_step(False, True)

    def update_layout_chain(self) -> None:
        self.ui.qcb_ik.setEnabled(self.create_chain and not self.align)
        self.ui.qcb_switch.setEnabled(self.create_chain and not self.align)
        self.ui.qcb_stretch.setEnabled(self.create_chain and not self.align)
        if self.rop.previs_step and self.rop.check_ribbon():
            self.rop.update_control_joint(self.control_joints, self.create_chain, self.skin)
            self.rop.end_step(False, True)

    def update_layout_control_joints(self) -> None:
        self.ui.qcb_ik.setEnabled(self.create_chain and self.control_joints and not self.align)
        self.ui.qcb_switch.setEnabled(self.create_chain and self.control_joints and not self.align)
        self.ui.qcb_stretch.setEnabled(self.create_chain and self.control_joints and not self.align)
        self.ui.qcb_chain.setEnabled(self.control_joints and self.control_joints and not self.align)
        self.ui.qcb_skin.setEnabled(self.control_joints and not self.align)
        if self.rop.previs_step and self.rop.check_ribbon():
            self.rop.update_control_joint(self.control_joints, self.create_chain, self.skin)
            self.rop.end_step(False, True)

    def on_radio_changed_vector(self, qRadio):
        if all([self.ui.qrb_forward_x.isChecked(), self.ui.qrb_up_x.isChecked()]):
            if qRadio == "fx":
                self.ui.qrb_up_y.setChecked(True)
            elif qRadio == "ux":
                self.ui.qrb_forward_y.setChecked(True)
        elif all([self.ui.qrb_forward_y.isChecked(), self.ui.qrb_up_y.isChecked()]):
            if qRadio == "fy":
                self.ui.qrb_up_x.setChecked(True)
            elif qRadio == "uy":
                self.ui.qrb_forward_x.setChecked(True)
        elif all([self.ui.qrb_forward_z.isChecked(), self.ui.qrb_up_z.isChecked()]):
            if qRadio == "fz":
                self.ui.qrb_up_x.setChecked(True)
            elif qRadio == "uz":
                self.ui.qrb_forward_x.setChecked(True)
        self.rop.store_vectors(self.forward_vector, self.up_vector)
        self.update_main_iso()

    def on_slider_moved_main_joints(self) -> None:
        self.ui.qsb_main_joints.setValue(self.ui.qs_main_joints.sliderPosition())
        self.update_main_iso()

    def on_value_changed_main_joints(self, pValue) -> None:
        if pValue:
            self.ui.qs_main_joints.setValue(pValue)
            self.update_main_iso()

    def on_slider_moved_roll_joints(self) -> None:
        self.ui.qsb_roll_joints.setValue(self.ui.qs_roll_joints.sliderPosition())
        self.update_roll_iso()

    def on_value_changed_roll_joints(self, pValue) -> None:
        self.ui.qs_roll_joints.setValue(pValue)
        self.update_roll_iso()

    def on_slider_moved_length(self) -> None:
        self.ui.qsb_length.setValue(self.ui.qs_length.sliderPosition() / 10)
        self.update_length()

    def on_value_changed_length(self, pValue) -> None:
        if pValue:
            self.ui.qs_length.setValue(int(pValue) * 10)
            self.update_length()

    def connect_buttons(self) -> None:
        self.ui.qle_name.textChanged.connect(self.check_ribbon_name)

        self.ui.qrb_forward_x.toggled.connect(lambda axis: self.on_radio_changed_vector("fx"))
        self.ui.qrb_forward_y.toggled.connect(lambda axis: self.on_radio_changed_vector("fy"))
        self.ui.qrb_forward_z.toggled.connect(lambda axis: self.on_radio_changed_vector("fz"))
        self.ui.qrb_up_x.toggled.connect(lambda axis: self.on_radio_changed_vector("ux"))
        self.ui.qrb_up_y.toggled.connect(lambda axis: self.on_radio_changed_vector("uy"))
        self.ui.qrb_up_z.toggled.connect(lambda axis: self.on_radio_changed_vector("uz"))

        self.ui.qpb_previs.clicked.connect(self.previs_ribbon)
        self.ui.qpb_build.clicked.connect(self.build_ribbon)

        self.ui.qs_main_joints.sliderMoved.connect(self.on_slider_moved_main_joints)
        self.ui.qs_main_joints.sliderPressed.connect(self.on_slider_moved_main_joints)

        self.ui.qs_roll_joints.sliderMoved.connect(self.on_slider_moved_roll_joints)
        self.ui.qs_roll_joints.sliderPressed.connect(self.on_slider_moved_roll_joints)

        self.ui.qs_length.sliderMoved.connect(self.on_slider_moved_length)
        self.ui.qs_length.sliderPressed.connect(self.on_slider_moved_length)

        self.ui.qsb_main_joints.valueChanged.connect(self.on_value_changed_main_joints)
        self.ui.qsb_roll_joints.valueChanged.connect(self.on_value_changed_roll_joints)
        self.ui.qsb_length.valueChanged.connect(self.on_value_changed_length)

        self.ui.qcb_align.toggled.connect(self.update_layout_align)
        self.ui.qcb_chain.toggled.connect(self.update_layout_chain)

        self.ui.qcb_control_joints.toggled.connect(self.update_layout_control_joints)
        self.ui.qcb_pinch.toggled.connect(self.update_main_iso)
        self.ui.qcb_skin.toggled.connect(self.update_skin)

    def connect_tooltips(self) -> None:
        self.ui.qcb_align.setStatusTip("Select the chain from first joint to last joint, then check this button.")
        self.ui.qcb_pinch.setStatusTip("This will snap isoparms of the ribbon to main joints.")
        self.ui.qcb_skin.setStatusTip("This will skin control joints to the ribbon")
        self.ui.qcb_chain.setStatusTip("This will make a leaf setup, so roll joints will be parented to main joints")
        self.ui.qcb_control_joints.setStatusTip("This will create control joints.")
        self.ui.qcb_flare.setStatusTip("This will create a flare deformer.")
        self.ui.qcb_sine.setStatusTip("This will create a sine deformer.")
        self.ui.qcb_twist.setStatusTip("This will create a twist deformer.")

    def closeEvent(self, event) -> None:
        """
        on close, this closes the ui
        """
        self.rop.init_params()
        self.close()

    def switch_previs(self, pPrevisOn: bool, pSendMessage: bool = True) -> None:
        self.ui.qgb_name.setEnabled(not pPrevisOn)
        message = "Preview active. You can now customize parameters." if pPrevisOn else "Ready"
        qpb_stylesSheet = "background-color: seagreen" if pPrevisOn else ""
        qgb_styleSheet = "#qgb_dynamic { border: 1px solid seagreen;padding: 14 1 px}" if pPrevisOn else ""
        self.ui.qpb_previs.setStyleSheet(qpb_stylesSheet)
        self.ui.qgb_dynamic.setStyleSheet(qgb_styleSheet)
        if pSendMessage:
            self.send_message(message)

    def previs_ribbon(self) -> None:
        if not self.rop.previs_step:
            message = self.rop.previs_ribbon(self.ribbon_name, self.forward_vector, self.up_vector, self.length,
                                             self.main_joint_count, self.roll_joint_count, self.control_joints,
                                             self.create_chain, self.skin, self.pinch)
            self.show_popup(message)
        else:
            self.rop.delete_ribbon(self.ribbon_name)
        self.switch_previs(self.rop.previs_step)

    def build_ribbon(self) -> None:
        ribbonName = self.ribbon_name
        message = self.rop.build_ribbon(ribbonName, self.forward_vector, self.up_vector, self.length,
                                        self.main_joint_count, self.roll_joint_count, self.control_joints,
                                        self.create_chain, self.skin, pPinch=self.pinch, bend=self.create_bend,
                                        sine=self.create_sine, twist=self.create_twist, flare=self.create_flare)
        self.send_message("Done !")
        self.ui.qle_name.setText(self.rop.generate_new_name(ribbonName))
        self.show_popup(message)
        self.switch_previs(self.rop.previs_step)

    def update_length(self) -> None:
        if self.rop.previs_step and self.rop.check_ribbon():
            self.rop.update_length(self.length)
            self.rop.end_step(False, True)

    def update_main_iso(self) -> None:
        if self.rop.previs_step and self.rop.check_ribbon():
            self.rop.update_main_iso(self.main_joint_count, self.roll_joint_count,
                                     self.control_joints, self.create_chain, self.skin, self.pinch)

    def update_roll_iso(self) -> None:
        if self.rop.previs_step and self.rop.check_ribbon():
            self.rop.update_roll_iso(self.roll_joint_count, self.create_chain, self.control_joints, self.skin)

    def update_skin(self) -> None:
        if self.rop.previs_step and self.rop.check_ribbon():
            if self.skin:
                self.rop.update_skin()
            else:
                self.rop.unbind_skin(self.rop.ribbon)
            self.rop.end_step(False, True)


def show_ui():
    # because the tool is parented to maya window:
    # if cmds.window(ToolName, exists=Ture):
    #     cmds.deleteUI(ToolName, window=True)
    # I can also use :
    ui = get_top_widget_by_name(RibbonInterface)
    if ui:
        ui.close()
        ui.deleteLater()

    RibbonInterface.delete_instance()  # clear instance before running it, in case I would like to run it more than once

    ui = RibbonInterface(maya_window)
    ui.show()


if __name__ == '__main__':
    show_ui()

# Naming rules updates :
# TODO: I should add a namespace like "Ribbon:" and when clicking "build", "Ribbon:" becomes "Ribbon_".
#  So the nurb is named like "Ribbon:Nurb" and will be named as "Ribbon_Nurb" in the end.
#  Right before building, the script should check if a ribbon is already named like "Ribbon_Nurb"
#  and create a popup to ask users to not use the name Ribbon.
#  So if the user rename the ribbon after pre-build, it could be easy to rename all the nodes,
#  I just have to update the namespace.
# TODO: I should add the prefix "Ribbon" on everything I create, even on properties of sine, twist, etc.
#  note: I don't need to add namespace on properties.
# TODO: maybe change the naming of controlers and joints ? Because almost all components are named like {RibbonName}...
#  but controlers, joints, control joints and locators are named like ctrl_{RibbonName}_...
#  So maybe it would be better to be named like {RibbonName}_ctrl_...
#  it could break a standard naming convention of a rig, but the user is free to rename himself everything..

# Rolls updates :
# TODO: constraint rollIsoPos at equidistant position between each main joint control
#  That will allows user to move control joints and keeping same distances. Useful for stretch.

# Pinch updates :
# TODO : instead of using multiple knots for the same isoparms,
#  we could also create a new insertKnotSurface at pIsoPos positions.
#  That way we could delete the modifier easier and update the skinning rather than rebuilding control joints
# TODO: instead of using nbKnots for pinch, it could be nice to add knots before and after mainIsoparms
#  and control them with a factor of pinch from the interface

# Others:
# TODO: It would be great to have an option to use custom control joints.
#  But it should check if the selected control joints can be moved to center of world for skinning step, and moved back
# TODO: add a tab where I would be able to manage things like connect deformers to a network node,
#  match ribbon to selected, rename ribbon etc.

# TODO: add a feature to use an existing ribbon. It will reactivate the switch instead of rebuild all the ribbon
#  It will also update lenght, main joints and roll joints interface from the selected ribbon.
#  It could be dependant of a checkbox or from two QLineEdit where I store the selected ribbon and the selected setup
