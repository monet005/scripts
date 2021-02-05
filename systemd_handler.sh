#!/bin/bash

SYSTEMD_DIR=$HOME/.config/systemd/user
KV_PREFIX=systemd
SVC_NAME=$1

[ -d $SYSTEMD_DIR ] || mkdir -p $SYSTEMD_DIR

consul kv get $KV_PREFIX/${SVC_NAME} > ${SYSTEMD_DIR}/${SVC_NAME}.service

sudo systemd-analyze verify ${SYSTEMD_DIR}/${SVC_NAME}.service >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
    echo "${SVC_NAME}.service added" | systemd-cat -t sabre-systemd -p info
    systemctl --user daemon-reload
    systemctl --user start ${SVC_NAME}.service && \
    echo "${SVC_NAME}.service started" | systemd-cat -t sabre-systemd -p info
else
    echo "${SVC_NAME}.service - systemd configuration checks failed" \
    | systemd-cat -t sabre-systemd -p info
    rm -f ${SYSTEMD_DIR}/${SVC_NAME}.service
    systemctl --user daemon-reload
fi