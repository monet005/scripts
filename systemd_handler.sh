#!/bin/bash

SYSTEMD_DIR=$HOME/.config/systemd/user
KV_PREFIX=systemd
KEY=$1
SVC_KEY=$(echo $1 | tr ' ', '-')
SVC_NAME=${SVC_KEY}.service
SVC_TMP=/tmp/${SVC_NAME}
SVC_USER=${SYSTEMD_DIR}/${SVC_NAME}


logit () {
  case "$1" in
    info) echo "$2" | systemd-cat -t sabre-systemd -p info ;;
    warn) echo "$2" | systemd-cat -t sabre-systemd -p warning ;;
  esac
}

[ -d $SYSTEMD_DIR ] || mkdir -p $SYSTEMD_DIR

consul kv get $KV_PREFIX/"${KEY}" > $SVC_TMP && \
logit info "$SVC_NAME change detected"

sudo systemd-analyze verify $SVC_TMP >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
    mv $SVC_TMP $SVC_USER
    systemctl --user daemon-reload
    systemctl --user enable $SVC_NAME
    CHECK=$(systemctl --user is-active $SVC_NAME)
    if [[ $CHECK != 'active' ]]; then
        systemctl --user start $SVC_NAME && \
        logit info "$SVC_NAME started"
    else
        logit info "$SVC_NAME already running"
    fi
else
    logit warn "$SVC_NAME config checks failed, not updating the service"
    rm -f $SVC_TMP
fi
