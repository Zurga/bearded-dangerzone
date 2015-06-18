import glob, os
from v3 import *


json_dir = 'data/json/'
if not os.path.exists(json_dir):
    print('creating the json dir')
    os.makedirs(json_dir)

filelist = glob.glob('convert/data/json/*.json')

if filelist:
    for f in filelist:
        os.remove(f)

# Dictionary of correct variables for all years.
print('creating normal json')
write_json(variables, inp_dir_prefix='', outdir='data/json/')
print('creating tree json')
write_json(variables, tree=True,
            inp_dir_prefix='', outdir='data/json/')
