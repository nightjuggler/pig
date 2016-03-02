#
# pimly.py (Pius' Image Library)
#
import time

__all__ = ('Image')

# Big Endian

def beInt4(b):
	return ord(b[3]) + (ord(b[2])<<8) + (ord(b[1])<<16) + (ord(b[0])<<24)
def beInt2(b):
	return ord(b[1]) + (ord(b[0])<<8)

# Little Endian

def leInt4(b):
	return ord(b[0]) + (ord(b[1])<<8) + (ord(b[2])<<16) + (ord(b[3])<<24)
def leInt2(b):
	return ord(b[0]) + (ord(b[1])<<8)

# Convert 32-bit unsigned integer to 32-bit signed integer
def sInt4(n):
	return n - (1 << 32) if (n >> 31) == 1 else n

def escapeString(s):
	return '\'{}\''.format(''.join(
		[('\\' + c if c == '\\' or c == '\'' else c)
			if 32 <= ord(c) <= 126 else '\\x{:02X}'.format(ord(c))
			for c in s]))

# PNG Spec: https://www.w3.org/TR/PNG/

def pngReadChunk(b, f):
	assert len(b) == 8

	chunkLength = beInt4(b[:4])
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

toInt2 = leInt2
toInt4 = leInt4

# Exif Spec: http://www.cipa.jp/std/documents/e/DC-008-2012_E_C.pdf

exifTagName = {
	270: 'ImageDescription',
	271: 'Make',
	272: 'Model',
	274: 'Orientation',
	282: 'XResolution',
	283: 'YResolution',
	296: 'ResolutionUnit',
	305: 'Software',
	306: 'DateTime',
	531: 'YCbCrPositioning',
	33434: 'ExposureTime',
	33437: 'FNumber',
	34850: 'ExposureProgram',
	34855: 'PhotographicSensitivity',
	34864: 'SensitivityType',
	36864: 'ExifVersion',
	36867: 'DateTimeOriginal',
	36868: 'DateTimeDigitized',
	37121: 'ComponentsConfiguration',
	37122: 'CompressedBitsPerPixel',
	37377: 'ShutterSpeedValue',
	37378: 'ApertureValue',
	37379: 'BrightnessValue',
	37380: 'ExposureBiasValue',
	37381: 'MaxApertureValue',
	37383: 'MeteringMode',
	37384: 'LightSource',
	37385: 'Flash',
	37386: 'FocalLength',
	37500: 'MakerNote',
	37510: 'UserComment',
	37520: 'SubSecTime',
	37521: 'SubSecTimeOriginal',
	37522: 'SubSecTimeDigitized',
	40960: 'FlashpixVersion',
	40961: 'ColorSpace',
	40962: 'PixelXDimension',
	40963: 'PixelYDimension',
	41486: 'FocalPlaneXResolution',
	41487: 'FocalPlaneYResolution',
	41488: 'FocalPlaneResolutionUnit',
	41495: 'SensingMethod',
	41728: 'FileSource',
	41729: 'SceneType',
	41730: 'CFAPattern',
	41985: 'CustomRendered',
	41986: 'ExposureMode',
	41987: 'WhiteBalance',
	41988: 'DigitalZoomRatio',
	41989: 'FocalLengthIn35mmFilm',
	41990: 'SceneCaptureType',
	41991: 'GainControl',
	41992: 'Contrast',
	41993: 'Saturation',
	41994: 'Sharpness',
	41996: 'SubjectDistanceRange',
	42032: 'CameraOwnerName',
	42036: 'LensModel',
}

# IFD = Image File Directory

exifSubIFD = {
	34665: 'Exif',
	34853: 'GPS',
	40965: 'Interoperability',
}

def exifPrintTag(tag, type, value):
	if type == 2:
		value = escapeString(value)
	elif type == 7:
		value = '...'
	elif type == 5 or type == 10:
		value = '{}/{}'.format(*value)

	print '{}: {}'.format(exifTagName.get(tag, tag), value)

def exifReadByte(b, i, count, offset):
	if count == 1:
		return ord(b[i])
	if count <= 4:
		return [ord(b[i + j]) for j in xrange(count)]

	return [ord(b[offset + j]) for j in xrange(count)]

def exifReadAscii(b, i, count, offset):
	if count <= 4:
		offset = i

	value = b[offset : offset + count]
	assert value[-1] == '\x00'
	return value.rstrip('\x00\t\n\r ')

def exifReadShort(b, i, count, offset):
	if count == 1:
		return toInt2(b[i:i+2])
	if count == 2:
		return [toInt2(b[i:i+2]), toInt2(b[i+2:i+4])]

	return [toInt2(b[j:j+2]) for j in xrange(offset, offset + count*2, 2)]

def exifReadLong(b, i, count, offset):
	if count == 1:
		return offset

	return [toInt4(b[j:j+4]) for j in xrange(offset, offset + count*4, 4)]

def exifReadRational(b, i, count, offset):
	return [toInt4(b[offset:offset+4]), toInt4(b[offset+4:offset+8])]

def exifReadUndefined(b, i, count, offset):
	if count <= 4:
		offset = i

	return b[offset : offset + count]

def exifReadSignedLong(b, i, count, offset):
	if count == 1:
		return sInt4(offset)

	return [sInt4(toInt4(b[j:j+4])) for j in xrange(offset, offset + count*4, 4)]

def exifReadSignedRational(b, i, count, offset):
	return [sInt4(toInt4(b[offset:offset+4])), sInt4(toInt4(b[offset+4:offset+8]))]

exifReadValue = {
	1: exifReadByte,
	2: exifReadAscii,
	3: exifReadShort,
	4: exifReadLong,
	5: exifReadRational,
	7: exifReadUndefined,
	9: exifReadSignedLong,
	10: exifReadSignedRational,
}

def exifReadIFD(b, i):
	exifData = {}

	n = toInt2(b[i:i+2]) # Number of fields
	i += 2

	while n > 0:
		tag = toInt2(b[i:i+2])
		type = toInt2(b[i+2:i+4])
		count = toInt4(b[i+4:i+8])
		offset = toInt4(b[i+8:i+12])

		n -= 1
		i += 12

		if tag in exifSubIFD:
			assert type == 4 # LONG (4-byte unsigned integer)
			assert count == 1
			exifData[tag] = exifReadIFD(b, offset)
		else:
			exifData[tag] = exifReadValue[type](b, i - 4, count, offset)
#			exifPrintTag(tag, type, exifData[tag])

	return exifData

def exifRead(b):
	if b[0:2] == 'II':
		toInt2 = leInt2
		toInt4 = leInt4
	else:
		assert b[0:2] == 'MM'
		toInt2 = beInt2
		toInt4 = beInt4

	assert toInt2(b[2:4]) == 42

	ifd0_offset = toInt4(b[4:8])

	return exifReadIFD(b, ifd0_offset)

startOfFrameMarkers = (
	0xC0, 0xC1, 0xC2, 0xC3,
	0xC5, 0xC6, 0xC7,
	0xC9, 0xCA, 0xCB,
	0xCD, 0xCE, 0xCF
)

def jpegReadSegments(f):
	width = None
	height = None
	exifData = None

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
			width = beInt2(b[3:5])
			height = beInt2(b[1:3])
			break

		segmentLength = beInt2(b) - 2

		if marker == 0xE1:
			b = f.read(6)
			segmentLength -= 6
			if b == 'Exif\x00\x00':
				b = f.read(segmentLength)
				exifData = exifRead(b)
				b = f.read(2)
				continue

		f.seek(segmentLength, 1)
		b = f.read(2)

	return (width, height), exifData

class Image(object):
	def __init__(self, filename):
		f = None
		try:
			f = open(filename, 'rb')
			b = f.read(16)
			if b[:4] == '\xFF\xD8\xFF\xE1' and b[6:11] == 'Exif\x00':
				self.size, self.exifData = jpegReadSegments(f)

			elif b[:4] == '\xFF\xD8\xFF\xE0' and b[6:11] == 'JFIF\x00':
				self.size, self.exifData = jpegReadSegments(f)

			elif b[:8] == '\x89PNG\r\n\x1A\n':
				chunkType, chunkData, b = pngReadChunk(b[8:], f)
				assert chunkType == 'IHDR'
				width = beInt4(chunkData[:4])
				height = beInt4(chunkData[4:8])
				self.size = (width, height)
				self.exifData = None
#				pngReadChunks(b, f)
		finally:
			if f is not None:
				f.close()

	def getTimeCreated(self):
		if self.exifData is None:
			return 0

		exifData = self.exifData.get(34665)
		if exifData is None:
			return 0

		timeCreated = exifData.get(36867) # DateTimeOriginal, e.g. '2008:06:27 08:36:55'
		if timeCreated is None:
			return 0

		try:
			return time.mktime(time.strptime(timeCreated, '%Y:%m:%d %H:%M:%S'))
		except ValueError:
			return 0
