#!/bin/bash

# List all overrides
declare -A OVERRIDES

OVERRIDES[ADMIN_EMAILS]="admin@ppm.com"

OVERRIDES[SECRET_KEY]="$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1)"
OVERRIDES[DJANGO_DEBUG]="True"
OVERRIDES[RAVEN_URL]=""

OVERRIDES[MYSQL_PASSWORD]="Q9ID8!2nkljadb@n5AEW9V"
OVERRIDES[MYSQL_HOST]="stackdb"
OVERRIDES[MYSQL_PORT]="3306"

OVERRIDES[EMAIL_BACKEND]="django.core.mail.backends.smtp.EmailBackend"
OVERRIDES[EMAIL_HOST]="email-smtp.us-east-1.amazonaws.com"
OVERRIDES[EMAIL_HOST_USER]=""
OVERRIDES[EMAIL_HOST_PASSWORD]=""
OVERRIDES[EMAIL_PORT]="1025"
OVERRIDES[EMAIL_USE_SSL]="False"

OVERRIDES[RECAPTCHA_DISABLED]="True"

OVERRIDES[FHIR_URL]="http://ppm-test-fhir.aws.dbmi.hms.harvard.edu:8008/baseDstu3"
OVERRIDES[FHIR_CONSENT_URL]="http://consent.aws.dbmi-dev.hms.harvard.edu:8003"
OVERRIDES[FHIR_SURVEY_URL]="http://questionnaire.aws.dbmi-dev.hms.harvard.edu:8001"
OVERRIDES[FHIR_CONSENT_URL_NEER]="http://consent-neer.aws.dbmi-dev.hms.harvard.edu:8009"
OVERRIDES[FHIR_SURVEY_URL_NEER]="http://questionnaire-neer.aws.dbmi-dev.hms.harvard.edu:8007"

# p2m2
if [[ $1 == "p2m2" ]]; then

    # Make sure curl is installed
    apt-get update && apt-get install -y curl

fi

if [[ $1 == "proxy" ]]; then

    OVERRIDES[SQLALCHEMY_DATABASE_URI]="mysql+pymysql://proxy:Q9ID8!2nkljadb@n5AEW9V@stackdb:3306/proxy"
    OVERRIDES[API_SERVER]="http://ppm-test-fhir.aws.dbmi.hms.harvard.edu:8008/baseDstu3"
    OVERRIDES[PREFERRED_URL_SCHEME]="https"

    # Update fixtures
    sed -i 's|#REDIRECT_URL#:8001|http://questionnaire.aws.dbmi-dev.hms.harvard.edu:8001|g' /auth_proxy/auth_proxy/fixtures.yml
    sed -i 's|#REDIRECT_URL#:8007|http://questionnaire-neer.aws.dbmi-dev.hms.harvard.edu:8007|g' /auth_proxy/auth_proxy/fixtures.yml
    sed -i 's|#REDIRECT_URL#:8003|http://consent.aws.dbmi-dev.hms.harvard.edu:8003|g' /auth_proxy/auth_proxy/fixtures.yml
    sed -i 's|#REDIRECT_URL#:8009|http://consent-neer.aws.dbmi-dev.hms.harvard.edu:8009|g' /auth_proxy/auth_proxy/fixtures.yml

    cat /auth_proxy/auth_proxy/fixtures.yml
fi

if [[ $1 == "consent"* || $1 == "questionnaire"* ]]; then

    OVERRIDES[FHIR_API_BASE]="https://smart.aws.dbmi-dev.hms.harvard.edu:8005/api/fhir"
    OVERRIDES[FHIR_INTERNAL_URL]="http://ppm-test-fhir.aws.dbmi.hms.harvard.edu:8008/baseDstu3"

    # Remove all SSL from the NGINX config
    for conf in /etc/nginx/sites-available/*; do
        sed -i -e '/ssl_/d' "$conf"
        sed -i -e 's/ssl//g' "$conf"
    done
fi

if [[ $1 == "fhir" ]]; then

    OVERRIDES[FHIR_MYSQL_URL]="jdbc:mysql://stackdb:3306/fhir"
    OVERRIDES[FHIR_MYSQL_USERNAME]="fhir"
    OVERRIDES[FHIR_MYSQL_PASSWORD]="Q9ID8!2nkljadb@n5AEW9V"
    OVERRIDES[FHIR_SERVER_URL]="http://ppm-test-fhir.aws.dbmi.hms.harvard.edu:8008/baseDstu3"
    OVERRIDES[FHIR_SERVER_NAME]="PPM-TEST"
    OVERRIDES[APP_PORT]="8008"

    for conf in /etc/nginx/conf.d/*; do
        sed -i -e '/ssl_/d' "$conf"
        sed -i -e 's/ssl//g' "$conf"
    done

fi

# Iterate over the array and make the replacements
for K in "${!OVERRIDES[@]}"; do

    # Remove all existing occurrences of this environment variable
    sed -i "s|^export $K=.*||g" "$2"
    sed -i "s|^export $K\$||g" "$2"
    sed -i "s|^$K=.*||g" "$2"

    echo "Adding: $K=${OVERRIDES[$K]}"
    sed -i "s|SSL_KEY=.*|export $K=\"${OVERRIDES[$K]}\"\n&|" "$2"

done

# Run the usual entrypoint
exec $2