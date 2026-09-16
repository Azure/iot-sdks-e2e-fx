

# <[Certificate Handling]>

function Export-Pkcs8PrivateKeyPem {
    param($Key) 
    # Key of type [System.Security.Cryptography.RSA] or [System.Security.Cryptography.ECDsa]

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $KeyPemHex = [Convert]::ToBase64String($Key.Key.Export([System.Security.Cryptography.CngKeyBlobFormat]::Pkcs8PrivateBlob), 'InsertLineBreaks')
        return "-----BEGIN PRIVATE KEY-----`n$KeyPemHex`n-----END PRIVATE KEY-----"
    } else {
        return $Key.ExportPkcs8PrivateKeyPem()
    }
}

function Export-RsaPkcs1PrivateKeyPem {
    param([System.Security.Cryptography.RSA]$Key)

    try {
        if ($PSVersionTable.PSVersion.Major -lt 7) {
            throw "ExportRSAPrivateKeyPem is unavailable"
        }

        return $Key.ExportRSAPrivateKeyPem()
    }
    catch {
        # Fallback for older runtimes; PKCS8 is still accepted by non-Schannel paths.
        return Export-Pkcs8PrivateKeyPem -Key $Key
    }
}

function New-RsaKeyFromPem {
    param([string]$Pem)

    $rsa = [System.Security.Cryptography.RSA]::Create()

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $Base64 = ($Pem -replace "-----BEGIN PRIVATE KEY-----", "" -replace "-----END PRIVATE KEY-----", "").Trim() -replace "\s+", ""
        $KeyBytes = [Convert]::FromBase64String($Base64)
        $bytesRead = 0
        $rsa.ImportPkcs8PrivateKey($KeyBytes, [ref]$bytesRead)
    } else {
        $rsa.ImportFromPem($Pem)
    }

    return $rsa
}

function New-RsaPrivateKey {
    param(
        [string]$Path = $null,
        [switch]$Verbose
    )

    $rsa = [System.Security.Cryptography.RSA]::Create(4096)

    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        $pem = Export-Pkcs8PrivateKeyPem -Key $rsa

        if ($Verbose) {
            Write-Host "Saving private key to $Path"
        }

        Set-FileContent -Path $Path -Content $pem
    }

    return $rsa
}

function New-EcdsaPrivateKey {
    param(
        [string]$Curve = "nistP256",
        [string]$Path = $null,
        [switch]$Verbose
    )

    $ecdsa = [System.Security.Cryptography.ECDsa]::Create([System.Security.Cryptography.ECCurve]::CreateFromFriendlyName($Curve))

    if (-not [string]::IsNullOrWhiteSpace($Path)) {
        $pem = Export-Pkcs8PrivateKeyPem -Key $ecdsa

        if ($Verbose) {
            Write-Host "Saving ECDSA private key ($Curve) to $Path"
        }

        Set-FileContent -Path $Path -Content $pem
    }

    return $ecdsa
}

function New-X509CertificateSigningRequest {
    param(
        [string]$Subject,
        $Key = $null,
        [System.Security.Cryptography.HashAlgorithmName]$HashAlgorithm = [System.Security.Cryptography.HashAlgorithmName]::SHA256,
        [Switch]$AsBytes,
        [Switch]$NoHeaders
    )

    $DistinguishedName = [System.Security.Cryptography.X509Certificates.X500DistinguishedName]::new("CN=$Subject")
    $csr = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new($DistinguishedName, $Key, $HashAlgorithm)
    
    if ($AsBytes) {
        return $csr.CreateSigningRequest()
    } else {

        if ($NoHeaders) {
            return [Convert]::ToBase64String($csr.CreateSigningRequest())
        } else {
            $Base64Csr = [Convert]::ToBase64String($csr.CreateSigningRequest(), 'InsertLineBreaks')
            return "-----BEGIN CERTIFICATE REQUEST-----`n$Base64Csr`n-----END CERTIFICATE REQUEST-----"
        }
    }
}

function New-Certificate {
    param(
        [string]$Subject,
        [System.Security.Cryptography.RSA]$Key,
        [System.Security.Cryptography.X509Certificates.X509Certificate2]$IssuerCert = $null,
        [System.Security.Cryptography.RSA]$IssuerKey = $null,
        [bool]$IsCA = $false,
        [int]$Days = $DefaultCertificateExpiration.TotalDays,
        [string]$OutFile = $null
    )
    Write-Host "Running New-Certificate($Subject)"

    $req = [System.Security.Cryptography.X509Certificates.CertificateRequest]::new($Subject, [System.Security.Cryptography.RSA]$Key, [System.Security.Cryptography.HashAlgorithmName]::SHA256, [System.Security.Cryptography.RSASignaturePadding]::Pkcs1)

    $SubjectKeyIdentifierExtension = [System.Security.Cryptography.X509Certificates.X509SubjectKeyIdentifierExtension]::new($req.PublicKey, $false)
    $req.CertificateExtensions.Add($SubjectKeyIdentifierExtension)

    if ($IsCA) {
        $BasicConstraintExtension = New-Object System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension -ArgumentList $true, $false, 0, $true
        $req.CertificateExtensions.Add($BasicConstraintExtension)
    } else {
        $BasicConstraintExtension = New-Object System.Security.Cryptography.X509Certificates.X509BasicConstraintsExtension -ArgumentList $false, $false, 0, $false
        $req.CertificateExtensions.Add($BasicConstraintExtension)
    }

    if ($IsCA) {
        $KeyUsageExtension = [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new( `
            [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature `
            -bor [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::CrlSign `
            -bor [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyCertSign,
            $true)
    } else {
        $KeyUsageExtension = [System.Security.Cryptography.X509Certificates.X509KeyUsageExtension]::new( `
            [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::DigitalSignature `
            -bor [System.Security.Cryptography.X509Certificates.X509KeyUsageFlags]::KeyEncipherment,
            $true)
    }

    $req.CertificateExtensions.Add($KeyUsageExtension)

    if (-not $IsCA) {
        $EkuOids = [System.Security.Cryptography.OidCollection]::new()
        [void]$EkuOids.Add(
            [System.Security.Cryptography.Oid]::new("1.3.6.1.5.5.7.3.2") # clientAuth = 1.3.6.1.5.5.7.3.2
        ) 
        $EnhancedKeyUsageExtension = [System.Security.Cryptography.X509Certificates.X509EnhancedKeyUsageExtension]::new($EkuOids, $false)
        $req.CertificateExtensions.Add($EnhancedKeyUsageExtension)
    }

    $NotBefore = [datetime]::UtcNow
    $NotAfter = [datetime]::UtcNow.AddDays($Days)

    if ($null -eq $IssuerCert) {
        # Self-signed (Root CA)
        $NewCertificate = $req.CreateSelfSigned($NotBefore, $NotAfter)

        if (-not [string]::IsNullOrWhiteSpace($OutFile)) {
            Export-X509CertificateToPemFile -Cert $NewCertificate -Path $OutFile
        }

        return $NewCertificate
    } else {
        # Signed by issuer (Intermediate or Device)

        # Adjust NotBefore and NotAfter to match issuer certificate.
        if ($null -ne $IssuerCert.NotBefore -and $NotBefore -lt $IssuerCert.NotBefore) {
            $NotBefore = $IssuerCert.NotBefore
        }

        if ($null -ne $IssuerCert.NotAfter -and $NotAfter -gt $IssuerCert.NotAfter) {
            $NotAfter = $IssuerCert.NotAfter
        }

        # Serial number must be random bytes (8–20 bytes is typical)
        $SerialNumber = New-RandomNumber -Length 16

        # Use the issuer *private key* for signing
        $SignatureGenerator = [System.Security.Cryptography.X509Certificates.X509SignatureGenerator]::CreateForRSA(
            $IssuerKey,
            [System.Security.Cryptography.RSASignaturePadding]::Pkcs1
        )

        # Use issuer subject name from the issuer cert
        $NewCertificate = $req.Create(
            $IssuerCert.SubjectName,
            $SignatureGenerator,
            $NotBefore,
            $NotAfter,
            $SerialNumber
        )

        if (-not [string]::IsNullOrWhiteSpace($OutFile)) {
            Export-X509CertificateToPemFile -Cert $NewCertificate -Path $OutFile
        }

        return $NewCertificate
    }
}

function Export-X509CertificateToPem {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Certificate)

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        $CertificatePemHex = [Convert]::ToBase64String($Certificate.Export([System.Security.Cryptography.X509Certificates.X509ContentType]::Cert), 'InsertLineBreaks')
        return "-----BEGIN CERTIFICATE-----`n$CertificatePemHex`n-----END CERTIFICATE-----"
    } else {
        return $Certificate.ExportCertificatePem()
    }
}

function New-X509Certificate2FromPem {
    param([string]$Pem)

    $Base64 = ($Pem -replace "-----BEGIN CERTIFICATE-----", "" -replace "-----END CERTIFICATE-----", "").Trim() -replace "\s+", ""
    $CertBytes = [Convert]::FromBase64String($Base64)

    if ($PSVersionTable.PSVersion.Major -lt 7) {
        return [System.Security.Cryptography.X509Certificates.X509Certificate2]::new($CertBytes)
    } else {
        $Cert = [System.Security.Cryptography.X509Certificates.X509Certificate2]::new()
        $Cert.ImportFromPem($Pem)
        return $Cert
    }
}

function Export-X509CertificateToPemFile {
    param([System.Security.Cryptography.X509Certificates.X509Certificate2]$Cert, [string]$Path)
    $pem = Export-X509CertificateToPem -Certificate $Cert
    Write-Host "Exporting certificate to $Path"
    Set-FileContent -Path $Path -Content $pem
}
