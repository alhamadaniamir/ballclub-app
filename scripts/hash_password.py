import sys

import bcrypt

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: python scripts/hash_password.py <password>")
        sys.exit(1)
    print(bcrypt.hashpw(sys.argv[1].encode(), bcrypt.gensalt()).decode())
