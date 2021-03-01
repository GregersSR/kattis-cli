#!/usr/bin/env python3

from asyncio import subprocess
import os, requests
from typing import Iterable
from io import BytesIO
from zipfile import ZipFile
from pathlib import Path
from argparse import ArgumentParser as ArgParser
import asyncio
import aiofiles
import time
from inspect import cleandoc

NEWLINE = "\n"

OPEN_KATTIS = "https://open.kattis.com/problems/{id}/file/statement/samples.zip"
ITU_KATTIS = "https://itu.kattis.com/problems/{id}/file/statement/samples.zip"

MD_TEMPLATE = """
# Failed test result at {ts_hr}

The following test results were obtained from running {exec} against {input_filename}, which contains:
{input}
---------------
## Expected

{expected}

## Actual output

{output}
             
"""

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
    print(args)
    in2ans = dict()
    tasks = []
    for file in Path(args.dir).glob('*.ans'):
        in2ans[file.stem] = file.read_text()
    for entry in in2ans.keys():
        tasks.append(exec_test(args.program, arguments=args.prog_arguments, input_file=f"{entry}.in", expected=in2ans[entry]))
    asyncio.run(run_tests(tasks))
        
async def run_tests(tasks: list):
    await asyncio.gather(*tasks)

async def exec_test(program, arguments: Iterable, input_file: str, expected: str):
    async with aiofiles.open(input_file) as fp:
        p = await asyncio.create_subprocess_exec(program, *arguments, stdin=fp, stdout=subprocess.PIPE)
    await p.wait()
    output = await p.stdout.read()
    output = output.decode()
    if expected == output:
        print(f"Input file {input_file} passes")
    else:
        await write_error(program + " " + " ".join(arguments), input_filename=input_file, expected=expected, output=output)

async def write_error(exec: str, input_filename: str, expected: str, output: str):
    info: dict = {
        'exec': exec,
        'input_filename': input_filename,
        'expected': expected,
        'output': output
    }
    info['ts'] = time.time()
    info['ts_hr'] = info['ts']
    print(f"Input file {input_filename} does not pass.")
    async with aiofiles.open(input_filename) as fp_in:
        info['input'] = await fp_in.read()
        filename = f"{input_filename}-{info['ts']}.testresult.md"
        async with aiofiles.open(f"{filename}", 'w') as fp_out:
            await fp_out.write(MD_TEMPLATE.format(**info))
        print(f"Detailed info can be found in {filename}")

parser = ArgParser()
parser.add_argument("--dir", default=os.getcwd())
subparsers = parser.add_subparsers()

init_parser = subparsers.add_parser('init')
init_parser.add_argument("problem")
init_parser.add_argument("--no-download", action='store_true', help="Specifies that sample data should not be downloaded from the Kattis server")
init_parser.set_defaults(func=init_dir)

test_parser = subparsers.add_parser('test')
test_parser.add_argument("program")
test_parser.add_argument("prog_arguments", nargs='*')
test_parser.set_defaults(func=test_dir)

def main():
    args = parser.parse_args()
    args.func(args)
 

if __name__ == "__main__":
    main()