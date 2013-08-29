#/usr/bin/env bash

PROFILE_DATA_DIR='/opt/stack/data/swift/profile'
sudo mkdir -p ${PROFILE_DATA_DIR}

SERVER_TYPE=$1
PROFILE_NAME=$2

function print_usage() {
    set echo off
    echo "Usage:  enable_profile.sh all|proxy|account|container|object [PROFILE_NAME]"
    echo ""
    return 0
}

function configure_paste() {
    local paste=$1
    local server=$2
    local profile=$3
    
    [ ! -e "$paste" ] && echo "Skip file ${paste} since it does not exist" && return 0

    if ! egrep filter:profile ${paste} > /dev/null; then
        echo "Exit since profile has not been configured. \
              you can use inject_profile tool to configure it."
        return 0
    fi
    if egrep "pipeline = profile" ${paste} > /dev/null; then
        echo "The paste file $paste has configured profile."
    else
        echo "enabling repoze.profile into paste config file ${paste}."
        sudo sed -e 's/^pipeline = /pipeline = profile /g' -i $paste
    fi
    
    if [ -n "$profile" ]; then
        echo "Just trying to change the profile name in paste file."
        mkdir -p $PROFILE_DATA_DIR/$profile
        sudo sed -e "
            s#^log_filename_prefix.*#log_filename_prefix = $PROFILE_DATA_DIR\/$profile\/$server.profile#g;
            s#^cachegrind_filename.*#cachegrind_filename = $PROFILE_DATA_DIR\/$profile\/cachegrind.out.$server#g;
        " -i $paste
    fi    
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