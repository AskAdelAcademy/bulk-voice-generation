# Dot-source in your own terminal. Does not persist or display the key.
if ([string]::IsNullOrWhiteSpace($env:TOPMEDIAI_API_KEY)) {
    $voiceSecureKey = Read-Host 'Enter your TopMediai API key (hidden)' -AsSecureString
    $voiceKeyPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($voiceSecureKey)
    try {
        $env:TOPMEDIAI_API_KEY = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($voiceKeyPointer)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($voiceKeyPointer)
        Remove-Variable voiceSecureKey, voiceKeyPointer -ErrorAction SilentlyContinue
    }
}
Write-Host 'Key configured for this terminal session. Its value has not been displayed or saved.'
