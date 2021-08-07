import os

def writeCropList(imageDir):
	js_file = open('cropList.js', 'w')
	js_file.write('var showCropGeometry = true;\n')
	js_file.write('var imagePath = "{}/";\n'.format(imageDir))
	js_file.write('var imageNames = [\n')
	js_file.write(',\n'.join(['\t"{}"'.format(name) for name in os.listdir(imageDir)
		if name[-4:] in ('.JPG', '.jpg', '.PNG', '.png')]))
	js_file.write('\n];\n')
	js_file.close()

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('imageDir', nargs='?', default='originals')
	args = parser.parse_args()

	writeCropList(args.imageDir)
