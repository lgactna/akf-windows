To get the AKF Windows agent running, the current procedure is as follows:
- Install Python 3.11+
- Install Git
- Run `uv pip install git+https://github.com/lgactna/akf-windows.git` (`uv` optional)
- Run `akf-agent` on the command-line

In the future:
- this may be distributed as a standalone executable, through PyInstaller
- a script may be included to make `akf-agent` persistent, such as an automatic on-startup Windows Service