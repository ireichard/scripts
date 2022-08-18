import pandas as pd
import os
import sys
import shutil

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
    if n % 500 == 0:
        j += 1
        os.mkdir(cwd + '/' + fd + f'_sort_{j}')
    shutil.copy(cwd + '/' + fd + '/' + i, cwd + '/' + fd + f'_sort_{j}/' + i)
    n += 1
