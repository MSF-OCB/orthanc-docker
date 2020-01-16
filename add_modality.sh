
AUTH_USERNAME="${1}"

MOD_AE_TITLE="${2}"
MOD_IP_ADDR="${3}"
MOD_PORT="${4:-104}"

if [ -z "${AUTH_USERNAME}" ] || \
   [ -z "${MOD_AE_TITLE}" ]  || \
   [ -z "${MOD_IP_ADDR}" ]   || \
   [ -z "${MOD_PORT}" ];     then
  echo "Usage: add_modality.sh <auth username> <ae title> <ip addr> <port>"
  exit 1
fi

echo -e "\nAE title: ${MOD_AE_TITLE}"
echo -e "IP address: ${MOD_IP_ADDR}"
echo -e "Port: ${MOD_PORT}\n"
read -p "IS the above information correct? Please type \"yes\": " CORRECT

if [ "${CORRECT}" = "yes" ]; then
  read -sp "Auth password: " AUTH_PASSWD

  curl -u "${AUTH_USERNAME}":"${AUTH_PASSWD}" \
       -v \
       -X PUT \
       http://localhost:8042/modalities/"${MOD_AE_TITLE}" \
       -d "{\"AET\" : \"${MOD_AE_TITLE}\", \"Host\": \"${MOD_IP_ADDR}\", \"Port\": ${MOD_PORT}}"
fi

