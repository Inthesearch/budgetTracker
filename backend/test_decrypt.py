"""
Quick test script to decrypt a password
Usage: python test_decrypt.py
"""
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.auth import decrypt_password, encrypt_password

def main():
    print("=== Password Decryption Test ===\n")
    
    # Example 1: Encrypt then decrypt
    original_password = input("Enter a password to encrypt: ")
    
    # Encrypt it
    encrypted = encrypt_password(original_password)
    print(f"\nEncrypted: {encrypted}")
    
    # Decrypt it
    decrypted = decrypt_password(encrypted)
    print(f"Decrypted: {decrypted}")
    print(f"Match: {original_password == decrypted}\n")
    
    # Example 2: Decrypt an existing encrypted password
    print("=== Decrypt Existing Password ===")
    existing_encrypted = input("Enter encrypted password to decrypt: ")
    
    try:
        decrypted = decrypt_password(existing_encrypted)
        print(f"Decrypted password: {decrypted}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()

