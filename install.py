#!/usr/bin/env python3

# version: 2023-06-22

import sys, re, ruamel.yaml
from os import getlogin, path, system

dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, "bycon" )
sys.path.append( pkg_path )

from bycon import *

"""
The install script copies the relevant bycon files to the webserver directory
specified in the `config/config.yaml` file and sets the file permissions
accordingly. It requires admin permissions (sudo).

Versions after 2023-02-07 _only_ copy the script directories and package __init__.py
to the server path; additionally a bycon package install is needed with
`pip3 install "bycon>=1.0.55"`.
"""

################################################################################
################################################################################
################################################################################

def main():

    install_beacon_server()

################################################################################
################################################################################
################################################################################

def install_beacon_server():

    yaml = ruamel.yaml.YAML()
    yaml.indent(mapping=2, sequence=4, offset=2)

    i_f = path.join( dir_path, "install.yaml" )
    try:
        with open( i_f ) as y_c:
            install = yaml.load( y_c )
    except Exception as e:
        print(e)
        exit()

    # WARNING: This assumes that the values are sensible...
    for p in ["system_user", "system_group", "bycon_install_dir"]:
        p_v = install.get(p, None)
        if p_v is None:
            print("¡¡¡ No `{}` value defined in {} !!!".format(p, i_f))
            exit()

    s_u = install["system_user"]
    s_g = install["system_group"]

    # for p in ["server_tmp_dir_loc", "server_tmp_dir_web"]:
    #     p_v = install["bycon_instance_pars"].get(p, None)
    #     if p_v is None:
    #         print("¡¡¡ No `bycon_instance_pars.{}` value defined in {} !!!".format(p, i_f))
    #         exit()

    b_i_d_p = path.join( *install["bycon_install_dir"] )

    # for s_p in [b_i_d_p, w_t_d_p]:
    #     if not path.isdir(s_p):
    #         print("¡¡¡ {} does not exist - please check & create !!!".format(s_p))
    #         exit()

    # # this block modifies the main config file, so that the `server_tmp_dir_loc`
    # # etc. are in line with the install
    # c_f = path.join( pkg_path, "config.yaml" )
    # c_f_bck = path.join( pkg_path, "config.yaml.bck" )
    # try:
    #     with open( c_f ) as y_c:
    #         config = yaml.load( y_c )
    #     system('cp {} {}'.format(c_f, c_f_bck))
    # except Exception as e:
    #     print(e)
    #     exit()

    # for c_p_k, c_p_v in install["bycon_instance_pars"].items():
    #     config.update({ c_p_k: c_p_v})
    
    # with open(c_f, 'w') as out_f:
    #     yaml.dump(config, out_f)

    system(f'sudo rsync -avh --delete {pkg_path}/beaconServer/ {b_i_d_p}/beaconServer/')
    system(f'sudo rsync -avh --delete {dir_path}/local/ {b_i_d_p}/beaconServer/local/')

    system(f'sudo cp {pkg_path}/__init__.py {b_i_d_p}/__init__.py')
    system(f'sudo chown -R {s_u}:{s_g} {b_i_d_p}')
    system(f'sudo chmod 775 {b_i_d_p}/beaconServer/*.py')
    # system(f'sudo chmod -R 1777 {w_t_d_p}')
    
    # print(f'Updated the `server_tmp_dir_loc` in {c_f} to\n{w_t_d_p}')
    print(f'Updated bycon files from\n{pkg_path}\nto\n{b_i_d_p}')

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
