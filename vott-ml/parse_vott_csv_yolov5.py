import pandas as pd
import os
import sys

DIV_X = 640
DIV_Y = 480

print('Parse vott csv script. arg1 = vott csv | arg2 = out folder | arg3 = labels')

fd = sys.argv[1].strip()
out = sys.argv[2].strip()
cwd = os.getcwd()

#csv_loc = cwd + '/' + fd + '/vott-csv-export/Scion-export.csv'
#csv_loc = cwd + '/' + fd + '/Scion-export.csv'
csv_loc = cwd + '/' + fd + '/vott-csv-export/Scion2-export.csv'
out_loc = cwd + '/' + out
print(csv_loc)

df = pd.read_csv(csv_loc)
f = open(sys.argv[3].strip(), 'r+')
labels = f.readlines()
labels = [label.rstrip('\n') for label in labels]
labels = [i.split(',') for i in labels]
labels_str = []
[labels_str.append(i[0]) for i in labels]
print(labels)
print(labels_str)

df['xmin-float'] = df['xmin'] / 1
df['ymin-float'] = df['ymin'] / 1
df['xmax-float'] = df['xmax'] / 1
df['ymax-float'] = df['ymax'] / 1
df['cx_box'] = (df['xmin-float'] + df['xmax-float']) / 2 / DIV_X
df['cy_box'] = (df['ymin-float'] + df['ymax-float']) / 2 / DIV_Y
df['w_box'] = (df['xmax-float'] - df['xmin-float']) / DIV_X
df['h_box'] = (df['ymax-float'] - df['ymin-float']) / DIV_Y
df = df.drop(['xmin', 'ymin', 'xmax', 'ymax'], axis=1)
print(df.head())
df_size = int(df.size/10)
known_files = []

for i in range(df_size):
        # Already seen image, append new labels to file
        # if df.at[i, 'image'] in known_files:
        #    f = open(f"{out_loc}/{df.at[i, 'image'][:-3]}txt", 'a+')
            f.write(f"df.at[i, 'label']")
	# if df.at[i, 'label'] == 'ppole':
	#	df.at[i, 'label'] = 1
	#elif df.at[i, 'label'] == 'pgate':
	#	df.at[i, 'label'] = 0
	f = open(f"{out_loc}/{df.at[i, 'image'][:-3]}txt", 'a+')
	f.write(f"{df.at[i, 'label']} {df.at[i, 'cx_box']} {df.at[i, 'cy_box']} {df.at[i, 'w_box']} {df.at[i, 'h_box']}\n")
	f.close()
print(df.head())
