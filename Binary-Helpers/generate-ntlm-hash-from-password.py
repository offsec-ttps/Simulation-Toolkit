from Cryptodome.Hash import MD4

def get_ntlm_hash(password):
    # NTLM uses UTF-16 Little Endian encoding
    utf16_password = password.encode('utf-16le')
    
    # MD4 hash of the UTF-16 encoded password
    ntlm_hash = MD4.new(utf16_password).hexdigest().upper()
    return ntlm_hash

# Example usage
password = "ItsSOCTime@2030@@!"  # Replace with the domain user's password
print(f"NTLM Hash: {get_ntlm_hash(password)}")
