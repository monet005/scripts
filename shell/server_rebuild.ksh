#!/bin/ksh
# 
# Pre and Post server rebuild script
#

BACKUPFS=/vagrant
BACKUPDIR=$BACKUPFS/${HOSTNAME}_backup
TARFILE=${HOSTNAME}_backup.tar.gz
POSTDIR=$BACKUPFS/${HOSTNAME}_post_rebuild
RESTOREDIR=$POSTDIR/restore_tmp
COMMIT=$2

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

set -A system_accounts root bin daemon adm lp sync shutdown halt mail operator games ftp nobody \
       systemd-network dbus polkitd sshd postfix chrony vagrant rpc rpcuser nfsnobody vboxadd

set -A system_groups root bin daemon sys adm tty disk lp mem kmem wheel cdrom mail man dialout floppy games \
       tape video ftp lock audio nobody users utmp utempter input systemd-journal systemd-network dbus polkitd \
       ssh_keys sshd postdrop postfix chrony vagrant rpc rpcuser nfsnobody printadmin vboxsf raemone ruth biboy

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

extractBackup () {
    if [[ -f $BACKUPDIR/$TARFILE ]]; then
        tar -xzf $BACKUPDIR/$TARFILE -C $TARGET && echo "Backup files extracted to $TARGET successfully"
    fi  
}

restoreConfigs () {
    if [[ ! -d $RESTOREDIR ]]; then
        mkdir $RESTOREDIR
    fi

    rm -f $RESTOREDIR/*

    # sysctl
    grep -v '^#' $TARGET/etc/security/limits.conf | sed '/^$/d' >> $RESTOREDIR/limits \
                && echo "check limit values at $RESTOREDIR/limits_tmp"
    
    # users
    for user in $(cut -d: -f1 $TARGET/etc/passwd); do
        echo "${system_accounts[@]}" | grep -vq $user
        if [[ $? -eq 0 ]]; then
            echo $(grep $user $TARGET/etc/passwd) >> $RESTOREDIR/passwd
        fi
    done

    # groups
    for group in $(cut -d: -f1 $TARGET/etc/group); do
        echo "${system_groups[@]}" | grep -vq $group
        if [[ $? -eq 0 ]]; then
            echo $(grep $group $TARGET/etc/group) >> $RESTOREDIR/group
        fi
    done
 
    
    if [[ $COMMIT == "commit" ]]; then
        echo "Extra customizations applied"
        cat $RESTOREDIR/limits >> /etc/security/limits.conf
        cat $RESTOREDIR/passwd >> /etc/passwd
        cat $RESTOREDIR/group >> /etc/group
    fi
 
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
        #extractBackup
        restoreConfigs
        ;;
    *) echo "Usage: `basename $0` <pre|post> [commit]"
        ;;    
esac

#TODO
# post rebuild functions, compare and spot the differences.

