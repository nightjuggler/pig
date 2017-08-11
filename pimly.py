#
# pimly.py (Pius' Image Library)
#
import operator
import time

__all__ = ('Image',)

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
	return ''.join([c if 32 <= ord(c) <= 126 else '\\x{:02X}'.format(ord(c)) for c in s])

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
# DCF Spec: http://www.cipa.jp/std/documents/e/DC-009-2010_E.pdf
# IFD = Image File Directory

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

escapeValue = lambda v: escapeString(v)
escapeStrOrd = lambda v: escapeString(str(ord(v)))

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
	531: ExifTagInfo('YCbCrPositioning'),

	34665: ExifTagInfo('Exif IFD', subIFD={
		33434: ExifTagInfo('ExposureTime'),
		33437: ExifTagInfo('FNumber'),
		34850: ExifTagInfo('ExposureProgram'),
		34855: ExifTagInfo('PhotographicSensitivity'),
		34864: ExifTagInfo('SensitivityType'),
		36864: ExifTagInfo('ExifVersion', toStr=escapeValue),
		36867: ExifTagInfo('DateTimeOriginal'),
		36868: ExifTagInfo('DateTimeDigitized'),
		37121: ExifTagInfo('ComponentsConfiguration', toStr=lambda v: ' '.join([str(ord(i)) for i in v])),
		37122: ExifTagInfo('CompressedBitsPerPixel'),
		37377: ExifTagInfo('ShutterSpeedValue'),
		37378: ExifTagInfo('ApertureValue'),
		37379: ExifTagInfo('BrightnessValue'),
		37380: ExifTagInfo('ExposureBiasValue'),
		37381: ExifTagInfo('MaxApertureValue'),
		37383: ExifTagInfo('MeteringMode'),
		37384: ExifTagInfo('LightSource'),
		37385: ExifTagInfo('Flash'),
		37386: ExifTagInfo('FocalLength'),
		37500: ExifTagInfo('MakerNote'),
		37510: ExifTagInfo('UserComment'),
		37520: ExifTagInfo('SubSecTime'),
		37521: ExifTagInfo('SubSecTimeOriginal'),
		37522: ExifTagInfo('SubSecTimeDigitized'),
		40960: ExifTagInfo('FlashpixVersion', toStr=escapeValue),
		40961: ExifTagInfo('ColorSpace'),
		40962: ExifTagInfo('PixelXDimension'),
		40963: ExifTagInfo('PixelYDimension'),
		40965: ExifTagInfo('Interoperability IFD', subIFD={
			1: ExifTagInfo('InteroperabilityIndex'),
			2: ExifTagInfo('InteroperabilityVersion'),
			4097: ExifTagInfo('RelatedImageWidth'),
			4098: ExifTagInfo('RelatedImageLength'),
		}),
		41486: ExifTagInfo('FocalPlaneXResolution'),
		41487: ExifTagInfo('FocalPlaneYResolution'),
		41488: ExifTagInfo('FocalPlaneResolutionUnit'),
		41495: ExifTagInfo('SensingMethod'),
		41728: ExifTagInfo('FileSource', toStr=escapeStrOrd),
		41729: ExifTagInfo('SceneType', toStr=escapeStrOrd),
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
		42036: ExifTagInfo('LensModel'),
	}),
	34853: ExifTagInfo('GPS IFD', subIFD={
		0: ExifTagInfo('GPSVersionID', toStr=lambda v: '.'.join([str(i) for i in v])),
		16: ExifTagInfo('GPSImgDirectionRef'),
		17: ExifTagInfo('GPSImgDirection'),
	}),
})

def exifPrintSorted(ifdData, level=0):
	indent = '\t' * level

	for tagData in sorted(ifdData.itervalues(), key=operator.attrgetter('name')):

		name = tagData.name
		value = tagData.value
		valueType = tagData.valueType

		if valueType is None:
			print '{}{}:'.format(indent, name)
			exifPrintSorted(value, level + 1)
			continue

		if tagData.toStr is not None:
			value = tagData.toStr(value)
		elif valueType == 2:
			value = escapeString(value)
		elif valueType == 7:
			value = '...'
		elif valueType == 5 or valueType == 10:
			value = '{}/{}'.format(*value)

		print '{}{}: {}'.format(indent, name, value)

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

def exifReadIFD(b, i, ifdInfo):
	ifdData = {}

	n = toInt2(b[i:i+2]) # Number of fields
	i += 2

	while n > 0:
		tag = toInt2(b[i:i+2])
		valueType = toInt2(b[i+2:i+4])
		count = toInt4(b[i+4:i+8])
		offset = toInt4(b[i+8:i+12])

		n -= 1
		i += 12

		tagInfo = ifdInfo.setdefault(tag, ExifTagInfo(str(tag)))
		ifdData[tag] = tagData = ExifTagData(tagInfo)

		if tagInfo.subIFD is None:
			tagData.valueType = valueType
			tagData.value = exifReadValue[valueType](b, i - 4, count, offset)
		else:
			assert valueType == 4
			assert count == 1
			tagData.value = exifReadIFD(b, offset, tagInfo.subIFD)

	return ifdData

def exifRead(b):
	global toInt2, toInt4

	if b[0:2] == 'II':
		toInt2 = leInt2
		toInt4 = leInt4
	else:
		assert b[0:2] == 'MM'
		toInt2 = beInt2
		toInt4 = beInt4

	assert toInt2(b[2:4]) == 42

	ifd0_offset = toInt4(b[4:8])

	return exifReadIFD(b, ifd0_offset, exifIFD0.subIFD)

# JPEG Spec: https://www.w3.org/Graphics/JPEG/itu-t81.pdf

startOfFrameMarkers = (
	0xC0,
	0xC1, 0xC2, 0xC3,
	0xC5, 0xC6, 0xC7,
	0xC9, 0xCA, 0xCB,
	0xCD, 0xCE, 0xCF,
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
		self.size = None
		self.exifData = None
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
#				pngReadChunks(b, f)
		finally:
			if f is not None:
				f.close()

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

	def printExif(self):
		if self.exifData is not None:
			exifPrintSorted(self.exifData)
