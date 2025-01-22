import bcrypt

def generate_hashed_password(plain_password):
    """
    Hashes a plain text password using bcrypt.
    :param plain_password: The plain text password to hash.
    :return: The hashed password as bytes.
    """
    # Generate a salt
    salt = bcrypt.gensalt()

    # Hash the password
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), salt)

    return hashed_password



