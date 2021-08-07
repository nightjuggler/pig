import operator
import optparse
import os
import time

from pimly import Image
import spec as global_spec

page_path_format = 'page%03u.html'

def format_ar(kind, aspect_ratio):
	return '{} aspect ratio ({}:{})'.format(kind, *aspect_ratio)

def check_ar(name, kind1, ar1, kind2, ar2):
	if ar1 != ar2:
		print(format_ar(kind1, ar1), 'for "{}" not equal to'.format(name), format_ar(kind2, ar2))

def adjust_time(timestamp, spec):
	if timestamp > spec.time_adjust_cutoff:
		timestamp += spec.time_adjust

	(year, month, day, hour, minute) = time.localtime(timestamp)[0:5]

	if hour < 12:
		suffix = 'am'
		if hour == 0:
			hour = 12
	else:
		suffix = 'pm'
		if hour > 12:
			hour -= 12

	display_time = '%u-%u-%02u %u:%02u%s' % (month, day, year % 100, hour, minute, suffix)
	return timestamp, display_time

def get_greatest_common_divisor(a, b):
	while b != 0:
		a, b = b, a % b
	return a

def get_aspect_ratio(w, h):
	gcd = get_greatest_common_divisor(w, h)
	return (w/gcd, h/gcd)

def get_dimensions(spec_height, ar_width, ar_height):
	return int(float(spec_height) * ar_width / ar_height + 0.5), spec_height

class ImageInfo(object):
	def __init__(self, name, spec, dir_spec):
		self.name = name
		self.spec = spec
		self.dir = dir_spec

		original_filename = os.path.join(dir_spec.originals, name)
		stat_object = os.stat(original_filename)
		original_image = Image(original_filename)

		original_info = ['{}x{}'.format(*original_image.size),
			'{:.1f}MB'.format(stat_object.st_size / 1024 / 1024)]

		timestamp = original_image.getTimeCreated()
		if timestamp == 0:
			timestamp = stat_object.st_mtime
		if timestamp > 0:
			timestamp, display_time = adjust_time(timestamp, spec)
			original_info.append(display_time)

		self.original_info = ', '.join(original_info)
		self.time_and_name = (timestamp, name)

		width, height = original_image.size
		if width < height:
			aspect_ratio = get_aspect_ratio(height, width)
			self.height, self.width = get_dimensions(spec.height, *aspect_ratio)
			self.thumb_height, self.thumb_width = get_dimensions(spec.thumb_height, *aspect_ratio)
		else:
			aspect_ratio = get_aspect_ratio(width, height)
			self.width, self.height = get_dimensions(spec.height, *aspect_ratio)
			self.thumb_width, self.thumb_height = get_dimensions(spec.thumb_height, *aspect_ratio)

		self.resize_width = self.width

		check_ar(original_filename, 'Image', aspect_ratio, 'spec', spec.aspect_ratio)

	def rotate90(self):
		self.width, self.height = self.height, self.width
		self.thumb_width, self.thumb_height = self.thumb_height, self.thumb_width

def print_image_pages(images):
	page_template_file = open('page_template.html')
	page_template = page_template_file.read()
	page_template_file.close()

	thumbs_per_page = global_spec.thumb_cols * global_spec.thumb_rows

	num_images = len(images)
	for image_number, image in enumerate(images, start=1):
		if image_number > 1:
			prev_page = image_number - 1
			page_path = page_path_format % prev_page
			left_arrow = '<a href="{}#c">(Previous)</a> '.format(page_path)
			if prev_page > 1:
				page_path = page_path_format % 1
				left_arrow = '<a href="{}#c">(First)</a> '.format(page_path) + left_arrow
		else:
			prev_page = num_images
			left_arrow = ''
		if image_number < num_images:
			next_page = image_number + 1
			page_path = page_path_format % next_page
			right_arrow = ' <a href="{}#c">(Next)</a>'.format(page_path)
			if next_page < num_images:
				page_path = page_path_format % num_images
				right_arrow += ' <a href="{}#c">(Last)</a>'.format(page_path)
		else:
			next_page = 1
			right_arrow = ''

		index_page_number = (image_number - 1) // thumbs_per_page + 1

		caption = image.spec.captions.get(image.name)
		if caption is None:
			caption = ''
		else:
			caption = '<p class="caption">{}</p>\n'.format(caption)

		width, height = Image(os.path.join(image.dir.images, image.name)).size
		if (width, height) != (image.width, image.height):
			print('Changing image size for {} from {}x{} to {}x{}'.format(image.name,
				image.width, image.height, width, height))
			image.width, image.height = width, height

		template_vars = {
			'title': global_spec.title,
			'date': global_spec.date,
			'number': '%u/%u' % (image_number, num_images),
			'dir': image.dir.images,
			'name': image.name,
			'width': image.width,
			'height': image.height,
			'next_page': page_path_format % next_page,
			'index_page': get_index_path(index_page_number),
			'left_arrow': left_arrow,
			'right_arrow': right_arrow,
			'original_info': image.original_info,
			'original_dir': image.dir.originals,
			'caption': caption,
		}
		page_path = page_path_format % image_number
		page_file = open(page_path, 'w')
		page_file.write(page_template % template_vars)
		page_file.close()

def get_index_path(page_number):
	if page_number == 1:
		return 'index.html'

	return 'index%02u.html' % page_number

def print_index_page(index_template, table_data, page_number, num_pages):
	if page_number > 2:
		first_link = '(<a href="{}">First</a>) '.format(get_index_path(1))
	else:
		first_link = ''
	if page_number > 1:
		previous_link = '(<a href="{}">Previous</a>) '.format(get_index_path(page_number - 1))
	else:
		previous_link = ''

	if page_number < num_pages - 1:
		last_link = ' (<a href="{}">Last</a>)'.format(get_index_path(num_pages))
	else:
		last_link = ''
	if page_number < num_pages:
		next_link = ' (<a href="{}">Next</a>)'.format(get_index_path(page_number + 1))
	else:
		next_link = ''

	if num_pages > 1:
		page_number_str = '%u/%u' % (page_number, num_pages)
		pager = '<p>{}{}{}{}{}</p>'.format(first_link, previous_link, page_number_str, next_link, last_link)
	else:
		page_number_str = ''
		pager = ''

	template_vars = {
		'title': global_spec.title,
		'date': global_spec.date,
		'number': page_number_str,
		'table_data': '\n'.join(table_data),
		'pager': pager,
	}

	index_file = open(get_index_path(page_number), 'w')
	index_file.write(index_template % template_vars)
	index_file.close()

def print_thumb_pages(images):
	index_template_file = open('index_template.html')
	index_template = index_template_file.read()
	index_template_file.close()

	thumb_cols = global_spec.thumb_cols
	thumb_rows = global_spec.thumb_rows

	thumbs_per_page = thumb_cols * thumb_rows
	num_pages = (len(images) + thumbs_per_page - 1) // thumbs_per_page

	td_format = (
		'<td><a href="%(page)s#c">'
		'<img src="%(dir)s/%(name)s" width="%(width)u" height="%(height)u">'
		'</a></td>'
	)

	page_number = 0
	col, row = 0, 0
	table_data = []

	for image_number, image in enumerate(images, start=1):
		if col == 0:
			table_data.append('<tr>')

		width, height = Image(os.path.join(image.dir.thumbs, image.name)).size
		if (width, height) != (image.thumb_width, image.thumb_height):
			print('Changing thumb size for {} from {}x{} to {}x{}'.format(image.name,
				image.thumb_width, image.thumb_height, width, height))
			image.thumb_width, image.thumb_height = width, height

		td_vars = {
			'dir': image.dir.thumbs,
			'name': image.name,
			'width': image.thumb_width,
			'height': image.thumb_height,
			'page': page_path_format % image_number,
		}
		table_data.append(td_format % td_vars)
		col += 1
		if col == thumb_cols:
			table_data.append('</tr>')
			col = 0
			row += 1
			if row == thumb_rows:
				page_number += 1
				print_index_page(index_template, table_data, page_number, num_pages)
				table_data = []
				row = 0

	if table_data:
		if col > 0 and col < thumb_cols:
			table_data.extend(['<td>&nbsp;</td>'] * (thumb_cols - col))
			table_data.append('</tr>')
		print_index_page(index_template, table_data, page_number + 1, num_pages)

def convert(in_path, out_path, conversions):
	command = ['/usr/local/bin/magick', in_path, out_path]
	command[2:2] = conversions
	command = ' '.join(command)

	print(command)
	os.system(command)

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

class DirSpec(object):
	def __init__(self, suffix):
		self.originals = 'originals' + suffix
		self.images = 'images' + suffix
		self.thumbs = 'thumbs' + suffix

		if not os.path.exists(self.images):
			os.mkdir(self.images)
		if not os.path.exists(self.thumbs):
			os.mkdir(self.thumbs)

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

def get_images(d):
	dir_suffix = d.get('dir_suffix', '')
	dir_spec = DirSpec(dir_suffix)
	originals = dir_spec.originals
	spec = SharedSpec(d)

	spec.aspect_ratio = get_aspect_ratio(spec.width, spec.height)
	thumb_aspect_ratio = get_aspect_ratio(spec.thumb_width, spec.thumb_height)
	check_ar(originals, 'Spec', spec.aspect_ratio, 'thumb', thumb_aspect_ratio)

	time_adjust_cutoff = d.get('time_adjust_cutoff', 0)
	if time_adjust_cutoff != 0:
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

	skip = frozenset(d.get('skip', ()))
	images = [ImageInfo(name, spec, dir_spec) for name in os.listdir(originals)
		if name not in skip and name[-4:] in ('.JPG', '.jpg', '.PNG', '.png')]

	for image in images:
		image.rotate, rotate90 = rotate_info.get(image.name, (None, False))
		if rotate90:
			image.rotate90()

	crop_list = d.get('crop')
	if crop_list:
		crop_dir = DirSpec(dir_suffix + '_cropped')

		if not os.path.exists(crop_dir.originals):
			os.mkdir(crop_dir.originals)

		crop_count_map = {}
		for image_name, crop_geometry in crop_list:
			crop_count = crop_count_map.get(image_name, 1)
			crop_count_map[image_name] = crop_count + 1
			crop_image_name = '%s_%u%s' % (image_name[:-4], crop_count, image_name[-4:])

			crop_path = os.path.join(crop_dir.originals, crop_image_name)

			if not os.path.exists(crop_path):
				original_path = os.path.join(originals, image_name)

				convert(original_path, crop_path, ['-crop', crop_geometry])

				original_stat = os.stat(original_path)
				os.utime(crop_path, (original_stat.st_atime, original_stat.st_mtime))

			crop_image = ImageInfo(crop_image_name, spec, crop_dir)
			crop_image.rotate, rotate90 = rotate_info.get(image_name, (None, False))
			if rotate90:
				crop_image.rotate90()

			images.append(crop_image)

	return images

def run(options):
	images = get_images(vars(global_spec))
	for spec in getattr(global_spec, 'more_photos', ()):
		images.extend(get_images(spec))

	if getattr(global_spec, 'sort_by_time', False):
		sort_attr = 'time_and_name'
	else:
		sort_attr = 'name'

	images.sort(key=operator.attrgetter(sort_attr))

	if options.images:
		image_names = options.images.split()
		images = [image for image in images if image.name in image_names]
		options.image_pages = False
		options.thumb_pages = False
		options.best = False

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

if __name__ == '__main__':
	option_parser = optparse.OptionParser()
	option_parser.set_defaults(
		convert=True,
		convert_images=True,
		convert_thumbs=True,
		normalize_all=False,
		images=None,
		image_pages=True,
		thumb_pages=True,
		best=True,
		)

	option_parser.add_option('--no-convert',
		action='store_false',
		dest='convert',
		)
	option_parser.add_option('--no-convert-images',
		action='store_false',
		dest='convert_images',
		)
	option_parser.add_option('--no-convert-thumbs',
		action='store_false',
		dest='convert_thumbs',
		)
	option_parser.add_option('--normalize-all',
		action='store_true',
		dest='normalize_all',
		)
	option_parser.add_option('--images',
		action='store',
		dest='images',
		)
	option_parser.add_option('--no-image-pages',
		action='store_false',
		dest='image_pages',
		)
	option_parser.add_option('--no-thumb-pages',
		action='store_false',
		dest='thumb_pages',
		)
	option_parser.add_option('--no-best',
		action='store_false',
		dest='best',
		)

	options, args = option_parser.parse_args()

	run(options)
