#!/bin/bash
# Copyright © 2014 EasyStack, Inc
# Author: Branty <jun.wang@easystack.cn>>

# multi-controllers own the command of crm, single conroller node without it.
# single controller nodes , set the value of auth_vip equal to external ip
# single controller nodes , set the value of auth_internal_vip equal to management ip
if which crm > /dev/null 2>&1  ;then
        auth_vip=$(crm resource meta vip__public_old show ip)
        auth_internal_vip=$(crm resource meta vip__management_old show  ip)
else
        auth_vip=$(ifconfig br-ex  | grep -v inet6  | grep inet | awk '{print $2}')
        auth_internal_vip=$(ifconfig br-mgmt  | grep -v inet6  | grep inet | awk '{print $2}')
fi

user=$(grep "OS_USERNAME" /root/openrc | awk -F \'  '{print $2}')
if [ ! -n "$user" ];then
   user=$(grep "OS_USERNAME" /root/openrc | awk -F =  '{print $2}')
fi

region=$(grep "OS_REGION_NAME" /root/openrc | awk -F \'  '{print $2}')
if [ ! -n "$region" ];then
   region=$(grep "OS_REGION_NAME" /root/openrc | awk -F =  '{print $2}')
fi

password=$(grep "OS_PASSWORD" /root/openrc | awk -F \'  '{print $2}')
if [ ! -n "$password" ];then
   password=$(grep "OS_PASSWORD" /root/openrc | awk -F =  '{print $2}')
fi

tenant=$(grep "OS_TENANT_NAME" /root/openrc | awk -F \'  '{print $2}')
if [ ! -n "$tenant" ];then
   tenant=$(grep "OS_TENANT_NAME" /root/openrc | awk -F =  '{print $2}')
fi

admin_user=$user

admin_password=$password

os_region=$region

admin_tenant_name=$tenant

service_tenant_name=$(grep -E "^admin_tenant_name" /etc/nova/nova.conf  | head -1 | awk -F = '{print $2}')

ceilometer_admin_password=$(grep -E "^admin_password" /etc/ceilometer/ceilometer.conf  | head -1 | awk -F = '{print $2}')

cinder_admin_password=$(grep -E "^admin_password" /etc/cinder/cinder.conf  | head -1 | awk -F = '{print $2}')

glance_admin_password=$(grep -E "^admin_password" /etc/glance/glance-api.conf  | head -1 | awk -F = '{print $2}')

heat_admin_password=$(grep -E "^admin_password" /etc/heat/heat.conf  | head -1 | awk -F = '{print $2}')

nova_admin_password=$(grep -E "^admin_password" /etc/nova/nova.conf  | head -1 | awk -F = '{print $2}')

neutron_admin_password=$(grep -E "^admin_password" /etc/neutron/neutron.conf  | head -1 | awk -F = '{print $2}')

swift_admin_password=$(grep -E "^admin_password" /etc/swift/swift.conf  | head -1 | awk -F = '{print $2}')

if [ -f "/tmp/multi-region.outfile" ];then
    mv /tmp/multi-region.outfile /tmp/multi-region.outfile.bak
    echo > /tmp/multi-region.outfile
else
    touch /tmp/multi-region.outfile
fi
echo "auth_vip=$auth_vip"                                  >> /tmp/multi-region.outfile
echo "auth_internal_vip=$auth_internal_vip"                >> /tmp/multi-region.outfile
echo "admin_user=$admin_user"                              >> /tmp/multi-region.outfile
echo "admin_password=$admin_password"                      >> /tmp/multi-region.outfile
echo "auth_region=$os_region"                              >> /tmp/multi-region.outfile
echo "admin_tenant_name=$admin_tenant_name"                >> /tmp/multi-region.outfile
echo "service_tenant_name=$service_tenant_name"            >> /tmp/multi-region.outfile
echo "ceilometer_admin_password=$ceilometer_admin_password">> /tmp/multi-region.outfile
echo "cinder_admin_password=$cinder_admin_password"        >> /tmp/multi-region.outfile
echo "heat_admin_password=$heat_admin_password"            >> /tmp/multi-region.outfile
echo "glance_admin_password=$glance_admin_password"        >> /tmp/multi-region.outfile
echo "nova_admin_password=$nova_admin_password"            >> /tmp/multi-region.outfile
echo "neutron_admin_password=$neutron_admin_password"      >> /tmp/multi-region.outfile
echo "swift_admin_password=$swfit_admin_password"          >> /tmp/multi-region.outfile
