"""
A general scenario in which a user visits a variety of cat websites, before
eventually downloading ransomware and running it. This occurs over the span of two
days, as "faked" by advancing the BIOS clock to specific dates.

In addition to the disk image of the resulting virtual machine, this scenario
also generates a network capture that is intended to be used as part of building
a decryptor for the ransomware.

To prepare a virtual machine for use with this scenario, you can use the Vagrantfile
that is included in this directory. Note that the process of copying the agent may
take a while.
"""

import datetime
import logging
import random
import sys
import time
from pathlib import Path

from akflib.core.hypervisor.vbox import VBoxExportFormatEnum, VBoxHypervisor
from akflib.rendering.core import bundle_to_pdf, get_pandoc_path, get_renderer_classes
from akflib.rendering.objs import AKFBundle

from akf_windows.api.artifacts import WindowsArtifactServiceAPI
from akf_windows.api.chromium import ChromiumServiceAPI
from akf_windows.api.autogui import PyAutoGuiServiceAPI

# Change this based on what you've named the resulting VirtualBox machine.
MACHINE_NAME = "akf-windows-3"

# Set up logging
logging.basicConfig(
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("scenario.log", mode="w", encoding="utf-8"),
    ],
    level=logging.INFO,
    format="%(filename)s:%(lineno)d | %(asctime)s | [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger()

# Create a new CASE bundle to be reused throughout the scenario. This will contain
# much of the relevant ground truth for the scenario, but we can also supplement
# it with Python logging output, as well.
akf_bundle = AKFBundle()

# Instantiate a hypervisor object tied to a specific virtual machine
logger.info(f'Using virtual machine "{MACHINE_NAME}"')
vbox_obj = VBoxHypervisor(MACHINE_NAME, akf_bundle)

# # Start the machine
# logger.info("Starting the VM and enabling network capturing")
# vbox_obj.start_network_capture(Path("traffic.pcap"))
# vbox_obj.start_vm(wait_for_guest_additions=True)

# with ChromiumServiceAPI.auto_connect(vbox_obj.get_maintenance_ip()) as chromium_service:
#     # Visit a list of websites from a file with some jitter, and save their screenshots
#     # to the Downloads folder
#     logger.info("Visiting reddit websites")
    
#     url_file = Path("cat_urls.txt")
#     with open(url_file, "rt") as f:
#         urls = [line.strip() for line in f.readlines()]
#     chromium_service.kill_edge()
#     chromium_service.set_browser("msedge")
#     page = chromium_service.browser.new_page()

#     # Visit these sites in order
#     for idx, url in enumerate(urls, start=1):
#         logger.info(f"Visiting {url} and generating screenshot")
#         page.goto(url)
#         page.screenshot(path=f"C:/Users/user/Downloads/cat_page_{idx}.png", full_page=True)
#         time.sleep(60 + random.randint(-15, 15))
    
#     # Now visit a suspicious looking link directly
#     logger.info("Downloading ransomware")
#     with ChromiumServiceAPI.auto_connect(vbox_obj.get_maintenance_ip()) as chromium_service:
#         page.goto("https://www.google.com/search?q=free+cat+wallpapers")
#         page.goto("https://pastebin.com/C7jhGFSr")
#         page.goto("https://drive.google.com/file/d/1EdYkhP0C6ouo1sh2N8JAUerNiHd5LYFK/view?usp=sharing")
#         # Manually visit next page - we won't click on the link since it opens a new tab,
#         # but as far as artifacts go, the effect is the largely the same
#         page.goto("https://drive.usercontent.google.com/download?id=1EdYkhP0C6ouo1sh2N8JAUerNiHd5LYFK&export=download&authuser=0")
#         with page.expect_download() as download_info:
#             page.locator("[type='submit']").click()
#             download = download_info.value
#             download.save_as(rf"C:\Users\user\Downloads\{download.suggested_filename}")

# # Now manually open Explorer to open the file - we can trivially execute this
# # through guest additions or by opening the command prompt since we know where
# # the file is, but that's not how a user normally does it. For the sake of an
# # example, this is how we'd use PyAutoGUI to do it.
# logger.info("Running ransomware")
# with PyAutoGuiServiceAPI.auto_connect(vbox_obj.get_maintenance_ip()) as autogui_service:    
#     autogui_service.pyautogui.hotkey("win", "e")
#     time.sleep(2)

#     # Focus address bar
#     autogui_service.pyautogui.hotkey("ctrl", "l")
#     autogui_service.pyautogui.typewrite(r"C:\Users\user\Downloads")
#     autogui_service.pyautogui.press("enter")
#     time.sleep(2)

#     # Search for file
#     autogui_service.pyautogui.hotkey("ctrl", "f")
#     autogui_service.pyautogui.typewrite("cats.exe")
#     autogui_service.pyautogui.press("enter")
#     time.sleep(2)

#     # Focus and open file
#     autogui_service.pyautogui.press("f6")
#     autogui_service.pyautogui.press("f6")
#     autogui_service.pyautogui.press("down")
#     autogui_service.pyautogui.press("enter")
#     time.sleep(2)

# # Collect volatile memory
# logger.info("Creating memory dump")
vbox_obj.create_memory_dump(Path("memory.dmp"))

# Collect Edge artifacts
logger.info("Collecting Edge artifacts")
with ChromiumServiceAPI.auto_connect(vbox_obj.get_maintenance_ip()) as chromium_service:
    history = chromium_service.get_history("msedge", None)
    akf_bundle.add_object(history)

# Generate Prefetch artifacts
logger.info("Collecting Prefetch artifacts")
with WindowsArtifactServiceAPI.auto_connect(
    vbox_obj.get_maintenance_ip()
) as win_artifact:
    prefetch_objs = win_artifact.collect_prefetch_dir(None)
    akf_bundle.add_objects(prefetch_objs)

# Stop the virtual machine; end network capture
logger.info("Tearing down the VM and finishing packet capture")
# vbox_obj.stop_vm(force=False)
vbox_obj.stop_network_capture()

# Export the virtual machine to a disk image
logger.info("Creating disk image")
vbox_obj.create_disk_image(Path("disk.raw"), VBoxExportFormatEnum.RAW)

# Export the CASE bundle to a JSON-LD file
logger.info("Writing artifacts.jsonld")
akf_bundle.write_to_jsonld(Path("artifacts.jsonld"), indent=2)

# Generate a PDF of the CASE bundle
logger.info("Generating PDF of the CASE bundle")
renderer_classes = get_renderer_classes(
    [
        "akflib.renderers.prefetch.PrefetchRenderer",
        "akflib.renderers.urlhistory.URLHistoryRenderer",
    ]
)

pandoc_path = get_pandoc_path()
if pandoc_path is None:
    raise RuntimeError(
        "Unable to find path to Pandoc executable (make sure it is on PATH)"
    )

pandoc_output_folder = Path("pandoc_out")
pandoc_output_folder.mkdir(parents=True, exist_ok=True)

bundle_to_pdf(
    akf_bundle,
    renderer_classes,
    pandoc_output_folder,
    pandoc_path,
    group_renderers=False,
)
