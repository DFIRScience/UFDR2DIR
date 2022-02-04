# -*- coding: utf-8 -*-

"""
Convert a Cellebrite Reader UFDR file to it's original directory structure.
MIT License.
"""

# Imports
import argparse
import logging
import re, io
import platform

from alive_progress import alive_it
from pathlib import Path
from pathlib import PurePath
from zipfile import ZipFile

__software__ = 'UFDR2DIR'
__author__ = 'Joshua James'
__copyright__ = 'Copyright 2022, UFDR2DIR'
__credits__ = []
__license__ = 'MIT'
__version__ = '0.1.1'
__maintainer__ = 'Joshua James'
__email__ = 'joshua+github@dfirscience.org'
__status__ = 'active'

# Set logging level and format
def setLogging(debug):
    fmt = "[%(levelname)s] %(asctime)s %(message)s"
    LOGLEVEL = logging.INFO if debug is False else logging.DEBUG
    logging.basicConfig(level=LOGLEVEL, format=fmt, datefmt='%Y-%M-%dT%H:%M:%S')

# Argparser config and argument setup
def setArgs():
    parser = argparse.ArgumentParser(description=__copyright__)
    parser.add_argument('ufdr', help="Celebrite Reader UFDR file")
    parser.add_argument('-o', '--out', required=False, action='store_true', help='Output directory path')
    parser.add_argument('--debug', required=False, action='store_true', help='Set the log level to DEBUG')
    return(parser.parse_args())

def getZipReportXML(ufdr, OUTD):
    ORIGF = ""
    LOCALF = ""
    logging.info("Extracting report.xml...")
    with ZipFile(ufdr, 'r') as zip:
        with io.TextIOWrapper(zip.open("report.xml"), encoding="utf-8") as f:
            #count = sum(1 for _ in f)
            logging.info("Creating original directory structure...")
            for l in alive_it(f): # Run though each line... this is gonna be slow.
                if l.__contains__('<file fs'):
                    result = re.search('path="(.*?)" ', l) # This gets original path / FN
                    if result:
                        ORIGF = result.group(1)
                        logging.debug(f'Original: {ORIGF}')
                        # Create the original file directory structure
                        makeDirStructure(ORIGF, OUTD)
                elif l.__contains__('name="Local Path"'):
                    result = re.search('CDATA\[(.*?)\]\]', l) # This gets original path / FN
                    if result:
                        if platform.system() == "Windows": LOCALF = result.group(1)
                        else: LOCALF = result.group(1).replace("\\", "/")
                        logging.debug(f'Local: {LOCALF}')
                        extractToDir(zip, LOCALF, ORIGF, OUTD)

def extractToDir(zip, LOCALP, ORIGP, OUTD): 
    OUTPATH = PurePath(Path(OUTD), Path(ORIGP[1:len(ORIGP)]).parent)
    logging.debug(f'extracting {LOCALP} to {OUTPATH}')
    try:
        zip.extract(LOCALP, OUTPATH)
    except KeyError as e:
        logging.debug(e)


# This might not be necessary if we can extract directly.                    
def makeDirStructure(FP, OUTD): # FP is a string
    OUTPATH = PurePath(Path(OUTD), Path(FP[1:len(FP)]).parent)
    logging.debug(f'Outpath set to: {OUTPATH}')
    Path(OUTPATH).mkdir(parents=True, exist_ok=True)

def main():
    args = setArgs()
    UFDR = Path(args.ufdr)
    OUTD = Path.cwd().joinpath("UFDRConvert")
    setLogging(args.debug)
    print(f"{__software__} v{__version__}")
    if Path.is_file(UFDR):
        logging.debug(f'UDFR set to {args.ufdr}')
    if args.out and Path.is_dir(Path(args.out)):
        logging.debug(f'Output directory set to {args.out}')
        OUTD = args.out + "UFDRConvert"
    getZipReportXML(UFDR, OUTD)

if __name__ == '__main__':
    main()