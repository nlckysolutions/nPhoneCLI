# nPhoneCLI
nPhoneKIT as a interfaceable and easy-to-implement Python PYPI package.

---

**Legal Warning: FRP Unlocking is only legal on your own devices. I am not responsible for misuse of this package. Only use it on your own devices.**

---

# Usage

> [!NOTE]
> On your system, to use nPhoneCLI, you will also need ADB and Python3 installed. Also, please report any unexpected errors/issues by opening a GitHub issue.

> [!IMPORTANT]
> If you have any contributions to make, feel free to fork, modify, and submit a PR to get it pushed to the main repo!

First, install nphonecli:
```bash
pip install nphonecli
```

Then, import nphonecli into your code:

```python
import nphonecli
```

Then, use whatever functions are neccesary:

Example: 
```python
import nphonecli

try:
  # Save the status to check whether it succeeded later
  status = nphonecli.reboot(verbose=False)
except ConnectionAbortedError:
  # Catch the ConnectionAbortedError if the device couldn't connect.
  print("Error, the device could not reboot.")

if status = "Success"
  # Print success message if status indicates a successful reboot.
  print("Success, device rebooted")
```
List of all functions and purposes:

| Title                               | Function                                       | Params                      | Uses                                                  | Successful                                                                               | Unsuccessful                                        | Method(s) |
|-------------------------------------|------------------------------------------------|-----------------------------|-------------------------------------------------------|------------------------------------------------------------------------------------------|-----------------------------------------------------|-----------|
| Get Version Info                    | verinfo(gui: bool)                             | gui: bool                   | Fetch version info from a device.                     | Returns a dict which contains version info,  or prints the dict if the gui bool is true. | Raises a ConnectionError.                           | AT        |
| Reboot (Android)                    | reboot(verbose: bool)                          | verbose: bool               | Force-reboot a device (excl. Samsung).                | Returns "Success".                                                                       | Raises a ConnectionAbortedError.                    | AT        |
| Reboot (Samsung)                    | reboot_sam(verbose: bool)                      | verbose: bool               | Force-reboot a device (incl. Samsung).                | Returns "Success".                                                                       | Raises a ConnectionAbortedError.                    | AT        |
| Reboot Download Mode (Samsung)      | reboot_download_sam(verbose: bool)             | verbose: bool               | Force-reboot a Samsung device to Download Mode.       | Returns "Success".                                                                       | Raises a ConnectionRefusedError.                    | AT        |
| Open WIFITEST (Samsung)             | wifitest(verbose: bool)                        | verbose: bool               | Open WIFITEST menu on Samsung devices.                | Returns "Success".                                                                       | Raises a RuntimeError.                              | AT        |
| LG Screen Unlock                    | lg_screen_unlock(verbose: bool)                | verbose: bool               | Unlock the screen of older LG devices.                | Returns "Success".                                                                       | Raises a ConnectionRefusedError.                    | AT        |
| Motorola Fastboot FRP Unlock        | moto_frp(verbose: bool)                        | verbose: bool               | Remove FRP lock from Motorola devices.                | Returns "Success".                                                                       | Raises a ConnectionError.                           | Fastboot  |
| FRP Unlock 2024 (Samsung, USA Only) | frp_unlock_2024(verbose: bool)                 | verbose: bool               | Remove FRP lock from 2024-patch Samsung USA devices.  | Returns "Success".                                                                       | Raises a ConnectionError or ConnectionRefusedError. | AT, ADB   |
| FRP Unlock 2022-2023 (Samsung)      | frp_unlock_2022_2023(verbose: bool)            | verbose: bool               | Remove FRP lock from 2022-2023-patch Samsung devices. | Returns "Success".                                                                       | Raises a ConnectionError or ConnectionRefusedError. | AT, ADB   |
| FRP Unlock Pre-2022 (Samsung)       | frp_unlock_pre2022(verbose: bool)              | verbose: bool               | Remove FRP lock from pre-2022-patch Samsung devices.  | Returns "Success".                                                                       | Raises a ConnectionError or ConnectionRefusedError. | AT, ADB   |
| Set Battery Percentage              | setBatteryPercent(percent: int, verbose: bool) | percent: int, verbose: bool | Set a battery percentage (faked).                     | Returns "Success".                                                                       | Raises a ConnectionRefusedError.                    | ADB       |
| Reset Battery Percentage            | resetBatteryPercent(verbose: bool)             | verbose: bool               | Reset the battery percent to normal.                  | Returns "Success".                                                                       | Raises a ConnectionRefusedError.                    | ADB       |
| Remove Bloatware                    | bloatRemove(verbose: bool)                     | verbose: bool               | Remove bloatware on Samsung devices.                  | Returns "Success".                                                                       | Raises a ConnectionError or ConnectionRefusedError. | ADB       |

---

**That's about it! You can inspect the code in src/nphonecli/core.py! Remember, do not use this on devices you do not own or have explicit permission from the owner to unlock.** 

> [!TIP]
> Use verbose=True/gui=True in order to provide detailed instructions, if using the package with an end user. Automation should not need this, but the instructions will still need to be performed.

---

*****Happy New Year 2026 from NlckySolutions™!*****

This will be the final NlckySolutions™ project to be released in 2025.

Released on Dec. 31st 2025.
