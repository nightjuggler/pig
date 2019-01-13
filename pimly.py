#!/usr/bin/python
#
# pimly.py (Pius' Image Library)
#
from __future__ import print_function

import operator
import os
import sys
import time

__all__ = ('Image',)

class BigEndian(object):
	name = 'Big Endian'
	@staticmethod
	def int4(b, i=0):
		return ord(b[i+3]) + (ord(b[i+2])<<8) + (ord(b[i+1])<<16) + (ord(b[i])<<24)
	@staticmethod
	def int2(b, i=0):
		return ord(b[i+1]) + (ord(b[i])<<8)
	@staticmethod
	def str4(n):
		return ''.join((chr((n>>24)&255), chr((n>>16)&255), chr((n>>8)&255), chr(n&255)))
	@staticmethod
	def str2(n):
		return ''.join((chr((n>>8)&255), chr(n&255)))

class LittleEndian(object):
	name = 'Little Endian'
	@staticmethod
	def int4(b, i=0):
		return ord(b[i]) + (ord(b[i+1])<<8) + (ord(b[i+2])<<16) + (ord(b[i+3])<<24)
	@staticmethod
	def int2(b, i=0):
		return ord(b[i]) + (ord(b[i+1])<<8)
	@staticmethod
	def str4(n):
		return ''.join((chr(n&255), chr((n>>8)&255), chr((n>>16)&255), chr((n>>24)&255)))
	@staticmethod
	def str2(n):
		return ''.join((chr(n&255), chr((n>>8)&255)))

E = LittleEndian

# Convert 32-bit unsigned integer to 32-bit signed integer
def sInt4(n):
	return n - (1 << 32) if (n >> 31) == 1 else n

def escapeString(s):
	return ''.join([c if 32 <= ord(c) <= 126 else '\\x{:02X}'.format(ord(c)) for c in s])

def stringBytes(s):
	return ' '.join([str(ord(c)) for c in s])

# PNG Spec: https://www.w3.org/TR/PNG/

def pngReadChunk(b, f):
	assert len(b) == 8

	chunkLength = BigEndian.int4(b)
	chunkType = b[4:8]

	# Read chunk data + CRC (4 bytes) + next chunk's length (4 bytes) and type (4 bytes)
	b = f.read(chunkLength + 12)

	chunkData = b[:chunkLength]
	crc = b[chunkLength:chunkLength + 4]
	b = b[chunkLength + 4:]

	return chunkType, chunkData, b

def pngReadChunks(b, f):
	while b != '':
		chunkType, chunkData, b = pngReadChunk(b, f)

	assert chunkType == 'IEND'
	assert chunkData == ''

def pngReadHeader(image, b, f):
	chunkType, chunkData, b = pngReadChunk(b, f)
	assert chunkType == 'IHDR'
	width = BigEndian.int4(chunkData)
	height = BigEndian.int4(chunkData, 4)
	image.size = (width, height)
#	pngReadChunks(b, f)

# Exif Spec: http://www.cipa.jp/std/documents/e/DC-008-Translation-2016-E.pdf
# DCF Spec: http://www.cipa.jp/std/documents/e/DC-009-2010_E.pdf
# IFD = Image File Directory

def exifReadByte(b, offset, count):
	return [ord(b[i]) for i in xrange(offset, offset + count)]

def exifReadAscii(b, offset, count):
	value = b[offset : offset + count]
	if value[-1] != '\x00':
		print('ASCII value not terminated with NULL:', escapeString(value), file=sys.stderr)
	return value.rstrip('\x00\t\n\r ')

def exifReadShort(b, offset, count):
	return [E.int2(b, i) for i in xrange(offset, offset + count*2, 2)]

def exifReadLong(b, offset, count):
	return [E.int4(b, i) for i in xrange(offset, offset + count*4, 4)]

def exifReadRational(b, offset, count):
	return [(E.int4(b, i), E.int4(b, i+4)) for i in xrange(offset, offset + count*8, 8)]

def exifReadUndefined(b, offset, count):
	return b[offset : offset + count]

def exifReadSignedLong(b, offset, count):
	return [sInt4(E.int4(b, i)) for i in xrange(offset, offset + count*4, 4)]

def exifReadSignedRational(b, offset, count):
	return [(sInt4(E.int4(b, i)), sInt4(E.int4(b, i+4))) for i in xrange(offset, offset + count*8, 8)]

def toStrInteger(value):
	return ' '.join([str(v) for v in value])

def toStrRational(value):
	return ' '.join(['{}/{}'.format(n, d) for n, d in value])

def toStrUndefined(value):
	if len(value) <= 10:
		return escapeString(value)

	return '{} ... [{}]'.format(escapeString(value[:10]), len(value))

class ExifType(object):
	lookup = {}

	def __init__(self, key, read, toStr, size):
		self.read = read
		self.size = size
		self.toStr = toStr
		self.lookup[key] = self

ExifTypeByte           = ExifType( 1, exifReadByte,           toStrInteger,   1)
ExifTypeAscii          = ExifType( 2, exifReadAscii,          escapeString,   1)
ExifTypeShort          = ExifType( 3, exifReadShort,          toStrInteger,   2)
ExifTypeLong           = ExifType( 4, exifReadLong,           toStrInteger,   4)
ExifTypeRational       = ExifType( 5, exifReadRational,       toStrRational,  2*ExifTypeLong.size)
ExifTypeUndefined      = ExifType( 7, exifReadUndefined,      toStrUndefined, 1)
ExifTypeSignedLong     = ExifType( 9, exifReadSignedLong,     toStrInteger,   4)
ExifTypeSignedRational = ExifType(10, exifReadSignedRational, toStrRational,  2*ExifTypeSignedLong.size)

class ExifTagInfo(object):
	def __init__(self, name, subIFD=None, toStr=None):
		self.name = name
		self.subIFD = subIFD
		self.toStr = toStr

class ExifTagData(object):
	def __init__(self, info):
		self.name = info.name
		self.toStr = info.toStr
		self.valueType = None
		self.value = None

def parseBPList(bplist):
	return '{} ... [{}]'.format(bplist[:8], len(bplist))

appleIFD = {
	2: ExifTagInfo(2, toStr=parseBPList),
	3: ExifTagInfo(3, toStr=parseBPList),
}

def toStrMakerNote(value):
	if isinstance(value, list):
		return toStrInteger(value)

	if value.startswith('Apple iOS\x00'):
		assert value[12:14] == 'MM'
		assert E is BigEndian
		assert E.int2(value, 10) == 1

		print('Apple iOS', end='')
		return exifReadIFD(value, 14, appleIFD)

	return toStrUndefined(value)

def toStrDegrees(value):
	(n, d), = value
	return '{}/{} ({:.2f} degrees)'.format(n, d, float(n)/d)

def toStrDegMinSec(value):
	(d1, d2), (m1, m2), (s1, s2) = value
	degrees = float(d1)/d2 + float(m1)/m2/60 + float(s1)/s2/3600
	return '{}/{} {}/{} {}/{} ({:.6f} degrees)'.format(d1, d2, m1, m2, s1, s2, degrees)

def toStrAltitude(value):
	(n, d), = value
	return '{}/{} ({:.1f} meters)'.format(n, d, float(n)/d)

exifIFD0 = ExifTagInfo('IFD0', subIFD={
	270: ExifTagInfo('ImageDescription'),
	271: ExifTagInfo('Make'),
	272: ExifTagInfo('Model'),
	274: ExifTagInfo('Orientation'),
	282: ExifTagInfo('XResolution'),
	283: ExifTagInfo('YResolution'),
	296: ExifTagInfo('ResolutionUnit'),
	305: ExifTagInfo('Software'),
	306: ExifTagInfo('DateTime'),
	315: ExifTagInfo('Artist'),
	316: ExifTagInfo('HostComputer'),
	531: ExifTagInfo('YCbCrPositioning'),

	33432: ExifTagInfo('Copyright'),
	34665: ExifTagInfo('Exif IFD', subIFD={
		33434: ExifTagInfo('ExposureTime'),
		33437: ExifTagInfo('FNumber'),
		34850: ExifTagInfo('ExposureProgram'),
		34855: ExifTagInfo('PhotographicSensitivity'),
		34864: ExifTagInfo('SensitivityType'),
		34866: ExifTagInfo('RecommendedExposureIndex'),
		36864: ExifTagInfo('ExifVersion', toStr=escapeString),
		36867: ExifTagInfo('DateTimeOriginal'),
		36868: ExifTagInfo('DateTimeDigitized'),
		36880: ExifTagInfo('OffsetTime'),
		36881: ExifTagInfo('OffsetTimeOriginal'),
		36882: ExifTagInfo('OffsetTimeDigitized'),
		37121: ExifTagInfo('ComponentsConfiguration', toStr=stringBytes),
		37122: ExifTagInfo('CompressedBitsPerPixel'),
		37377: ExifTagInfo('ShutterSpeedValue'),
		37378: ExifTagInfo('ApertureValue'),
		37379: ExifTagInfo('BrightnessValue'),
		37380: ExifTagInfo('ExposureBiasValue'),
		37381: ExifTagInfo('MaxApertureValue'),
		37382: ExifTagInfo('SubjectDistance'),
		37383: ExifTagInfo('MeteringMode'),
		37384: ExifTagInfo('LightSource'),
		37385: ExifTagInfo('Flash'),
		37386: ExifTagInfo('FocalLength'),
		37396: ExifTagInfo('SubjectArea'),
		37500: ExifTagInfo('MakerNote', toStr=toStrMakerNote),
		37510: ExifTagInfo('UserComment'),
		37520: ExifTagInfo('SubSecTime'),
		37521: ExifTagInfo('SubSecTimeOriginal'),
		37522: ExifTagInfo('SubSecTimeDigitized'),
		40960: ExifTagInfo('FlashpixVersion', toStr=escapeString),
		40961: ExifTagInfo('ColorSpace'),
		40962: ExifTagInfo('PixelXDimension'),
		40963: ExifTagInfo('PixelYDimension'),
		40964: ExifTagInfo('RelatedSoundFile'),
		40965: ExifTagInfo('Interoperability IFD', subIFD={
			1: ExifTagInfo('InteroperabilityIndex'),
			2: ExifTagInfo('InteroperabilityVersion'),
			4097: ExifTagInfo('RelatedImageWidth'),
			4098: ExifTagInfo('RelatedImageLength'),
		}),
		41486: ExifTagInfo('FocalPlaneXResolution'),
		41487: ExifTagInfo('FocalPlaneYResolution'),
		41488: ExifTagInfo('FocalPlaneResolutionUnit'),
		41492: ExifTagInfo('SubjectLocation'),
		41493: ExifTagInfo('ExposureIndex'),
		41495: ExifTagInfo('SensingMethod'),
		41728: ExifTagInfo('FileSource', toStr=stringBytes),
		41729: ExifTagInfo('SceneType', toStr=stringBytes),
		41730: ExifTagInfo('CFAPattern'),
		41985: ExifTagInfo('CustomRendered'),
		41986: ExifTagInfo('ExposureMode'),
		41987: ExifTagInfo('WhiteBalance'),
		41988: ExifTagInfo('DigitalZoomRatio'),
		41989: ExifTagInfo('FocalLengthIn35mmFilm'),
		41990: ExifTagInfo('SceneCaptureType'),
		41991: ExifTagInfo('GainControl'),
		41992: ExifTagInfo('Contrast'),
		41993: ExifTagInfo('Saturation'),
		41994: ExifTagInfo('Sharpness'),
		41996: ExifTagInfo('SubjectDistanceRange'),
		42032: ExifTagInfo('CameraOwnerName'),
		42033: ExifTagInfo('BodySerialNumber'),
		42034: ExifTagInfo('LensSpecification'),
		42035: ExifTagInfo('LensMake'),
		42036: ExifTagInfo('LensModel'),
		42037: ExifTagInfo('LensSerialNumber'),
	}),
	34853: ExifTagInfo('GPS IFD', subIFD={
		0: ExifTagInfo('GPSVersionID', toStr=lambda v: '.'.join([str(i) for i in v])),
		1: ExifTagInfo('GPSLatitudeRef'),
		2: ExifTagInfo('GPSLatitude', toStr=toStrDegMinSec),
		3: ExifTagInfo('GPSLongitudeRef'),
		4: ExifTagInfo('GPSLongitude', toStr=toStrDegMinSec),
		5: ExifTagInfo('GPSAltitudeRef'),
		6: ExifTagInfo('GPSAltitude', toStr=toStrAltitude),
		7: ExifTagInfo('GPSTimeStamp'),
		8: ExifTagInfo('GPSSatellites'),
		9: ExifTagInfo('GPSStatus'),
		10: ExifTagInfo('GPSMeasureMode'),
		11: ExifTagInfo('GPSDOP'),
		12: ExifTagInfo('GPSSpeedRef'),
		13: ExifTagInfo('GPSSpeed'),
		14: ExifTagInfo('GPSTrackRef'),
		15: ExifTagInfo('GPSTrack'),
		16: ExifTagInfo('GPSImgDirectionRef'),
		17: ExifTagInfo('GPSImgDirection', toStr=toStrDegrees),
		18: ExifTagInfo('GPSMapDatum'),
		19: ExifTagInfo('GPSDestLatitudeRef'),
		20: ExifTagInfo('GPSDestLatitude', toStr=toStrDegMinSec),
		21: ExifTagInfo('GPSDestLongitudeRef'),
		22: ExifTagInfo('GPSDestLongitude', toStr=toStrDegMinSec),
		23: ExifTagInfo('GPSDestBearingRef'),
		24: ExifTagInfo('GPSDestBearing', toStr=toStrDegrees),
		25: ExifTagInfo('GPSDestDistanceRef'),
		26: ExifTagInfo('GPSDestDistance'),
		27: ExifTagInfo('GPSProcessingMethod'),
		28: ExifTagInfo('GPSAreaInformation'),
		29: ExifTagInfo('GPSDateStamp'),
		30: ExifTagInfo('GPSDifferential'),
		31: ExifTagInfo('GPSHPositioningError'),
	}),
	50341: ExifTagInfo('PrintImageMatching'),
})

def exifPrintSorted(ifdData, level=0, oneLine=False):
	if oneLine:
		indent = ''
		tagEnd = '='
		valEnd = ','
	else:
		indent = '\t' * level
		tagEnd = ': '
		valEnd = '\n'

	for tagData in sorted(ifdData.itervalues(), key=operator.attrgetter('name')):

		value = tagData.value
		valueType = tagData.valueType

		if valueType is None:
			if not oneLine:
				print(indent, tagData.name, sep='', end=':\n')

			exifPrintSorted(value, level + 1, oneLine)
			continue

		print(indent, tagData.name, sep='', end=tagEnd)

		if tagData.toStr is not None:
			value = tagData.toStr(value)
			if isinstance(value, dict):
				print(end=valEnd)
				exifPrintSorted(value, level + 1, oneLine)
				continue
		else:
			value = valueType.toStr(value)

		print(value, end=valEnd)

	if oneLine and level == 0:
		print()

badExifOffset = {
	('2010:07:24 14:25:32', 194): 12, # IMG_0317.JPG
	('2010:07:24 14:25:56', 194): 12, # IMG_0318.JPG
}

def exifReadIFD(b, i, ifdInfo):
	ifdData = {}

	n = E.int2(b, i) # Number of fields
	i += 2

	while n > 0:
		tag = E.int2(b, i)
		valueType = E.int2(b, i+2)
		typeInfo = ExifType.lookup.get(valueType)

		if typeInfo is None:
			print('Unrecognized type', valueType, 'at offset', i+2, file=sys.stderr)
			break

		count = E.int4(b, i+4)
		i += 8

		tagInfo = ifdInfo.setdefault(tag, ExifTagInfo(tag))
		ifdData[tag] = tagData = ExifTagData(tagInfo)

		if tagInfo.subIFD is None:
			tagData.valueType = typeInfo
			tagData.offset = offset = E.int4(b, i) if typeInfo.size * count > 4 else i
			tagData.value = typeInfo.read(b, offset, count)
			tagData.count = count
		else:
			assert valueType == 4
			assert count == 1
			offset = E.int4(b, i)

			if tag == 34665:
				dateTime = ifdData.get(306)
				if dateTime is not None:
					offset += badExifOffset.get((dateTime.value, offset), 0)

			tagData.value = exifReadIFD(b, offset, tagInfo.subIFD)

		i += 4
		n -= 1

	return ifdData

def exifRead(b):
	global E

	if b[0:2] == 'II':
		E = LittleEndian
	else:
		assert b[0:2] == 'MM'
		E = BigEndian

	assert E.int2(b, 2) == 42

	ifd0_offset = E.int4(b, 4)

	return exifReadIFD(b, ifd0_offset, exifIFD0.subIFD)

# JPEG Spec: https://www.w3.org/Graphics/JPEG/itu-t81.pdf

startOfFrameMarkers = (
	0xC0,
	0xC1, 0xC2, 0xC3,
	0xC5, 0xC6, 0xC7,
	0xC9, 0xCA, 0xCB,
	0xCD, 0xCE, 0xCF,
)

def jpegReadSegments(image, f):
	beInt2 = BigEndian.int2

	f.seek(0) # Rewind to the beginning of the file

	b = f.read(2)
	while b != '':
		assert b[0] == '\xFF'
		marker = ord(b[1])
		b = f.read(2)

		if 0xD0 <= marker <= 0xD9:
			# 0xD0 thru 0xD7 => restart (RSTm)
			# 0xD8 => start of image (SOI)
			# 0xD9 => end of image (EOI)
			continue
		if marker in startOfFrameMarkers:
			b = f.read(6)
			width = beInt2(b, 3)
			height = beInt2(b, 1)
			image.size = (width, height)
			break

		segmentLength = beInt2(b) - 2

		if marker == 0xE1:
			b = f.read(6)
			segmentLength -= 6
			if b == 'Exif\x00\x00':
				image.exifOffset = f.tell()
				b = f.read(segmentLength)
				image.exifData = exifRead(b)
				image.byteOrder = E
				b = f.read(2)
				continue

		f.seek(segmentLength, 1)
		b = f.read(2)

class Image(object):
	def __init__(self, filename):
		self.fileName = filename
		self.size = None
		self.exifData = None

		with open(filename, 'rb') as f:
			b = f.read(16)
			if b[:4] == '\xFF\xD8\xFF\xE1' and b[6:11] == 'Exif\x00':
				jpegReadSegments(self, f)

			elif b[:4] == '\xFF\xD8\xFF\xE0' and b[6:11] == 'JFIF\x00':
				jpegReadSegments(self, f)

			elif b[:8] == '\x89PNG\r\n\x1A\n':
				pngReadHeader(self, b[8:], f)

	def getTimeCreated(self):
		if self.exifData is None:
			return 0

		exifSubIFD = self.exifData.get(34665)
		if exifSubIFD is None:
			return 0

		tagData = exifSubIFD.value.get(36867) # DateTimeOriginal, e.g. '2008:06:27 08:36:55'
		if tagData is None:
			return 0

		try:
			return time.mktime(time.strptime(tagData.value, '%Y:%m:%d %H:%M:%S'))
		except ValueError:
			return 0

	def printExif(self, oneLine=False):
		if self.exifData is not None:
			if oneLine:
				print(self.fileName, end=',')
				print('ByteOrder', self.byteOrder.name, sep='=', end=',')
			else:
				print('FileName', self.fileName, sep=': ')
				print('ByteOrder', self.byteOrder.name, sep=': ')

			exifPrintSorted(self.exifData, oneLine=oneLine)

def setOrientation(image, args):
	if image.exifData is None:
		print(image.fileName, 'doesn\'t have Exif metadata')
		return

	tagData = image.exifData.get(274)
	if tagData is None:
		print(image.fileName, 'doesn\'t have an Orientation tag')
		return

	assert tagData.valueType is ExifTypeShort
	assert tagData.count == 1

	newValue = args.orientation

	if tagData.value[0] == newValue:
		print(image.fileName, 'already has Orientation', newValue)
		return

	if not image.fileName.endswith(('.JPG', '.jpg', '.JPEG', '.jpeg')):
		print(image.fileName, 'must end with .JPG, .jpg, .JPEG, or .jpeg')
		return

	fileName, suffix = image.fileName.rsplit('.', 1)
	fileName = '.'.join((fileName, 'new', suffix))

	if os.path.exists(fileName):
		print(fileName, 'already exists (will not overwrite)')
		return

	print('Creating', fileName, '...', end=' ')

	with open(image.fileName, 'rb') as oldFile, open(fileName, 'wb') as newFile:

		newFile.write(oldFile.read(image.exifOffset + tagData.offset))
		oldFile.read(2)

		b = E.str2(newValue)
		while b != '':
			newFile.write(b)
			b = oldFile.read(1<<12)

		fileInfo = os.fstat(oldFile.fileno())
		os.fchmod(newFile.fileno(), fileInfo.st_mode)

	os.utime(fileName, (fileInfo.st_atime, fileInfo.st_mtime))
	print('Done')

def printExif(image, args):
	image.printExif(oneLine=args.one_line)

def main():
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('-o', '--orientation', type=int, default=0, choices=range(1, 9))
	parser.add_argument('-l', '--one-line', action='store_true')
	parser.add_argument('imagePath', nargs='+')
	args = parser.parse_args()

	if args.orientation != 0:
		action = setOrientation
	else:
		action = printExif

	for fileName in args.imagePath:
		try:
			image = Image(fileName)
		except IOError as e:
			print(e, file=sys.stderr)
			return
		action(image, args)

if __name__ == '__main__':
	main()
