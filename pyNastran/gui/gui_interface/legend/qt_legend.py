"""
defines:
 - AnimationWindow
 - LegendPropertiesWindow
"""
from __future__ import print_function
import os
from six import integer_types
import numpy as np

from pyNastran.gui.qt_version import qt_version
if qt_version == 4:
    from PyQt4 import QtCore#, QtGui
    from PyQt4.QtGui import (
        QApplication, QLabel, QPushButton, QLineEdit, QComboBox, QWidget, QRadioButton,
        QButtonGroup, QGridLayout, QHBoxLayout, QVBoxLayout, QSpinBox, QDoubleSpinBox, QCheckBox)
elif qt_version == 5:
    #from PyQt5 import QtCore, QtGui
    from PyQt5.QtWidgets import (
        QApplication, QLabel, QPushButton, QLineEdit, QComboBox, QWidget, QRadioButton,
        QButtonGroup, QGridLayout, QHBoxLayout, QVBoxLayout, QSpinBox, QDoubleSpinBox, QCheckBox)
elif qt_version == 'pyside':
    from PySide import QtCore#, QtGui
    from PySide.QtGui import (
        QApplication, QLabel, QPushButton, QLineEdit, QComboBox, QWidget, QRadioButton,
        QButtonGroup, QGridLayout, QHBoxLayout, QVBoxLayout, QSpinBox, QDoubleSpinBox, QCheckBox)
else:
    raise NotImplementedError('qt_version = %r' % qt_version)

#from pyNastran.gui.qt_files.menu_utils import eval_float_from_string
from pyNastran.gui.colormaps import colormap_keys

from pyNastran.gui.gui_interface.common import PyDialog
from pyNastran.gui.gui_utils import open_directory_dialog


class AnimationWindow(PyDialog):
    """
    +-------------------+
    | Animation         |
    +-------------------------+
    | scale   ______  Default |
    | time    ______  Default |
    |                         |
    | nframes ______  Default |
    | resolu. ______  Default |
    | Dir     ______  Browse  |
    | iFrame  ______          |
    |                         |
    | Animations:             |
    | o Scale, Phase, Time    |  # TODO: add time
    |                         |
    | x delete images         |
    | x repeat                |  # TODO: change to an integer
    | x make gif              |
    |                         |
    |      Step, RunAll       |
    |         Close           |
    +-------------------------+

    TODO: add key-frame support
    """
    def __init__(self, data, win_parent=None):
        PyDialog.__init__(self, data, win_parent)
        self.istep = 0

        self._updated_animation = False
        self._icase = data['icase']
        self._default_name = data['name']
        self._default_time = data['time']
        self._default_fps = data['frames/sec']
        self._default_resolution = data['resolution']

        self._scale = data['scale']
        self._default_scale = data['default_scale']
        self._default_is_scale = data['is_scale']

        self._phase = data['phase']
        self._default_phase = data['default_phase']

        self._default_dirname = data['dirname']
        self._default_gif_name = os.path.join(self._default_dirname, data['name'] + '.gif')

        self.setWindowTitle('Animate Model')
        self.create_widgets()
        self.create_layout()
        self.set_connections()
        self.win_parent.is_animate_open = True

    def create_widgets(self):
        """creates the menu objects"""
        self.scale = QLabel("Scale:")
        self.scale_edit = QLineEdit(str(self._scale))
        self.scale_button = QPushButton("Default")

        self.time = QLabel("Total Time (sec):")
        self.time_edit = QDoubleSpinBox(self)
        self.time_edit.setValue(self._default_time)
        self.time_edit.setRange(0.1, 10.0)
        self.time_edit.setDecimals(1)
        self.time_edit.setSingleStep(0.1)
        self.time_button = QPushButton("Default")

        self.fps = QLabel("Frames/Second:")
        self.fps_edit = QSpinBox(self)
        self.fps_edit.setRange(10, 60)
        self.fps_edit.setSingleStep(1)
        self.fps_edit.setValue(self._default_fps)
        self.fps_button = QPushButton("Default")

        self.resolution = QLabel("Resolution Scale:")
        self.resolution_edit = QSpinBox(self)
        self.resolution_edit.setRange(1, 5)
        self.resolution_edit.setSingleStep(1)
        self.resolution_edit.setValue(self._default_resolution)
        self.resolution_button = QPushButton("Default")

        #self.browse = QLabel("Animation File:")
        self.browse = QLabel("Output Directory:")
        self.browse_edit = QLineEdit(str(self._default_dirname))
        self.browse_button = QPushButton("Browse")

        self.gif = QLabel("Gif Filename:")
        self.gif_edit = QLineEdit(str(self._default_name + '.gif'))
        self.gif_button = QPushButton("Default")

        # scale / phase
        self.animate_scale_radio = QRadioButton("Animate Scale")
        self.animate_phase_radio = QRadioButton("Animate Phase")
        self.animate_time_radio = QRadioButton("Animate Time")
        self.animate_scale_radio.setChecked(self._default_is_scale)
        self.animate_phase_radio.setChecked(not self._default_is_scale)
        self.animate_time_radio.setChecked(False)
        if self._default_phase is None:
            self.animate_phase_radio.setDisabled(True)

        self.animate_time_radio.setDisabled(True)
        widget = QWidget(self)
        horizontal_vertical_group = QButtonGroup(widget)
        horizontal_vertical_group.addButton(self.animate_scale_radio)
        horizontal_vertical_group.addButton(self.animate_phase_radio)
        horizontal_vertical_group.addButton(self.animate_time_radio)

        # one / two sided
        self.onesided_radio = QRadioButton("One Sided")
        self.twosided_radio = QRadioButton("Two Sided")
        if self._default_phase is None:
            self.onesided_radio.setChecked(False)
            self.twosided_radio.setChecked(True)
        else:
            self.onesided_radio.setChecked(True)
            self.twosided_radio.setChecked(False)
        widget = QWidget(self)
        horizontal_vertical_group = QButtonGroup(widget)
        horizontal_vertical_group.addButton(self.onesided_radio)
        horizontal_vertical_group.addButton(self.twosided_radio)

        # delete images when finished
        self.delete_images_checkbox = QCheckBox("Delete images when finished?")
        self.delete_images_checkbox.setChecked(True)

        # endless loop
        self.repeat_checkbox = QCheckBox("Repeat?")
        self.repeat_checkbox.setChecked(True)

        # endless loop
        self.make_gif_checkbox = QCheckBox("Make Gif?")
        self.make_gif_checkbox.setChecked(True)

        # bottom buttons
        self.step_button = QPushButton("Step")
        self.run_button = QPushButton("Run All")

        #self.apply_button = QPushButton("Apply")
        #self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Close")

    def set_connections(self):
        """creates button actions"""
        self.scale_button.clicked.connect(self.on_default_scale)
        self.time_button.clicked.connect(self.on_default_time)

        self.fps_button.clicked.connect(self.on_default_fps)
        self.resolution_button.clicked.connect(self.on_default_resolution)
        self.browse_button.clicked.connect(self.on_browse)
        self.gif_button.clicked.connect(self.on_default_name)

        self.step_button.clicked.connect(self.on_step)
        self.run_button.clicked.connect(self.on_run)

        #self.apply_button.clicked.connect(self.on_apply)
        #self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.on_cancel)

    def on_browse(self):
        dirname = open_directory_dialog(self, 'Select a Directory')
        if not dirname:
            return
        self.browse_edit.setText(dirname)

    def on_default_name(self):
        self.gif_edit.setText(self._default_name + '.gif')

    def on_default_scale(self):
        self.scale_edit.setText(str(self._default_scale))
        self.scale_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_time(self):
        self.time_edit.setValue(self._default_time)

    def on_default_fps(self):
        self.fps_edit.setValue(self._default_fps)

    def on_default_resolution(self):
        self.resolution_edit.setValue(self._default_resolution)

    def create_layout(self):
        """displays the menu objects"""
        grid = QGridLayout()

        grid.addWidget(self.scale, 0, 0)
        grid.addWidget(self.scale_edit, 0, 1)
        grid.addWidget(self.scale_button, 0, 2)

        grid.addWidget(self.time, 1, 0)
        grid.addWidget(self.time_edit, 1, 1)
        grid.addWidget(self.time_button, 1, 2)

        # spacer
        spacer = QLabel('')
        #grid.addWidget(spacer, 2, 0)

        grid.addWidget(self.fps, 3, 0)
        grid.addWidget(self.fps_edit, 3, 1)
        grid.addWidget(self.fps_button, 3, 2)

        grid.addWidget(self.resolution, 4, 0)
        grid.addWidget(self.resolution_edit, 4, 1)
        grid.addWidget(self.resolution_button, 4, 2)

        grid.addWidget(self.browse, 5, 0)
        grid.addWidget(self.browse_edit, 5, 1)
        grid.addWidget(self.browse_button, 5, 2)

        grid.addWidget(self.gif, 6, 0)
        grid.addWidget(self.gif_edit, 6, 1)
        grid.addWidget(self.gif_button, 6, 2)

        grid.addWidget(spacer, 7, 0)

        #grid2 = QGridLayout()
        grid.addWidget(self.animate_scale_radio, 8, 0)
        grid.addWidget(self.animate_phase_radio, 8, 1)
        grid.addWidget(self.animate_time_radio, 8, 2)

        grid.addWidget(self.twosided_radio, 9, 0)
        grid.addWidget(self.onesided_radio, 9, 1)

        grid.addWidget(self.repeat_checkbox, 10, 0)
        grid.addWidget(self.delete_images_checkbox, 10, 1)
        grid.addWidget(self.make_gif_checkbox, 10, 2)

        grid.addWidget(spacer, 11, 0)

        #grid.addWidget(self.scale_radio, 6, 0)
        #grid.addWidget(self.phase_radio, 6, 1)
        #grid.addWidget(self.delete_images_checkbox, 6, 0)

        # bottom buttons
        step_run_box = QHBoxLayout()
        step_run_box.addWidget(self.step_button)
        step_run_box.addWidget(self.run_button)

        ok_cancel_box = QHBoxLayout()
        #ok_cancel_box.addWidget(self.apply_button)
        #ok_cancel_box.addWidget(self.ok_button)
        ok_cancel_box.addWidget(self.cancel_button)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        #vbox.addLayout(checkboxes)
        #vbox.addLayout(grid2)
        vbox.addStretch()
        vbox.addLayout(step_run_box)
        vbox.addLayout(ok_cancel_box)
        self.setLayout(vbox)

    def on_step(self):
        """click the Step button"""
        passed, validate_out = self.on_validate()
        if passed:
            self._make_gif(validate_out, istep=self.istep)
            self.istep += 1

    def on_run(self):
        """click the Run button"""
        self.istep = 0
        passed, validate_out = self.on_validate()
        if passed:
            self._make_gif(validate_out, istep=None)
        return passed

    def _make_gif(self, validate_out, istep=None):
        """interface for making the gif"""
        scale, time, fps, output_dir, gifbase = validate_out
        if gifbase.lower().endswith('.gif'):
            gifbase = gifbase[:-3]
        gif_filename = os.path.join(output_dir, gifbase + '.gif')

        animate_scale = self.animate_scale_radio.isChecked()
        animate_phase = self.animate_phase_radio.isChecked()
        animate_time = self.animate_time_radio.isChecked()
        delete_images = self.delete_images_checkbox.isChecked()
        make_gif = self.make_gif_checkbox.isChecked()
        onesided = self.onesided_radio.isChecked()
        nrepeat = self.repeat_checkbox.isChecked()  # TODO: change this to an integer

        #self.out_data['is_shown'] = self.show_radio.isChecked()
        analysis_time = self.get_analysis_time(time, onesided)


        nframes = int(analysis_time * fps)
        scales = None
        phases = None
        if animate_scale:
            # TODO: we could start from 0 deflection, but that's more work
            # TODO: we could do a sine wave, but again, more work
            scales = np.linspace(-scale, scale, num=nframes, endpoint=True)
            isteps = np.linspace(0, nframes, endpoint=True)
            phases = [None] * nframes
        elif animate_phase:
            # animate phase
            phases = np.linspace(0., 360, num=nframes, endpoint=False)
            isteps = np.linspace(0, nframes, endpoint=False)
            scales = [None] * nframes
        elif animate_time:
            pass
        else:
            raise NotImplementedError()
        if istep is not None:
            assert isinstance(istep, integer_types), 'istep=%r' % istep
            scales = (scales[istep],)
            phases = (phases[istep],)
            isteps = (istep,)

        self.out_data['clicked_ok'] = True
        self.out_data['close'] = True
        self.win_parent.win_parent.make_gif(
            gif_filename, self._icase, scales=scales, phases=phases,
            isteps=isteps,
            time=time, analysis_time=analysis_time, fps=fps,
            onesided=onesided, nrepeat=nrepeat, delete_images=delete_images,
            make_gif=make_gif)

    def on_validate(self):
        """checks to see if the input is valid"""
        scale, flag0 = self.check_float(self.scale_edit)
        time, flag1 = self.check_float(self.time_edit)
        fps, flag2 = self.check_float(self.fps_edit)
        output_dir, flag3 = self.check_path(self.browse_edit)
        gifbase, flag4 = self.check_name(self.gif_edit)
        passed = all([flag0, flag1, flag2, flag3, flag4])
        return passed, (scale, time, fps, output_dir, gifbase)

    def get_analysis_time(self, time, onesided):
        """
        TODO: could we define time as 1/2-sided time so we can do less work?
        TODO: we could be more accurate regarding dt
              Nonesided = 5
              Ntwosided = 2 * Nonesided - 1 = 9
              Nonesided = (Ntwosided + 1) / 2

              Nframes = int(fps * t)
              Nonesided = Nframes
              Ntwosided = 2 * Nonesided - 1 = 9
              Nonesided = (Ntwosided + 1) / 2
        """
        if onesided:
            analysis_time = time / 2.
        else:
            analysis_time = time
        return analysis_time

    @staticmethod
    def check_name(cell):
        cell_value = cell.text()
        try:
            text = str(cell_value).strip()
        except UnicodeEncodeError:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

        if len(text):
            cell.setStyleSheet("QLineEdit{background: white;}")
            return text, True
        else:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

    def check_path(self, cell):
        text, passed = self.check_name(cell)
        if not passed:
            return None, False

        if os.path.exists(text):
            cell.setStyleSheet("QLineEdit{background: white;}")
            return text, True
        else:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

    #def on_ok(self):
        #"""click the OK button"""
        #passed = self.on_apply()
        #if passed:
            #self.win_parent._animation_window_shown = False
            #self.close()
            ##self.destroy()

    def on_cancel(self):
        """click the Cancel button"""
        self.out_data['close'] = True
        self.close()

class LegendPropertiesWindow(PyDialog):
    """
    +-------------------+
    | Legend Properties |
    +-----------------------+
    | Title  ______ Default |
    | Min    ______ Default |
    | Max    ______ Default |
    | Format ______ Default |
    | Scale  ______ Default |
    | Phase  ______ Default |
    | Number of Colors ____ |
    | Number of Labels ____ |
    | Label Size       ____ | (TODO)
    | ColorMap         ____ | (TODO)
    |                       |
    | x Min/Max (Blue->Red) |
    | o Max/Min (Red->Blue) |
    |                       |
    | x Vertical/Horizontal |
    | x Show/Hide           |
    |                       |
    |        Animate        |
    |    Apply OK Cancel    |
    +-----------------------+
    """

    def __init__(self, data, win_parent=None):
        PyDialog.__init__(self, data, win_parent)

        #Init the base class
        self._updated_legend = False
        self._animation_window_shown = False
        self._icase = data['icase']
        self._default_icase = self._icase

        self._default_name = data['name']
        self._default_min = data['min']
        self._default_max = data['max']

        self._default_scale = data['default_scale']
        self._scale = data['scale']

        self._default_phase = data['default_phase']
        self._phase = data['phase']

        self._default_format = data['default_format']
        self._format = data['format']

        self._default_labelsize = data['default_labelsize']
        self._labelsize = data['labelsize']

        self._default_nlabels = data['default_nlabels']
        self._nlabels = data['nlabels']

        self._default_ncolors = data['default_ncolors']
        self._ncolors = data['ncolors']

        self._default_colormap = data['default_colormap']
        self._colormap = data['colormap']

        self._default_is_low_to_high = data['is_low_to_high']

        self._default_is_discrete = data['is_discrete']
        self._default_is_horizontal = data['is_horizontal']
        self._default_is_shown = data['is_shown']

        self._update_defaults_to_blank()

        #self.setupUi(self)
        self.setWindowTitle('Legend Properties')
        self.create_widgets()
        self.create_layout()
        self.set_connections()
        #self.show()

    def _update_defaults_to_blank(self):
        """Changes the default (None) to a blank string"""
        if self._default_colormap is None:
            self._default_colormap = 'jet'
        if self._default_labelsize is None:
            self._default_labelsize = ''
        if self._default_ncolors is None:
            self._default_ncolors = ''
        if self._default_nlabels is None:
            self._default_nlabels = ''

        if self._colormap is None:
            self._colormap = 'jet'
        if self._labelsize is None:
            self._labelsize = ''
        if self._ncolors is None:
            self._ncolors = ''
        if self._nlabels is None:
            self._nlabels = ''

    def update_legend(self, icase, name,
                      min_value, max_value, data_format, scale, phase,
                      nlabels, labelsize,
                      ncolors, colormap,

                      default_title, default_min_value, default_max_value,
                      default_data_format, default_scale, default_phase,
                      default_nlabels, default_labelsize,
                      default_ncolors, default_colormap,
                      is_low_to_high, is_horizontal_scalar_bar):
        """
        We need to update the legend if there's been a result change request
        """
        if icase != self._default_icase:
            self._icase = icase
            self._default_icase = icase
            self._default_name = default_title
            self._default_min = default_min_value
            self._default_max = default_max_value
            self._default_format = default_data_format
            self._default_is_low_to_high = is_low_to_high
            self._default_is_discrete = True
            self._default_is_horizontal = is_horizontal_scalar_bar
            self._default_scale = default_scale
            self._default_phase = default_phase
            self._default_nlabels = default_nlabels
            self._default_labelsize = default_labelsize
            self._default_ncolors = default_ncolors
            self._default_colormap = default_colormap


            if colormap is None:
                colormap = 'jet'
            if labelsize is None:
                labelsize = ''
            if ncolors is None:
                ncolors = ''
            if nlabels is None:
                nlabels = ''

            self._update_defaults_to_blank()

            assert isinstance(scale, float), 'scale=%r' % scale
            assert isinstance(default_scale, float), 'default_scale=%r' % default_scale
            if self._default_scale == 0.0:
                self.scale_edit.setEnabled(False)
                self.scale_button.setEnabled(False)
            else:
                self.scale_edit.setEnabled(True)
                self.scale_button.setEnabled(True)

            if self._default_phase is None:
                self._phase = None
                self.phase.setEnabled(False)
                self.phase_edit.setEnabled(False)
                self.phase_button.setEnabled(False)
                self.phase_edit.setText('0.0')
                self.phase_edit.setStyleSheet("QLineEdit{background: white;}")
            else:
                self._phase = phase
                self.phase.setEnabled(True)
                self.phase_edit.setEnabled(True)
                self.phase_button.setEnabled(True)
                self.phase_edit.setText(str(phase))
                self.phase_edit.setStyleSheet("QLineEdit{background: white;}")

            #self.on_default_name()
            #self.on_default_min()
            #self.on_default_max()
            #self.on_default_format()
            #self.on_default_scale()
            # reset defaults
            self._name = name
            self.name_edit.setText(name)
            self.name_edit.setStyleSheet("QLineEdit{background: white;}")

            self.min_edit.setText(str(min_value))
            self.min_edit.setStyleSheet("QLineEdit{background: white;}")

            self.max_edit.setText(str(max_value))
            self.max_edit.setStyleSheet("QLineEdit{background: white;}")

            self.format_edit.setText(str(data_format))
            self.format_edit.setStyleSheet("QLineEdit{background: white;}")

            self._scale = scale
            self.scale_edit.setText(str(scale))
            self.scale_edit.setStyleSheet("QLineEdit{background: white;}")

            self.nlabels_edit.setText(str(nlabels))
            self.nlabels_edit.setStyleSheet("QLineEdit{background: white;}")

            self.labelsize_edit.setText(str(labelsize))
            self.labelsize_edit.setStyleSheet("QLineEdit{background: white;}")

            self.ncolors_edit.setText(str(ncolors))
            self.ncolors_edit.setStyleSheet("QLineEdit{background: white;}")

            self.colormap_edit.setCurrentIndex(colormap_keys.index(str(colormap)))
            self.on_apply()

    def create_widgets(self):
        """creates the menu objects"""
        # Name
        self.name = QLabel("Title:")
        self.name_edit = QLineEdit(str(self._default_name))
        self.name_button = QPushButton("Default")

        # Min
        self.min = QLabel("Min:")
        self.min_edit = QLineEdit(str(self._default_min))
        self.min_button = QPushButton("Default")

        # Max
        self.max = QLabel("Max:")
        self.max_edit = QLineEdit(str(self._default_max))
        self.max_button = QPushButton("Default")

        # Format
        self.format = QLabel("Format (e.g. %.3f, %g, %.6e):")
        self.format_edit = QLineEdit(str(self._format))
        self.format_button = QPushButton("Default")

        # Scale
        self.scale = QLabel("Scale:")
        self.scale_edit = QLineEdit(str(self._scale))
        self.scale_button = QPushButton("Default")
        if self._default_scale == 0.0:
            self.scale_edit.setEnabled(False)
            self.scale_button.setEnabled(False)

        # Phase
        self.phase = QLabel("Phase (deg):")
        self.phase_edit = QLineEdit(str(self._phase))
        self.phase_button = QPushButton("Default")
        if self._default_phase is None:
            self.phase.setEnabled(False)
            self.phase_edit.setEnabled(False)
            self.phase_button.setEnabled(False)
            self.phase_edit.setText('0.0')
        #tip = QtGui.QToolTip()
        #tip.setTe
        #self.format_edit.toolTip(tip)

        #---------------------------------------
        # nlabels
        self.nlabels = QLabel("Number of Labels:")
        self.nlabels_edit = QLineEdit(str(self._nlabels))
        self.nlabels_button = QPushButton("Default")

        self.labelsize = QLabel("Label Size:")
        self.labelsize_edit = QLineEdit(str(self._labelsize))
        self.labelsize_button = QPushButton("Default")

        self.ncolors = QLabel("Number of Colors:")
        self.ncolors_edit = QLineEdit(str(self._ncolors))
        self.ncolors_button = QPushButton("Default")

        self.colormap = QLabel("Color Map:")
        self.colormap_edit = QComboBox(self)
        self.colormap_button = QPushButton("Default")
        for key in colormap_keys:
            self.colormap_edit.addItem(key)
        self.colormap_edit.setCurrentIndex(colormap_keys.index(self._colormap))


        # red/blue or blue/red
        self.low_to_high_radio = QRadioButton('Low -> High')
        self.high_to_low_radio = QRadioButton('High -> Low')
        widget = QWidget(self)
        low_to_high_group = QButtonGroup(widget)
        low_to_high_group.addButton(self.low_to_high_radio)
        low_to_high_group.addButton(self.high_to_low_radio)
        self.low_to_high_radio.setChecked(self._default_is_low_to_high)
        self.high_to_low_radio.setChecked(not self._default_is_low_to_high)

        # horizontal / vertical
        self.horizontal_radio = QRadioButton("Horizontal")
        self.vertical_radio = QRadioButton("Vertical")
        widget = QWidget(self)
        horizontal_vertical_group = QButtonGroup(widget)
        horizontal_vertical_group.addButton(self.horizontal_radio)
        horizontal_vertical_group.addButton(self.vertical_radio)
        self.horizontal_radio.setChecked(self._default_is_horizontal)
        self.vertical_radio.setChecked(not self._default_is_horizontal)

        # on / off
        self.show_radio = QRadioButton("Show")
        self.hide_radio = QRadioButton("Hide")
        widget = QWidget(self)
        show_hide_group = QButtonGroup(widget)
        show_hide_group.addButton(self.show_radio)
        show_hide_group.addButton(self.hide_radio)
        self.show_radio.setChecked(self._default_is_shown)
        self.hide_radio.setChecked(not self._default_is_shown)

        self.animate_button = QPushButton('Create Animation')

        # closing
        self.apply_button = QPushButton("Apply")
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Cancel")

    def create_layout(self):
        """displays the menu objects"""
        grid = QGridLayout()
        grid.addWidget(self.name, 0, 0)
        grid.addWidget(self.name_edit, 0, 1)
        grid.addWidget(self.name_button, 0, 2)

        grid.addWidget(self.min, 1, 0)
        grid.addWidget(self.min_edit, 1, 1)
        grid.addWidget(self.min_button, 1, 2)

        grid.addWidget(self.max, 2, 0)
        grid.addWidget(self.max_edit, 2, 1)
        grid.addWidget(self.max_button, 2, 2)

        grid.addWidget(self.format, 3, 0)
        grid.addWidget(self.format_edit, 3, 1)
        grid.addWidget(self.format_button, 3, 2)

        grid.addWidget(self.scale, 4, 0)
        grid.addWidget(self.scale_edit, 4, 1)
        grid.addWidget(self.scale_button, 4, 2)

        grid.addWidget(self.phase, 5, 0)
        grid.addWidget(self.phase_edit, 5, 1)
        grid.addWidget(self.phase_button, 5, 2)

        grid.addWidget(self.nlabels, 6, 0)
        grid.addWidget(self.nlabels_edit, 6, 1)
        grid.addWidget(self.nlabels_button, 6, 2)

        #grid.addWidget(self.labelsize, 6, 0)
        #grid.addWidget(self.labelsize_edit, 6, 1)
        #grid.addWidget(self.labelsize_button, 6, 2)

        grid.addWidget(self.ncolors, 7, 0)
        grid.addWidget(self.ncolors_edit, 7, 1)
        grid.addWidget(self.ncolors_button, 7, 2)

        grid.addWidget(self.colormap, 8, 0)
        grid.addWidget(self.colormap_edit, 8, 1)
        grid.addWidget(self.colormap_button, 8, 2)

        ok_cancel_box = QHBoxLayout()
        ok_cancel_box.addWidget(self.apply_button)
        ok_cancel_box.addWidget(self.ok_button)
        ok_cancel_box.addWidget(self.cancel_button)


        grid2 = QGridLayout()
        title = QLabel("Color Scale:")
        grid2.addWidget(title, 0, 0)
        grid2.addWidget(self.low_to_high_radio, 1, 0)
        grid2.addWidget(self.high_to_low_radio, 2, 0)

        grid2.addWidget(self.vertical_radio, 1, 1)
        grid2.addWidget(self.horizontal_radio, 2, 1)

        grid2.addWidget(self.show_radio, 1, 2)
        grid2.addWidget(self.hide_radio, 2, 2)

        grid2.addWidget(self.animate_button, 3, 1)


        #grid2.setSpacing(0)

        vbox = QVBoxLayout()
        vbox.addLayout(grid)
        #vbox.addLayout(checkboxes)
        vbox.addLayout(grid2)
        vbox.addStretch()
        vbox.addLayout(ok_cancel_box)

        #Create central widget, add layout and set
        #central_widget = QtGui.QWidget()
        #central_widget.setLayout(vbox)
        #self.setCentralWidget(central_widget)
        self.setLayout(vbox)

    def set_connections(self):
        self.name_button.clicked.connect(self.on_default_name)
        self.min_button.clicked.connect(self.on_default_min)
        self.max_button.clicked.connect(self.on_default_max)
        self.format_button.clicked.connect(self.on_default_format)
        self.scale_button.clicked.connect(self.on_default_scale)
        self.phase_button.clicked.connect(self.on_default_phase)

        self.nlabels_button.clicked.connect(self.on_default_nlabels)
        self.labelsize_button.clicked.connect(self.on_default_labelsize)
        self.ncolors_button.clicked.connect(self.on_default_ncolors)
        self.colormap_button.clicked.connect(self.on_default_colormap)

        self.animate_button.clicked.connect(self.on_animate)

        self.apply_button.clicked.connect(self.on_apply)
        self.ok_button.clicked.connect(self.on_ok)
        self.cancel_button.clicked.connect(self.on_cancel)

        if qt_version == 4:
            self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)
            #self.colormap_edit.activated[str].connect(self.onActivated)
        #else:
            # closeEvent???

    def on_animate(self):
        name, flag0 = self.check_name(self.name_edit)
        if not flag0:
            return
        data = {
            'icase' : self._icase,
            'name' : name,
            'time' : 2,
            'frames/sec' : 30,
            'resolution' : 1,
            'iframe' : 0,
            'scale' : self._scale,
            'default_scale' : self._default_scale,

            'is_scale' : self._default_phase is None,
            'phase' : self._phase,
            'default_phase' : self._default_phase,
            'dirname' : os.path.abspath(os.getcwd()),
            'clicked_ok' : False,
            'close' : False,
        }
        if not self._animation_window_shown:
            self._animation_window = AnimationWindow(data, win_parent=self)
            self._animation_window.show()
            self._animation_window_shown = True
            self._animation_window.exec_()
        else:
            self._animation_window.activateWindow()

        if data['close']:
            if not self._animation_window._updated_animation:
                #self._apply_animation(data)
                pass
            self._animation_window_shown = False
            del self._animation_window
        else:
            self._animation_window.activateWindow()

    def on_default_name(self):
        name = str(self._default_name)
        self.name_edit.setText(name)
        self.name_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_min(self):
        self.min_edit.setText(str(self._default_min))
        self.min_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_max(self):
        self.max_edit.setText(str(self._default_max))
        self.max_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_format(self):
        self.format_edit.setText(str(self._default_format))
        self.format_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_scale(self):
        self.scale_edit.setText(str(self._default_scale))
        self.scale_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_phase(self):
        self.phase_edit.setText(str(self._default_phase))
        self.phase_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_ncolors(self):
        self.ncolors_edit.setText(str(self._default_ncolors))
        self.ncolors_edit.setStyleSheet("QLineEdit{background: white;}")

    def on_default_colormap(self):
        self.colormap_edit.setCurrentIndex(colormap_keys.index(self._default_colormap))

    def on_default_nlabels(self):
        self.nlabels_edit.setStyleSheet("QLineEdit{background: white;}")
        self.nlabels_edit.setText(str(self._default_nlabels))

    def on_default_labelsize(self):
        self.labelsize_edit.setText(str(self._default_labelsize))
        self.labelsize_edit.setStyleSheet("QLineEdit{background: white;}")

    @staticmethod
    def check_name(cell):
        cell_value = cell.text()
        try:
            text = str(cell_value).strip()
        except UnicodeEncodeError:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

        if len(text):
            cell.setStyleSheet("QLineEdit{background: white;}")
            return text, True
        else:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

    @staticmethod
    def check_colormap(cell):
        text = str(cell.text()).strip()
        if text in colormap_keys:
            cell.setStyleSheet("QLineEdit{background: white;}")
            return text, True
        else:
            cell.setStyleSheet("QLineEdit{background: red;}")
            return None, False

    def on_validate(self):
        name_value, flag0 = self.check_name(self.name_edit)
        min_value, flag1 = self.check_float(self.min_edit)
        max_value, flag2 = self.check_float(self.max_edit)
        format_value, flag3 = self.check_format(self.format_edit)
        scale, flag4 = self.check_float(self.scale_edit)
        phase, flag5 = self.check_float(self.phase_edit)

        nlabels, flag6 = self.check_positive_int_or_blank(self.nlabels_edit)
        ncolors, flag7 = self.check_positive_int_or_blank(self.ncolors_edit)
        labelsize, flag8 = self.check_positive_int_or_blank(self.labelsize_edit)
        colormap = str(self.colormap_edit.currentText())

        if all([flag0, flag1, flag2, flag3, flag4, flag5, flag6, flag7, flag8]):
            if 'i' in format_value:
                format_value = '%i'

            assert isinstance(scale, float), scale
            self.out_data['name'] = name_value
            self.out_data['min'] = min_value
            self.out_data['max'] = max_value
            self.out_data['format'] = format_value
            self.out_data['scale'] = scale
            self.out_data['phase'] = phase

            self.out_data['nlabels'] = nlabels
            self.out_data['ncolors'] = ncolors
            self.out_data['labelsize'] = labelsize
            self.out_data['colormap'] = colormap

            self.out_data['is_low_to_high'] = self.low_to_high_radio.isChecked()
            self.out_data['is_horizontal'] = self.horizontal_radio.isChecked()
            self.out_data['is_shown'] = self.show_radio.isChecked()

            self.out_data['clicked_ok'] = True
            self.out_data['close'] = True
            #print('self.out_data = ', self.out_data)
            #print("name = %r" % self.name_edit.text())
            #print("min = %r" % self.min_edit.text())
            #print("max = %r" % self.max_edit.text())
            #print("format = %r" % self.format_edit.text())
            return True
        return False

    def on_apply(self):
        passed = self.on_validate()
        if passed:
            self.win_parent._apply_legend(self.out_data)
        return passed

    def on_ok(self):
        passed = self.on_apply()
        if passed:
            self.close()
            #self.destroy()

    def on_cancel(self):
        self.out_data['close'] = True
        self.close()


def main(): # pragma: no cover
    # kills the program when you hit Cntl+C from the command line
    # doesn't save the current state as presumably there's been an error
    import signal
    signal.signal(signal.SIGINT, signal.SIG_DFL)


    import sys
    # Someone is launching this directly
    # Create the QApplication
    app = QApplication(sys.argv)
    #The Main window
    d = {
        'icase' : 1,
        'name' : 'asdf',
        'min' : 0.,
        'max' : 10,
        'scale' : 1e-12,
        'default_scale' : 1.0,

        'phase' : 0.0,
        #'default_phase' : 180.0,
        'default_phase' : None,

        'nlabels' : 11,
        'default_nlabels' : 11,

        'labelsize' : 12,
        'default_labelsize' : 12,

        'ncolors' : 13,
        'default_ncolors' : 13,

        'colormap' : 'jet',
        'default_colormap' : 'jet',

        'default_format' : '%s',
        'format' : '%g',

        'is_low_to_high': True,
        'is_discrete' : False,
        'is_horizontal' : False,
        'is_shown' : True,
    }
    main_window = LegendPropertiesWindow(d)

    data = {
        'icase' : 1,
        'name' : 'cat',
        'time' : 2,
        'frames/sec' : 30,
        'resolution' : 1,
        'iframe' : 0,
        'is_scale' : False,
        'dirname' : os.getcwd(),
    }
    #main_window = AnimationWindow(data)
    main_window.show()
    # Enter the main loop
    app.exec_()

if __name__ == "__main__": # pragma: no cover
    main()
