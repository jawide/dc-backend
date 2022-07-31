import shelve
import os


if __name__ == '__main__':
    with shelve.open('data/user', 'c') as data:
        data.clear()
        data[os.environ.get('USERNAME') or 'admin'] = os.environ.get('PASSWORD') or 'password'