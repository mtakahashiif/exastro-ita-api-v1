#!/bin/bash

##############################################################################
# variables (general)

BASE_SCRIPT_NAME=$(basename $0 .sh)

if [ -f .env ]; then
    source .env
fi

: ${EXASTRO_PROTOCOL:=http}
: ${EXASTRO_HOST:=localhost}
: ${EXASTRO_PORT:=8080}
: ${EXASTRO_USERNAME:=administrator}
: ${EXASTRO_INITIAL_PASSWORD:=password}
: ${EXASTRO_PASSWORD:?"No value assigned."}
: ${TMPDIR:=/tmp}

EXASTRO_URL=${EXASTRO_PROTOCOL}://${EXASTRO_HOST}:${EXASTRO_PORT}


##############################################################################
# variables (file paths)

EXASTRO_COOKIE_FILE=${TMPDIR}/${BASE_SCRIPT_NAME}-cookie.txt
EXASTRO_CURL_OUTPUT_00_FILE=${TMPDIR}/${BASE_SCRIPT_NAME}-curl-00.html
EXASTRO_CURL_OUTPUT_01_FILE=${TMPDIR}/${BASE_SCRIPT_NAME}-curl-01.html
EXASTRO_CURL_OUTPUT_02_FILE=${TMPDIR}/${BASE_SCRIPT_NAME}-curl-02.html
EXASTRO_CURL_OUTPUT_03_FILE=${TMPDIR}/${BASE_SCRIPT_NAME}-curl-03.html


##############################################################################
# variables (URL encoded username and password)

function urlencode() {
    python3 -c "import urllib.parse, sys; print(urllib.parse.quote(sys.argv[1]))" "${1}"
}

EXASTRO_URL_ENCODED_USERNAME=$(urlencode ${EXASTRO_USERNAME})
EXASTRO_URL_ENCODED_INITIAL_PASSWORD=$(urlencode ${EXASTRO_INITIAL_PASSWORD})
EXASTRO_URL_ENCODED_PASSWORD=$(urlencode ${EXASTRO_PASSWORD})


##############################################################################
# initialize password

# Login dialog
curl \
    --silent \
    --show-error \
    --request GET \
    --location \
    --cookie-jar ${EXASTRO_COOKIE_FILE} \
    --output ${EXASTRO_CURL_OUTPUT_00_FILE} \
    ${EXASTRO_URL}'/common/common_auth.php?login'

# Get CSRF token by XPath.
# The stderr is throwed away to suppress warning for invalid child tags (<span> and <div>) in <head>.
CSRF_TOKEN=$(xmllint --html --xpath 'string(//input[@name="csrf_token"]/@value)' ${EXASTRO_CURL_OUTPUT_00_FILE} 2> /dev/null)

# Send user name and initial password.
curl \
    --silent \
    --show-error \
    --request POST \
    --location \
    --cookie ${EXASTRO_COOKIE_FILE} \
    --cookie-jar ${EXASTRO_COOKIE_FILE} \
    --header 'Referer: '${EXASTRO_URL}'/common/common_auth.php?login' \
    --data 'username='${EXASTRO_URL_ENCODED_USERNAME}'&password='${EXASTRO_URL_ENCODED_INITIAL_PASSWORD}'&csrf_token='${CSRF_TOKEN}'&login=%E3%83%AD%E3%82%B0%E3%82%A4%E3%83%B3' \
    --output ${EXASTRO_CURL_OUTPUT_01_FILE} \
    ${EXASTRO_URL}'/common/common_auth.php?login='

# Then return "401 not auth" and automatically post by javascript (see blow curl command).

# Automatic POST (why?)
curl \
    --silent \
    --show-error \
    --request POST \
    --location \
    --cookie ${EXASTRO_COOKIE_FILE} \
    --cookie-jar ${EXASTRO_COOKIE_FILE} \
    --header 'Referer: '${EXASTRO_URL}'/default/mainmenu/01_browse.php' \
    --data 'expiry=0&username='${EXASTRO_URL_ENCODED_USERNAME} \
    --output ${EXASTRO_CURL_OUTPUT_02_FILE} \
    ${EXASTRO_URL}'/common/common_change_password_form.php?login'

# Send new password.
curl \
    --silent \
    --show-error \
    --request POST \
    --location \
    --cookie ${EXASTRO_COOKIE_FILE} \
    --cookie-jar ${EXASTRO_COOKIE_FILE} \
    --header 'Referer: '${EXASTRO_URL}'/common/common_change_password_form.php?login\r\n' \
    --data 'old_password='${EXASTRO_URL_ENCODED_INITIAL_PASSWORD}'&new_password='${EXASTRO_URL_ENCODED_PASSWORD}'&new_password_2='${EXASTRO_URL_ENCODED_PASSWORD}'&submit=%E5%A4%89%E6%9B%B4&expiry=0' \
    --output ${EXASTRO_CURL_OUTPUT_03_FILE} \
    ${EXASTRO_URL}'/common/common_change_password_do.php?login='


##############################################################################
# test

EXASTRO_API_CREDENTIAL=$(echo -n "${EXASTRO_USERNAME}:${EXASTRO_PASSWORD}" | base64)

curl \
    --silent \
    --show-error \
    --request POST \
    --header "Authorization: ${EXASTRO_API_CREDENTIAL}" \
    --header 'X-Command: INFO' \
    ${EXASTRO_URL}'/default/menu/07_rest_api_ver1.php?no=2100000303' | jq
