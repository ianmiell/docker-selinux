make -f /usr/share/selinux/devel/Makefile docker_apache.pp
semodule -i docker_apache.pp
docker run -d --security-opt type:docker_apache_t httpd
