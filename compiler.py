import argparse
parser = argparse.ArgumentParser()
method = parser.add_mutually_exclusive_group(required=True)
method.add_argument("-c", "--compiled", action="store_true",
                    help="Put already-compiled code from Octo in a file")
# method.add_argument("-o", "--octocode",
                    # help="Compile Octocode to a file")
parser.add_argument("output",
                    help="File to put output in")
args = parser.parse_args()

if args.compiled:
    code = input("Please enter the compiled code: ")
    print("Converting input...")
    code = code.split()
    code = [i[2:] for i in code]
    code = [int(i, 16) for i in code]
    code = bytes(code)
    print("Writing to file...")
    f = open(args.output + ("" if "." in args.output else ".ch8"), "wb+")
    f.write(code)
    f.close()
    print("Done!")