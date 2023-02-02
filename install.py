#!/usr/local/bin/python3

import sys, yaml
from os import path, system

dir_path = path.dirname( path.abspath(__file__) )
pkg_path = path.join( dir_path, "bycon" )
sys.path.append( pkg_path )

"""
The install script copies the relevant bycon files to the webserver directory
specified in the `config/config.yaml` file and sets the file permissions
accordingly. It requires admin permissions (sudo).
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

    c_f = path.join( pkg_path, "config", "config.yaml" )

    try:
        with open( c_f ) as y_c:
            config = yaml.load( y_c , Loader=yaml.FullLoader)
    except Exception as e:
        print(e)
        exit()

    # WARNING: This assumes that the values are sensible...
    for p in ["system_user", "system_group", "bycon_install_dir", "web_temp_dir"]:
        p_v = config.get(p, None)
        if p_v is None:
            print("¡¡¡ No `{}` value defined in {} !!!".format(p, c_f))
            exit()

    for d in ["bycon_install_dir", "web_temp_dir"]:
        d_p = path.join( *config.get(d, ["___path-error___"]) )
        if not path.isdir(d_p):
            print("¡¡¡ {}: {} does not exist - please check & create !!!".format(d, d_p))
            exit()

    b_i_d_p = path.join( *config["bycon_install_dir"] )
    w_t_d_p = path.join( *config["web_temp_dir"] )

    excludes = [
        "__pycache__",
        ".DS_*",
        ".git*",
    ]

    e_s = '--exclude="{}"'.format('" --exclude="'.join(excludes))
 
    system('sudo rsync -av {} {}/ {}/'.format(e_s, pkg_path, b_i_d_p))
    system('sudo chown -R {}:{} {}'.format(config["system_user"], config["system_group"], b_i_d_p))
    system('sudo chmod 775 {}/beaconServer/*.py'.format(b_i_d_p))
    system('sudo chmod 775 {}/services/*.py'.format(b_i_d_p))
    system('sudo chmod -R 1777 {}'.format(w_t_d_p))
    print("Updated bycon files from\n{}\nto\n{}".format(pkg_path, b_i_d_p))

    exit()

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
