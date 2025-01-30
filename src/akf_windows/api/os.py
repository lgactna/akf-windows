"""
Remotely interact with the Windows operating system.
"""


class WindowsAPI:
    def disable_uac(self) -> None:
        """
        Disable UAC on the Windows operating system.
        """
        raise NotImplementedError

    def install_ssh(self) -> None:
        """
        Install an SSH server on the Windows operating system.

        long process... lol

        in an admin prompt, do the following:
            Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0
        OR
            dism /Online /Add-Capability /CapabilityName:OpenSSH.Server~~~~0.0.1.0

        Assert that it's installed with
            Get-WindowsCapability -Online | ? Name -like 'OpenSSH.Server*'

        Start the service with
            Start-Service sshd
            Start-Service ssh-agent

        Make it automatically start on logon
            Set-Service -Name sshd -StartupType 'Automatic'
            Set-Service -Name ssh-agent -StartupType 'Automatic'

        Finally, create a new firewall rule (or disable the firewall)
            New-NetFirewallRule -Name sshd -DisplayName 'OpenSSH Server (sshd)' -Enabled True -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22

        It should now be possible to SSH into the machine over the host-only
        interface. If necessary, set a password for the account.

        Consider following https://learn.microsoft.com/en-us/troubleshoot/windows-server/user-profiles-and-logon/turn-on-automatic-logon
        and https://www.reddit.com/r/WindowsHelp/comments/1byuyu6/how_to_bypass_windows_11_oobe_forced_microsoft/.
        """
        raise NotImplementedError
