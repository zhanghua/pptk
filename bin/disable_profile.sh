#/usr/bin/env bash

PROFILE_DATA_DIR='/opt/stack/data/swift/profile'
sudo mkdir -p ${PROFILE_DATA_DIR}

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
    sudo sed -e 's/^pipeline = profile /pipeline = /g' -i ${paste}
}

SERVER_TYPE=$1
case $SERVER_TYPE in
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
        configure_paste="/etc/swift/${SERVER_TYPE}-server/1.conf"
        configure_paste="/etc/swift/${SERVER_TYPE}-server/2.conf"
        configure_paste="/etc/swift/${SERVER_TYPE}-server/3.conf"
        ;;
     * )
        print_usage
        exit 0
        ;;
esac

echo 'Done!'
