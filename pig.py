#!/usr/bin/python
import operator
import optparse
import os
import time

from pimly import Image
import spec

page_path_format = 'page%03u.html'

time_adjust_cutoff = getattr(spec, 'time_adjust_cutoff', None)
if time_adjust_cutoff is None:
	time_adjust_cutoff = 0
else:
	try:
		time_adjust_cutoff = time.mktime(time.strptime(time_adjust_cutoff, '%Y:%m:%d %H:%M:%S'))
	except ValueError:
		time_adjust_cutoff = 0

def adjust_time(timestamp, dir_spec):
	if timestamp > time_adjust_cutoff:
		timestamp += dir_spec.time_adjust

	(year, month, day, hour, minute) = time.localtime(timestamp)[0:5]

	if hour < 12:
		suffix = 'am'
		if hour == 0:
			hour = 12
	else:
		suffix = 'pm'
		if hour > 12:
			hour -= 12

	display_time = "%u-%u-%02u %u:%02u%s" % (month, day, year % 100, hour, minute, suffix)
	return timestamp, display_time

def get_greatest_common_divisor(a, b):
	while b != 0:
		a, b = b, a % b
	return a

def get_aspect_ratio(w, h):
	gcd = get_greatest_common_divisor(w, h)
	return (w/gcd, h/gcd)

class ImageInfo(object):
	NUMBER = 0
	def __init__(self, name, dir_spec):
		self.name = name
		self.spec = dir_spec
		ImageInfo.NUMBER += 1

		if name in dir_spec.rotate_left or name in dir_spec.rotate_right:
			self.width = dir_spec.height
			self.height = dir_spec.width
			self.thumb_width = dir_spec.thumb_height
			self.thumb_height = dir_spec.thumb_width
		else:
			self.width = dir_spec.width
			self.height = dir_spec.height
			self.thumb_width = dir_spec.thumb_width
			self.thumb_height = dir_spec.thumb_height

		original_filename = os.path.join(dir_spec.originals_dir, name)
		stat_object = os.stat(original_filename)
		original_filesize = stat_object.st_size
		original_image = Image(original_filename)

		original_info = ["%ux%u" % original_image.size]
		original_info.append("%.1fMB" % (float(original_filesize) / 1024 / 1024))

		timestamp = original_image.getTimeCreated()

		if timestamp == 0:
			timestamp = stat_object.st_mtime

		if timestamp > 0:
			timestamp, display_time = adjust_time(timestamp, dir_spec)
			original_info.append(display_time)

		self.original_info = ', '.join(original_info)
		self.time_and_name = (timestamp, name)

		width, height = original_image.size
		if width < height:
			aspect_ratio = get_aspect_ratio(height, width)
			self.resize_width = dir_spec.height
			self.width, self.height = self.height, self.width
			self.thumb_width, self.thumb_height = self.thumb_height, self.thumb_width
		else:
			aspect_ratio = get_aspect_ratio(width, height)
			self.resize_width = dir_spec.width

		if aspect_ratio != dir_spec.aspect_ratio:
			print 'Image aspect ratio ({}:{}) for "{}" not equal to spec aspect ratio ({}:{})'.format(
				aspect_ratio[0], aspect_ratio[1], original_filename,
				dir_spec.aspect_ratio[0], dir_spec.aspect_ratio[1])

def print_image_pages(images):
	page_template_file = open('page_template.html')
	page_template = page_template_file.read()
	page_template_file.close()

	thumbs_per_page = spec.thumb_cols * spec.thumb_rows

	for image in images:
		if image.number > 1:
			prev_page = image.number - 1
			page_path = page_path_format % prev_page
			left_arrow = "<a href=\"%s#c\">(Previous)</a> " % page_path
			if prev_page > 1:
				page_path = page_path_format % 1
				left_arrow = "<a href=\"%s#c\">(First)</a> " % page_path + left_arrow
		else:
			prev_page = image.NUMBER
			left_arrow = ''
		if image.number < image.NUMBER:
			next_page = image.number + 1
			page_path = page_path_format % next_page
			right_arrow = " <a href=\"%s#c\">(Next)</a>" % page_path
			if next_page < image.NUMBER:
				page_path = page_path_format % image.NUMBER
				right_arrow += " <a href=\"%s#c\">(Last)</a>" % page_path
		else:
			next_page = 1
			right_arrow = ''

		index_page_number = (image.number - 1) / thumbs_per_page + 1

		caption = image.spec.captions.get(image.name)
		if caption is None:
			caption = ''
		else:
			caption = '<p class="caption">%s</p>\n' % caption

		width, height = Image(os.path.join(image.spec.images_dir, image.name)).size
		if (width, height) != (image.width, image.height):
			print 'Changing image size for {} from {}x{} to {}x{}'.format(image.name,
				image.width, image.height, width, height)
			image.width, image.height = width, height

		template_vars = {
			'title': spec.title,
			'date': spec.date,
			'number': "%u/%u" % (image.number, image.NUMBER),
			'dir': image.spec.images_dir,
			'name': image.name,
			'width': image.width,
			'height': image.height,
			'next_page': page_path_format % next_page,
			'index_page': get_index_path(index_page_number),
			'left_arrow': left_arrow,
			'right_arrow': right_arrow,
			'original_info': image.original_info,
			'original_dir': image.spec.originals_dir,
			'caption': caption,
		}
		page_path = page_path_format % image.number
		page_file = open(page_path, 'w')
		page_file.write(page_template % template_vars)
		page_file.close()

def get_index_path(page_number):
	if page_number == 1:
		return 'index.html'

	return "index%02u.html" % page_number

def print_index_page(index_template, table_data, page_number):
	thumbs_per_page = spec.thumb_cols * spec.thumb_rows
	num_index_pages = (ImageInfo.NUMBER + thumbs_per_page - 1) / thumbs_per_page

	if page_number > 2:
		first_link = "(<a href=\"%s\">First</a>) " % get_index_path(1)
	else:
		first_link = ''
	if page_number > 1:
		previous_link = "(<a href=\"%s\">Previous</a>) " % get_index_path(page_number - 1)
	else:
		previous_link = ''

	if page_number < num_index_pages - 1:
		last_link = " (<a href=\"%s\">Last</a>)" % get_index_path(num_index_pages)
	else:
		last_link = ''
	if page_number < num_index_pages:
		next_link = " (<a href=\"%s\">Next</a>)" % get_index_path(page_number + 1)
	else:
		next_link = ''

	if num_index_pages > 1:
		page_number_str = "%u/%u" % (page_number, num_index_pages)
		pager = "<p>%s%s%s%s%s</p>" % (first_link, previous_link, page_number_str, next_link, last_link)
	else:
		page_number_str = ''
		pager = ''

	template_vars = {
		'title': spec.title,
		'date': spec.date,
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

	td_format = (
		'<td><a href="%(page)s#c">'
		'<img src="%(dir)s/%(name)s" width="%(width)u" height="%(height)u">'
		'</a></td>'
	)

	page_number = 0
	col, row = 0, 0
	table_data = []

	for image in images:
		if col == 0:
			table_data.append('<tr>')

		width, height = Image(os.path.join(image.spec.thumbs_dir, image.name)).size
		if (width, height) != (image.thumb_width, image.thumb_height):
			print 'Changing thumb size for {} from {}x{} to {}x{}'.format(image.name,
				image.thumb_width, image.thumb_height, width, height)
			image.thumb_width, image.thumb_height = width, height

		td_vars = {
			'dir': image.spec.thumbs_dir,
			'name': image.name,
			'width': image.thumb_width,
			'height': image.thumb_height,
			'page': page_path_format % image.number,
		}
		table_data.append(td_format % td_vars)
		col += 1
		if col == spec.thumb_cols:
			table_data.append('</tr>')
			col = 0
			row += 1
			if row == spec.thumb_rows:
				page_number += 1
				print_index_page(index_template, table_data, page_number)
				table_data = []
				row = 0

	if table_data:
		if col > 0 and col < spec.thumb_cols:
			table_data.extend(['<td>&nbsp;</td>'] * (spec.thumb_cols - col))
			table_data.append('</tr>')
		print_index_page(index_template, table_data, page_number + 1)

def convert(in_path, out_path, conversions):
	command = ['/usr/local/bin/magick', in_path, out_path]
	command[2:2] = conversions
	command = ' '.join(command)

	print command
	os.system(command)

def convert_all(images, options):
	for image in images:
		original_path = os.path.join(image.spec.originals_dir, image.name)
		image_path = os.path.join(image.spec.images_dir, image.name)
		thumb_path = os.path.join(image.spec.thumbs_dir, image.name)

		pre_convert = image.spec.pre_convert.get(image.name)
		post_convert = image.spec.post_convert.get(image.name)

		conversions = ['-strip']
		if pre_convert:
			conversions.append(pre_convert)
		conversions.append('-resize')
		conversions.append(str(image.resize_width))

		if image.name in image.spec.rotate_right:
			conversions.append('-rotate 90')
		elif image.name in image.spec.rotate_left:
			conversions.append('-rotate -90')
		elif image.name in image.spec.rotate_180:
			conversions.append('-rotate 180')

		if image.name in image.spec.normalize or options.normalize_all:
			conversions.append('-normalize')
		if post_convert:
			conversions.append(post_convert)

		if options.convert_images and not os.path.exists(image_path):
			convert(original_path, image_path, conversions)
		if options.convert_thumbs and not os.path.exists(thumb_path):
			convert(image_path, thumb_path, ['-resize', str(image.thumb_width)])

class DirSpec(object):
	def __init__(self, dir_suffix='', time_adjust=0,
		rotate_left=(), rotate_right=(), rotate_180=(), normalize=(),
		pre_convert=None, post_convert=None, captions=None,
		width=None, height=None, thumb_width=None, thumb_height=None,
		skip=(), crop=(), best=()):
		self.time_adjust = time_adjust
		self.rotate_left = set(rotate_left)
		self.rotate_right = set(rotate_right)
		self.rotate_180 = set(rotate_180)
		self.normalize = set(normalize)
		self.pre_convert = {} if pre_convert is None else pre_convert
		self.post_convert = {} if post_convert is None else post_convert
		self.captions = {} if captions is None else captions
		self.skip = frozenset(skip)
		self.best = frozenset(best)

		self.width = spec.width if width is None else width
		self.height = spec.height if height is None else height
		self.thumb_width = spec.thumb_width if thumb_width is None else thumb_width
		self.thumb_height = spec.thumb_height if thumb_height is None else thumb_height

		self.aspect_ratio = get_aspect_ratio(self.width, self.height)
		thumb_aspect_ratio = get_aspect_ratio(self.thumb_width, self.thumb_height)

		self.originals_dir = 'originals' + dir_suffix
		self.images_dir = 'images' + dir_suffix
		self.thumbs_dir = 'thumbs' + dir_suffix

		if self.aspect_ratio != thumb_aspect_ratio:
			print 'Spec aspect ratio ({}:{}) for "{}" not equal to thumb aspect ratio ({}:{})'.format(
				self.aspect_ratio[0], self.aspect_ratio[1], self.originals_dir,
				thumb_aspect_ratio[0], thumb_aspect_ratio[1])

		if not os.path.exists(self.images_dir):
			os.mkdir(self.images_dir)
		if not os.path.exists(self.thumbs_dir):
			os.mkdir(self.thumbs_dir)

		self.crop_list = crop
		if crop:
			self.crop_spec = DirSpec(
				dir_suffix = dir_suffix + '_cropped',
				time_adjust = time_adjust,
				pre_convert = pre_convert,
				post_convert = post_convert,
				captions = captions,
				width = width,
				height = height,
				thumb_width = thumb_width,
				thumb_height = thumb_height,
				)
			self.crop_spec.best = self.best

	def get_cropped_images(self):
		cropped_images = []
		crop_count_map = {}

		if self.crop_list and not os.path.exists(self.crop_spec.originals_dir):
			os.mkdir(self.crop_spec.originals_dir)

		for image_name, crop_geometry in self.crop_list:
			crop_count = crop_count_map.get(image_name, 1)
			crop_count_map[image_name] = crop_count + 1
			crop_image_name = "%s_%u%s" % (image_name[:-4], crop_count, image_name[-4:])

			if image_name in self.rotate_left:
				self.crop_spec.rotate_left.add(crop_image_name)
			elif image_name in self.rotate_right:
				self.crop_spec.rotate_right.add(crop_image_name)
			elif image_name in self.rotate_180:
				self.crop_spec.rotate_180.add(crop_image_name)
			if image_name in self.normalize:
				self.crop_spec.normalize.add(crop_image_name)

			crop_path = os.path.join(self.crop_spec.originals_dir, crop_image_name)

			if not os.path.exists(crop_path):
				original_path = os.path.join(self.originals_dir, image_name)

				convert(original_path, crop_path, ['-crop', crop_geometry])

				original_stat = os.stat(original_path)
				os.utime(crop_path, (original_stat.st_atime, original_stat.st_mtime))

			cropped_images.append(ImageInfo(crop_image_name, self.crop_spec))

		return cropped_images

	def get_images(self):
		images = [ImageInfo(name, self) for name in os.listdir(self.originals_dir)
				if name not in self.skip and name[-4:] in ('.JPG', '.jpg', '.PNG', '.png')]
		images.extend(self.get_cropped_images())
		return images

def run(options):
	dir_spec = DirSpec(
		time_adjust=getattr(spec, 'time_adjust', 0),
		rotate_left=getattr(spec, 'rotate_left', ()),
		rotate_right=getattr(spec, 'rotate_right', ()),
		rotate_180=getattr(spec, 'rotate_180', ()),
		normalize=getattr(spec, 'normalize', ()),
		pre_convert=getattr(spec, 'pre_convert', None),
		post_convert=getattr(spec, 'post_convert', None),
		captions=getattr(spec, 'captions', None),
		skip=getattr(spec, 'skip', ()),
		crop=getattr(spec, 'crop', ()),
		best=getattr(spec, 'best', ()),
	)

	images = dir_spec.get_images()
	for dir_spec in getattr(spec, 'more_photos', ()):
		images.extend(DirSpec(**dir_spec).get_images())

	if getattr(spec, 'sort_by_time', False):
		sort_attr = 'time_and_name'
	else:
		sort_attr = 'name'

	images.sort(key=operator.attrgetter(sort_attr))

	for i, image in enumerate(images):
		image.number = i + 1

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
		for i, image in enumerate(images):
			image.number = i + 1
		ImageInfo.NUMBER = len(images)

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
