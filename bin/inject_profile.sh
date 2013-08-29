#/usr/bin/env bash

SERVER_TYPE=$1
PROFILE_NAME=$2

PROFILE_DATA_DIR='/opt/stack/data/swift/profile'
sudo mkdir -p ${PROFILE_DATA_DIR}

function print_usage() {
    set echo off
    echo "Usage:  ingest_profile.sh all|proxy|account|container|object [PROFILE_NAME]"
    echo ""
    return 0
}

function configure_paste() {
    local paste=$1
    local server=$2
    local profile=$3
    
    [ ! -e "$paste" ] && echo "Skip file ${paste} since it doesn't exist." && return 0
                  
    if egrep filter:profile ${paste} > /dev/null; then
        echo "Exit since repoze.profile has already been configured in ${paste}."
        return 0
    fi

    echo 'injecting repoze.profile into paste config file '${paste}
    sudo sed -e 's/^pipeline = /pipeline = profile /g' -i $paste
    [ -n "$profile" ] && [ ! -e "$profile" ] && sudo mkdir -p ${PROFILE_DATA_DIR}/${profile}
    
    sudo cat << EOF >> $paste
    
[filter:profile]
use = egg:repoze.profile
log_filename_prefix = ${PROFILE_DATA_DIR}/${profile}/${server}.profile
cachegrind_filename = ${PROFILE_DATA_DIR}/${profile}/cachegrind.out.${server}
dump_interval = 5
dump_timestamp = false
discard_first_request = true
path = /__profile__
flush_at_shutdown = false
unwind = false
EOF

    return 0
}


case $SERVER_TYPE in
    "all")
        configure_paste "/etc/swift/proxy-server.conf" "proxy" $PROFILE_NAME
        configure_paste "/etc/swift/account-server/1.conf" "account" $PROFILE_NAME
        configure_paste "/etc/swift/account-server/2.conf" "account" $PROFILE_NAME
        configure_paste "/etc/swift/account-server/3.conf" "account" $PROFILE_NAME
        configure_paste "/etc/swift/container-server/1.conf" "container" $PROFILE_NAME
        configure_paste "/etc/swift/container-server/2.conf" "container" $PROFILE_NAME
        configure_paste "/etc/swift/container-server/3.conf" "container" $PROFILE_NAME
        configure_paste "/etc/swift/object-server/1.conf" "object" $PROFILE_NAME
        configure_paste "/etc/swift/object-server/2.conf" "object" $PROFILE_NAME
        configure_paste "/etc/swift/object-server/3.conf" "object" $PROFILE_NAME
        ;;
    "proxy")
        configure_paste "/etc/swift/proxy-server.conf" "proxy" $PROFILE_NAME
        ;;
     "account" | "container" | "object")
        configure_paste "/etc/swift/${SERVER_TYPE}-server/1.conf" $SERVER_TYPE $PROFILE_NAME
        configure_paste "/etc/swift/${SERVER_TYPE}-server/2.conf" $SERVER_TYPE $PROFILE_NAME
        configure_paste "/etc/swift/${SERVER_TYPE}-server/3.conf" $SERVER_TYPE $PROFILE_NAME
        ;;
     * )
        print_usage
        exit 0
        ;;
esac

echo 'Done!'
