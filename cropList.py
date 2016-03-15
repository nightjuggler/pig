#!/usr/bin/python
import os

if __name__ == '__main__':
	js_file = open('cropList.js', 'w')
	js_file.write('var imageNames = [\n')
	js_file.write(',\n'.join(['\t"{}"'.format(name) for name in os.listdir('originals')
		if name[-4:] in ('.JPG', '.jpg', '.PNG', '.png')]))
	js_file.write('\n];\n')
	js_file.close()
