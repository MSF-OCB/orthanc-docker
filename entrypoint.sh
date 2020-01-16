#! /usr/bin/env bash

CMD="$@"

sed -e "s/%orthanc_http_password%/${ORTHANC_HTTP_PASSWORD}/" /etc/orthanc/orthanc.json.tmpl > /etc/orthanc/orthanc.json

# Original entrypoint was "Orthanc"
Orthanc /etc/orthanc

