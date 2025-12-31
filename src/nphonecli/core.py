#
#             ███████████  █████                                     █████████  █████       █████
#            ░░███░░░░░███░░███                                     ███░░░░░███░░███       ░░███ 
#  ████████   ░███    ░███ ░███████    ██████  ████████    ██████  ███     ░░░  ░███        ░███ 
# ░░███░░███  ░██████████  ░███░░███  ███░░███░░███░░███  ███░░███░███          ░███        ░███ 
#  ░███ ░███  ░███░░░░░░   ░███ ░███ ░███ ░███ ░███ ░███ ░███████ ░███          ░███        ░███ 
#  ░███ ░███  ░███         ░███ ░███ ░███ ░███ ░███ ░███ ░███░░░  ░░███     ███ ░███      █ ░███ 
#  ████ █████ █████        ████ █████░░██████  ████ █████░░██████  ░░█████████  ███████████ █████
# ░░░░ ░░░░░ ░░░░░        ░░░░ ░░░░░  ░░░░░░  ░░░░ ░░░░░  ░░░░░░    ░░░░░░░░░  ░░░░░░░░░░░ ░░░░░ 
#

# (c) 2025 NlckySolutions - GNU GPLv3
# Last & Final NlckySolutions Project created in 2025.

# IMPORTS AND WHY EACH ONE IS NEEDED

import time # Waiting before executing something
import os # Executing most commands
from serial.tools import list_ports # Listing connected devices
import sys # Getting basic system info
import re # Finding strings within text
import subprocess # Opening new processes
import serial # Communicating with device
import platform # Checking the current OS
import glob # Finding/listing ports
import asyncio # Running different actions asynchronously
import threading # Using multiple threads
import json # Parsing and creating JSON
import hashlib # Hashing strings
import xml.etree.ElementTree as ET # Importing strings.xml
from datetime import datetime, timedelta
from functools import partial # Register button clicks to functions
import shutil # Fastboot partition eraser for Motorola
from importlib.resources import files # Load strings.xml as a PyPi package.
from pathlib import Path # Load strings.xml

## nPhoneCLI permissions (these are the things that nPhoneCLI is capable of doing):

# Communicate with USB devices using ADB, MTP, and AT commands.
# Communicate with external servers to verify whether an action worked or not.
# Open a new tab in the default browser
# Checking and getting basic information about the current system

version = "1.5.0"

# This program is free software: you can redistribute it and/or modify it 
# under the terms of the GNU General Public License as published by the Free Software Foundation, 
# either version 3 of the License, or any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
# See the LICENSE (included in the nPhoneCLI source) for more details.

# ===========================================================================================================

# Requirements:
#
# Ubuntu >=20.0.4-LTS
# Windows support exists but is not well-supported yet.
# At least 1 USB A or USB C port
# Python
# Everything in requirements.txt
# 
# ===================================
#
# Already-Installed Requirements:
#
# usbsend.py (by nPhoneCLI) # not needed anymore but still here
#
# ===================================

# ============================================================================= #
# You shouldn't edit anything below this line unless you know what you're doing #
# ============================================================================= #

verbose2 = False
debugMode = False # If True, removes root/admin requirement. Most serial/usb features will stop working. As of v1.5.0, this will only affect Windows users.
firstunlock = False # This variable helps ModemPreload work

def load_strings(xml_path=None):
    if xml_path is None:
        #cwd_path = Path("strings.xml")
        #if cwd_path.exists():
        #    xml_path = cwd_path
        #else:
        #    xml_path = files("myscript") / "strings.xml"
        xml_path = files("myscript") / "strings.xml"

    tree = ET.parse(xml_path)
    root = tree.getroot()

    return {
        elem.attrib["name"]: (elem.text or "").replace("\\n", "\n")
        for elem in root.findall("string")
    }


# Load strings
#strings = load_strings("strings.xml") # Load almost every string from strings.xml (ez translations)
strings = load_strings()

os_config = "WINDOWS" if platform.system() == "Windows" else "LINUX" # Auto-get OS and save to var

class SerialManager: # AT command sender via class
    def __init__(self, baud=115200): # Start the serial port early
        self.port = self.detect_port() # Detect which port it is
        self.baud = baud # Choose a baud rate
        self.ser = None

        if not self.port: # No device connected
            raise ConnectionError(strings['noDeviceSermanError']) 
        elif self.port:
            try:
                self.ser = serial.Serial(self.port, self.baud, timeout=2) # Save the port for use with the rest of the class
                time.sleep(0.5)
                if verbose2:
                    print(f"{strings['sermanConnectedPort']}{self.port}")
            except serial.SerialException as e:
                raise RuntimeError(f"{strings['sermanOpeningPortError']}{self.port}: {e}")

    def reset(self):
        self.__init__()

    def detect_port(self):
        system = platform.system()

        # Detect port for different systems/OSes

        if system == "Windows": 
            for i in range(1, 256):
                try:
                    s = serial.Serial(f"COM{i}")
                    s.close()
                    return f"COM{i}"
                except:
                    pass
        elif system == "Darwin":  # macOS
            ports = glob.glob("/dev/tty.usb*")
            return ports[0] if ports else None
        else:  # Linux
            ports = glob.glob("/dev/ttyACM*") + glob.glob("/dev/ttyUSB*")
            return ports[0] if ports else None

        return None

    def send(self, command):
        if not self.ser or not self.ser.is_open:
            raise ConnectionError(strings['noDeviceGenericError'])
        else:
            self.ser.flushInput()
            self.ser.flushOutput()
            self.ser.write((command.strip() + '\r\n').encode())
            time.sleep(0.1)

            output = []
            while True:
                line = self.ser.readline()
                if not line:
                    break
                output.append(line.decode(errors='ignore').strip())

            return '\n'.join(output)

    def close(self):
        if self.ser and self.ser.is_open:
            self.ser.close()

class SerialManagerWindows: # Version of SerialManager class specifically for Windows
    def __init__(self, port: str = None, baud: int = 115200, debug: bool = False):
        """
        Windows-only serial helper.
        :param port: Override COM port (e.g. "COM3"). If None, auto-detects.
        :param baud: Baud rate.
        :param debug: Print connection details if True.
        """
        if platform.system() != "Windows":
            raise RuntimeError(strings['sermanWindowsOsError'])

        self.debug = debug
        self.baud = baud
        self.ser = None

        # allow override, else auto-detect
        self.port = port or self.detect_port()
        if not self.port:
            raise RuntimeError(strings['sermanNoComPort'])

        try:
            self.ser = serial.Serial(self.port, self.baud, timeout=2)
            time.sleep(0.5)
            if self.debug:
                print(f"{strings['sermanConnectedPort']}{self.port} @ {self.baud} baud")
        except serial.SerialException as e:
            raise RuntimeError(f"{strings['sermanOpeningPortError']}{self.port}: {e}")
        
    def reset(self):
        self.__init__()

    def detect_port(self) -> str:
        """Return the first COM* port or None."""
        ports = list_ports.comports()
        if self.debug:
            print(f"{strings['sermanWinAvailablePorts']}{[p.device for p in ports]}")
        for p in ports:
            if p.device.upper().startswith("COM"):
                if self.debug:
                    print(f"{strings['sermanWinDev']}{p.device}")
                return p.device
        return None

    def send(self, command: str, wait: float = 0.1) -> str:
        """
        Send a command and collect all response lines.
        :param command: Text/AT command to send.
        :param wait: Seconds to pause before reading.
        """
        if not self.ser or not self.ser.is_open:
            raise RuntimeError(strings['serPortNotOpen'])

        self.ser.reset_input_buffer()
        self.ser.reset_output_buffer()
        self.ser.write((command.strip() + "\r\n").encode())
        time.sleep(wait)

        lines = []
        while True:
            line = self.ser.readline()
            if not line:
                break
            lines.append(line.decode(errors="ignore").strip())
        return "\n".join(lines)

    def close(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            self.ser.close()
            if self.debug:
                print(strings['sermanWinConClosed'])

if os_config == "WINDOWS": # Choose which serial manager to use based on OS
    serman = SerialManagerWindows()
elif os_config == "LINUX":
    serman = SerialManager()

class AT:
    def send(command, not_first=False):
        # Making usbsend.py into a built-in class (SerialManager for Linux, or SerialManagerWindows for Windows) improves command speed by 10-20x, and improves multi-OS compatibility
        rt()
        if not_first:
            serman.reset()
        with open("tmp_output.txt", "w", encoding="utf-8") as f:
            try:
                result = serman.send(command)
                if result is None:
                    result = serman.send(command)
                    if result is None: # (If result is STILL None)
                        result = "" # Then give up after the second try.
                f.write(result)
            except Exception: # If the connection isn't there, reset to attempt to gain the connection back
                serman.reset()
                time.sleep(1) 
                try:
                    result = serman.send(command)
                    if result is None:
                        result = serman.send(command)
                        if result is None: # (If result is STILL None)
                            result = "" # Then give up after the second try.
                    f.write(result)
                except Exception:
                    # Device must not be plugged in?
                    print(strings['deviceConCheckNotPlugged'])
    
class ADBc: # ADB class for sending ADB commands if needed
    def send(command):
        rt()
        if os_config == "LINUX":
            os.system(f"sudo bash -c 'sudo adb {command} > tmp_output_adb.txt 2>&1'")
        elif os_config == "WINDOWS":
            with open('tmp_output.txt', 'w') as f:
                subprocess.run(['adb', command], stdout=f, stderr=subprocess.STDOUT)
        time.sleep(0.5)
    
    def usbswitch(arg, action):
        # Later, add logic to allow switching of device interface to AT, for more compatibility.
        return True

def check_serial_permissions():
    if os_config == "LINUX":
        import grp
        import getpass
        import platform

        user = getpass.getuser()

        # Serial device groups used across most distros
        serial_groups = ["dialout", "uucp", "lock", "tty"]

        # Collect groups the user is currently in
        user_groups = [g.gr_name for g in grp.getgrall() if user in g.gr_mem]

        # Also check primary group ID (some distros put uucp as primary)
        try:
            primary_group = grp.getgrgid(os.getgid()).gr_name
            user_groups.append(primary_group)
        except:
            pass

        # Check if user is good
        for g in serial_groups:
            if g in user_groups:
                return True  # Permissions OK

        # If we reach here, user is missing required groups
        # Decide which command to show based on distro
        distro = platform.system()

        if distro == "Linux":
            # Try reading OS-release for better accuracy
            import distro as distro_lib
            name = distro_lib.id()

            if name in ["ubuntu", "debian", "linuxmint", "zorin"]:
                cmd = f"sudo usermod -aG dialout {user}"
            elif name in ["arch", "endeavouros", "cachyos", "manjaro", "garuda"]:
                cmd = f"sudo usermod -aG uucp,lock {user}"
            elif name in ["fedora", "rhel", "centos"]:
                cmd = f"sudo usermod -aG dialout {user}"
            else:
                # Fallback universal command
                cmd = f"sudo usermod -aG dialout,uucp,lock {user}"
        else:
            cmd = "Unsupported OS for serial permissions."

        raise PermissionError("You need to be in the Linux dialout group.")
    else:
        return True

class FastbootPartitionEraser:
    """
    This class attempts to erase FRP partition(s) on Motorola devices.
    """

    def __init__(self, fastboot_path='fastboot'):
        # Ensure the fastboot executable is available
        if not shutil.which(fastboot_path):
            raise FileNotFoundError(f"Fastboot binary '{fastboot_path}' not found in PATH.")
        self.fastboot = fastboot_path

    def _run(self, args):
        """
        Internal helper to run a fastboot command.
        Raises RuntimeError if command fails.
        """
        cmd = [self.fastboot] + args
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Command {' '.join(cmd)} failed: {result.stderr.strip()}")
        return result.stdout.strip()

    def erase_config(self, device_id=None):
        """
        Erase the 'config' partition.
        Optionally specify a device serial with device_id.
        """
        args = []
        if device_id:
            args += ['-s', device_id]
        args += ['erase', 'config']
        return self._run(args)

    def erase_persist(self, device_id=None):
        """
        Erase the 'persist' partition.
        Optionally specify a device serial with device_id.
        """
        args = []
        if device_id:
            args += ['-s', device_id]
        args += ['erase', 'persist']
        return self._run(args)

    def erase_frp(self, device_id=None):
        """
        Erase the 'frp' partition.
        Optionally specify a device serial with device_id.
        """
        args = []
        if device_id:
            args += ['-s', device_id]
        args += ['erase', 'frp']
        return self._run(args)

    def wipe_data_cache(self, device_id=None):
        """
        Wipe data and cache partitions via 'fastboot -w'.
        Optionally specify a device serial with device_id.
        """
        args = []
        if device_id:
            args += ['-s', device_id]
        args += ['-w']
        return self._run(args)

# =============================================
#  Different instructions for the user
# =============================================

def MTPmenu():
    #x = input(strings['mtpMenu'] + "-- Hit enter to proceed...")
    show(strings['mtpMenu'])
    # Show user instructions to enable MTP mode

def adbMenu():
    ADBc.send("devices")
    #x = input(strings['adbMenu'] + "-- Hit enter to proceed...")
    show(strings['adbMenu'])
    # Show user instructions to enable ADB mode

# ================================================
#  Simple functions to eliminate repetitive tasks
# ================================================

def show(text, verbosecheck=True): # This is for nPhoneCLI in order to show text if Verbose is enabled.
    # if verbosecheck:
    #     if verbose:
    #         #x = input(text + " -- Press Enter to continue...")
    #         x = input(text + "-- Hit enter to proceed...")
    # else:
    #     x = input(text + "-- Hit enter to proceed...")
    x = input(text + "-- Hit enter to proceed...")

def rt(): # Flush the output buffer. May be deprecated and replaced soon with a new output collection method
    """if os_config == "LINUX": # Flush output buffer on different OSes
        os.system("sudo bash -c 'rm -f tmp_output.txt'") 
        os.system("sudo bash -c 'rm -f tmp_output_adb.txt'")
    elif os_config == "WINDOWS":
        os.system("del /F tmp_output.txt")
        os.system("del /F tmp_output_adb.txt")"""
    
    # Better rt() method + crossplatform + no errors
    for f in ["tmp_output.txt", "tmp_output_adb.txt"]:
        try:
            os.remove(f)
        except FileNotFoundError:
            pass

def readOutput(type): # Read the output buffer based on command type AT or ADB
    if type == "AT":
        with open("tmp_output.txt", "r") as f:
            output = f.read()
    elif type == "ADB":
        with open("tmp_output_adb.txt", "r") as f:
            output = f.read()
    return output

def modemUnlock(manufacturer, softUnlock=False): # Unlock the modem per-action if preload wasn't enabled
    if manufacturer == "SAMSUNG": # Select the manufacturer to preload
        if softUnlock:
            AT.send("AT+SWATD=0") # Disables some sort of a proprietary "AT commands lock" from SAMSUNG
        else:
            AT.send("AT+SWATD=0") # Disables some sort of a proprietary "AT commands lock" from SAMSUNG
            AT.send("AT+ACTIVATE=0,0,0") # An activation sequence that unlocks the modem when paired with the above command.

# Function that can parse DEVCONINFO in order to make it more readable
def parse_devconinfo(raw_input): 
    lines = raw_input.strip().splitlines()
    parsed_output = []

    for line in lines:
        if "+DEVCONINFO:" in line:
            # Extract the part after "+DEVCONINFO:"
            content = line.split(":", 1)[1].strip()
            # Split by semicolon
            items = content.split(";")
            for item in items:
                if not item:
                    continue
                match = re.match(r'(\w+)\((.*?)\)', item)
                if match:
                    key, value = match.groups()
                    friendly_key = {
                        "MN": "Model",
                        "BASE": "Baseband",
                        "VER": "Software Version",
                        "HIDVER": "Hidden Version",
                        "MNC": "Mobile Network Code",
                        "MCC": "Mobile Country Code",
                        "PRD": "Product Code",
                        "AID": "App ID",
                        "CC": "Country Code",
                        "OMCCODE": "OMC Code",
                        "SN": "Serial Number",
                        "IMEI": "IMEI",
                        "UN": "Unique Number",
                        "PN": "Phone Number",
                        "CON": "Connection Types",
                        "LOCK": "SIM Lock",
                        "LIMIT": "Limit Status",
                        "SDP": "SDP Mode",
                        "HVID": "Partition Info"
                    }.get(key, key)
                    parsed_output.append(f"{friendly_key}: {value if value else 'N/A'}")
    return "\n".join(parsed_output)
               
# =============================================
#  Unlocking methods for different devices
# =============================================

def frp_unlock_pre2022(verbose): # FRP unlock for pre-aug2022 security patch update
    if verbose:
        print(strings['getVerInfo'], end="")
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info) # Extract only the model no. from the output

    if info == "Fail":
        raise ConnectionError(strings['deviceCheckPluggedIn2'])
    else:
        ATcommands = [
            "AT+DUMPCTRL=1,0",
            "AT+DEBUGLVC=0,5",
            "AT+SWATD=0", # Removes some kind of proprietary SAMSUNG modem lock
            "AT+ACTIVATE=0,0,0", # So that you can ACTIVATE
            "AT+SWATD=1", # Then relocks it.
            "AT+DEBUGLVC=0,5"
        ]

        ADBcommands = [ # Run list of commands in order to complete the unlock with newly-enabled ADB
            "shell settings put global setup_wizard_has_run 1",
            "shell settings put secure user_setup_complete 1",
            "shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1",
            "shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1",
            "shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1",
            "shell am start -c android.intent.category.HOME -a android.intent.action.MAIN"
        ]

        if verbose:
            show(strings['misuseFrpGuidance'])
            print(strings['attemptingEnableAdb'], end="")
            show(strings['frpUnlockStepsPre2022'])

        for command in ATcommands:
            AT.send(command)

        output = readOutput("AT")

        if "error" in output.lower():
            raise ConnectionRefusedError(strings['frpNotCompatible'])
        else:
            if verbose:
                print(strings['okText'])
                print(strings['runUnlock'])
                show(strings['usbDebuggingPromptCheck'])
            for command in ADBcommands:
                ADBc.send(command)
            if verbose:
                print(strings['unlockSuccess'])
            return "Success"
            
def frp_unlock_2022_2023(verbose): # FRP unlock for aug2022-dec2022 security patch update
    if verbose:
        print(strings['getVerInfo'])
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info) # Extract only the model no. from the output

    if info == "Fail":
        raise ConnectionError(strings['deviceCheckPluggedIn2'])
    else:
        commands = ['AT+SWATD=0', 'AT+ACTIVATE=0,0,0', 'AT+DEVCONINFO','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0', 'AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5','AT+SWATD=0','AT+ACTIVATE=0,0,0','AT+SWATD=1','AT+DEBUGLVC=0,5','AT+KSTRINGB=0,3','AT+DUMPCTRL=1,0','AT+DEBUGLVC=0,5']
        # These commands are supposed to overwhelm the phone and trick it into enabling ADB. The rest after this is the same as the other unlock method.

        ADBcommands = [ # Run list of commands in order to complete the unlock with newly-enabled ADB
            "shell settings put global setup_wizard_has_run 1",
            "shell settings put secure user_setup_complete 1",
            "shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1",
            "shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1",
            "shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1",
            "shell am start -c android.intent.category.HOME -a android.intent.action.MAIN"
        ]

        if verbose:
            show(strings['misuseFrpGuidance2022'])
            print(strings['attemptingEnableAdb'])
            show(strings['frpUnlockSteps2022'])

        for command in commands:
            AT.send(command)

        output = readOutput("AT")

        if "error" in output.lower():
            raise ConnectionRefusedError(strings['frpNotCompatible'])
        else:
            if verbose:
                print(strings['okText'])
                print(strings['runUnlock'])
                show(strings['usbDebuggingPromptCheck'])
            for command in ADBcommands:
                ADBc.send(command)
            if verbose:
                print(strings['unlockSuccess'])
            return "Success"

def frp_unlock_2024(verbose): # FRP unlock for early 2024-ish security patch update
    if verbose:
        print(strings['getVerInfo'])
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info) # Extract only the model no. from the output

    if info == "Fail":
        raise ConnectionError(strings['deviceCheckPluggedIn2'])
    else:
        commands = [
            "AT+SWATD=0", # Modem unlocking
            "AT+ACTIVATE=0,0,0", # Modem unlocking
            "AT+DEVCONINFO", # Get device info
            "AT+VERSNAME=3.2.3", # FRP unlocking commands
            "AT+REACTIVE=1,0,0", # FRP unlocking commands
            "AT+SWATD=0", # Re-Modem unlocking
            "AT+ACTIVATE=0,0,0", # Re-Modem unlocking
            "AT+SWATD=1", # Lock quickly
            "AT+SWATD=1", # Lock again
            "AT+PRECONFIG=2,VZW", # Quickly change CSC
            "AT+PRECONFIG=1,0", # Quickly change it back
        ]

        ADBcommands = [ # Run list of commands in order to complete the unlock with newly-enabled ADB
            "shell settings put global setup_wizard_has_run 1", 
            "shell settings put secure user_setup_complete 1",
            "shell content insert --uri content://settings/secure --bind name:s:DEVICE_PROVISIONED --bind value:i:1",
            "shell content insert --uri content://settings/secure --bind name:s:user_setup_complete --bind value:i:1",
            "shell content insert --uri content://settings/secure --bind name:s:INSTALL_NON_MARKET_APPS --bind value:i:1",
            "shell am start -c android.intent.category.HOME -a android.intent.action.MAIN"
        ]
        
        if verbose:
            show(strings['misuseFrpGuidance2024'])
            print(strings['attemptingEnableAdb'])
            show(strings['frpUnlockSteps2024'])

        for command in commands:
            AT.send(command)

        output = readOutput("AT")

        if "error" in output.lower():
            raise ConnectionRefusedError(strings['frpNotCompatible'])
        else:
            if verbose:
                print(strings['runUnlock'])
                show(strings['usbDebuggingPromptCheck'])
            for command in ADBcommands:
                ADBc.send(command)
            if verbose:
                print(strings['unlockSuccess'])
            return "Success"
            
def general_frp_unlock(): # Not completed yet
    raise NotImplementedError("This function is not completed yet.")
    info = verinfo(False)
    if "Model: SM" in info:
        frp_unlock_pre2022()
    else:
        # to do, add FULLY universal FRP unlock
        raise NotImplementedError(strings['deviceNotSupportedUniversal'])

def lg_screen_unlock(verbose): # Screen unlock on supported LG devices *untested*
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info) # Extract only the model no. from the output (may not work)
    # I noticed that alot of this code is way too bloated, so some of these functions are shrunken but function relatively the same
    # Also, nPhoneCLI does not include success checks. It will use usage pings, which are less verbose and cleaner.
    if verbose:
        show(strings['lgScreenUnlockSupportedDevs'])
        print(strings['lgRunningScreenUnlock'])
        # Prepare phone for unlock
        show(strings['lgScreenUnlockSteps'])
    
    time.sleep(1)
    if AT.usbswitch("-l", "LG Screen Unlock"): # I'm not sure whether we need usbswitch, keeping it for backwards compatibility
        rt() # Flush the output buffer
        AT.send('AT%KEYLOCK=0') # This AT command SHOULD unlock the screen instantly. (yes, one command.)
        with open("tmp_output.txt", "r") as f:
            output = f.read()
        # debug only: print("\n\nOutput: \n\n" + output + "\n\n")
        if "error" in output or "Error" in output:
            #print(strings['failText'] + "\n")
            raise ConnectionRefusedError(strings['lgScreenUnlockError'])
        else:
            rt()
            return "Success"
            #print(strings['lgScreenUnlockSuccess'])

def moto_frp(verbose):
    if verbose:
        x = input(strings["motoFastbootGuide"] + " -- Press Enter to continue...")
    try:
        # erase frp partitions upon fastboot access granted
        eraser = FastbootPartitionEraser()
        ecf_stat = eraser.erase_config()
        eps_stat = eraser.erase_persist()
        efr_stat = eraser.erase_frp()
        wdc_stat = eraser.wipe_data_cache()
        return "Success"
    except:
        raise ConnectionError("Unknown unlocking error. Reminder: Moto FRP unlock is expiremental.")

# ==============================================
#  Simple functions that do stuff to the device
# ==============================================

# This version info function works really well with Samsung devices.
# GUI is False by default on nPhoneCLI.
def verinfo(gui=False): # Get version info on the device. Pretty simple. (not simple, this has taken me hours.)
    if gui:
        print(strings['getVerInfo'], end="")
        modemUnlock("SAMSUNG") # Run the command to allow more AT access for SAMSUNG devices unless preloading is enabled
        rt() # Flush the command output file
        AT.send("AT+DEVCONINFO") # Only works when the modem is working with modemUnlock("SAMSUNG")
        output = readOutput("AT") # Output is retrieved from the command
        if output == "" or output == None:
            AT.send("AT+DEVCONINFO") # Only works when the modem is working with modemUnlock("SAMSUNG")
            output = readOutput("AT")
            if output == "" or output == None:
                AT.send("AT+DEVCONINFO", True) # Only works when the modem is working with modemUnlock("SAMSUNG")
                output = readOutput("AT")
                try:
                    if output == "" or output == None:
                        raise ConnectionError(strings['verInfoCheckConn'])
                    else:
                        output = parse_devconinfo(output) # Make the output actually readable
                        model = re.search(r'Model:\s*(\S+)', output) # Extract only the model no. from the output
                        print(strings['okText'])
                except Exception:
                    raise ConnectionError(strings['verInfoCheckConn'])
            else:
                output = parse_devconinfo(output) # Make the output actually readable
                print(strings['okText'])
                print(output) # Print the version info to the output box
        else:
            output = parse_devconinfo(output) # Make the output actually readable
            model = re.search(r'Model:\s*(\S+)', output) # Extract only the model no. from the output
            print(strings['okText'])
            print(output) # Print the version info to the output box
    else:
        modemUnlock("SAMSUNG") # Run the command to allow more AT access for SAMSUNG devices unless preloading is enabled
        rt() # Flush the command output file
        AT.send("AT+DEVCONINFO") # Only works when the modem is working with modemUnlock("SAMSUNG")
        output = readOutput("AT") # Output is retrieved from the command
        if output == "" or output == None:
            AT.send("AT+DEVCONINFO") # Only works when the modem is working with modemUnlock("SAMSUNG")
            output = readOutput("AT")
            if output == "" or output == None:
                if gui:
                    print(strings['failText'])
            else:
                if gui:
                    print(strings['okText'])
        output = parse_devconinfo(output) # Make the output actually readable (parse the output)
        model = re.search(r'Model:\s*(\S+)', output) # Extract only the model no. from the output
        if output == "" or output == None:
            # return "Fail"
            raise ConnectionError("Failed to get version info over modem commands.")
        else:
            return output # Return the version info

def wifitest(verbose): # Opens a hidden WLANTEST menu on Samsung devices
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info)
    success = [
    "AT+WIFITEST=9,9,9,1",
    "+WIFITEST:9,",
    "OK"
    ]
    if verbose:
        print(strings['openingWifitest'])
    MTPmenu()
    modemUnlock("SAMSUNG") # Unlock modem
    AT.send("AT+SWATD=1") # Modem must be relocked for this to work
    rt()
    AT.send("AT+WIFITEST=9,9,9,1") # WifiTEST command to open
    output = readOutput("AT")
    counter = 0
    for i in success:
        if i in output:
            counter += 1
    if counter == 3:
        return "Success"
    else:
        raise RuntimeError("Failed to open WifiTest.")

def reboot(verbose): # Crash an android phone to reboot
    if verbose:
        print(strings['crashingToReboot'])
    MTPmenu()
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info)
    rt()
    try:
        AT.send("AT+CFUN=1,1") # Crashes the phone immediately.
    except Exception as e:
        if "disconnected" in str(e):
            #print(strings['okText']) # Error opening serial means that the command worked, because it reset the phone before it could give a response.
            return "Success"
    output = readOutput("AT")
    if "OK" in output:
        raise ConnectionAbortedError(strings['crashRebootFailed'])

def reboot_sam(verbose): # Crash a Samsung phone to reboot
    if verbose:
        print(strings['crashingToReboot'])
    MTPmenu()
    modemUnlock("SAMSUNG", True)
    info = verinfo(False)
    model = re.search(r'Model:\s*(\S+)', info)
    rt()
    try:
        AT.send("AT+CFUN=1,1") # Crashes the phone immediately.
    except Exception as e:
        if "disconnected" in str(e):
            return "Success" # Error opening serial means that the command worked, because it reset the phone before it could give a response.
    output = readOutput("AT")
    if "OK" in output:
        raise ConnectionAbortedError(strings['crashRebootFailed'])

def bloatRemove(verbose):
    print(strings['uninstallingPackages'])
    adbMenu()
    # Samsung ONLY
    packages = [
        # Samsung default bloatware
        "com.microsoft.office.outlook","com.samsung.android.bixby.ondevice.frfr","com.google.android.apps.photos","com.sec.android.app.sbrowser","com.samsung.android.calendar","com.samsung.android.app.reminder","com.google.android.apps.youtube.music","com.sec.android.app.shealth","com.samsung.android.nmt.apps.t2t.languagepack.enfr","com.sec.android.app.popupcalculator","com.booking.aidprovider","com.samsung.SMT.lang_en_us_l03","com.samsung.android.bixby.ondevice.enus","com.google.android.apps.docs","com.samsung.android.arzone","com.samsung.android.voc","com.samsung.android.app.tips","com.sec.android.app.clockpackage","com.samsung.android.app.find","com.samsung.android.app.notes","com.amazon.appmanager","com.google.android.videos","com.sec.android.app.voicenote","com.amazon.mShop.android.shopping","com.facebook.katana","com.samsung.sree","com.samsung.android.app.spage","com.samsung.android.oneconnect","com.samsung.android.game.gamehome","com.samsung.SMT.lang_fr_fr_l01","com.microsoft.office.officehubrow","com.samsung.android.spay","com.samsung.android.app.watchmanager","com.samsung.android.tvplus","com.sec.android.app.kidshome","com.booking",
        # Verizon bloatware (Note: do not uninstall anything like com.verizon.mips.services. Basic SMS/MMS relies on this in my testing.)
        "com.verizon.appmanager","com.vzwnavigator","com.vzw.syncservice","com.verizon.syncservice","com.verizon.login","com.vzw.voicemail","com.vzw.nflmobile","com.vzw.familybase","com.vzw.familylocator",
        # AT&T bloatware
        "com.att.devicehelp","com.att.addressbooksync","com.dti.att","com.dti.folderlauncher","com.myatt.mobile",
        # T-Mobile bloatware
        "com.tmobile.nameid","com.tmobile.visualvm","com.tmobile.account","com.tmobile.appmanager","com.tmobile.appselector","com.tmobile.pr.mytmobile","com.tmobile.echolocate","com.ironsrc.aura.tmo","com.tmobile.pr.adapt"
    ]
    for package in packages:
        ADBc.send(f"shell pm uninstall --user 0 {package}")
        if "Success" in readOutput("ADB") or "[n" in readOutput("ADB") or "age:" in readOutput("ADB"):
            continue
        elif "unauthorized" in readOutput("ADB"):
            raise ConnectionRefusedError("ADB unauthorized. You need to authorize the device via the USB Debugging prompt. Unplugging and replugging the device may help with this.")
        else:
            raise ConnectionError(strings['devNotConnectedOrOtherErr'])
    if "Success" in readOutput("ADB") or "[n" in readOutput("ADB") or "age:" in readOutput("ADB"):
        #print(strings['okText'])
        if verbose:
            print(strings['debloatSucceeded'])
        return "Success"

def reboot_download_sam(verbose): # Reboot Samsung device to download mode
    try:
        if verbose:
            print(strings['rebootingDownloadMode'])
            MTPmenu() 
        AT.send("AT+FUS?") # Thankfully, no modem unlocking required for this command.
        return "Success"
    except:
        return ConnectionRefusedError(strings['devNotConnectedOrOtherErr'])

def setBatteryPercent(percent, verbose):
    adbMenu()
    percent = str(percent)
    percent = percent.replace("%", "")
    if verbose:
        print(f"Setting percentage to {percent}%...")
    ADBc.send(f"shell dumpsys battery set level {percent}")
    output = readOutput("ADB")
    if "unauthorized" in output:
        raise ConnectionRefusedError("ADB unauthorized. You need to authorize the device via the USB Debugging prompt. Unplugging and replugging the device may help with this.")
    else:
        return "Success"

def resetBatteryPercent(verbose):
    adbMenu()
    if verbose:
        print(f"Resetting percentage...")
    ADBc.send(f"shell dumpsys battery reset")
    output = readOutput("ADB")
    if "unauthorized" in output:
        raise ConnectionRefusedError("ADB unauthorized. You need to authorize the device via the USB Debugging prompt. Unplugging and replugging the device may help with this.")
    else:
        return "Success"

def is_root():
    if os_config == "WINDOWS":  # Windows
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    elif os_config == "LINUX":  # POSIX (Linux, macOS, etc)
        return os.geteuid() == 0

# Check if nPhoneCLI will be able to use serial ports:

if os_config == "LINUX":
    if not check_serial_permissions():
        sys.exit(0)
elif os_config == "WINDOWS":
    if not is_root():
        if not debugMode:
            raise PermissionError(strings['sudoReqdError'])
