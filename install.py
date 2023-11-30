'''
installer for monkey chrome
'''
import shutil
import os
import zipfile
import tempfile
import gzip
import win32com.client
import requests
from tqdm import tqdm
from colorama import Fore, Style
import pefile


def download_file(url, filename):
    response = requests.get(url, stream=True, timeout=15)

    total_size_in_bytes = int(response.headers.get("content-length", 0))
    block_size = 1024

    progress_bar = tqdm(
        total=total_size_in_bytes,
        unit="iB",
        unit_scale=True,
        desc=os.path.basename(filename),
        ascii=True,
        ncols=75,
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt}",
    )

    with open(filename, "wb") as file:
        for data in response.iter_content(block_size):
            progress_bar.update(len(data))
            file.write(data)
    progress_bar.close()

    if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
        print(Fore.RED + f"ERROR, something went wrong downloading {url}" + Style.RESET_ALL)
        return False
    else:
        return filename


def extract_file(zip_path, extract_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    os.remove(zip_path)


def extract_gz_file(gz_file_path, output_file_path):
    with gzip.open(gz_file_path, 'rb') as gz_file:
        with open(output_file_path, 'wb') as out_file:
            shutil.copyfileobj(gz_file, out_file)


def move_files(src_dir, dst_dir):
    files = os.listdir(src_dir)
    for file in files:
        shutil.move(os.path.join(src_dir, file), dst_dir)


def compress_file_gzip(src_file_path, dst_file_path):
    with open(src_file_path, 'rb') as src, gzip.open(dst_file_path, 'wb') as dst:
        shutil.copyfileobj(src, dst)


def split_file(file_path, size_in_mb):
    chunk_size = size_in_mb * 1024 * 1024  # Convert size from MB to bytes
    part_num = 0

    with open(file_path, 'rb') as src_file:
        while True:
            chunk = src_file.read(chunk_size)
            if not chunk:  # End of file
                break

            part_num += 1
            part_file_path = f"{file_path}.part{part_num}"

            with open(part_file_path, 'wb') as part_file:
                part_file.write(chunk)


def join_files(file_prefix, output_file_path):
    part_num = 1
    with open(output_file_path, 'ab') as output_file:  # Open file in append mode
        while True:
            try:
                with open(f"{file_prefix}.part{part_num}", 'rb') as part_file:
                    chunk = part_file.read(1024 * 1024)  # Read in chunks of 1MB
                    while chunk:
                        output_file.write(chunk)
                        chunk = part_file.read(1024 * 1024)
                part_num += 1
            except FileNotFoundError:
                break  # No more part files


def assemble_dll(path):
    join_files(f"{path}/dll/chrome.gz", f"{path}/chrome.gz")


def create_shortcut(path, target):
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortCut(path)
    shortcut.Targetpath = target
    shortcut.save()


if __name__ == "__main__":
    print("Downloading monkey chrome...")
    zip_temp = os.path.join(tempfile.gettempdir(), "monkey-chrome.zip")
    doc_extract_path = os.path.join(os.path.expanduser('~/Documents'), "monkey-chrome")
    download_file("https://github.com/lflowers01/ungoogled-setup-for-monkies/archive/refs/heads/main.zip", zip_temp)
    print("Extracting files...")
    extract_file(zip_temp, doc_extract_path)
    move_files(os.path.join(doc_extract_path, "ungoogled-setup-for-monkies-main"), doc_extract_path)
    shutil.rmtree(os.path.join(doc_extract_path, "ungoogled-setup-for-monkies-main"))
    print("Assembling DLL...")
    assemble_dll(f"{doc_extract_path}")
    extract_gz_file(f"{doc_extract_path}/chrome.gz", f"{doc_extract_path}/chrome.dll")
    print("Cleaning up...")
    os.remove(f"{doc_extract_path}/chrome.gz")
    # shutil.rmtree(f"{doc_extract_path}/dll")
    desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    create_shortcut(f"{desktop_path}/monkey-chrome.lnk", f"{doc_extract_path}/chrome.exe")
    print("Done!")
