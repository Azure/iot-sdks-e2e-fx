#!/bin/bash

# This script will follow the edgeHub logs and attempt to reconnect when edgeHub is disconnected

if [ -z $1 ]; then 
	echo "To run, specify the container as the following: follow-logs.sh <container-name>"
	exit 1
fi

while true
do
	docker logs -f $1
	echo "=======================DISCONNECTED FROM CONTAINER $1============================"
	sleep 3
	echo "........................ATTEMPTING TO RECONNECT TO $1............................."
	sleep 2
done 
