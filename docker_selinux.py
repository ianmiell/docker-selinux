"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docker_selinux(ShutItModule):

	def build(self, shutit):
		vagrant_dir = shutit.cfg[self.module_id]['vagrant_dir']
		shutit.install('virtualbox')
		shutit.send('wget -qO- https://dl.bintray.com/mitchellh/vagrant/vagrant_1.7.2_x86_64.deb > /tmp/vagrant.deb')
		shutit.send('dpkg -i /tmp/vagrant.deb')
		shutit.send('rm /tmp/vagrant.deb')
		shutit.login(user='imiell',command='su')
		shutit.send('mkdir -p ' + vagrant_dir)
		shutit.send('cd ' + vagrant_dir)
		# If the Vagrantfile exists, we assume we've already init'd appropriately.
		if not shutit.file_exists('Vagrantfile'):
			shutit.send('vagrant init wrossmck/centos')
		# Query the status - if it's powered off or not created, bring it up.
		shutit.multisend('vagrant status',{'poweroff':'vagrant up','is not created':'vagrant up'})
		# It should be up now, ssh into it and get root.
		shutit.login(command='vagrant ssh')
		shutit.login(command='sudo su')
		shutit.send('yum install -y wget')
		shutit.send('yum install -y selinux-policy-devel')
		shutit.send('cd /root')
		shutit.send('mkdir -p /root/selinux')
		shutit.send('cd /root/selinux')
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
		# Recycle docker service.
		shutit.send('systemctl stop docker')
		shutit.send('systemctl start docker')
		# Remove any pre-existing containers.
		shutit.send('docker rm -f selinuxdock || /bin/true')
		# optional code for enforcing
		#shutit.send('''sed -i 's/=permissive/=enforcing/' /etc/selinux/config''')
		#shutit.logout()
		#shutit.logout(command='sudo reboot')
		#shutit.send('sleep 20')
		#shutit.login(command='vagrant ssh')
		#shutit.login(command='sudo su')
		shutit.send('/root/selinux/script.sh')
		# Have a look at the log output.
		shutit.send('sleep 2 && docker logs selinuxdock')
		# Un-comment this to get a shell interactively if you want.
		#shutit.pause_point('Have a shell:')
		shutit.logout()
		shutit.logout()
		shutit.logout()
		return True

	def get_config(self, shutit):
		shutit.get_config(self.module_id, 'vagrant_dir', '/tmp/vagrant_dir')
		return True


def module():
	return docker_selinux(
		'io.dockerinpractice.docker_selinux.docker_selinux', 1184271914.00,
		description='Test of docker selinux on a vagrant box',
		maintainer='ian.miell@gmail.com',
		depends=['shutit.tk.setup']
	)

