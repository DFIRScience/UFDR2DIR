# -*- coding: utf-8 -*-

"""
Convert a Cellebrite Reader UFDR file to it's original directory structure.
MIT License.
"""

# Imports
import argparse
import logging
import re, io, os
import signal
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
__version__ = '0.1.8'
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
    parser.add_argument('-o', '--out', required=False, action='store', dest="out", help='Output directory path')
    parser.add_argument('--debug', required=False, action='store_true', help='Set the log level to DEBUG')
    return(parser.parse_args())

def getZipReportXML(ufdr, OUTD):
    ORIGF = ""
    LOCALF = ""
    logging.info("Extracting report.xml...")
    with ZipFile(ufdr, 'r') as zip:
        with io.TextIOWrapper(zip.open("report.xml"), encoding="utf-8") as f:
            logging.info("Creating original directory structure...")
            for l in alive_it(f): # Run though each line... is lxml faster?
                if l.__contains__('<file fs'):
                    result = re.search('path="(.*?)" ', l) # This gets original path / FN
                    if result:
                        ORIGF = result.group(1)
                        if platform.system() == "Windows": ORIGF = re.sub('[:*?"<>|]', '-', ORIGF)
                        logging.debug(f'Original: {ORIGF}')
                        # Create the original file directory structure
                        makeDirStructure(ORIGF, OUTD)
                elif l.__contains__('name="Local Path"'):
                    result = re.search('CDATA\[(.*?)\]\]', l) # This gets local path / FN
                    if result:
                        LOCALF = result.group(1).replace("\\", "/")
                        logging.debug(f'Local: {LOCALF}')
                        extractToDir(zip, LOCALF, ORIGF, OUTD)

def extractToDir(zip, LOCALP, ORIGP, OUTD):
    if ORIGP[:1] == "/": # Sometimes the first slash is missing in report.xml
        ORIGP = ORIGP[1:len(ORIGP)]
    OUTPATH = PurePath(Path(OUTD), Path(ORIGP).parent)
    logging.debug(f'Extracting {LOCALP} to {OUTPATH}')
    try:
        zip.extract(LOCALP, OUTPATH)
    except KeyError as e:
        logging.debug(e)
    except NotADirectoryError as e:
        logging.debug(f'Error writing to directory: {e}')
    except PermissionError as e:
        print(f'Cannot write to the out directory. Check permissions: {e}')
        exit(0)
    except:
        logging.debug(f'General error extracting file to path.')

# This might not be necessary if we can extract directly.                    
def makeDirStructure(FP, OUTD): # FP is a string
    OUTPATH = PurePath(Path(OUTD), Path(FP[1:len(FP)]).parent)
    logging.debug(f'Outpath set to: {OUTPATH}')
    try:
        Path(OUTPATH).mkdir(parents=True, exist_ok=True)
    except NotADirectoryError as e:
        logging.debug(f'Error creating directory: {e}')
    except PermissionError as e:
        print(f'Cannot write to the out directory. Check permissions: {e}')
        exit(1)
    except:
        logging.debug(f'General error creating file path.')

def windowsWarning():
    print("Note: Windows paths are not POSIX compliant.")
    print("      Illegal original-path chracters will be replaced with \"-\".")

def exitHandler(sig, frame):
    logging.info('Process terminated by user.')
    if platform.system == "Windows": os._exit()
    else: os.kill(os.getpid(), signal.SIGINT)

def main():
    signal.signal(signal.SIGINT, exitHandler)
    args = setArgs()
    UFDR = Path(args.ufdr)
    OUTD = Path.cwd().joinpath("UFDRConvert")
    setLogging(args.debug)
    print(f"{__software__} v{__version__} - Use ctrl+c to exit")
    if platform.system() == "Windows":
        windowsWarning()
    if Path.is_file(UFDR):
        logging.debug(f'UDFR set to {args.ufdr}')
    if args.out and Path.is_dir(Path(args.out)):
        logging.debug(f'Output directory set to {args.out}')
        OUTD = args.out + "UFDRConvert"
    getZipReportXML(UFDR, OUTD)

if __name__ == '__main__':
    main()