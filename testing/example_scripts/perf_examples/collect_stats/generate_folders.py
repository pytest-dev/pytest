import argparse
import pathlib


HERE = pathlib.Path(__file__).parent
TEST_CONTENT = (HERE / "template_test.py").read_bytes()

parser = argparse.ArgumentParser()
parser.add_argument("root", type=str)
parser.add_argument("numbers", nargs="*", type=int)


def generate_folders(root, elements, *more_numbers, level=None):
    fill_len = len(str(elements))
    level = level or 1
    if more_numbers:
        for i in range(1, elements + 1):
            new_folder = root.joinpath(f"dir{level}_{i:0>{fill_len}}")
            new_folder.mkdir()
            new_folder.joinpath("__init__.py").write_bytes(TEST_CONTENT)
            generate_folders(new_folder, *more_numbers, level=level + 1)
    else:
        for i in range(1, elements + 1):
            new_test = root.joinpath(f"test_{i:0>{fill_len}}.py")
            new_test.write_bytes(TEST_CONTENT)


if __name__ == "__main__":
    args = parser.parse_args()
    root = pathlib.Path(args.root)
    root.mkdir(parents=True, exist_ok=True)
    generate_folders(root, *(args.numbers or (10, 100)))
