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

# Visit a list of websites from a file with some jitter
chromium_service = ChromiumServiceAPI.auto_connect("192.168.50.4")
autogui_service = PyAutoGuiServiceAPI.auto_connect("192.168.50.4")

# Visit a list of websites from a file with some jitter, and save their screenshots
# to the Downloads folder
url_file = Path("cat_urls.txt")
with open(url_file, "rt") as f:
    urls = [line.strip() for line in f.readlines()]
chromium_service.kill_edge()
chromium_service.set_browser("msedge")
page = chromium_service.browser.new_page()

# Visit these sites in order, and save some photos of the pages to the
# Downloads folder
for idx, url in enumerate(urls, start=1):
    page.goto(url)
    page.screenshot(path=f"C:/Users/user/Downloads/cat_page_{idx}.png", full_page=True)
    time.sleep(60 + random.randint(-15, 15))


exit()

# Manually visit next page - we won't click on the link since it opens a new tab,
# but as far as artifacts go, the effect is the same
page.goto("https://www.google.com/search?q=free+cat+wallpapers")
page.goto("https://drive.google.com/file/d/1EdYkhP0C6ouo1sh2N8JAUerNiHd5LYFK/view?usp=sharing")
page.goto("https://drive.usercontent.google.com/download?id=1EdYkhP0C6ouo1sh2N8JAUerNiHd5LYFK&export=download&authuser=0")
with page.expect_download() as download_info:
    page.locator("[type='submit']").click()
    download = download_info.value
    download.save_as(rf"C:\Users\user\Downloads\{download.suggested_filename}")

# Now manually open Explorer to open the file - we can trivially execute this
# through guest additions or by opening the command prompt since we know where
# the file is, but that's not how a user normally does it. For the sake of an
# example, this is how we'd use PyAutoGUI to do it.
autogui_service.pyautogui.hotkey("win", "e")
time.sleep(2)

# Focus address bar
autogui_service.pyautogui.hotkey("ctrl", "l")
autogui_service.pyautogui.typewrite(r"C:\Users\user\Downloads")
autogui_service.pyautogui.press("enter")
time.sleep(2)

# Search for file
autogui_service.pyautogui.hotkey("ctrl", "f")
autogui_service.pyautogui.typewrite("cats.exe")
autogui_service.pyautogui.press("enter")
time.sleep(2)

# Focus and open file
autogui_service.pyautogui.press("f6")
autogui_service.pyautogui.press("f6")
autogui_service.pyautogui.press("down")
autogui_service.pyautogui.press("enter")
time.sleep(2)

# page.locator("div[role='button']").click()