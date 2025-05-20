For development (note that this is a separate virtual environment from the agent
itself):

``` 
pip install uv
uv venv
uv sync
```

To generate the ransomware executable (which must be done on a Windows machine):
```
pyinstaller -F src/encrypt.py
```

This is a destructive operation. Don't run this on your own machine!
