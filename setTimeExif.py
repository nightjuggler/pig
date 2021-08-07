import os
import time
from pimly import Image

def formatTime(timestamp):
	ymdhms = time.localtime(timestamp)[0:6]
	return "{}-{:02}-{:02} {:02}:{:02}:{:02}".format(*ymdhms)

def setFromExifTime(fileName, verbose=0):
	try:
		image = Image(fileName)
	except Exception as e:
		print(fileName, e.__class__.__name__, str(e))
		return False
	exifTime = image.getTimeCreated()
	if exifTime == 0:
		if verbose > 1:
			print(fileName, "doesn't have Exif DateTimeOriginal")
		return False

	modTime = os.stat(fileName).st_mtime

	if modTime in (exifTime, exifTime + 1):
		if verbose > 2:
			print(fileName, "already has its mod time equal to its Exif time")
		return False

	if verbose > 0:
		print(fileName, "mod time set to {} (was {})".format(formatTime(exifTime), formatTime(modTime)))

	os.utime(fileName, (exifTime, exifTime))
	return True

def setFromBirthTime(fileName, verbose=0):
	try:
		fileInfo = os.stat(fileName)
	except Exception as e:
		print(fileName, e.__class__.__name__, str(e))
		return False

	oldTime = fileInfo.st_mtime
	newTime = fileInfo.st_birthtime

	if oldTime in (newTime, newTime + 1):
		if verbose > 2:
			print(fileName, "already has its mod time equal to its birth time")
		return False

	if verbose > 0:
		print(fileName, "mod time set to {} (was {})".format(formatTime(newTime), formatTime(oldTime)))

	os.utime(fileName, (newTime, newTime))
	return True

def parseArgs():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('imagePath', nargs='+')
	parser.add_argument('--verbose', '-v', action='count', default=0)
	parser.add_argument('--birthtime', '-b', action='store_true')
	args = parser.parse_args()
	args.verbose += 1

	setTime = setFromBirthTime if args.birthtime else setFromExifTime

	for fileName in args.imagePath:
		setTime(fileName, args.verbose)

if __name__ == '__main__':
	parseArgs()
