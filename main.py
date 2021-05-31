import os
import re
import sys
import glob
import pdfx
import argparse as ap
import givemebib.functions as gmb

argv = ap.ArgumentParser()
argv.add_argument('path', nargs='?', default=os.getcwd())
argv.add_argument('--debug', action="store_true")
argv = argv.parse_args()


def blockPrint():
    """ HackyFuckyWacky way to block unwanted print output """
    sys.stdout = open(os.devnull, 'w')


def enablePrint():
    """ Revert print output to STDOUT """
    sys.stdout = sys.__stdout__


def printd(*args, **kwargs):
    """ Print debug information to STDERR """
    global argv
    if argv.debug:
        print(*args, file=sys.stderr, **kwargs)


def sieveDOI(l: list) -> list:
    """ Within a list of strings find DOI related ones with RegExp """
    res = []
    for item in l:
        if re.search('doi', str(item), flags=re.IGNORECASE):
            res.append(item)
    return res


def compareDOI(arg1: str, arg2: str) -> bool:
    regex = r'\d{2}\.\d{4}\/'
    if re.findall(regex, arg1) == re.findall(regex, arg2):
        return True
    return False


def extractDict(d: dict) -> list:
    """ Extract data from nested dictionary as a list of strings """
    res = []
    if hasattr(d, 'items'):
        for value in d.values():
            if isinstance(value, dict):
                res += extractDict(value)
            elif isinstance(value, list):
                res += value
            else:
                res.append(value)
    return res


def listifyDict(d: dict) -> dict:
    """ Turn a given dictionary values into string lists of nested values """
    res = {}
    for key, value in d.items():
        res[key] = sieveDOI(extractDict(value))
        if not res[key]:
            printd(f"Empty result in {key}")
    return res


def main(argv: ap.Namespace):
    pfD = {}    # PresentFilesDOIs
    pfR = {}    # PresentFilesReferences
    gfl = glob.glob(os.path.join(argv.path, r'*.pdf'))  # GlobbedFileList

    print(f"Total PDF files found: {len(gfl)}")
    printd(os.path.join(argv.path, r'*.pdf'))  # Correct globing path

    if len(gfl) == 0:
        exit(print(f"No PDFs found!"))

    blockPrint()
    for item in gfl:
        try:
            pfD[os.path.basename(item)] = gmb.pdf2doi(item)
        except Exception as e:
            enablePrint()
            printd(f'Error occurred at {item} {e}')
            blockPrint()
    enablePrint()

    printd(pfD)  # Correct data structure for dict, (basename:doi)

    for item in gfl:
        try:
            pdf = pdfx.PDFx(item)
            pfR[os.path.basename(item)] = pdf.get_references_as_dict()
        except Exception as e:
            printd(f'Error occurred at {item} {e}')
    pfR = listifyDict(pfR)

    found = []
    for source, refs in pfR.items():
        for target, doi in pfD.items():
            for item in refs:
                if compareDOI(item, doi) and not source == target:
                    if f"{source} => {target}" not in found:
                        found.append(f"{source} => {target}")

    print(f"Found referencing pairs: {len(found)}")
    for pair in found:
        print(pair)


if __name__ == '__main__':
    sys.exit(main(argv) or 0)
