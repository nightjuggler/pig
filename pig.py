import argparse
from collections import defaultdict
import operator
import os
import subprocess
import time

from pimly import Image
import spec as global_spec
import temple

magick = getattr(global_spec, 'magick', '/usr/local/bin/magick')
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

	return f'{month}-{day}-{year%100:02} {hour}:{minute:02}{suffix}'

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

		self.size_px = f'{width}x{height}'
		self.size_mb = f'{stat.st_size/1024/1024:.1f}MB'

		if timestamp := image.getTimeCreated() or stat.st_mtime:
			if timestamp > spec.time_adjust_cutoff: timestamp += spec.time_adjust
			self.time = format_time(timestamp)

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
		self.process_exif(image.exifData)
		if spec.custom_image_info:
			spec.custom_image_info(self, image)
		self.images.append(self)

	def rotate90(self):
		self.width, self.height = self.height, self.width
		self.thumb_width, self.thumb_height = self.thumb_height, self.thumb_width

	def process_exif(self, d):
		self.camera = ''
		self.camera_info = ''
		if not d: return

		def get_str(key):
			v = d.get(key)
			return v.valueType.toStr(v.value) if v else None

		make = get_str(271)
		model = get_str(272)
		if not (make and model): return
		self.camera = model if model.startswith(make) else f'{make} {model}'
		info = [self.camera]
		if d := d.get(34665):
			d = d.value
			if v := d.get(34855): # PhotographicSensitivity (short)
				a, = v.value
				info.append(f'ISO{a}')
			if v := d.get(41989): # FocalLengthIn35mmFilm (short)
				a, = v.value
				info.append(f'{a}mm')
			if v := d.get(33437): # FNumber (rational)
				(a, b), = v.value
				info.append(f'&fnof;{a/b:.2f}'.rstrip('.0'))
			if v := d.get(42082): # SourceExposureTimesOfCompositeImage
				info.append(v.toStr(v.value, p=1).split(', ')[1] + 's')
			elif v := d.get(33434): # ExposureTime (rational)
				(a, b), = v.value
				info.append(f'{a}/{b}s')
		self.camera_info = ', '.join(info)

	@classmethod
	def sort(cls):
		if getattr(global_spec, 'sort_by_time', False):
			sort_attr = 'time_and_name'
		else:
			sort_attr = 'name'
		cls.images.sort(key=operator.attrgetter(sort_attr))
		return cls.images

def read_template(path):
	with open(path) as file:
		try:
			template = temple.parse(file.read())
		except temple.TemplateError as error:
			template = None
			print(path, error, sep=': ')
	return template

def create_image_pages(images, options):
	template = options.image_pages and read_template('page_template.html')
	num_images = len(images)

	for image_number, image in enumerate(images, start=1):
		image.number = image_number
		image.page = page_path(image_number)
		template_vars = {
			'spec': global_spec,
			'image': image,
			'num_images': num_images,
			'half_width': image.width // 2,
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
		if template:
			with open(image.page, 'w') as file:
				template.write(file, template_vars)

def fit_sizes1(row_width, sizes):
	((w, h), images), = sizes
	new_w = round(row_width / len(images))
	new_h = round(new_w * h/w)
	for image in images:
		image.thumb_width, image.thumb_height = new_w, new_h

def fit_sizes2(row_width, sizes):
	((w1, h1), images1), ((w2, h2), images2) = sizes
	n1 = len(images1)
	n2 = len(images2)

	# (1) n1*(w1+d1) + n2*(w2+d2) = row_width
	# (2) (w1+d1)*h1/w1 = (w2+d2)*h2/w2

	# w2+d2 = (row_width - n1*(w1+d1)) / n2
	# w1+d1 = row_width*w1*h2 / (n1*w1*h2 + n2*w2*h1)

	new_w1 = row_width*w1*h2 / (n1*w1*h2 + n2*w2*h1)
	new_w2 = (row_width - n1*new_w1) / n2

	new_w1 = round(new_w1)
	new_h1 = round(new_w1 * h1/w1)
	new_w2 = round(new_w2)
	new_h2 = round(new_w2 * h2/w2)

	for image in images1:
		image.thumb_width, image.thumb_height = new_w1, new_h1
	for image in images2:
		image.thumb_width, image.thumb_height = new_w2, new_h2

def calculate_fitted_sizes(pages):
	sizemap = defaultdict(list)
	for page_num, table in enumerate(pages, start=1):
		max_widths = {}
		row_width = max(sum(image.thumb_width for image in row) for row in table)
		last_row = table[-1]
		for row_num, row in enumerate(table, start=1):
			for image in row:
				sizemap[image.thumb_width, image.thumb_height].append(image)
			sizes = sorted(sizemap.items())
			if row is last_row and len(row) < global_spec.thumb_cols:
				row_width = min(row_width, sum(len(images) * max_widths.get(size, size[0])
					for size, images in sizes))
			if len(sizes) == 2:
				fit_sizes2(row_width, sizes)
			elif len(sizes) == 1:
				fit_sizes1(row_width, sizes)
			else:
				sizes = [f'{w}x{h} [{len(images)}]' for (w, h), images in sizes]
				sizes = ', '.join(sizes[:-1]) + ', and ' + sizes[-1]
				print('Cannot calculate fitted sizes for thumbs on '
					f'page {page_num}, row {row_num}!\n'
					f'More than two different sizes: {sizes}')
			for size, images in sizemap.items():
				w = images[0].thumb_width
				if w > max_widths.get(size, 0):
					max_widths[size] = w
			sizemap.clear()

def prep_thumb_pages(images, fit):
	thumb_cols = global_spec.thumb_cols
	thumb_rows = global_spec.thumb_rows
	row, table, pages = [], [], []
	index_page = index_path(1)

	for image in images:
		image.index_page = index_page
		row.append(image)
		if len(row) == thumb_cols:
			table.append(row)
			row = []
			if len(table) == thumb_rows:
				pages.append(table)
				table = []
				index_page = index_path(len(pages) + 1)
	if row:
		if not fit:
			row.extend([None] * (thumb_cols - len(row)))
		table.append(row)
	if table:
		pages.append(table)
	if fit:
		calculate_fitted_sizes(pages)
	return pages

def create_thumb_pages(pages, options):
	fit = options.fit
	template = options.thumb_pages and read_template('index_template.html')
	num_pages = len(pages)

	for page, table in enumerate(pages, start=1):
		template_vars = {
			'spec': global_spec,
			'table': table,
			'fit': fit,
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
		if template:
			with open(index_path(page), 'w') as file:
				template.write(file, template_vars)

def mkdir(name):
	if not os.path.exists(name):
		os.mkdir(name)

def convert(in_path, out_path, conversions):
	command = [magick, in_path, *conversions, out_path]
	print(*command)
	subprocess.run(command)

def create_album(images, options):
	thumb_pages = prep_thumb_pages(images, options.fit)

	create_images = options.convert and options.convert_images
	create_thumbs = options.convert and options.convert_thumbs
	normalize_all = options.normalize_all

	for spec in {image.dir for image in images}:
		if create_images: mkdir(spec.images)
		if create_thumbs: mkdir(spec.thumbs)

	for image in images:
		name = image.name
		spec = image.spec

		original_path = os.path.join(image.dir.originals, name)
		image_path = os.path.join(image.dir.images, name)
		thumb_path = os.path.join(image.dir.thumbs, name)

		conversions = ['-strip']
		if pre_convert := spec.pre_convert.get(name):
			conversions.append(pre_convert)
		conversions.append('-resize')
		conversions.append(str(image.resize_width))
		if image.rotate:
			conversions.append('-rotate')
			conversions.append(image.rotate)
		if post_convert := spec.post_convert.get(name):
			conversions.append(post_convert)
		if normalize_all or name in spec.normalize:
			conversions.append('-normalize')

		if not os.path.exists(image_path) and create_images:
			convert(original_path, image_path, conversions)
		if os.path.exists(image_path):
			size = Image(image_path).size
			if size != (image.width, image.height):
				print('Changing size for {} from {}x{} to {}x{}'.format(image_path,
					image.width, image.height, *size))
				image.width, image.height = size

		if not os.path.exists(thumb_path) and create_thumbs:
			convert(image_path, thumb_path, ['-strip', '-resize', str(image.thumb_width)])
		if os.path.exists(thumb_path):
			size = Image(thumb_path).size
			if size != (image.thumb_width, image.thumb_height):
				print('Changing size for {} from {}x{} to {}x{}'.format(thumb_path,
					image.thumb_width, image.thumb_height, *size))
				image.thumb_width, image.thumb_height = size

	create_image_pages(images, options)
	create_thumb_pages(thumb_pages, options)

class DirSpec(object):
	def __init__(self, suffix):
		self.originals = 'originals' + suffix
		self.images = 'images' + suffix
		self.thumbs = 'thumbs' + suffix

class SharedSpec(object):
	def __init__(self, d):
		self.time_adjust = d.get('time_adjust', 0)
		self.pre_convert = d.get('pre_convert', {})
		self.post_convert = d.get('post_convert', {})
		self.captions = d.get('captions', {})
		self.normalize = frozenset(d.get('normalize', ()))
		self.best = frozenset(d.get('best', ()))
		self.custom_image_info = d.get('custom_image_info')

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

	def convert_orig(name, suffix, conversions):
		new_name = os.path.splitext(name)[0] + suffix + '.JPG'
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
			convert_orig(name, '', [])

	if crop_list := d.get('crop'):
		dir_spec = DirSpec(dir_suffix + '_cropped')
		mkdir(dir_spec.originals)

		crop_count_map = {}
		for name, geometry in crop_list:
			crop_count = crop_count_map.get(name, 1)
			crop_count_map[name] = crop_count + 1
			convert_orig(name, f'_{crop_count}', ['-crop', geometry])

def get_options():
	parser = argparse.ArgumentParser(allow_abbrev=False)
	parser.add_argument('--no-convert', dest='convert', action='store_false')
	parser.add_argument('--no-convert-images', dest='convert_images', action='store_false')
	parser.add_argument('--no-convert-thumbs', dest='convert_thumbs', action='store_false')
	parser.add_argument('--normalize-all', action='store_true')
	parser.add_argument('--no-image-pages', dest='image_pages', action='store_false')
	parser.add_argument('--no-thumb-pages', dest='thumb_pages', action='store_false')
	parser.add_argument('--no-best', dest='best', action='store_false')
	parser.add_argument('--fit', action='store_true')
	return parser.parse_args()

def main():
	options = get_options()

	add_images(vars(global_spec))
	for spec in getattr(global_spec, 'more_photos', ()):
		add_images(spec)

	images = ImageInfo.sort()
	create_album(images, options)

	if options.best and os.path.exists('best'):
		images = [image for image in images if image.name in image.spec.best]
		os.chdir('best')
		create_album(images, options)
		os.chdir('..')

if __name__ == '__main__':
	main()
