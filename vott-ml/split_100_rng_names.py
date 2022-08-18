import pandas as pd
import os
import sys
import shutil
import random as rng

fd = sys.argv[1].strip()
cwd = os.getcwd()

#csv_loc = cwd + '/' + fd + '/vott-csv-export/Scion2-export.csv'
#print(csv_loc)

#df = pd.read_csv(csv_loc)
# df = df.drop(['xmin', 'ymin', 'ymax', 'xmax', 'label'], axis=1)

#f = open('labeled_imgs.txt', 'w+')

j = -1
n = 0
os.chdir(fd)
print(fd)
print(f'{cwd}/{fd}/')
for i in os.listdir():
    if n % 100 == 0:
        j += 1
        new_fd = hex(rng.randint(0, sys.maxsize))[2:]
        os.mkdir(cwd + '/' + new_fd)
    shutil.copy(cwd + '/' + fd + '/' + i, cwd + '/' + new_fd + '/' + new_fd + '_' + i)
    n += 1
