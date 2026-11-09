local_ips=$(hostname --all-ip-addresses 2>/dev/null) || local_ips=""
export APP_DRIVE_LOCAL_IPS="$local_ips"
