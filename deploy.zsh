#!/usr/bin/env zsh

timestamp=$(date '+%Y-%m-%d@%H:%M')
folder='build'
filename='mrz-deployment'
deployment="${filename}-${timestamp}.zip"
location="${folder}/${deployment}"

echo "Building: ${location}"

ls *.{py,txt} | xargs zip $location

scp -i ~/.ssh/id_rsa $location hcole@ciri:deployments/nimbus/mrz/

echo "Uploaded: ${location}"

rm $location

echo "Deleted: ${location}"