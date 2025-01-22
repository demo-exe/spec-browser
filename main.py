#!/usr/bin/env python3

import dmenu
import os
import pickle
import pathlib
import ftplib
import tempfile
import zipfile
import subprocess
import shutil
import notify2
from dateutil import parser


SCORE_DECAY_FACTOR = 0.9 # for recomendations order
CACHE_DIR = os.path.join(os.getenv('XDG_CACHE_HOME', os.getenv('HOME', '/')), 'ts-spec-browser')
SPECS_DIR = os.path.join(CACHE_DIR, 'specs')
TEMP_DIR = tempfile.mkdtemp(suffix=None, prefix='ts-spec-browser-', dir=None)

PICKLE = os.path.join(CACHE_DIR, 'known_specs.pickle')

# validate path exists
pathlib.Path(SPECS_DIR).mkdir(parents=True, exist_ok=True)

notify2.init('ts-spec-browser')

# TODO: other readers ?
zathura = shutil.which("zathura")
if zathura is None:
    msg = 'zathura not found in PATH!'
    print(msg)
    notify2.Notification("Error", msg).show()
    exit(1)

# load cache
known_specs = { 
# '29.501': {'score': 1, 'file': '/home//.cache/ts-spec-browser/specs/29.501/29501-j10.pdf' },
}
try:
    with open(PICKLE, 'rb') as file:
        known_specs = pickle.load(file)
except:
    pass

# sort specs by access frequency
sorted_knowns = [k for k, _ in sorted(known_specs.items(), key=lambda item: item[1]['score'], reverse = True)]

# run dmenu for user selection
selection = dmenu.show(sorted_knowns)
if selection is None:
    msg = 'No selection provided'
    print(msg)
    notify2.Notification("Error", msg).show()
    exit(1)

pdf_file = None

# look in cache or download
cached = known_specs.get(selection) 
if cached is not None:
    pdf_file = cached['file']
    cached['score'] += 1
else:
    tokens = selection.split('.')
    if len(tokens) != 2:
        msg = 'invalid selection: {}'.format(selection)
        print (msg)
        notify2.Notification("Error", msg).show()
        exit(1)

    series, spec = tokens

    lines = []
    def append_line(line): 
        tokens = line.split(maxsplit = 9)
        time_str = tokens[0] + " " + tokens[1]
        time = parser.parse(time_str)
        lines.append((time, tokens[3]))


    notify2.Notification("Downloading TS{}".format(selection)).show()
    # retrieve archive
    try:
        with ftplib.FTP('ftp.3gpp.org') as ftp:
            ftp.login()
            ftp.cwd("/Specs/archive/{series}_series/{series}.{spec}".format(series=series, spec=spec))
            ftp.dir('', append_line)
            sorted_names =  sorted(lines, key=lambda line: line[0], reverse = True)
            fname = sorted_names[0][1]
            with open(os.path.join(TEMP_DIR, fname), 'wb+') as file:
                ftp.retrbinary("RETR {}".format(fname), file.write)
    except Exception as e:
        msg = 'error during retrieving: {}'.format(e)
        print(msg)
        notify2.Notification("Error", msg).show()
        exit(1)

    notify2.Notification("Unzipping TS{}".format(selection)).show()
    # unzip archive
    try:
        with zipfile.ZipFile(os.path.join(TEMP_DIR, fname), 'r') as zip_ref:
            zip_ref.extractall(TEMP_DIR)
    except Exception as e:
        msg = 'error during unzipping: {}'.format(e)
        print(msg)
        notify2.Notification("Error", msg).show()
        exit(1)

    fname_noext = os.path.splitext(fname)[0]
    temp_docx = os.path.join(TEMP_DIR, fname_noext + '.docx')
    target_spec_dir = os.path.join(SPECS_DIR, selection)

    notify2.Notification("Converting TS{} to pdf...".format(selection), "This may take a long time").show()
    # convert docx to pdf for viewing
    subprocess.run(["libreoffice", "--headless", "--convert-to", "pdf", temp_docx, "--outdir", target_spec_dir])
    pdf_file = os.path.join(target_spec_dir, fname_noext + '.pdf')

    # create cached entry
    known_specs[selection] = {'score': 1, 'file': pdf_file}

if pdf_file is None:
    print('BUG: spec not found!')
    exit(1)

# decay scores
for k, v in known_specs.items():
    v['score'] *= SCORE_DECAY_FACTOR

# save known
with open(PICKLE, 'wb+') as file:
    pickle.dump(known_specs, file)

# run zathura and exit
subprocess.Popen([zathura, pdf_file])

