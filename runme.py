import glob, os
from convert.v3 import *


json_dir = 'convert/data/json/'
if not os.path.exists(json_dir):
    print('creating the json dir')
    os.makedirs(json_dir)

filelist = glob.glob('convert/data/json/*.json')

if filelist:
    for f in filelist:
        os.remove(f)
    print('creating normal json')
    write_json(variables, inp_dir_prefix='convert', outdir='convert/data/json/')
    write_json(variables, tree=False,
               inp_dir_prefix='convert', outdir='convert/data/json/')

