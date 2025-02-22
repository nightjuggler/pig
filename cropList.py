import os

def writeCropList(imageDir):
	imageNames = sorted(name for name in os.listdir(imageDir)
		if name.endswith(('.JPG', '.jpg', '.PNG', '.png')))
	with open('cropList.js', 'w') as f:
		f.write('var showCropGeometry = true;\n')
		f.write(f'var imagePath = "{imageDir}/";\n')
		f.write('var imageNames = [\n')
		f.write(',\n'.join([f'\t"{name}"' for name in imageNames]))
		f.write('\n];\n')

if __name__ == '__main__':
	import argparse
	parser = argparse.ArgumentParser()
	parser.add_argument('imageDir', nargs='?', default='originals')
	args = parser.parse_args()

	writeCropList(args.imageDir)
