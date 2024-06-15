import argparse
import operator
import os
import subprocess
import time

from pimly import Image
import spec as global_spec
import temple

def page_path(n): return f'page{n:03}.html'
def index_path(n): return 'index.html' if n == 1 else f'index{n:02}.html'

def format_ar(kind, aspect_ratio):
	return '{} aspect ratio ({}:{})'.format(kind, *aspect_ratio)

def check_ar(name, kind1, ar1, kind2, ar2):
	if ar1 != ar2:
		print(format_ar(kind1, ar1), 'for "{}" not equal to'.format(name), format_ar(kind2, ar2))

def format_time(timestamp):
	year, month, day, hour, minute = time.localtime(timestamp)[:5]

	if hour < 12:
		suffix = 'am'
		if hour == 0:
			hour = 12
	else:
		suffix = 'pm'
		if hour > 12:
			hour -= 12

	return f', {month}-{day}-{year%100:02} {hour}:{minute:02}{suffix}'

def get_greatest_common_divisor(a, b):
	while b:
		a, b = b, a % b
	return a

def get_aspect_ratio(w, h):
	gcd = get_greatest_common_divisor(w, h)
	return w/gcd, h/gcd

def get_dimensions(spec_height, ar_width, ar_height):
	return int(spec_height * ar_width / ar_height + 0.5), spec_height

class ImageInfo(object):
	images = []
	def __init__(self, name, spec, dir_spec):
		self.name = name
		self.spec = spec
		self.dir = dir_spec

		path = os.path.join(dir_spec.originals, name)
		stat = os.stat(path)
		image = Image(path)
		width, height = image.size

		self.info = f'{width}x{height}, {stat.st_size/1024/1024:.1f}MB'

		if timestamp := image.getTimeCreated() or stat.st_mtime:
			if timestamp > spec.time_adjust_cutoff: timestamp += spec.time_adjust
			self.info += format_time(timestamp)

		self.time_and_name = timestamp, name

		if width < height:
			aspect_ratio = get_aspect_ratio(height, width)
			self.height, self.width = get_dimensions(spec.height, *aspect_ratio)
			self.thumb_height, self.thumb_width = get_dimensions(spec.thumb_height, *aspect_ratio)
		else:
			aspect_ratio = get_aspect_ratio(width, height)
			self.width, self.height = get_dimensions(spec.height, *aspect_ratio)
			self.thumb_width, self.thumb_height = get_dimensions(spec.thumb_height, *aspect_ratio)

		check_ar(path, 'Image', aspect_ratio, 'spec', spec.aspect_ratio)
		self.resize_width = self.width
		self.images.append(self)

	def rotate90(self):
		self.width, self.height = self.height, self.width
		self.thumb_width, self.thumb_height = self.thumb_height, self.thumb_width

	@classmethod
	def sort(cls):
		if getattr(global_spec, 'sort_by_time', False):
			sort_attr = 'time_and_name'
		else:
			sort_attr = 'name'
		cls.images.sort(key=operator.attrgetter(sort_attr))
		return cls.images

def print_image_pages(images):
	template = temple.read('page_template.html')
	thumbs_per_page = global_spec.thumb_cols * global_spec.thumb_rows

	num_images = len(images)
	for image_number, image in enumerate(images, start=1):
		template_vars = {
			'date': global_spec.date,
			'title': global_spec.title,
			'image': image,
			'number': f'{image_number}/{num_images}',
			'index_page': index_path((image_number - 1) // thumbs_per_page + 1),
			'caption': image.spec.captions.get(image.name, ''),
		}

		if image_number > 1:
			prev_page = image_number - 1
			template_vars['prev_link'] = True
			if prev_page > 1:
				template_vars['first_page'] = page_path(1)
		else:
			prev_page = num_images
		template_vars['prev_page'] = page_path(prev_page)

		if image_number < num_images:
			next_page = image_number + 1
			template_vars['next_link'] = True
			if next_page < num_images:
				template_vars['last_page'] = page_path(num_images)
		else:
			next_page = 1
		template_vars['next_page'] = page_path(next_page)

		width, height = Image(os.path.join(image.dir.images, image.name)).size
		if (width, height) != (image.width, image.height):
			print('Changing image size for {} from {}x{} to {}x{}'.format(image.name,
				image.width, image.height, width, height))
			image.width, image.height = width, height

		temple.write(template, page_path(image_number), template_vars)

def print_index_page(template, table, page, num_pages):
	template_vars = {
		'date': global_spec.date,
		'title': global_spec.title,
		'table': table,
	}
	if num_pages > 1:
		template_vars['number'] = f'{page}/{num_pages}'
		if page > 1:
			template_vars['prev_page'] = index_path(page - 1)
			if page > 2:
				template_vars['first_page'] = index_path(1)
		if page < num_pages:
			template_vars['next_page'] = index_path(page + 1)
			if page < num_pages - 1:
				template_vars['last_page'] = index_path(num_pages)

	temple.write(template, index_path(page), template_vars)

def print_thumb_pages(images):
	template = temple.read('index_template.html')
	thumb_cols = global_spec.thumb_cols
	thumb_rows = global_spec.thumb_rows

	thumbs_per_page = thumb_cols * thumb_rows
	num_pages = (len(images) + thumbs_per_page - 1) // thumbs_per_page

	page_number = 0
	table = []
	row = []

	for image_number, image in enumerate(images, start=1):

		width, height = Image(os.path.join(image.dir.thumbs, image.name)).size
		if (width, height) != (image.thumb_width, image.thumb_height):
			print('Changing thumb size for {} from {}x{} to {}x{}'.format(image.name,
				image.thumb_width, image.thumb_height, width, height))
			image.thumb_width, image.thumb_height = width, height

		row.append({'image': image, 'page': page_path(image_number)})
		if len(row) == thumb_cols:
			table.append(row)
			row = []
			if len(table) == thumb_rows:
				page_number += 1
				print_index_page(template, table, page_number, num_pages)
				table = []
	if table:
		if row:
			row.extend([{}] * (thumb_cols - len(row)))
			table.append(row)
		print_index_page(template, table, page_number + 1, num_pages)

def convert(in_path, out_path, conversions):
	command = ['/usr/local/bin/magick', in_path, *conversions, out_path]
	print(*command)
	subprocess.run(command)

def convert_all(images, options):
	for image in images:
		original_path = os.path.join(image.dir.originals, image.name)
		image_path = os.path.join(image.dir.images, image.name)
		thumb_path = os.path.join(image.dir.thumbs, image.name)

		pre_convert = image.spec.pre_convert.get(image.name)
		post_convert = image.spec.post_convert.get(image.name)

		conversions = ['-strip']
		if pre_convert:
			conversions.append(pre_convert)
		conversions.append('-resize')
		conversions.append(str(image.resize_width))
		if image.rotate:
			conversions.append('-rotate')
			conversions.append(image.rotate)

		if post_convert:
			conversions.append(post_convert)
		if options.normalize_all or image.name in image.spec.normalize:
			conversions.append('-normalize')

		if options.convert_images and not os.path.exists(image_path):
			convert(original_path, image_path, conversions)
		if options.convert_thumbs and not os.path.exists(thumb_path):
			convert(image_path, thumb_path, ['-strip', '-resize', str(image.thumb_width)])

def mkdir(name):
	if not os.path.exists(name):
		os.mkdir(name)

class DirSpec(object):
	def __init__(self, suffix):
		self.originals = 'originals' + suffix
		self.images = 'images' + suffix
		self.thumbs = 'thumbs' + suffix
		mkdir(self.images)
		mkdir(self.thumbs)

class SharedSpec(object):
	def __init__(self, d):
		self.time_adjust = d.get('time_adjust', 0)
		self.pre_convert = d.get('pre_convert', {})
		self.post_convert = d.get('post_convert', {})
		self.captions = d.get('captions', {})
		self.normalize = frozenset(d.get('normalize', ()))
		self.best = frozenset(d.get('best', ()))

		self.width = d.get('width', global_spec.width)
		self.height = d.get('height', global_spec.height)
		self.thumb_width = d.get('thumb_width', global_spec.thumb_width)
		self.thumb_height = d.get('thumb_height', global_spec.thumb_height)

def add_images(d):
	dir_suffix = d.get('dir_suffix', '')
	dir_spec = DirSpec(dir_suffix)
	originals = dir_spec.originals
	spec = SharedSpec(d)
	skip = frozenset(d.get('skip', ()))
	convert_list = []

	spec.aspect_ratio = get_aspect_ratio(spec.width, spec.height)
	thumb_aspect_ratio = get_aspect_ratio(spec.thumb_width, spec.thumb_height)
	check_ar(originals, 'Spec', spec.aspect_ratio, 'thumb', thumb_aspect_ratio)

	if time_adjust_cutoff := d.get('time_adjust_cutoff', 0):
		try:
			time_adjust_cutoff = time.mktime(time.strptime(time_adjust_cutoff, '%Y:%m:%d %H:%M:%S'))
		except ValueError:
			print('Cannot parse time_adjust_cutoff for "{}"'.format(originals))
			time_adjust_cutoff = 0
	spec.time_adjust_cutoff = time_adjust_cutoff

	rotate_info = {name: rotate_value
		for attr, rotate_value in (
			('rotate_left', ('-90', True)),
			('rotate_right', ('90', True)),
			('rotate_180', ('180', False)))
				for name in d.get(attr, ())}

	def add_image(name, orig_name):
		image = ImageInfo(name, spec, dir_spec)
		image.rotate, rotate90 = rotate_info.get(orig_name, (None, False))
		if rotate90:
			image.rotate90()

	for name in sorted(os.listdir(originals)):
		if name in skip:
			continue
		elif name.endswith('.HEIC'):
			convert_list.append(name)
		elif name.endswith(('.JPG', '.jpg', '.PNG', '.png')):
			add_image(name, name)

	def convert_orig(name, new_name, conversions):
		new_path = os.path.join(dir_spec.originals, new_name)
		if not os.path.exists(new_path):
			path = os.path.join(originals, name)
			stat = os.stat(path)
			convert(path, new_path, conversions)
			os.utime(new_path, ns=(stat.st_atime_ns, stat.st_mtime_ns))
		add_image(new_name, name)

	if convert_list:
		dir_spec = DirSpec(dir_suffix)
		dir_spec.originals += '_converted'
		mkdir(dir_spec.originals)

		for name in convert_list:
			convert_orig(name, os.path.splitext(name)[0] + '.JPG', [])

	if crop_list := d.get('crop'):
		dir_spec = DirSpec(dir_suffix + '_cropped')
		mkdir(dir_spec.originals)

		crop_count_map = {}
		for name, geometry in crop_list:
			crop_count = crop_count_map.get(name, 1)
			crop_count_map[name] = crop_count + 1
			convert_orig(name, f'{name[:-4]}_{crop_count}{name[-4:]}', ['-crop', geometry])

def run(options):
	add_images(vars(global_spec))
	for spec in getattr(global_spec, 'more_photos', ()):
		add_images(spec)

	images = ImageInfo.sort()
	if options.convert:
		convert_all(images, options)
	if options.image_pages:
		print_image_pages(images)
	if options.thumb_pages:
		print_thumb_pages(images)

	if options.best and os.path.exists('best'):
		images = [image for image in images if image.name in image.spec.best]

		os.chdir('best')
		print_image_pages(images)
		print_thumb_pages(images)
		os.chdir('..')

def main():
	parser = argparse.ArgumentParser(allow_abbrev=False)
	parser.add_argument('--no-convert', dest='convert', action='store_false')
	parser.add_argument('--no-convert-images', dest='convert_images', action='store_false')
	parser.add_argument('--no-convert-thumbs', dest='convert_thumbs', action='store_false')
	parser.add_argument('--normalize-all', action='store_true')
	parser.add_argument('--no-image-pages', dest='image_pages', action='store_false')
	parser.add_argument('--no-thumb-pages', dest='thumb_pages', action='store_false')
	parser.add_argument('--no-best', dest='best', action='store_false')
	run(parser.parse_args())

if __name__ == '__main__':
	main()
