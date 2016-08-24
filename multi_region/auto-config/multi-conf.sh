#!/bin/bash
#set -x
# Copyright © 2014 EasyStack, Inc
# Author: Branty <jun.wang@easystack.cn>

#begin time
START_TIME=$(date +%s)

CURRENT_SCRIPT=$0
#new regoin name
OS_REGION=RegionTwo

#new region public vip or host ip, it also can be a IDC gw ip
PUBLIC_VIP=172.70.0.2

#new region internal vip
INTERNAL_VIP=192.168.0.2

#region description
DESCRIPTION=hello world

#which roll of node that you want to deploy
#valid values:['controller','compute','others']
NODE_ROLE=controller

#AUTH_HOST
AUTH_HOST=172.70.0.2

#SELECTED_NODE_IP
SELECTED_NODE_IP=172.70.0.3

#function usage_print(){
# If necessary , add the Mannual help
#}

function error_exit(){
    echo "$1" 1>&2
    exit 1
}

function build_trust(){
  if [ -f /etc/multi-region/build_trust.sh ];then
     sed -i "s/set host.*/set host $SELECTED_NODE_IP/g" /etc/multi-region/build_trust.sh
     # run build_trust script
     /etc/multi-region/build_trust.sh
  else
     error_exit "Can'f find build trust file:/etc/multi-region/build_trust.sh"
  fi
}

#function new_region_conf(){
#    while true ; do
#        read -p 'Please input the value of public_vip: '   PUBLIC_VIP
#        read -p 'Please input the value of internal_vip: ' INTERNAL_VIP
#        read -p 'Please input the value of descriptoin: '  DESCRIPTION
#        read -p 'Please input the value of node_role: '    NODE_ROLE
#        read -p 'Please input the value of os_region: '    OS_REGION
#        read -p 'Please input the public ip of the selected controller node: ' SELECTED_NODE_IP
#        echo 'The following values are selected : '
#        echo '    os_region        = ' $OS_REGION
#        echo '    public_vip       = ' $PUBLIC_VIP
#        echo '    internal_vip     = ' $INTERNAL_VIP
#        echo '    description      = ' $DESCRIPTION
#        echo '    node_role        = ' $NODE_ROLE
#        echo '    selected_node_ip = ' $SELECTED_NODE_IP
#        read -p 'Are you sure of the values ? [Y/y] for ok, [N/n] for cancle,[Q/q] exit the script :' flag
#        case $flag in
#            [Yy] )  break;;
#            [Nn] )  echo "Cancel the input and reset";;
#            [Qq] )  error_exit '$LINENO:Stop to run the script';;
#            *   )  echo "Invalid inpute, only 'Y/y', 'N/n' ,'Q/q' support" ;;
#        esac
#    done
#}

# try 3 times
function test_ssh_connection(){
    RegionOne_SELECTED_NODE_IP=$1
    if ! ping -c 3 $1 > /dev/null;then
        return -1
    fi
    for i in `seq 1 3`;do
        ssh root@$RegionOne_SELECTED_NODE_IP 'exit' >> /dev/null
        if [ "$?" = 0 ];then
            echo "$LINENO:ssh $1 success "
            return 0
        else
            #echo "$LINENO:ssh $1 failed "
            continue
        fi
    done
    return -1
}

function get_RegionOne_conf(){
    # login in one of the controller nodes
    # Build trust between the current node and one of the controller nodes in RegionOne
    ssh_connection_status=$(test_ssh_connection $SELECTED_NODE_IP)
    if [ '$ssh_connection_status' = -1  ];then
        error_exit "$LINENO:ssh $SELECTED_NODE_IP failed"
    fi

    # scp get_region_conf.sh to controller node in RegionOne
    scp /etc/multi-region/get_region_conf.sh  root@$SELECTED_NODE_IP:/root/
    if [ "$?" = 0 ];then
        echo "$LINENO:scp /etc/multi-region/get_region_conf.sh  success!"
    else
        error_exit "$LINENO:scp /etc/multi-region/get_region_conf.sh failed!"
    fi

    ssh root@$SELECTED_NODE_IP 'bash /root/get_region_conf.sh'

    if [ -f "/tmp/multi-region.outfile" ];then
        cp /tmp/multi-region.outfile /tmp/multi-region.outfile.bak
    else
        touch /tmp/multi-region.outfile
    fi

    # scp the information of RegionOne to Current node
    # maybe the role of current node is controller or compute in RegionTwo.
    scp root@$SELECTED_NODE_IP:/tmp/multi-region.outfile /tmp/multi-region.outfile
    if [ "$?" = 0 ];then
        echo "$LINENO:Scp /tmp/multi-region.outfile for $SELECTED_NODE_IP success!"
    else
        error_exit "$LINENO:Scp /tmp/multi-region.outfile from $SELECTED_NODE_IP failed!"
    fi
}
function prepare_RegionTwo_conf(){
    # backup multi-region.conf or create it
    if [ -f "/etc/multi-region/multi-region.conf" ];then
        mv /etc/multi-region/multi-region.conf /etc/multi-region/multi-region.conf.bak
    fi
    if [ -f /etc/multi-region/create_MultiRegion_template.sh ];then
            . /etc/multi-region/create_MultiRegion_template.sh
    else
            error_exit "$LINENO:Can't find shell file:/etc/multi-region/create_MultiRegion_template.sh"
    fi
    # backup get_region_conf.sh or create it
    if [ -f /etc/multi-region/get_region_conf.sh ];then
        echo "Successfully Find get_region_conf.sh script"
    else
        error_exit "$LINENO:Can't find shell file:/etc/multi-region/get_region_conf.sh"
    fi
}

function last_step(){
   sed -i "s/os_region=.*/os_region=$OS_REGION/g"           /etc/multi-region/multi-region.conf
   sed -i "s/public_vip=.*/public_vip=$PUBLIC_VIP/g"        /etc/multi-region/multi-region.conf
   sed -i "s/internal_vip=.*/internal_vip=$INTERNAL_VIP/g"  /etc/multi-region/multi-region.conf
   sed -i "s/description=.*/description=$DESCRIPTION/g"     /etc/multi-region/multi-region.conf
   sed -i "s/node_role=.*/node_role=$NODE_ROLE/g"           /etc/multi-region/multi-region.conf
   auth_vip=$(awk -F= '$0 ~/^auth_vip/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/auth_host=.*/auth_host=$auth_vip/g"           /etc/multi-region/multi-region.conf
   sed -i "s/auth_vip=.*/auth_vip=$auth_vip/g" /etc/multi-region/multi-region.conf
   internal_vip=$(awk -F= '$0 ~/^auth_internal/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/auth_internal_vip=.*/auth_internal_vip=$internal_vip/g" /etc/multi-region/multi-region.conf
   admin_user=$(awk -F= '$0 ~/^admin_user/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/admin_user=.*/admin_user=$admin_user/g" /etc/multi-region/multi-region.conf
   admin_password=$(awk -F= '$0 ~/^admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/admin_password=.*/admin_password=$admin_password/g" /etc/multi-region/multi-region.conf
   auth_region=$(awk -F= '$0 ~/^auth_region/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/auth_region=.*/auth_region=$auth_region/g" /etc/multi-region/multi-region.conf
   admin_tenant=$(awk -F= '$0 ~/^admin_tenant_name/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/admin_tenant_name=.*/admin_tenant_name=$admin_tenant/g" /etc/multi-region/multi-region.conf
   ser_tenant=$(awk -F= '$0 ~/^service_tenant_name/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/service_tenant_name=.*/service_tenant_name=$ser_tenant/g" /etc/multi-region/multi-region.conf
   ceilo_pwd=$(awk -F= '$0 ~/^ceilometer_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/ceilometer_admin_password=.*/ceilometer_admin_password=$ceilo_pwd/g" /etc/multi-region/multi-region.conf
   cinder_pwd=$(awk -F= '$0 ~/^cinder_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/cinder_admin_password=.*/cinder_admin_password=$cinder_pwd/g" /etc/multi-region/multi-region.conf
   glance_pwd=$(awk -F= '$0 ~/^glance_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/glance_admin_password=.*/glance_admin_password=$glance_pwd/g" /etc/multi-region/multi-region.conf
   heat_pwd=$(awk -F= '$0 ~/^heat_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/heat_admin_password=.*/heat_admin_password=$heat_pwd/g" /etc/multi-region/multi-region.conf
   nova_pwd=$(awk -F= '$0 ~/^nova_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/nova_admin_password=.*/nova_admin_password=$nova_pwd/g" /etc/multi-region/multi-region.conf
   neutron_pwd=$(awk -F= '$0 ~/^neutron_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/neutron_admin_password=.*/neutron_admin_password=$neutron_pwd/g" /etc/multi-region/multi-region.conf
   swfit_pwd=$(awk -F= '$0 ~/^swift_admin_password/ {print $2}'  /tmp/multi-region.outfile)
   sed -i "s/swift_admin_password=.*/swift_admin_password=$swift_pwd/g" /etc/multi-region/multi-region.conf
   # remove spaces
   sed -i "s/=[' ']*/=/g" /etc/multi-region/multi-region.conf
   case $NODE_ROLE in
       "controller" ) echo "You select the role of controller,actions set 'make_openrc, create_region, update_conf'" ;;
       "compute"    )
                      sed -i "s/actions=.*/actions=update_conf/g" /etc/multi-region/multi-region.conf
                      echo "You select the role of compute,actions set 'update_conf'" ;;
       'others' )     sed -i "s/actions=.*/actions=update_conf,make_openrc/g" /etc/multi-region/multi-region.conf
                      echo "You select the role of others(maybe is the another controller),actions set 'update_conf,make_openrc'" ;;
       *        )
                      error_exit 'Invaild the role of node you selected,please check it again'
   esac
}

# mkdir /etc/multi-region/
mkdir -p /etc/multi-region

# set RegionTwo configuration
#new_region_conf

#bulid trust
build_trust

# prepare_RegionTwo_conf
prepare_RegionTwo_conf

# get necessary configuration for RegionOne
get_RegionOne_conf

# last step,god bless you!
last_step

#END_TIME
END_TIME=$(date +%s)

if [ "$?" = "0" ];then
  echo "Successfully Run $(basename $CURRENT_SCRIPT)"
  echo "Total Seconds Spend: $(($END_TIME - $START_TIME))"
fi

