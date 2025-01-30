"""
Mouse and keyboard capabilities provided by the `pyautogui` and `keyboard`
libraries.

Although these capabilities are already provided through subclasses of the 
`HypervisorABC` base class, it may be the case that not all hypervisors support
mouse and keyboard events directly through the hypervisor. This subservice
gives access to "in-host" 
"""