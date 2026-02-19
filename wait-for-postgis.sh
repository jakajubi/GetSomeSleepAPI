#!/bin/bash
# wait-for-postgis.sh

set -e

host="$1"
shift
cmd="$@"

until PGPASSWORD=sleeppassword psql -h "$host" -U "sleepuser" -d "sleepdb" -c '\q' 2>/dev/null; do
  >&2 echo "PostGIS is unavailable - sleeping"
  sleep 2
done

>&2 echo "PostGIS is up - executing command"
exec $cmd