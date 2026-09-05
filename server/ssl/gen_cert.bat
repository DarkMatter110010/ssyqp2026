@echo off
rem ============================================================
rem  Generate local HTTPS certificates (local CA + server cert)
rem  using the bundled OpenSSL (server\openssl\openssl.exe)
rem  CA cert is imported into Windows trusted root store.
rem  Safe to re-run: old certs are kept as *.bak
rem ============================================================
setlocal
set "OPENSSL=%~dp0..\openssl\openssl.exe"
cd /d "%~dp0"

echo [1/5] Backup old certs...
if exist cert.pem copy /Y cert.pem cert.pem.bak >nul
if exist key.pem  copy /Y key.pem  key.pem.bak  >nul

echo [2/5] Create local CA (10 years)...
del ca.key ca.crt server.csr server.crt ca.srl 2>nul
"%OPENSSL%" genrsa -out ca.key 2048
"%OPENSSL%" req -new -x509 -key ca.key -out ca.crt -days 3650 ^
  -subj "/CN=YQP Local CA Root" ^
  -addext "basicConstraints=critical,CA:TRUE" ^
  -addext "keyUsage=critical,keyCertSign,cRLSign"

echo [3/5] Create server key and CSR...
"%OPENSSL%" genrsa -out key.pem 2048
"%OPENSSL%" req -new -key key.pem -out server.csr ^
  -subj "/CN=127.100.10.1" ^
  -addext "subjectAltName=IP:127.100.10.1,IP:127.0.0.1,DNS:localhost"

echo [4/5] Sign server cert with CA (825 days)...
(
echo basicConstraints=critical,CA:FALSE
echo keyUsage=critical,digitalSignature,keyEncipherment
echo extendedKeyUsage=serverAuth
echo subjectAltName=IP:127.100.10.1,IP:127.0.0.1,DNS:localhost
) > server_ext.cnf
"%OPENSSL%" x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial ^
  -out server.crt -days 825 -sha256 -extfile server_ext.cnf

echo [5/5] Build chain cert.pem and clean temp files...
type server.crt > cert.pem
type ca.crt >> cert.pem
del server.csr server_ext.cnf ca.srl 2>nul

echo.
echo ============================================
echo  Generated files in server\ssl:
echo    ca.crt     - local CA cert (for trust store)
echo    cert.pem   - server cert chain (for nginx)
echo    key.pem    - server private key (for nginx)
echo  Backup of old certs: cert.pem.bak key.pem.bak
echo ============================================
echo.
echo  Importing CA into Windows trusted root store...
certutil -user -addstore -f Root ca.crt
if errorlevel 1 (
    echo  Failed for current user, trying LocalMachine...
    certutil -addstore -f Root ca.crt
)
echo.
echo  Done. Verify with:  certutil -user -store Root ^| findstr "YQP"
pause >nul
