- Install Python 3.11+
- Install git
- Install `uv` with `pip install uv` (recommended)
- Run `uv venv` and `uv pip install .` 
- Download the VirtualBox SDK from [https://www.virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads), then *from the virtual environment*, run `python vboxapisetup.py install` inside the `/install` folder of the decompressed SDK.

To get a suitable Windows virtual machine running for AKF, do the following:
- Install Vagrant and Virtualbox
- `uv pip install pyinstaller`
- Build the agent executable with `pyinstaller --onefile --paths=.venv/Lib/site-packages src/akf_windows/server/__init__.py`
    - In the future, this may be downloaded from GitHub releases, but this isn't currently the case
- `vagrant up`
- Clone the resulting machine as many times as desired

If you don't like Vagrant, you can also set up your own Windows machine. Manually copy the agent executable and have it run on startup. It is strongly recommended that you have auto-logon enabled.

You can also install this library with `uv pip install git+https://github.com/lgactna/akf-windows.git`, then run `akf-agent` to start the agent script. This assumes you have Python installed on the target machine.


## PyInstaller

Sometimes it'll complain that `akflib` can't be found, probably because of my local environment:
```
pyinstaller --onefile --paths=.venv/Lib/site-packages src/akf_windows/server/__init__.py
```

The above command, run from the root of this repository, should work and generate `__init__.exe`. Ensure all of the following are true:
- `pyinstaller` is installed in the venv
- The venv is activated

See [`black`'s GitHub Action](https://github.com/psf/black/blob/main/.github/workflows/upload_binary.yml) for auto-binary uploads on release.