I have developed a program that carries out well-defined actions on a virtual machine. These actions are expressed using a YAML file, and can also be called a "declarative script" or a "declarative scenario".

A scenario is composed of the following six keys:
- `name`: The name of the scenario.
- `description`: A description of the scenario.
- `author`: The author(s) who developed the scenario.
- `seed`: The random seed to use when executing this scenario. For scenarios that contain non-determinstic elements, this can be used to change how the scenario behaves.
- `libraries`: The Python libraries/modules that must be available for this scenario to be executed.
- `actions`: A sequence of actions, as described below. Actions are executed in order.

Each "action" under the `actions` key contains the following three keys:
- `name`: The description for this action.
- `module`: The module that will be used to execute this action.
- `args`: A dictionary of arguments that will be passed to the module defined in `module`.

A simple example can be seen in the following code block:

```yaml
name: Sample Scenario
description: Description goes here.
author: lgactna
seed: "0"
libraries:
  - akflib.modules
actions:
  # Setup: create a new CASE bundle and start a virtual machine
  - name: Create a new CASE bundle to be reused throughout the scenario
    module: akflib.modules.case.AKFBundleModule
  - name: Instantiate a hypervisor object tied to a specific virtual machine
    module: vbox_start
    args:
      machine_name: "akf-windows-1"
  - name: Start the virtual machine
    module: vbox_start_machine
```

This minimal example contains three actions. 
- The first action creates a new "CASE bundle", which is a variable that will be passed as global state to all successive actions. It initializes logging and reporting for the entire 
- The second action creates a new instance of a VirtualBox hypervisor object, which can be reused in the same manner as the CASE bundle. The hypervisor instance is bound to the machine "akf-windows-1", which means that all actions using the hypervisor instance will take effect against this machine.
- The third action uses the VirtualBox hypervisor instance (created as a result of the second action) to start the virtual machine. 

You are responsible for creating new declarative scenarios that adhere to the specifications above. You have access to the following modules and arguments:

| Name                     | Description                                                                                                       | Arguments                                                                                                                                                                                                                                 |
| ------------------------ | ----------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `create_akf_bundle`      | Creates a new CASE bundle for use throughout the declarative scenario.                                            | None                                                                                                                                                                                                                                      |
| `write_akf_bundle`       | Write the contents of the currently active CASE bundle to disk as a JSON-LD file.                                 | - `output_file`: The file to write the CASE bundle to.                                                                                                                                                                                    |
| `render_akf_bundle`      | Pass the currently active CASE bundle through a set of provided renderers and construct a valid PDF using Pandoc. | None                                                                                                                                                                                                                                      |
| `vbox_start`             | Create a new VirtualBox instance bound to a specific virtual machine by name.                                     | - `machine_name` (str): The machine to use.                                                                                                                                                                                               |
| `vbox_start_machine`     | Power on the currently active virtual machine.                                                                    | None                                                                                                                                                                                                                                      |
| `vbox_stop_machine`      | Power off the currently active virtual machine.                                                                   | None                                                                                                                                                                                                                                      |
| `vbox_create_disk_image` | Export a disk image of the current virtual machine.                                                               | - `output_path` (str): Where to write the disk image to.<br>- `image_format` (str): one of "raw", "vdi", "vmdk", or "vhd"                                                                                                                 |
| `artifact_service_start` | Remotely start and connect to the subservice responsible for collecting Windows artifacts.                        | None                                                                                                                                                                                                                                      |
| `artifact_service_stop`  | Disconnect from the subservice responsible for collecting Windows artifacts.                                      | None                                                                                                                                                                                                                                      |
| `prefetch`               | Analyze all prefetch files on disk and construct their corresponding CASE objects.                                | None                                                                                                                                                                                                                                      |
| `chromium_service_start` | Remotely start and connect to the subservice responsible for interacting with Chromium browsers.                  | None                                                                                                                                                                                                                                      |
| `chromium_service_stop`  | Disconnect from the subservice responsible for interacting with Chromium browsers.                                | None                                                                                                                                                                                                                                      |
| `chromium_visit_urls`    | Visit one or more URLs using a specified web browser.                                                             | - `browser` (str): one of "msedge", "chromium"<br>- `urls` (list[str]): a sequence of URLs to visit (mutually exclusive with `file`)<br>- `file`: a filepath to a newline-separated list of URLs on disk (mutually exclusive with `urls`) |
| `chromium_history`       | Collect browsing history from a specified web browser and construct their corresponding CASE objects.             | None                                                                                                                                                                                                                                      |

The contents of your `libraries` list should always be the following:
```yaml
libraries:
	- akflib.modules
	- akf_windows.modules
```

You will be provided a prompt in the `<scenario_prompt>` tag. Given the description of the modules above, please construct a declarative script that achieves the prompt requested within the `<scenario_prompt>` tag.

<scenario_prompt>
Please create a scenario in which a user visits news-related websites with Microsoft Edge, then visits entertainment-related websites with Google Chrome. The user should power their computer on and off at least three times during this scenario.
</scenario_prompt>