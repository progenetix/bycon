#!/usr/bin/env python3

# version: 2024-10-11

import sys, re, yaml
from os import getlogin, makedirs, path, system
dir_path = path.dirname( path.abspath(__file__) )

"""
The install script copies the relevant bycon files to the webserver directory
specified in the `./local/local_paths.yaml` file and sets the file permissions
accordingly. By default, it requires admin permissions (sudo). If you want to run
it without sudo, invoke it with `--no-sudo`. The current use will need to be able
to write into the target directories. 

Versions after 2023-02-07 _only_ copy the script directories and local configuration
directory to the server path; additionally a bycon package install is needed with
`pip3 install "bycon>=2.0.0"` (v2 "Taito City"). However, the preferred method is
to modify your local configuration and then perform a package build, installation
and server installation by running the `updev.sh` script.
"""

################################################################################
################################################################################
################################################################################

def main(no_sudo):
    if no_sudo:
        sudo_cmd = ""
    else:
        sudo_cmd = "sudo"

    local_conf_source = path.join(dir_path, "local", "")
    i_f = path.join(local_conf_source, "local_paths.yaml" )
 
    try:
        with open( i_f ) as y_c:
            install = yaml.load( y_c , Loader=yaml.FullLoader)
    except Exception as e:
        print(e)
        exit()

    # WARNING: This assumes that the values are sensible...
    for p in ["system_user", "system_group", "bycon_install_dir"]:
        p_v = install.get(p)
        if p_v is None:
            print("¡¡¡ No `{}` value defined in {} !!!".format(p, i_f))
            exit()

    s_u = install["system_user"]
    s_g = install["system_group"]
    b_i_d_p = path.join( *install["bycon_install_dir"] )

    server_source = path.join(dir_path, "beaconServer", "")
    services_source = path.join(dir_path, "byconServices", "")
    l_server_target = path.join(b_i_d_p, "local", "")
    server_target = path.join(b_i_d_p, "beaconServer", "")
    services_target = path.join(b_i_d_p, "services", "")

    system(f'{sudo_cmd} rsync -avh --delete {local_conf_source} {l_server_target}')
    print(f'==> Copied server configuration files from {local_conf_source} to {l_server_target}')
    system(f'{sudo_cmd} rsync -avh --delete {server_source} {server_target}')
    print(f'==> Copied server files from {server_source} to {server_target}')
    system(f'{sudo_cmd} rsync -avh --delete {services_source} {services_target}')
    print(f'==> Copied server files from {services_source} to {services_target}')

    system(f'{sudo_cmd} chown -R {s_u}:{s_g} {b_i_d_p}')
    system(f'{sudo_cmd} chmod 775 {server_target}*.py')
    print(f'{sudo_cmd} chmod 775 {server_target}*.py')
    system(f'{sudo_cmd} chmod 775 {services_target}*.py')
    print(f'{sudo_cmd} chmod 775 {services_target}*.py')

    print(f'Updated bycon files from\n{path.join(dir_path, "bycon")}\nto\n{b_i_d_p}')

################################################################################
################################################################################
################################################################################

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == "--no-sudo":
        no_sudo = True
    else:
        no_sudo = False

    main(no_sudo)
