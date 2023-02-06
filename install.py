#!/usr/local/bin/python3

import sys
from os import path, system

from ruamel.yaml.main import round_trip_load, round_trip_dump
from ruamel.yaml.comments import CommentedMap

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

    i_f = path.join( dir_path, "install.yaml" )

    try:
        with open( i_f ) as y_c:
            install = round_trip_load( y_c )
    except Exception as e:
        print(e)
        exit()

    # WARNING: This assumes that the values are sensible...
    for p in ["system_user", "system_group", "bycon_install_dir", "web_temp_dir"]:
        p_v = install.get(p, None)
        if p_v is None:
            print("¡¡¡ No `{}` value defined in {} !!!".format(p, i_f))
            exit()

    for d in ["bycon_install_dir", "web_temp_dir"]:
        d_p = path.join( *install.get(d, ["___path-error___"]) )
        if not path.isdir(d_p):
            print("¡¡¡ {}: {} does not exist - please check & create !!!".format(d, d_p))
            exit()

    b_i_d_p = path.join( *install["bycon_install_dir"] )
    w_t_d_p = path.join( *install["web_temp_dir"] )

    # this block modifies the main config file, so that the `web_temp_dir` is
    # in line

    c_f = path.join( pkg_path, "config", "config.yaml" )
    c_f_bck = path.join( pkg_path, "config", "config.yaml.bck" )
    try:
        with open( c_f ) as y_c:
            config = round_trip_load( y_c )
        system('cp {} {}'.format(c_f, c_f_bck))
    except Exception as e:
        print(e)
        exit()

    config.update({ "web_temp_dir":install["web_temp_dir"]})
    cf_p = CommentedMap(config)

    with open(c_f, 'w') as out_f:
        round_trip_dump(cf_p, out_f)

    # / config modification

    excludes = [
        "__pycache__",
        ".DS_*",
        ".git*",
    ]

    e_s = '--exclude="{}"'.format('" --exclude="'.join(excludes))
 
    system('sudo rsync -av {} {}/ {}/'.format(e_s, pkg_path, b_i_d_p))
    system('sudo chown -R {}:{} {}'.format(install["system_user"], install["system_group"], b_i_d_p))
    system('sudo chmod 775 {}/beaconServer/*.py'.format(b_i_d_p))
    system('sudo chmod 775 {}/services/*.py'.format(b_i_d_p))
    system('sudo chmod -R 1777 {}'.format(w_t_d_p))
    print("Updated the `web_temp_dir` in {} to\n{}".format(c_f, w_t_d_p))
    print("Updated bycon files from\n{}\nto\n{}".format(pkg_path, b_i_d_p))

    exit()

################################################################################
################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    main()
