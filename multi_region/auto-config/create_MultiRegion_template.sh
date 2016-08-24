#!/bin/bash
#set -x
# Copyright © 2014 EasyStack, Inc
# Author: Branty <jun.wang@easystack.cn>
cat > /etc/multi-region/multi-region.conf << EOF
[region]
# new region name
os_region=

# new region public vip or host ip, it also can be a IDC gw ip
public_vip=

# new region internal vip
internal_vip=

# region description
description=

# node role in the new region, it maybe controller or compute
node_role=controller

[authtoken]
# domain_conf
domain_id=default
domain_name=Default

# auth host, it maybe on the regionOne
auth_host=
# it also can be a IDC gw ip
auth_vip=
auth_internal_vip=

# auth user name
admin_user=

# auth password
admin_password=

# auth region name
auth_region=

# admin tenant
admin_tenant_id=
admin_tenant_name=

# service tenant
service_tenant_id=
service_tenant_name=

# ceilometer admin
ceilometer_admin_password=

# cinder admin
cinder_admin_password=

# glance admin
glance_admin_password=

# heat admin
heat_admin_password=

# nova admin
nova_admin_password=

# neutron admin
neutron_admin_password=

# swift admin
swift_admin_password=

[operation]
# operations -- in the first controller node we may execult 'make_openrc, create_region, update_conf' and
# in the other controller node we may execult 'make_openrc, update_conf' and
# in the compute node we may execult 'update_conf'
actions=make_openrc, create_region, update_conf
disable_services=openstack-keystone, httpd, openstack-chakra-api
EOF
