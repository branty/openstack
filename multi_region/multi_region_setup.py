#! /usr/bin/python

import sys
import os
import iniparse
import optparse

from keystoneclient.v3 import client
from keystoneclient import exceptions as ksc_exc

__author__ = 'Rayman'


def usage(usage):
    sys.stderr.write(usage)
    sys.exit(1)


def get_options(argv):
    parser = optparse.OptionParser(usage='python multi_region_setup --config <config>',
                                   option_list=['--config'])
    try:
        options, args = parser.parse_args(argv)
        if not options.config:
            if os.path.isfile('./multi-region.conf'):
                config = './multi-region.conf'
            else:
                usage(parser.usage)
        else:
            if not options.config.startswith("./"):
                config = "./%s" % options.config
            else:
                config = options.config
    except Exception, e:
        usage(parser.usage)
    return config


config = get_options(sys.argv)

conf = iniparse.ConfigParser()
conf.readfp(open(config))

os_region = conf.get('region', 'os_region')
public_vip = conf.get('region', 'public_vip')
internal_vip = conf.get('region', 'internal_vip')
region_desc = conf.get('region', 'description')
node_role = conf.get('region', 'node_role')

admin_tenant_id = conf.get('authtoken', 'admin_tenant_id')
admin_tenant_name = conf.get('authtoken', 'admin_tenant_name')
auth_region = conf.get('authtoken', 'auth_region')
admin_user = conf.get('authtoken', 'admin_user')
admin_password = conf.get('authtoken', 'admin_password')
auth_vip = conf.get('authtoken', 'auth_vip')
domain_id = conf.get('authtoken', 'domain_id')
domain_name = conf.get('authtoken', 'domain_name')
service_tenant_id = conf.get('authtoken', 'service_tenant_id')
service_tenant_name = conf.get('authtoken', 'service_tenant_name')
auth_url = 'http://%s:5000/v3' % auth_vip

ceilometer_admin_password = conf.get('authtoken', 'ceilometer_admin_password')
cinder_admin_password = conf.get('authtoken', 'cinder_admin_password')
glance_admin_password = conf.get('authtoken', 'glance_admin_password')
heat_admin_password = conf.get('authtoken', 'heat_admin_password')
nova_admin_password = conf.get('authtoken', 'nova_admin_password')
neutron_admin_password = conf.get('authtoken', 'neutron_admin_password')
swift_admin_password = conf.get('authtoken', 'swift_admin_password')

actions = conf.get('operation', 'actions').replace(' ', '').split(',')
disable_services = conf.get('operation', 'disable_services').replace(' ', '').split(',')

KEYSTONE_AUTHTOKEN_SESSION = 'keystone_authtoken'
AUTH_PASSWORD_OPTION = 'admin_password'


def _make_openrc_v2():
    # make new openrc
    with open('/root/openrc', 'w') as fp:
        openrc = "#!/bin/sh\n" \
                 "export OS_NO_CACHE='true'\n" \
                 "export OS_TENANT_NAME='admin'\n" \
                 "export OS_USERNAME='%s' \n" \
                 "export OS_PASSWORD='%s' \n" \
                 "export OS_AUTH_URL='http://%s:5000/v2.0/'\n" \
                 "export OS_AUTH_STRATEGY='keystone'\n" \
                 "export OS_REGION_NAME='%s'\n" \
                 "export CINDER_ENDPOINT_TYPE='publicURL'\n" \
                 "export GLANCE_ENDPOINT_TYPE='publicURL'\n" \
                 "export KEYSTONE_ENDPOINT_TYPE='publicURL'\n" \
                 "export NOVA_ENDPOINT_TYPE='publicURL'\n" \
                 "export NEUTRON_ENDPOINT_TYPE='publicURL'" % (admin_user, admin_password, auth_vip, os_region)
        fp.write(openrc)


def _make_openrc_v3():
    # make new openrc.v3
    with open('/root/openrc.v3', 'w') as fp:
        openrc = "#!/bin/sh\n" \
                 "export OS_NO_CACHE='true'\n" \
                 "export OS_DOMAIN_NAME='Default'\n" \
                 "export OS_USERNAME='%s' \n" \
                 "export OS_USER_DOMAIN_NAME='Default' \n" \
                 "export OS_PASSWORD='%s' \n" \
                 "export OS_AUTH_URL='http://%s:5000/v3/'\n" \
                 "export OS_IDENTITY_API_VERSION=3\n" \
                 "export OS_AUTH_STRATEGY='keystone'\n" \
                 "export OS_REGION_NAME='%s'\n" \
                 "export CINDER_ENDPOINT_TYPE='publicURL'\n" \
                 "export GLANCE_ENDPOINT_TYPE='publicURL'\n" \
                 "export KEYSTONE_ENDPOINT_TYPE='publicURL'\n" \
                 "export NOVA_ENDPOINT_TYPE='publicURL'\n" \
                 "export NEUTRON_ENDPOINT_TYPE='publicURL'" % (admin_user, admin_password, auth_vip, os_region)
        fp.write(openrc)


def make_openrc():
    print '****** Start to make openrc file ******\n'
    # backup openrc
    if os.path.isfile('/root/openrc'):
        os.system('mv /root/openrc /root/openrc.bak')
    if os.path.isfile('/root/openrc.v3'):
        os.system('mv /root/openrc.v3 /root/openrc.v3.bak')

    # make new openrc
    _make_openrc_v2()

    # make new openrc.v3
    _make_openrc_v3()
    print '****** End make openrc file ******\n'


def _create_region(keystone):
    print '****** Start to create region %s ******\n' % os_region
    try:
        # create new region
        region = keystone.regions.create(id=os_region, description=region_desc)
    except ksc_exc.Conflict as e:
        region = keystone.regions.get(os_region)
    except Exception, e:
        raise e
    print '****** Ended create region %s ******\n' % region
    return region


def _clean_region_endpoint(keystone, region):
    try:
        endpoints = keystone.endpoints.list(region=region)
    except Exception, e:
        return

    for endpoint in endpoints:
        try:
            keystone.endpoints.delete(endpoint.id)
        except Exception, e:
            # TODO: log
            pass


def _get_region_endpoints(keystone, region):
    try:
        endpoints = keystone.endpoints.list(region=region)
    except Exception, e:
        raise e
    return endpoints


def create_region():
    keystone = client.Client(user_domain_name=domain_name,
                             username=admin_user,
                             password=admin_password,
                             domain_name=domain_name,
                             auth_url=auth_url,
                             region_name=auth_region,
                             interface='public')
    try:
        # create new region
        region = _create_region(keystone)

        # clean dirty region endpoint
        _clean_region_endpoint(keystone, os_region)

        # get all endpoint at region one
        endpoints = _get_region_endpoints(keystone, region=auth_region)

        # get keystone service id
        identitys = [identity.id for identity in keystone.services.list(name='keystone', type='identity')]

        # get chakra service id
        chakras = [chakra.id for chakra in keystone.services.list(name='chakra', type='account')]

        for endpoint in endpoints:
            # filter keystone service
            if endpoint.service_id in identitys:
                continue
            # filter admin interface
            if 'admin' == endpoint.interface:
                continue
            # chakra service just in the regionOne, but we still need create a RegionTwo endpoint
            if endpoint.service_id in chakras:
                endpoint_url = endpoint.url
            else:
                if 'public' == endpoint.interface:
                    url_element = endpoint.url.split(conf.get('authtoken', 'auth_host'))
                    endpoint_url = url_element[0] + public_vip + url_element[-1]
                else:
                    url_element = endpoint.url.split(conf.get('authtoken', 'auth_internal_vip'))
                    endpoint_url = url_element[0] + internal_vip + url_element[-1]
            # create endpoint
            print '****** Start to create endpoint %s ******\n' % endpoint_url
            endpoint = keystone.endpoints.create(endpoint.service_id,
                                                 endpoint_url,
                                                 endpoint.interface,
                                                 region.id)
            print '****** Ended create endpoint %s ******\n' % endpoint
    except Exception, e:
        print('create region %s failed with exception %s' % (os_region, e))
        sys.exit(1)


def get_conf(cfgfile):
    # get conf
    conf = iniparse.ConfigParser()
    conf.readfp(open(cfgfile))
    return conf


def _rebuild_auth_url(cur_auth_url):
    if cur_auth_url.endswith('v2.0'):
        _auth_url = 'http://%s:5000/v2.0' % auth_vip
    else:
        _auth_url = auth_url
    return _auth_url


def _update_authtoken_normal_conf(conf, section):
    conf.set(section, 'auth_host', auth_vip)
    conf.set(section, 'auth_port', '5000')
    conf.set(section, 'auth_version', 'v3.0')
    if conf.has_option(section, 'auth_url'):
        conf.remove_option(section, 'auth_url')
    if conf.has_option(section, 'auth_uri'):
        conf.remove_option(section, 'auth_uri')


def _update_default_normal_conf(conf, section):
    # add os_region_name
    conf.set(section, 'os_region_name', os_region)

    # set os_auth_regioon
    if not conf.has_option(section, 'auth_region'):
        conf.set(section, 'os_auth_region', auth_region)

    # set os endpoint type to internalURL
    if not conf.has_option(section, 'endpoint_type'):
        conf.set(section, 'os_endpoint_type', 'internalURL')

    # set auth url
    if conf.has_option(section, 'os_auth_url'):
        _auth_url = _rebuild_auth_url(conf.get(section, 'os_auth_url'))
        conf.set(section, 'os_auth_url', _auth_url)
    if conf.has_option(section, 'auth_url'):
        _auth_url = _rebuild_auth_url(conf.get(section, 'auth_url'))
        conf.set(section, 'auth_url', _auth_url)


def update_normal_conf(conf):
    if conf.has_section(KEYSTONE_AUTHTOKEN_SESSION):
        section = KEYSTONE_AUTHTOKEN_SESSION
        _update_authtoken_normal_conf(conf, section)
    if conf.has_section('filter:authtoken'):
        section = 'filter:authtoken'
        _update_authtoken_normal_conf(conf, section)
    if conf.has_section('DEFAULT'):
        section = 'DEFAULT'
        _update_default_normal_conf(conf, section)


def update_special_conf(conf, section, param, value):
    if value is None:
        return
    if conf.has_section(section):
        conf.set(section, param, value)


def set_conf_to_cfgfile(cfgfile, conf):
    with open(cfgfile, 'w') as fp:
        conf.write(fp)


def backup_cfgfile(cfgfile):
    bak_file = "%s.bak" % cfgfile
    if os.path.isfile(bak_file):
        return True

    if os.path.isfile(cfgfile):
        os.system('cp -f %s %s' % (cfgfile, bak_file))
        return True
    return False


def get_lsb_release():
    return os.popen("lsb_release -r | awk '{print $2}' ").read()


def restart_service(service):
    # ESCloud OS may upgrade,currently, we only support 6.x, and 7.x
    lsb_release = get_lsb_release()
    if lsb_release.startswith('6'):
        status = os.popen('service %s status' % service).readlines()[0]
        if 'running' in status:
            os.system('service %s restart' % service)
            print 'service %s has been restart' % service
        else:
            print 'Warn: service %s is stopped' % service
            os.system('service %s start' % service)
    else:
        status = os.popen("systemctl status %s | sed -n '3p'" % service).read()
        if 'running' in status:
            os.system('systemctl restart %s' % service)
            print 'service %s has been restart' % service
        else:
            print 'Warn: service %s is stopped' % service
            os.system('systemctl start %s' % service)


def restart_services(services):
    for service in services:
        restart_service(service)


def stop_services(services):
    for service in services:
        os.system('service %s stop' % service)
        print 'service %s has been stopped' % service


def _update_cinder_conf():
    isupdate = False
    if backup_cfgfile('/etc/cinder/cinder.conf'):
        print '****** Start to update cinder conf ******\n'
        conf = get_conf('/etc/cinder/cinder.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', cinder_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/cinder/cinder.conf', conf)
        isupdate = True
        print '****** Ended update cinder conf ******\n'
    return isupdate


def _update_cinder_ini():
    isupdate = False
    if backup_cfgfile('/etc/cinder/api-paste.ini'):
        print '****** Start to update cinder api-paste ******\n'
        conf = get_conf('/etc/cinder/api-paste.ini')
        update_special_conf(conf, 'filter:authtoken', 'admin_password', cinder_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/cinder/api-paste.ini', conf)
        isupdate = True
        print '****** Ended update cinder api-paste ******\n'
    return isupdate


def update_cinder_conf():
    isupdate = _update_cinder_conf()
    isupdate |= _update_cinder_ini()
    if isupdate:
        services = ['openstack-cinder-api', 'openstack-cinder-backup',
                    'openstack-cinder-scheduler', 'openstack-cinder-volume']
        restart_services(services)


def _update_ceilometer_conf():
    isupdate = False
    if backup_cfgfile('/etc/ceilometer/ceilometer.conf'):
        print '****** Start to update ceilometer conf ******\n'
        conf = get_conf('/etc/ceilometer/ceilometer.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', ceilometer_admin_password)
        update_special_conf(conf, 'DEFAULT', 'os_password', ceilometer_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/ceilometer/ceilometer.conf', conf)
        isupdate = True
        print '****** Ended update ceilometer conf ******\n'
    return isupdate


def _update_ceilometer_ini():
    isupdate = False
    if backup_cfgfile('/etc/ceilometer/api-paste.ini'):
        print '****** Start to update ceilometer api-paste ******\n'
        conf = get_conf('/etc/cinder/api-paste.ini')
        update_special_conf(conf, 'filter:authtoken', 'admin_password', cinder_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/cinder/api-paste.ini', conf)
        isupdate = True
        print '****** Ended update ceilometer api-paste ******\n'
    return isupdate


def update_ceilometer_conf():
    isupdate = _update_ceilometer_conf()
    isupdate |= _update_ceilometer_ini()
    if isupdate:
        if node_role == 'compute':
            restart_service('openstack-ceilometer-compute')
        else:
            services = ['openstack-ceilometer-api', 'openstack-ceilometer-alarm-evaluator',
                        'openstack-ceilometer-alarm-notifier', 'openstack-ceilometer-central',
                        'openstack-ceilometer-collector', 'openstack-ceilometer-notification']
            restart_services(services)


def _update_esbilling_conf():
    isupdate = False
    if backup_cfgfile('/etc/esbilling/esbilling.conf'):
        print '****** Start to update billing conf ******\n'
        conf = get_conf('/etc/esbilling/esbilling.conf')
        update_special_conf(conf, 'openstack', 'os_password', ceilometer_admin_password)
        if conf.has_option('openstack', 'os_auth_url'):
            _auth_url = _rebuild_auth_url(conf.get('openstack', 'os_auth_url'))
            update_special_conf(conf, 'openstack', 'os_auth_url', _auth_url)
        set_conf_to_cfgfile('/etc/esbilling/esbilling.conf', conf)
        isupdate = True
        print '****** Ended update billing conf ******\n'
    return isupdate


def update_esbilling_conf():
    isupdate = _update_esbilling_conf()
    if isupdate:
        services = ['openstack-billing-agent', 'openstack-billing-api',
                    'openstack-billing-central']
        restart_services(services)


def update_glance_conf():
    isupdate = False
    if backup_cfgfile('/etc/glance/glance-api.conf'):
        print '****** Start to update glance api conf ******\n'
        conf = get_conf('/etc/glance/glance-api.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', glance_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/glance/glance-api.conf', conf)
        isupdate = True
        print '****** Ended update glance api conf ******\n'
    if backup_cfgfile('/etc/glance/glance-cache.conf'):
        print '****** Start to update glance cache conf ******\n'
        conf = get_conf('/etc/glance/glance-cache.conf')
        update_special_conf(conf, 'DEFAULT', 'admin_password', glance_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/glance/glance-cache.conf', conf)
        isupdate = True
        print '****** Ended update glance cache conf ******\n'
    if backup_cfgfile('/etc/glance/glance-registry.conf'):
        print '****** Start to update glance registry conf ******\n'
        conf = get_conf('/etc/glance/glance-registry.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', glance_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/glance/glance-registry.conf', conf)
        isupdate = True
        print '****** Ended update glance registry conf ******\n'
    if backup_cfgfile('/etc/glance/api-paste.ini'):
        print '****** Start to update glance api paste ini ******\n'
        conf = get_conf('/etc/glance/api-paste.ini')
        update_special_conf(conf, 'filter:authtoken', 'admin_password', glance_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/glance/api-paste.ini', conf)
        isupdate = True
        print '****** Ended update glance api paste ******\n'
    if isupdate:
        services = ['openstack-glance-api', 'openstack-glance-registry', 'openstack-glance-scrubber']
        restart_services(services)


def update_heat_conf():
    isupdate = False
    if backup_cfgfile('/etc/heat/heat.conf'):
        print '****** Start to update heat conf ******\n'
        conf = get_conf('/etc/heat/heat.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', heat_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/heat/heat.conf', conf)
        isupdate = True
        print '****** Ended update heat conf ******\n'
    if isupdate:
        services = ['openstack-heat-api', 'openstack-heat-api-cfn',
                    'openstack-heat-api-cloudwatch', 'openstack-heat-engine']
        restart_services(services)


def update_nova_conf():
    isupdate = False
    if backup_cfgfile('/etc/nova/nova.conf'):
        print '****** Start to update nova conf ******\n'
        conf = get_conf('/etc/nova/nova.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', nova_admin_password)
        update_special_conf(conf, 'DEFAULT', 'neutron_admin_password', neutron_admin_password)
        update_special_conf(conf, 'DEFAULT', 'neutron_region_name', os_region)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/nova/nova.conf', conf)
        isupdate = True
        print '****** Ended update nova conf ******\n'
    if backup_cfgfile('/etc/nova/api-paste.ini'):
        print '****** Start to update nova api paste ini ******\n'
        conf = get_conf('/etc/nova/api-paste.ini')
        update_special_conf(conf, 'filter:authtoken', 'admin_password', nova_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/nova/api-paste.ini', conf)
        isupdate = True
        print '****** Ended update nova api paste ******\n'
    if isupdate:
        if 'compute' == node_role:
            restart_service('openstack-nova-compute')
        else:
            services = ['openstack-nova-api', 'openstack-nova-cert', 'openstack-nova-conductor',
                        'openstack-nova-console', 'openstack-nova-consoleauth', 'openstack-nova-metadata-api',
                        'openstack-nova-novncproxy', 'openstack-nova-objectstore', 'openstack-nova-scheduler',
                        'openstack-nova-spicehtml5proxy', 'openstack-nova-xvpvncproxy']
            restart_services(services)


def update_neutron_conf():
    isupdate = False
    if backup_cfgfile('/etc/neutron/neutron.conf'):
        print '****** Start to update neutron conf ******\n'
        conf = get_conf('/etc/neutron/neutron.conf')
        update_special_conf(conf, 'keystone_authtoken', 'admin_password', neutron_admin_password)
        update_special_conf(conf, 'DEFAULT', 'nova_admin_password', nova_admin_password)
        update_special_conf(conf, 'DEFAULT', 'nova_admin_tenant_id', service_tenant_id)
        update_special_conf(conf, 'DEFAULT', 'nova_region_name', os_region)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/neutron/neutron.conf', conf)
        isupdate = True
        print '****** Ended update neutron conf ******\n'

    if backup_cfgfile('/etc/neutron/metadata_agent.ini'):
        print '****** Start to update neutron metadata_agent conf ******\n'
        conf = get_conf('/etc/neutron/metadata_agent.ini')
        update_special_conf(conf, 'DEFAULT', 'admin_password', neutron_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/neutron/metadata_agent.ini', conf)
        print '****** Ended update neutron metadata_agent conf ******\n'
        isupdate = True

    if backup_cfgfile('/etc/neutron/l3_agent.ini'):
        print '****** Start to update neutron l3_agent conf ******\n'
        conf = get_conf('/etc/neutron/l3_agent.ini')
        update_special_conf(conf, 'DEFAULT', 'admin_password', neutron_admin_password)
        set_conf_to_cfgfile('/etc/neutron/l3_agent.ini', conf)
        isupdate = True
        print '****** Ended update neutron l3_agent conf ******\n'

    if backup_cfgfile('/etc/neutron/dhcp_agent.ini'):
        print '****** Start to update neutron dhcp_agent conf ******\n'
        conf = get_conf('/etc/neutron/dhcp_agent.ini')
        update_special_conf(conf, 'DEFAULT', 'admin_password', neutron_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/neutron/dhcp_agent.ini', conf)
        isupdate = True
        print '****** Ended update neutron dhcp_agent conf ******\n'

    if backup_cfgfile('/etc/neutron/api-paste.ini'):
        print '****** Start to update neutron api-paste conf ******\n'
        conf = get_conf('/etc/neutron/api-paste.ini')
        update_special_conf(conf, 'filter:authtoken', 'admin_password', neutron_admin_password)
        update_normal_conf(conf)
        set_conf_to_cfgfile('/etc/neutron/api-paste.ini', conf)
        isupdate = True
        print '****** Ended update neutron api-paste conf ******\n'
    if isupdate:
        services = ['neutron-dhcp-agent', 'neutron-l3-agent', 'neutron-lbaas-agent',
                    'neutron-metadata-agent', 'neutron-openvswitch-agent',
                    'neutron-server']
        restart_services(services)


def update_conf():
    update_ceilometer_conf()
    update_nova_conf()
    update_neutron_conf()
    if node_role == 'controller':
        update_cinder_conf()
        update_esbilling_conf()
        update_glance_conf()
        update_heat_conf()
        # stop unneeded services: keystone, horizon, chakra
        stop_services(disable_services)


def multi_region_setup():
    if 'make_openrc' in actions:
        make_openrc()
    if 'create_region' in actions:
        create_region()
    if 'update_conf' in actions:
        update_conf()


if '__main__' == __name__:
    multi_region_setup()
