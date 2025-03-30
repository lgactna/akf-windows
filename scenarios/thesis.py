"""
This file is derived from the output of `akf-translate` for `thesis.yaml`.

It is the code shown in section 6.2a of the original thesis.
"""

from akf_windows.api.chromium import ChromiumServiceAPI
from akflib.core.hypervisor.vbox import VBoxExportFormatEnum
from akflib.core.hypervisor.vbox import VBoxHypervisor
from pathlib import Path

# Instantiate a hypervisor object tied to a specific virtual machine
vbox_obj = VBoxHypervisor("akf-windows-1")

# Start the virtual machine
vbox_obj.start_vm(wait_for_guest_additions=True)

# Visit a single website
with ChromiumServiceAPI.auto_connect(vbox_obj.get_maintenance_ip()) as chromium_service:
    chromium_service.kill_edge()
    chromium_service.set_browser("msedge")
    page = chromium_service.browser.new_page()
    page.goto("https://bbc.co.uk")  

# Stop the virtual machine
vbox_obj.stop_vm(force=False)

# Export the virtual machine to a disk image
vbox_obj.create_disk_image(
    Path("C:/Users/user/Desktop/akf-windows_1.raw"),
    VBoxExportFormatEnum.RAW
)


