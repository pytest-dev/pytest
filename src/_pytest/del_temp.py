import os
import shutil

def main():
    path = 'temp/temp_output'
    if os.path.exists(path):
        shutil.rmtree(path)
        print("File path deleted: {}".format(path))

if __name__ == "__main__":
    main()
