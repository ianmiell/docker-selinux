"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docker_selinux(ShutItModule):

	def build(self, shutit):
		# Some useful API calls for reference see shutit's docs for more info and options:
		# shutit.send(send) - send a command
		# shutit.multisend(send,send_dict) - send a command, dict contains {expect1:response1,expect2:response2,...}
		# shutit.log(msg) - send a message to the log
		# shutit.run_script(script) - run the passed-in string as a script
		# shutit.send_file(path, contents) - send file to path on target with given contents as a string
		# shutit.send_host_file(path, hostfilepath) - send file from host machine to path on the target
		# shutit.send_host_dir(path, hostfilepath) - send directory and contents to path on the target
		# shutit.host_file_exists(filename, directory=False) - returns True if file exists on host
		# shutit.file_exists(filename, directory=False) - returns True if file exists on target
		# shutit.add_to_bashrc(line) - add a line to bashrc
		# shutit.get_url(filename, locations) - get a file via url from locations specified in a list
		# shutit.user_exists(user) - returns True if the user exists on the target
		# shutit.package_installed(package) - returns True if the package exists on the target
		# shutit.pause_point(msg='') - give control of the terminal to the user
		# shutit.step_through(msg='') - give control to the user and allow them to step through commands
		# shutit.send_and_get_output(send) - returns the output of the sent command
		# shutit.send_and_match_output(send, matches) - returns True if any lines in output match any of 
		#                                               the regexp strings in the matches list
		# shutit.install(package) - install a package
		# shutit.remove(package) - remove a package
		# shutit.login(user='root', command='su -') - log user in with given command, and set up prompt and expects
		# shutit.logout() - clean up from a login
		# shutit.set_password(password, user='') - set password for a given user on target
		# shutit.get_config(module_id,option,default=None,boolean=False) - get configuration value
		# shutit.get_ip_address() - returns the ip address of the target
		# shutit.add_line_to_file(line, filename) - add line (or lines in an array) to the filename
		vagrant_dir = shutit.cfg[self.module_id]['vagrant_dir']
		setenforce  = shutit.cfg[self.module_id]['setenforce']
		compile_policy  = shutit.cfg[self.module_id]['compile_policy']
		shutit.install('linux-generic linux-image-generic linux-headers-generic linux-signed-generic')
		shutit.install('virtualbox')
		shutit.send('wget -qO- https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2_x86_64.deb > /tmp/vagrant.deb')
		shutit.send('dpkg -i /tmp/vagrant.deb')
		shutit.send('rm /tmp/vagrant.deb')
		shutit.send('mkdir -p ' + vagrant_dir)
		shutit.send('cd ' + vagrant_dir)
		# If the Vagrantfile exists, we assume we've already init'd appropriately.
		if not shutit.file_exists('Vagrantfile'):
			shutit.send('vagrant init jdiprizio/centos-docker-io')
		# Query the status - if it's powered off or not created, bring it up.
		if shutit.send_and_match_output('vagrant status',['.*poweroff.*','.*not created.*','.*aborted.*']):
			shutit.send('vagrant up')
		# It should be up now, ssh into it and get root.
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su')
		# Insure required software's installed.
		shutit.send('yum install -y wget selinux-policy-devel')
		shutit.send('rm -rf /root/selinux')
		shutit.send('mkdir -p /root/selinux')
		shutit.send('cd /root/selinux')
		# Ensure we've cleaned up the files we're adding here.
		shutit.add_line_to_file('''policy_module(docker_apache,1.0)
virt_sandbox_domain_template(docker_apache)
allow docker_apache_t self: capability { chown dac_override kill setgid setuid net_bind_service sys_chroot sys_nice sys_tty_config } ;
allow docker_apache_t self:tcp_socket create_stream_socket_perms;
allow docker_apache_t self:udp_socket create_socket_perms;
corenet_tcp_bind_all_nodes(docker_apache_t)
corenet_tcp_bind_http_port(docker_apache_t)
corenet_udp_bind_all_nodes(docker_apache_t)
corenet_udp_bind_http_port(docker_apache_t)
sysnet_dns_name_resolve(docker_apache_t)
permissive docker_apache_t;
'''.split('\n'),'/root/selinux/docker_apache.te')
		shutit.add_line_to_file('''make -f /usr/share/selinux/devel/Makefile docker_apache.pp
semodule -i docker_apache.pp
docker run -d --name selinuxdock --security-opt label:type:docker_apache_t httpd
'''.split('\n'),'/root/selinux/script.sh')
		shutit.send('chmod +x /root/selinux/script.sh')
		# Ensure we have the latest version of docker.
		shutit.send('wget -qO- https://get.docker.com/builds/Linux/x86_64/docker-latest > docker')
		shutit.send('mv -f docker /usr/bin/docker')
		shutit.send('chmod +x /usr/bin/docker')
		# Insure required software's installed.
		shutit.send('yum install -y wget selinux-policy-devel')
		# Optional code for enforcing>
		if setenforce: 
			shutit.send('''sed -i 's/=permissive/=enforcing/' /etc/selinux/config''')
		else:
			shutit.send('''sed -i 's/=enforcing/=permissive/' /etc/selinux/config''')
		# Log out to ensure the prompt stack is stable.
		shutit.logout()
		shutit.logout(command='sudo reboot')
		# Give it time...
		shutit.send('sleep 30')
		# Go back in.
		shutit.login(command='vagrant ssh')
		# Get back to root.
		shutit.login(command='sudo su')
		# Remove any pre-existing containers.
		# Recycle docker service.
		shutit.send('systemctl stop docker')
		shutit.send('systemctl start docker')
		# Remove any pre-existing containers.
		shutit.send('docker rm -f selinuxdock || /bin/true')
		shutit.send('mkdir -p /root/selinux')
		shutit.send('cd /root/selinux')
		if compile_policy:
			# Ensure we've cleaned up the files we're adding here.
			shutit.send('rm -rf /root/selinux/docker_apache.tc /root/selinux/script.sh')
			shutit.add_line_to_file('''policy_module(docker_apache,1.0)
virt_sandbox_domain_template(docker_apache)
allow docker_apache_t self: capability { chown dac_override kill setgid setuid net_bind_service sys_chroot sys_nice sys_tty_config } ;
allow docker_apache_t self:tcp_socket create_stream_socket_perms;
allow docker_apache_t self:udp_socket create_socket_perms;
corenet_tcp_bind_all_nodes(docker_apache_t)
corenet_tcp_bind_http_port(docker_apache_t)
corenet_udp_bind_all_nodes(docker_apache_t)
corenet_udp_bind_http_port(docker_apache_t)
sysnet_dns_name_resolve(docker_apache_t)
'''.split('\n'),'/root/selinux/docker_apache.te')
			if setenforce: 
				shutit.add_line_to_file('permissive docker_apache_t','/root/selinux/docker_apache.te')
			shutit.add_line_to_file('''make -f /usr/share/selinux/devel/Makefile docker_apache.pp
semodule -i docker_apache.pp
docker run -d --name selinuxdock --security-opt label:type:docker_apache_t httpd
'''.split('\n'),'/root/selinux/script.sh')
			shutit.send('chmod +x /root/selinux/script.sh')
			# Ensure we have the latest version of docker.
			# Optional code for enforcing>
			shutit.send('sleep 2 && docker logs selinuxdock')
			shutit.send('/root/selinux/script.sh')
			# Have a look at the log output.
			shutit.send('dmesg | grep -i SELinux')
			shutit.send('grep -w denied /var/log/audit/audit.log | tail')
		shutit.pause_point('Have a shell:')
		# Log out.
		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'vagrant_dir', '/tmp/vagrant_dir')
		shutit.get_config(self.module_id, 'setenforce', False, boolean=True)
		shutit.get_config(self.module_id, 'compile_policy', True, boolean=True)
		return True


def module():
	return docker_selinux(
		'io.dockerinpractice.docker_selinux.docker_selinux', 1184271914.00,
		description='Test of docker selinux on a vagrant box',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

