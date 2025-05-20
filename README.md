
## Installation
- Install Python 3.11+
- Install git
- Install `uv` with `pip install uv` (recommended)
- Run `uv venv` and `uv pip install .` 
- Download the VirtualBox SDK from [https://www.virtualbox.org/wiki/Downloads](https://www.virtualbox.org/wiki/Downloads), then *from the virtual environment*, run `python vboxapisetup.py install` inside the `/install` folder of the decompressed SDK.


## Agent/VM setup
To get a suitable Windows virtual machine running for AKF, do the following:
- Install Vagrant and Virtualbox
- `uv pip install pyinstaller`
- Build the agent executable with `pyinstaller --onefile -n agent.exe --paths=.venv/Lib/site-packages src/akf_windows/server/__init__.py`
- `vagrant up`, wait for the machine to be created
    - If Vagrant times out, you can increase the timeout limit or just run it again
- Clone the resulting machine as many times as desired

If you don't like Vagrant, you can also set up your own Windows machine. Manually copy the agent executable and have it run on startup. It is strongly recommended that you have auto-logon enabled.

You can also install this library with `uv pip install git+https://github.com/lgactna/akf-windows.git`, then run `akf-agent` to start the agent script. This assumes you have Python installed on the target machine.

## Demos
After you've followed the steps above, you can run some of the demos from the root of the repo:

```sh
# Convert the sample declarative scenario to a Python script, write to stdout
akf-translate scenarios/sample.yaml --translate

# Write to a file instead (this is how scenarios/sample_linted.py was made)
akf-translate scenarios/sample.yaml --translate --output-file scenarios/sample.py

# Execute a declarative scenario directly
akf-translate scenarios/sample.yaml --execute

# Execute the generated Python script
python scenarios/sample.py
```

`scenarios/sample_linted.py` is the immediate output of the second command above, but with `isort` and `black` modifications.


## PyInstaller

To generate the agent binary:
```
pyinstaller --onefile -n agent.exe --paths=.venv/Lib/site-packages src/akf_windows/server/__init__.py
```

The above command, run from the root of this repository, should work and generate `__init__.exe`. Ensure all of the following are true:
- `pyinstaller` is installed in the venv
- The venv is activated
- You've installed the VirtualBox SDK

The VirtualBox SDK cannot be redistributed with this project under the terms of the VirtualBox Extension Pack, so a pre-built agent cannot be provided.