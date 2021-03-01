#!/usr/bin/env python3

from asyncio import subprocess
import os, requests
from typing import Iterable
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
from argparse import ArgumentParser as ArgParser
import asyncio

OPEN_KATTIS = "https://open.kattis.com/problems/{id}/file/statement/samples.zip"
ITU_KATTIS = "https://itu.kattis.com/problems/{id}/file/statement/samples.zip"

def init_dir(args):
    try:
        olddir = Path(args.dir)
        newdir = olddir.joinpath(args.problem)
        os.mkdir(newdir)
        if not args.no_download:
            if args.problem.startswith("itu."):
                r = requests.get(ITU_KATTIS.format(id=args.problem))
            else:
                r = requests.get(OPEN_KATTIS.format(id=args.problem))
            if r.status_code >= 400:
                print("Warning! Could not download sample data. Proceeding without...")
            zip = ZipFile(BytesIO(r.content))
            zip.extractall(path=newdir)
    except FileExistsError:
        pass

    

def test_dir(args):
    if len(args.files) == 0:
        args.files = os.scandir('.')
    in2ans = dict()
    tasks = []
    for file in Path(args.dir).glob('*.ans'):
        in2ans[file.stem] = file.read_text()
    for entry in in2ans.keys():
        tasks.append(exec_test(args.program, f"{entry}.in"))
    asyncio.run(asyncio.gather(*tasks))
            

async def exec_test(arguments: Iterable, input_file: str, expected: str):
    with open(input_file) as fp:
        p = await asyncio.create_subprocess_exec(arguments, stdin=fp, stdout=subprocess.STDOUT)
    await p.wait()
    output = p.stdout
    if output == expected:
        print(f"Input file {input_file} passes")
    else:
        print(f"Input file {input_file} does not pass. Expected: {expected}. Got {output}")



parser = ArgParser()
parser.add_argument("--dir", default=os.getcwd())
subparsers = parser.add_subparsers()

init_parser = subparsers.add_parser('init')
init_parser.add_argument("problem")
init_parser.add_argument("--no-download", action='store_true', help="Specifies that sample data should not be downloaded from the Kattis server")
init_parser.set_defaults(func=init_dir)

test_parser = subparsers.add_parser('test')
test_parser.add_argument("program", nargs='+')
test_parser.set_defaults(func=test_dir)

def main():
    args = parser.parse_args()
    args.func(args)
 

if __name__ == "__main__":
    main()