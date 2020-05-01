#!/usr/bin/python3

import argparse, os, random
parser = argparse.ArgumentParser()
method = parser.add_mutually_exclusive_group(required=True)
method.add_argument("-c", "--compiled", action="store_true",
                    help="Put already-compiled code from Octo in a file")
method.add_argument("-o", "--octocode",
                    help="Compile Octocode .8o to a file")
parser.add_argument("output",
                    help="File to put output in")
args = parser.parse_args()

args.output = args.output + ("" if "." in args.output.split("/")[-1] else ".ch8")

if args.compiled:
    code = input("Please enter the compiled code: ")
    print("Converting input...")
    code = code.split()
    code = [i[2:] for i in code]
    code = [int(i, 16) for i in code]
    code = bytes(code)
    print("Writing to file...")
    f = open(args.output, "wb+")
    f.write(code)
    f.close()
elif args.octocode:
    print("Reading .8o file...")
    with open(args.octocode) as f:
        code = f.read()
        while code[0] > "\ueeee": #Octo sometimes adds strange symbols at the start
            code = code[1:]
    tmpFile = f".tmp_octocode_{str(random.randint(0,999999)).rjust(6, '0')}"
    with open(tmpFile, "w+") as f:
        f.write(code)
    print("Running Octo compiler...")
    os.system(
        os.path.dirname(os.path.realpath(__file__)) +
        f"/octo-compiler/octo {tmpFile} {args.output}"
    )
    os.remove(tmpFile)
print("Done!")
