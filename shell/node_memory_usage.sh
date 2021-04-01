#!/bin/bash


TEXTFILE_COLLECTOR_DIR=/home/raemone/monitor/node_exporter_current/textfile_collector
ps=$(ps auxh)

while read -r ps; do
   pid=$(echo $ps | awk '{print $2}')
   process_lname=$(cat /proc/$pid/cmdline)
   process_sname=$(echo $ps | awk '{print $11}')
   memory_usage_value=$(echo $ps | awk '{print $4}')
   process_owner=$(echo $ps | awk '{print $1}')

   if [[ $memory_usage_value != '0.0' ]]; then
      line="memory_usage_per_process{process_sname=\"$process_sname\", pid=\"$pid\", process_lname=\"$process_lname\", process_owner=\"$process_owner\"} $memory_usage_value"
      echo $line >> $TEXTFILE_COLLECTOR_DIR/node_memory_usage_per_process.prom.$$
   fi
done <<< "$ps"

# Rename the temporary file atomically.
# This avoids the node exporter seeing half a file.
mv "$TEXTFILE_COLLECTOR_DIR/node_memory_usage_per_process.prom.$$" \
  "$TEXTFILE_COLLECTOR_DIR/node_memory_usage_per_process.prom"

