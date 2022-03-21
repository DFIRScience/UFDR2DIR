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
import shutil

from pathlib import Path
from pathlib import PurePath
from zipfile import ZipFile

__software__ = 'UFDR2DIR'
__author__ = 'Joshua James'
__copyright__ = 'Copyright 2022, UFDR2DIR'
__credits__ = []
__license__ = 'MIT'
__version__ = '0.1.10'
__maintainer__ = 'Joshua James'
__email__ = 'joshua+github@dfirscience.org'
__status__ = 'active'

PROGRESSLIB = True

# Some users had trouble importing alive_progress on Windows
try:from alive_progress import alive_it
except ImportError:
    print('[E] Could not find alive_progress library. Will not show progress.')
    PROGRESSLIB = False

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
    logging.info("Extracting report.xml...")
    with ZipFile(ufdr, 'r') as zip:
        with io.TextIOWrapper(zip.open("report.xml"), encoding="utf-8") as f:
            logging.info("Creating original directory structure...")
            if PROGRESSLIB: extractProgress(zip, OUTD, f)
            else: extractNoProgress(zip, OUTD, f)

# Function to show progress if lib exists
# Optimize with progress functions instead of alive_it
def extractProgress(zip, OUTD, f):
    ORIGF = ""
    LOCALF = ""
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

def extractNoProgress(zip, OUTD, f):
    ORIGF = ""
    LOCALF = ""
    for l in f: # Run though each line... is lxml faster?
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
    Path('files').rename(f'{OUTD}/UFDR-Files') # Move remaining archive structure to output

def extractToDir(zip, LOCALP, ORIGP, OUTD):
    if ORIGP[:1] == "/": # Sometimes the first slash is missing in report.xml
        ORIGP = ORIGP[1:len(ORIGP)]
    #OUTPATH = PurePath(Path(OUTD), Path(ORIGP).parent)
    OUTPATH = PurePath(Path(OUTD), Path(ORIGP))
    logging.debug(f'Extracting {LOCALP} to {OUTPATH}')
    try:
        zip.extract(LOCALP)
    except KeyError as e:
        logging.debug(e)
    except NotADirectoryError as e:
        logging.debug(f'Error writing to directory: {e}')
    except PermissionError as e:
        print(f'Cannot write to the out directory. Check permissions: {e}')
        exit(0)
    except:
        logging.debug(f'General error extracting file to path.')
    else:
        try:
            Path(LOCALP).rename(OUTPATH) # Move from CWD to original path + FN
        except IsADirectoryError: # If an archive is found but the dir already exists
            logging.debug('An original archive was found. Renaming the directory...')
            Path(OUTPATH).rename(f'{OUTPATH}.extract')
            Path(LOCALP).rename(OUTPATH)
        except NotADirectoryError: # If an archive file already exists and extraction is found
            logging.debug('Archive extraction found but archive already exists. Skipping...')
        except FileExistsError:
            logging.debug('File already exists. Skipping...')
        except OSError as e:
            logging.debug(f'Error writing file: {e}') # Probably file name too long

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
    except FileExistsError:
        logging.debug(f"The file {OUTPATH} already exists. Skipping...")
    #except:
    #    logging.debug(f'General error creating file path.')

def windowsWarning():
    print("Note: Windows paths are not POSIX compliant.")
    print("      Illegal original-path chracters will be replaced with \"-\".")

def exitHandler(sig, frame):
    logging.info('Process terminated by user.')
    cleanWorking()
    if platform.system == "Windows": os._exit()
    else: os.kill(os.getpid(), signal.SIGINT)

def cleanWorking():
    try: shutil.rmtree('files')
    except: logging.debug('Files working directory not found')

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
    cleanWorking()
    getZipReportXML(UFDR, OUTD)

if __name__ == '__main__':
    main()