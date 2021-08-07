import os
import os.path
import sys

def main():
	time_name_pairs = [(os.stat(name).st_mtime, name) for name in os.listdir('.')
		if name[:4] == 'IMG_' and name[-4:] == '.JPG']
	time_name_pairs.sort()

	names = []
	for i, (mtime, oldname) in enumerate(time_name_pairs, start=1):
		newname = 'IMG_{:04d}.JPG'.format(i)
		tmpname = 'tmp_' + newname
		if os.path.exists(tmpname):
			sys.exit('"{}" already exists!'.format(tmpname))
		names.append((oldname, tmpname, newname))

	for oldname, tmpname, newname in names:
		print('Renaming', oldname, 'to', tmpname)
		os.rename(oldname, tmpname)

	for oldname, tmpname, newname in names:
		if os.path.exists(newname):
			sys.exit('"{}" already exists!'.format(newname))
		print('Renaming', tmpname, 'to', newname)
		os.rename(tmpname, newname)

if __name__ == '__main__':
	main()
