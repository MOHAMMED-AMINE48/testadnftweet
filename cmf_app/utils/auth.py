"""
Password hashing and verification module using bcrypt.
Secure password handling for authentication.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Hash a plain text password using bcrypt.
    
    Args:
        plain_password: The plain text password to hash
    
    Returns:
        The hashed password as a string
    """
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(plain_password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, password_hash: str) -> bool:
    """
    Verify a plain text password against a stored hash.
    
    Args:
        plain_password: The plain text password to verify
        password_hash: The stored hashed password
    
    Returns:
        True if the password matches, False otherwise
    """
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            password_hash.encode("utf-8")
        )
    except Exception:
        return False
