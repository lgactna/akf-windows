import multiprocessing

from akf_windows.server.main import main

if __name__ == "__main__":
    # On Windows calling this function is necessary.
    multiprocessing.freeze_support()

    main()
