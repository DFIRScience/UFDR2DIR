## UFDR2DIR

A script to convert a Cellebrite UFDR to it's original file and directory structure.

## Why??

Cellebrite Reader files (.ufdr) are processed mobile device images. They are compressed (zip) files that contain a ```report.xml``` file in the root, and files sorted into directories by category.

The ufdr has the original suspect data, but does not keep the original file path structure. This means that tools such as [ALEAPP](https://github.com/abrignoni/ALEAPP) have [poor results](https://dfir.science/2022/02/How-to-extract-files-from-Cellebrite-Reader-UFDR-for-ALEAPPiLEAPP) over the package.

UFDR2DIR converts the categorized data back into the original suspect directory structure. This will allow tools that do not support UFDR to load the data as a directory.

## Install and Run

Make sure you have [Python 3](https://www.python.org/) installed. Download the repository.
From a command prompt run:

```bash
pip3 install -r requirements
python3 ufdr2dir.py filename.ufdr
```

This will create an output folder in the current working directory. You can specify where you want to output to with -o [OUTDIR].

The output directory will mirror what was recorded in ```report.xml```. You can point tools like ALEAPP directly at the resulting folder.

## Note

Cellebrite apparently does some deleted data recovery. These files are currently **not** being extracted if they lack path information.

## Bug reports and suggestions

Pull requests considered! Otherwise create an issue or message me on [Twitter](https://twitter.com/dfirscience) if you find any bugs or have some recommendations.
