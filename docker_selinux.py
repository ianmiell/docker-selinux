"""ShutIt module. See http://shutit.tk
"""

from shutit_module import ShutItModule


class docker_selinux(ShutItModule):


	def build(self, shutit):
		shutit.send('cd /space/vagrant/centos7_docker')
		shutit.login(user='imiell',command='su')
		shutit.multisend('vagrant destroy',{'Are you sure':'y'})
		shutit.send('vagrant up')
		shutit.login(command='vagrant ssh',expect='vagrant')
		shutit.login(command='sudo su')
		shutit.send('yum install -y selinux-policy-devel wget')
		shutit.send('cd /root')
		shutit.send('mkdir /root/selinux')
		shutit.send('cd /root/selinux')
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
'''.split(),'/root/selinux/docker_apache.te')
		shutit.add_line_to_file('''make -f /usr/share/selinux/devel/Makefile docker_apache.pp
semodule -i docker_apache.pp
docker run -d --security-opt type:docker_apache_t httpd
'''.split(),'/root/selinux/script.sh')
		shutit.send('wget -qO- https://get.docker.com/builds/Linux/x86_64/docker-latest > docker')
		shutit.send('mv docker /usr/bin/docker')
		shutit.send('chmod +x /usr/bin/docker')
		shutit.send('systemctl stop docker')
		shutit.send('systemctl start docker')
		shutit.pause_point('Here you go')
		shutit.send('chmod +x /root/selinux/script.sh')
		shutit.send('/root/selinux/script.sh')
		return True

def module():
	return docker_selinux(
		'io.dockerinpractice.docker_selinux.docker_selinux', 1184271914.00,
		description='',
		maintainer='',
		depends=['shutit.tk.setup']
	)

