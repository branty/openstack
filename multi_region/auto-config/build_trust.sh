#!/usr/bin/expect -f
# Copyright © 2014 EasyStack, Inc
# Author: Branty <jun.wang@easystack.cn>

# user,default is root
set user root
# hostname
set host 10.20.0.3
# password
set password passw0rd
set timeout 100
spawn scp /root/.ssh/id_rsa.pub $user@$host:/root/
expect {
     "*)?*"       {send "yes\r";exp_continue}
    "*assword:*"  {send "$password\r";exp_continue}
}
spawn ssh $user@$host "cat /root/id_rsa.pub >> /root/.ssh/authorized_keys"
#spawn ssh $user@$host "ls -al"
expect {
     "*)?*"       {send "yes\r";exp_continue}
    "*assword:*"  {send "$password\r";exp_continue}
}
