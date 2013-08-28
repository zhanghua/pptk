#/usr/bin/env bash

profile_data_dir='/opt/stack/data/swift/profile'
sudo mkdir -p ${profile_data_dir}

function print_usage() {
    set echo off
    echo "Usage:  disable_profile.sh all|proxy|account|container|object"
    echo ""
    return 0
}

function configure_paste() {
    local paste=$1
    [ ! -e "$paste" ] && echo "Skip file ${paste} since it does not exist" && return 0

    if ! egrep filter:profile ${paste} > /dev/null; then
        echo "Exit since repoze.profile has not been configured."
        return 0
    fi

    echo 'disabling repoze.profile in paste config file '${paste}
    sudo sed -e 's/^pipeline = profile/pipeline =/g' -i ${paste}
}

server_type=$1
case $server_type in
    "all")
        configure_paste "/etc/swift/proxy-server.conf"
        configure_paste "/etc/swift/account-server/1.conf"
        configure_paste "/etc/swift/account-server/2.conf"
        configure_paste "/etc/swift/account-server/3.conf"
        configure_paste "/etc/swift/container-server/1.conf"
        configure_paste "/etc/swift/container-server/2.conf"
        configure_paste "/etc/swift/container-server/3.conf"
        configure_paste "/etc/swift/object-server/1.conf"
        configure_paste "/etc/swift/object-server/2.conf"
        configure_paste "/etc/swift/object-server/3.conf"
        ;;
    "proxy")
        configure_paste "/etc/swift/proxy-server.conf"
        ;;
     "account" | "container" | "object")
        configure_paste="/etc/swift/${server_type}-server/1.conf"
        configure_paste="/etc/swift/${server_type}-server/2.conf"
        configure_paste="/etc/swift/${server_type}-server/3.conf"
        ;;
     * )
        print_usage
        exit 0
        ;;
esac

echo 'Done!'
