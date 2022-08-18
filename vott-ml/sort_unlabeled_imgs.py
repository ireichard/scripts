import pandas as pd
import os
import sys

fd = sys.argv[1].strip()
cwd = os.getcwd()
imgs = 'labeled_imgs.txt'

fd = cwd + '/' + fd
fd_imgs = cwd + '/' + imgs
print(fd)

valid_img = []
with open(fd_imgs, 'r') as f:
	for line in f:
		valid_img.append(line.rstrip())
all_img = os.listdir(fd)

print(f'VALID: {len(valid_img)}')
print(f'ALL: {len(all_img)}')

removed = 0
for i in range(len(all_img)):
	if all_img[i] not in valid_img:
		try:
			os.remove(f'{fd}/{all_img[i]}')
		except OSError:
			pass
		removed += 1

print(f'REMOVED: {removed}')
"""
df = pd.read_csv(csv_loc)
df = df.drop(['xmin', 'ymin', 'ymax', 'xmax', 'label'], axis=1)
f = open('labeled_imgs.txt', 'w+')
for i in range(df.size):
	f.write(f'{df.iat[i, 0]}\n')
f.close()
print(df.head())
"""
