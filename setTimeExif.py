import os
import time
from pimly import Image

def formatTime(timestamp):
	ymdhms = time.localtime(timestamp)[0:6]
	return "{}-{:02}-{:02} {:02}:{:02}:{:02}".format(*ymdhms)

def setTime(fileName, oldTime, newTime, timeDesc, verbose):
	if abs(oldTime - newTime) <= 1:
		if verbose > 2:
			print(fileName, 'already has its mod time equal to its', timeDesc)
		return False

	os.utime(fileName, (newTime, newTime))
	if verbose > 0:
		print(fileName, 'mod time changed from', formatTime(oldTime), 'to', formatTime(newTime))
	return True

def setFromExifTime(fileName, verbose=0):
	try:
		image = Image(fileName)
	except Exception as e:
		print(fileName, e.__class__.__name__, str(e))
		return False
	exifTime = image.getTimeCreated()
	if not exifTime:
		if verbose > 1:
			print(fileName, "doesn't have Exif DateTimeOriginal")
		return False

	return setTime(fileName, os.stat(fileName).st_mtime, exifTime, 'Exif time', verbose)

def setFromBirthTime(fileName, verbose=0):
	try:
		fileInfo = os.stat(fileName)
	except Exception as e:
		print(fileName, e.__class__.__name__, str(e))
		return False

	return setTime(fileName, fileInfo.st_mtime, fileInfo.st_birthtime, 'birth time', verbose)

def main():
	import argparse
	parser = argparse.ArgumentParser(allow_abbrev=False)
	parser.add_argument('imagePath', nargs='+')
	parser.add_argument('--verbose', '-v', action='count', default=0)
	parser.add_argument('--birthtime', '-b', action='store_true')
	args = parser.parse_args()
	args.verbose += 1

	setTime = setFromBirthTime if args.birthtime else setFromExifTime

	for fileName in args.imagePath:
		setTime(fileName, args.verbose)

if __name__ == '__main__':
	main()
