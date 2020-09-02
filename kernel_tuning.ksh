#!/bin/ksh

MODE=$1
COMMIT=$2
BACKUPDIR=/shared
KERNEL_STAGING=$BACKUPDIR/staging_kernel_params

logit () {
  case "$1" in 
    fatal) echo "EXITING : $2" ; exit 1 ;;
    warn) echo "WARNING : $2";;
    info) echo "INFO : $2";; 
  esac
}

check_sysctl () {

  sysctl -N "$1" >/dev/null 2>&1
  if [[ $? -eq 0 ]]; then
    if [[ -n $(grep -w $1 /etc/sysctl.d/*) ]]; then
      # action=0 flag if kernel parameter is defined in the post sysctl files
      action=0
    else
      # action=1 flag if kernel parameter is not defined in post sysctl files
      action=1
    fi
  else
    #action=2 flag if kernel parameter is invalid
    action=2
  fi

}

kernel_tuning () {

  case $MODE in
    pre) 
      >$BACKUPDIR/pre_kernel_params
      while read -r line; do
        echo $line >> $BACKUPDIR/pre_kernel_params
      done <<< $(egrep -v '^#|^$' /etc/sysctl.conf)
    ;;

    post)
      if [[ -z $COMMIT ]]; then
        >$KERNEL_STAGING
        while read -r line; do
          pre_kernel_key=$(echo $line | cut -d= -f1)
          pre_kernel_value=$(echo $line | cut -d= -f2 | sed 's/^ //')
          current_kernel_value=$(echo $(sysctl -n $pre_kernel_key))

          check_sysctl $pre_kernel_key

          case $action in
            0) 
              if [[ "$pre_kernel_value" == "$current_kernel_value" ]]; then
                logit info "$pre_kernel_key = $current_kernel_value - defined in both pre & post sysctl and with matched value. No action required"
              else
                logit warn "$pre_kernel_key - defined in both pre & post sysctl but with mismatched value"
                echo -n "Add the the PRE value of $pre_kernel_key in staging (pre: $pre_kernel_value, post: $current_kernel_value) [y|n]?"
                read ANS </dev/tty
                if [[ $ANS == [Yy] ]]; then
                  logit info "PRE value selected for $pre_kernel_key"
                  echo "$pre_kernel_key = $pre_kernel_value" >> $KERNEL_STAGING && logit info "$pre_kernel_key - PRE value added in staging"
                elif [[ $ANS == [Nn] ]]; then
                  logit info "POST value selected for $pre_kernel_key, excluded in staging"
                fi
              fi
              ;;

            1) 
              if [[ "$pre_kernel_value" == "$current_kernel_value" ]]; then
                logit info "$pre_kernel_key - not defined in post sysctl but pre sysctl & post runtime value matched. No action required"
              else
                logit warn "$pre_kernel_key - not defined in post sysctl but defined in pre sysctl, and both value is mismatched"
                echo -n "Add the the PRE value of $pre_kernel_key in staging (pre: $pre_kernel_value, post: $current_kernel_value) [y|n]?"
                read ANS </dev/tty
                if [[ $ANS == [Yy] ]]; then
                  logit info "PRE value selected for $pre_kernel_key"
                  echo "$pre_kernel_key = $pre_kernel_value" >> $KERNEL_STAGING && logit info "$pre_kernel_key - PRE value added in staging"
                elif [[ $ANS == [Nn] ]]; then
                  logit info "POST value selected for $pre_kernel_key, excluded in staging"
                fi
              fi
              ;;
        
            2) logit info "$pre_kernel_key - invalid parameter, ignorning";;
          esac
        done <<< $(cat $BACKUPDIR/pre_kernel_params)
        logit info "Review the kernel staging file - $KERNEL_STAGING"
      else
        if [[ -f $KERNEL_STAGING ]]; then
          logit info "Adding the staging kernel parameters in /etc/sysctl.d"
          cat $KERNEL_STAGING
        else
          logit warn "Kernel staging file does not exist, run post again"
        fi
      fi
    ;;
  esac
}




kernel_tuning
