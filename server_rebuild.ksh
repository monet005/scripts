#!/bin/ksh
# 
# Pre and Post server rebuild script
#

BACKUPFS=/var/tmp
BACKUPDIR=$BACKUPFS/${HOSTNAME}_backup
POSTDIR=/tmp/${HOSTNAME}_post_rebuild
TARFILE=${HOSTNAME}_backup.tar.gz

# List of files to be backed up before rebuild
set -A files /etc /var/spool

# List of commands to capture before rebuild
set -A commands "uname -a" \
                "sysctl -a" \
                "ps -ef" \
                "uptime" \
                "cat /etc/sysctl.conf" \
                "cat /etc/security/limits.conf" \
                "netstat -rn" \
                "ip addr" \
                "rpm -qa" \

createBackup () {
    if [[ ! -d $BACKUPDIR ]]; then
        mkdir -p $BACKUPDIR
    fi

    if [[ -f $BACKUPDIR/$TARFILE ]]; then
        mv $BACKUPDIR/$TARFILE $BACKUPDIR/$(date +%F-%H%M%Z)_${TARFILE}
        echo "Previous backup exists, renaming it to $(date +%F-%H%M%S%Z)_${TARFILE}"
    fi

    if tar czf $BACKUPDIR/$TARFILE ${files[*]} 2>/dev/null; then
        echo "${files[*]} backed up successfully"
    else
        echo "Backup failed, please check"; exit 1
    fi
}

captureOutput () {
    if [[ ! -d $TARGET ]]; then
        mkdir -p $TARGET
    fi

    for command in "${commands[@]}"; do
        $command > $TARGET/$(echo $command | sed 's/[/|-]/_/g' | tr -s ' ' '_') 2>/dev/null
    done
}

case $1 in 
    pre) 
        TARGET=$BACKUPDIR
        createBackup
        captureOutput
        ;;
    post)
        TARGET=$POSTDIR
        captureOutput
        ;;
    *) echo "Usage: `basename $0` <pre|post>"
        ;;    
esac

#TODO
# post rebuild functions, compare and spot the differences.

