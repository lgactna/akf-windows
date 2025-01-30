To get the AKF Windows agent running, the current procedure is as follows:
- Install Python 3.11+
- Install Git
- Run `uv pip install git+https://github.com/lgactna/akf-windows.git` (`uv` optional)
- Run `akf-agent` on the command-line

In the future:
- this may be distributed as a standalone executable, through PyInstaller
- a script may be included to make `akf-agent` persistent, such as an automatic on-startup Windows Service


## PyInstaller

Sometimes it'll complain that `akflib` can't be found, probably because of my local environment:
```
pyinstaller --onefile --paths=.venv/Lib/site-packages src/akf_windows/server/__init__.py
```

The above command, run from the root of this repository, should work and generate `__init__.exe`. Ensure all of the following are true:
- `pyinstaller` is installed in the venv
- The venv is activated

See [`black`'s GitHub Action](https://github.com/psf/black/blob/main/.github/workflows/upload_binary.yml) for auto-binary uploads on release.