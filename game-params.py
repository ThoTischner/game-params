import sys
import os
import winreg
from PyQt5.QtWidgets import QApplication, QTabWidget, QPushButton, QStyle, QTableWidget, QHeaderView, QTableWidgetItem, QLineEdit, QMessageBox
from PyQt5.QtCore import pyqtSlot, QSize
from PyQt5.QtGui import QIcon
from pathlib import Path
import yaml
import xml.etree.ElementTree as ET
import glob
from functools import partial
from re import *

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def app():

    # load config file
    with open(resource_path("config.yaml"), 'r') as ymlfile:
        cfg = yaml.load(ymlfile)

    # Init gui
    my_app = QApplication(sys.argv)
    w = QTabWidget()
    w.setWindowTitle("Game Params")
    w.resize(900, 400)
    app_icon = QIcon(resource_path('logo.ico'))
    w.setWindowIcon(app_icon)
    buttons_set = {}
    buttons_remove = {}
    buttons_on = {}
    buttons_off = {}
    inputs = {}
    game_tabs = {}

    # Get user home
    home = str(Path.home())

    # loop trough config
    for section in cfg['main_conf']:

        # detect provider via home_dir
        if section['detect_type'] == "home_dir":

            detect_dir = home + section['dir']

            if os.path.isdir(detect_dir):

                # Set provider config file
                for filename in glob.glob(detect_dir + '\local_*.xml'):
                    provider_config = filename

                # Loop trough games
                for game in section['games']:

                    if game['detect_type'] == "reg":

                        name = game['name']
                        path = game['path']
                        dir = game['rege_dir']

                        game_exists = True
                        try:
                            aKey = winreg.OpenKey(getattr(winreg,path), dir)
                        except WindowsError:
                            game_exists = False

                        if game_exists:
                            param_count = len(game['params'])
                            game_tabs[name] = QTableWidget(param_count,7)
                            game_tabs[name].setEditTriggers(QTableWidget.NoEditTriggers)
                            game_tabs[name].verticalHeader().setVisible(False)
                            game_tabs[name].setHorizontalHeaderLabels(['Name', 'Description', 'Possible Values', 'Value', '', '', 'Status'])
                            game_tabs[name].horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                            w.addTab(game_tabs[name], name)
                            game_tabs[name].show()



                            for index, param in enumerate(game['params'], 0):

                                # Set button function
                                @pyqtSlot()
                                def set_clicked(index, param):
                                    # check if input field is filled
                                    print(inputs[param['name']].text())
                                    if param['type'] == 'input' and not inputs[param['name']].text():
                                        value_msg = QMessageBox()
                                        value_msg.setIcon(QMessageBox.Warning)
                                        value_msg.setText("Need value")
                                        value_msg.setWindowTitle("Game Params")
                                        value_msg.exec_()
                                    else:
                                        # check if game specific config already present
                                        if game['code'] in elem.attrib['value']:
                                            # Remove any old setting
                                            if param['type'] == 'input':
                                                regex_remove = r'' + '\\' + param['value'] + '\s\S*\s*'
                                            else:
                                                regex_remove = r'' + '\\' + param['value'] + '\s*'
                                            clean_string = sub(regex_remove, '', elem.attrib['value'])
                                            if param['type'] == 'input':
                                                new_string = clean_string.replace(game['code'], game['code'] + param['value'] + ' ' + inputs[param['name']].text() + ' ')
                                            else:
                                                new_string = clean_string.replace(game['code'], game['code'] + param['value'] + ' ')

                                            tree.find('Setting[@key="GameCommandLineArguments"]').set('value', new_string.rstrip())
                                            tree.write(provider_config)
                                        else:
                                            if param['type'] == 'input':
                                                new_value = elem.attrib['value'] + section['separator'] + game['code'] + param['value'] + ' ' + inputs[param['name']].text()
                                            else:
                                                new_value = elem.attrib['value'] + section['separator'] + game['code'] + param['value'] + ' '
                                            tree.find('Setting[@key="GameCommandLineArguments"]').set('value', new_value.rstrip())
                                            tree.write(provider_config)

                                        # Add green status icon
                                        buttons_on[param['name']] = QPushButton()
                                        buttons_on[param['name']].setIcon(buttons_on[param['name']].style().standardIcon(QStyle.SP_DialogApplyButton))
                                        game_tabs[name].setCellWidget(index, 6, buttons_on[param['name']])
                                @pyqtSlot()
                                def remove_clicked(index, param):
                                    # Remove any old setting
                                    if param['type'] == 'input':
                                        regex_remove = r'' + '\\' + param['value'] + '\s\S*'
                                        # Clear input field
                                        inputs[param['name']].setText('')
                                    else:
                                        regex_remove = r'' + '\\' + param['value']
                                    clean_string = sub(regex_remove, '', elem.attrib['value'])
                                    tree.find('Setting[@key="GameCommandLineArguments"]').set('value', clean_string)
                                    tree.write(provider_config)
                                    # Add red status icon
                                    buttons_off[param['name']] = QPushButton()
                                    buttons_off[param['name']].setIcon(buttons_off[param['name']].style().standardIcon(QStyle.SP_DialogCancelButton))
                                    game_tabs[name].setCellWidget(index, 6, buttons_off[param['name']])


                                # Get all parameter values
                                param_name = QTableWidgetItem(param['name'])
                                param_desc = QTableWidgetItem(param['desc'])
                                param_possible_value = QTableWidgetItem(param['possible_value'])
                                param_type = param['type']

                                buttons_set[param['name']] = QPushButton(game_tabs[name])
                                buttons_set[param['name']].setText('Set')
                                buttons_set[param['name']].clicked.connect(partial(set_clicked, index, param))
                                buttons_remove[param['name']] = QPushButton(game_tabs[name])
                                buttons_remove[param['name']].setText('Remove')
                                buttons_remove[param['name']].clicked.connect(partial(remove_clicked, index, param))
                                game_tabs[name].setItem(index, 0, param_name)
                                game_tabs[name].setItem(index, 1, param_desc)
                                game_tabs[name].setItem(index, 2, param_possible_value)
                                game_tabs[name].setCellWidget(index, 4, buttons_set[param['name']])
                                game_tabs[name].setCellWidget(index, 5, buttons_remove[param['name']])


                                # Check if value is already present

                                tree = ET.ElementTree(file=provider_config)

                                for elem in tree.iterfind('Setting[@key="GameCommandLineArguments"]'):
                                    line = elem.attrib['value'].split(section['separator'])
                                value = None
                                key = None
                                config_bool = None
                                regex = r"^" + game['code'] + '(.*?)(\\' + param['value'] + ')\s(\S*)(\s?)'
                                regex_bool = r"^" + game['code'] + '.*?\\' + param['value']
                                for i in line:
                                    config_value = match(regex, i)
                                    config_bool = search(regex_bool, i)
                                    try:
                                        key = config_value.group(2)
                                        value = config_value.group(3)
                                    except:
                                        value = None

                                # Add input field
                                if param['type'] == 'input':
                                    inputs[param['name']] = QLineEdit()
                                    inputs[param['name']].show()
                                if value:
                                    if param['type'] == 'input':
                                        # Add input field with actual value
                                        inputs[param['name']].setText(value)

                                    # Add green status icon
                                    buttons_on[param['name']] = QPushButton()
                                    buttons_on[param['name']].setIcon(buttons_on[param['name']].style().standardIcon(QStyle.SP_DialogApplyButton))
                                    game_tabs[name].setCellWidget(index, 6, buttons_on[param['name']])
                                else:
                                    if param['type'] == 'input':
                                        # Add input field with no actual value
                                        inputs[param['name']].setText('')

                                    # Add green button if boolean found
                                    if config_bool:
                                        # Add green status icon
                                        buttons_on[param['name']] = QPushButton()
                                        buttons_on[param['name']].setIcon(buttons_on[param['name']].style().standardIcon(QStyle.SP_DialogApplyButton))
                                        game_tabs[name].setCellWidget(index, 6, buttons_on[param['name']])
                                    else:
                                        # Add red status icon
                                        buttons_off[param['name']] = QPushButton()
                                        buttons_off[param['name']].setIcon(buttons_off[param['name']].style().standardIcon(QStyle.SP_DialogCancelButton))
                                        game_tabs[name].setCellWidget(index, 6, buttons_off[param['name']])

                                if param['type'] == 'input':
                                    game_tabs[name].setCellWidget(index, 3, inputs[param['name']])

        else:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("No Games found")
            msg.setWindowTitle("Game Params")
            sys.exit(msg.exec_())
            exit()

    w.show()
    sys.exit(my_app.exec_())

app()
