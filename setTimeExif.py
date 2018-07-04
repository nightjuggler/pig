#!/usr/bin/python
import os
import time
from pimly import Image

def formatTime(timestamp):
	ymdhms = time.localtime(timestamp)[0:6]
	return "{}-{:02}-{:02} {:02}:{:02}:{:02}".format(*ymdhms)

def setTimeExif(fileName, verbose=0):
	try:
		image = Image(fileName)
	except Exception as e:
		print fileName, e.__class__.__name__, str(e)
		return False
	exifTime = image.getTimeCreated()
	if exifTime == 0:
		if verbose > 1:
			print fileName, "doesn't have Exif DateTimeOriginal"
		return False

	fileInfo = os.stat(fileName)
	if fileInfo.st_mtime in (exifTime, exifTime + 1):
		if verbose > 2:
			print fileName, "already has its mod time equal to the Exif time"
		return False

	if verbose > 0:
		oldTime = formatTime(fileInfo.st_mtime)
		newTime = formatTime(exifTime)
		print fileName, "mod time set to {} (was {})".format(newTime, oldTime)

	os.utime(fileName, (exifTime, exifTime))
	return True

def parseArgs():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('imagePath', nargs='+')
	parser.add_argument('--verbose', '-v', action='count', default=0)
	args = parser.parse_args()
	args.verbose += 1

	for fileName in args.imagePath:
		setTimeExif(fileName, args.verbose)

if __name__ == '__main__':
	parseArgs()
