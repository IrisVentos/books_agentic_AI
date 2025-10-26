# Désactiver SSL globalement
$env:PYTHONHTTPSVERIFY = "0"
$env:REQUESTS_CA_BUNDLE = ""
$env:CURL_CA_BUNDLE = ""
$env:SSL_CERT_FILE = ""
$env:NODE_TLS_REJECT_UNAUTHORIZED = "0"
$env:PYTHONWARNINGS = "ignore:Unverified HTTPS request"
$env:GIT_SSL_NO_VERIFY = "true"

Write-Host "⚠️ SSL Verification Disabled - Development Mode" -ForegroundColor Yellow