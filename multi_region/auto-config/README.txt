# operations
# in the first controller node we may execult 'make_openrc, create_region, update_conf'
# in the other controller node we may execult 'make_openrc, update_conf' and
# in the compute node we may execult 'update_conf'
actions=make_openrc, create_region, update_conf

# Before running multi-conf.sh,
# please make sure that create_MultiRegion_template.sh and get_region_conf.sh exist
# below the directory of /etc/multi-region/
