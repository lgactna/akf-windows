Vagrant.configure("2") do |config|
    config.vm.box = "gusztavvargadr/windows-11"
    config.vm.communicator = "winrm"
    config.winrm.username = "vagrant"
    config.winrm.password = "vagrant"
  
    config.vm.provider "virtualbox" do |vb|
      vb.gui = true
      vb.memory = 4096
    end    

    # First network interface (NAT) is default
    # Second network interface (host-only)
    config.vm.network "private_network", ip: "192.168.50.4"
  
    # Create a new user
    config.vm.provision "shell", inline: <<-SHELL
      New-LocalUser -Name "user" -Password (ConvertTo-SecureString "user" -AsPlainText -Force)
      Add-LocalGroupMember -Group "Administrators" -Member "user"
    SHELL
  
    # Copy agent.exe from host to guest
    config.vm.provision "file", source: "dist/__init__.exe", destination: "C:/agent.exe"
  
    # Run agent.exe on startup
    config.vm.provision "shell", inline: <<-SHELL
      $action = New-ScheduledTaskAction -Execute "C:\\agent.exe"
      $trigger = New-ScheduledTaskTrigger -AtStartup
      Register-ScheduledTask -TaskName "AgentStartup" -Action $action -Trigger $trigger -User "NT AUTHORITY\\SYSTEM" -RunLevel Highest -Force
    SHELL

    # Allow all inbound and outbound traffic to agent.exe through Windows Firewall
    config.vm.provision "shell", inline: <<-SHELL
      New-NetFirewallRule -DisplayName "Allow inbound traffic to agent.exe" -Direction Inbound -Program "C:\\agent.exe" -Action Allow
      New-NetFirewallRule -DisplayName "Allow outbound traffic to agent.exe" -Direction Outbound -Program "C:\\agent.exe" -Action Allow
    SHELL

    # Run agent.exe when the machine is first run
    config.vm.provision "shell", inline: <<-SHELL
      Start-Process -FilePath "C:\\agent.exe"
    SHELL
  end