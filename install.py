#!/usr/bin/env python3

# version: 2023-02-13

import sys, re, ruamel.yaml
from os import getlogin, path, system

# from ruamel.yaml.main import round_trip_load, round_trip_dump
# from ruamel.yaml.comments. import CommentedMap

dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, "bycon" )
sys.path.append( pkg_path )

"""
The install script copies the relevant bycon files to the webserver directory
specified in the `config/config.yaml` file and sets the file permissions
accordingly. It requires admin permissions (sudo).

Versions after 2023-02-07 _only_ copy the script directories and package __init__.py
to the server path; additionally a bycon package install is needed with
`pip3 install "bycon>=1.0.16"`.
"""

################################################################################
################################################################################
################################################################################

def main():

    install()

################################################################################
################################################################################
################################################################################

def install():

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
    for p in ["system_user", "system_group", "bycon_install_dir", "bycon_instance_pars"]:
        p_v = install.get(p, None)
        if p_v is None:
            print("¡¡¡ No `{}` value defined in {} !!!".format(p, i_f))
            exit()

    for p in ["server_tmp_dir_loc", "server_tmp_dir_web"]:
        p_v = install["bycon_instance_pars"].get(p, None)
        if p_v is None:
            print("¡¡¡ No `bycon_instance_pars.{}` value defined in {} !!!".format(p, i_f))
            exit()

    b_i_d_p = path.join( *install["bycon_install_dir"] )
    w_t_d_p = path.join( *install["bycon_instance_pars"]["server_tmp_dir_loc"] )

    for s_p in [b_i_d_p, w_t_d_p]:
        if not path.isdir(s_p):
            print("¡¡¡ {} does not exist - please check & create !!!".format(s_p))
            exit()

    # this block modifies the main config file, so that the `server_tmp_dir_loc`
    # etc. are in line with the install

    c_f = path.join( pkg_path, "config.yaml" )
    c_f_bck = path.join( pkg_path, "config.yaml.bck" )
    try:
        with open( c_f ) as y_c:
            config = yaml.load( y_c )
        system('cp {} {}'.format(c_f, c_f_bck))
    except Exception as e:
        print(e)
        exit()

    for c_p_k, c_p_v in install["bycon_instance_pars"].items():
        config.update({ c_p_k:c_p_v})
    
    with open(c_f, 'w') as out_f:
        yaml.dump(config, out_f)

    system('sudo rsync -avh --delete {}/{}/ {}/{}/'.format(pkg_path, "services", b_i_d_p, "services"))
    system('sudo rsync -avh --delete {}/{}/ {}/{}/'.format(pkg_path, "beaconServer", b_i_d_p, "beaconServer"))
    system('sudo rsync -avh --delete {}/{}/ {}/{}/{}/'.format(dir_path, "local", b_i_d_p, "services", "local"))
    system('sudo rsync -avh --delete {}/{}/ {}/{}/{}/'.format(dir_path, "local", b_i_d_p, "beaconServer", "local"))
    for u_d in install["utility_dirs"]:
        u_p = path.join( *u_d )
        u_p = re.sub("__USERNAME__", getlogin(), u_p)
        if path.isdir(u_p):
            system('rsync -avh --delete {}/{}/ {}/{}/'.format(dir_path, "local", u_p, "local"))
        else:
            print("¡¡¡ Directory {} from install.yaml/#utility_dirs does not exist !!!".format(u_p))
    system('sudo cp {}/{} {}/{}'.format(pkg_path, "__init__.py", b_i_d_p, "__init__.py"))
    system('sudo chown -R {}:{} {}'.format(install["system_user"], install["system_group"], b_i_d_p))
    system('sudo chmod 775 {}/beaconServer/*.py'.format(b_i_d_p))
    system('sudo chmod 775 {}/services/*.py'.format(b_i_d_p))
    system('sudo chmod -R 1777 {}'.format(w_t_d_p))
    print("Updated the `server_tmp_dir_loc` in {} to\n{}".format(c_f, w_t_d_p))
    print("Updated bycon files from\n{}\nto\n{}".format(pkg_path, b_i_d_p))

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
