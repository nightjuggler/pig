import os
import os.path
import sys

def main():
	prefix = 'IMG_'
	time_name_pairs = [(os.stat(name).st_mtime, name) for name in os.listdir('.')
		if name.startswith(prefix) and name.endswith(('.HEIC', '.JPG'))]
	time_name_pairs.sort()

	names = []
	for i, (mtime, oldname) in enumerate(time_name_pairs, start=1):
		ext = oldname[oldname.rfind('.'):]
		newname = f'{prefix}{i:04}{ext}'
		tmpname = 'tmp_' + newname
		if os.path.exists(tmpname):
			sys.exit(f'"{tmpname}" already exists!')
		names.append((oldname, tmpname, newname))

	for oldname, tmpname, newname in names:
		print('Renaming', oldname, 'to', tmpname)
		os.rename(oldname, tmpname)

	for oldname, tmpname, newname in names:
		if os.path.exists(newname):
			sys.exit(f'"{newname}" already exists!')
		print('Renaming', tmpname, 'to', newname)
		os.rename(tmpname, newname)

if __name__ == '__main__':
	main()
