import re
import sys

class Variable(object):
	def __init__(self, name):
		self.name, *self.attr = name.split('.')

	def eval(self, varmap, *, expected_type=str):
		value = varmap.get(self.name, '')
		attrs = self.attr
		while attrs:
			attr, *attrs = attrs
			if isinstance(value, dict):
				value = value.get(attr, '')
			elif isinstance(value, (list, tuple)):
				index = int(attr)
				value = value[index] if 0 <= index < len(value) else ''
			else:
				value = getattr(value, attr, '')
		if isinstance(value, expected_type):
			return value
		if expected_type is str and isinstance(value, int):
			return str(value)
		return ''

	def write(self, f, varmap):
		f.write(self.eval(varmap))

class Conditional(object):
	def __init__(self, name):
		self.var = Variable(name)
		self.template = Template()
		self.else_template = None

	def write(self, f, varmap):
		if self.var.eval(varmap, expected_type=object):
			self.template.write(f, varmap)
		elif self.else_template:
			self.else_template.write(f, varmap)

class Loop(object):
	def __init__(self, loopvar, seqname):
		self.loopvar = loopvar
		self.seq = Variable(seqname)
		self.template = Template()

	def write(self, f, varmap):
		for item in self.seq.eval(varmap, expected_type=(list, tuple)):
			varmap[self.loopvar] = item
			self.template.write(f, varmap)

class Template(object):
	def __init__(self):
		self.blocks = []
		self.parent = None

	def write(self, f, varmap):
		for block in self.blocks:
			if isinstance(block, str):
				f.write(block)
			else:
				block.write(f, varmap)

	def add(self, block):
		self.blocks.append(block)
		if template := getattr(block, 'template', None):
			template.parent = self
			return template
		return self

def read(path):
	pattern_var = '[a-z][0-9_a-z]*(?:\.[0-9_a-z]+)*'
	pattern_cond = re.compile('if ' + pattern_var)
	pattern_loop = re.compile('for [a-z][0-9_a-z]* in ' + pattern_var)
	pattern_var = re.compile(pattern_var)

	with open(path) as f:
		data = f.read()

	template = Template()
	i = 0

	def err(message):
		line = data.count('\n', 0, i) + 1
		column = i - data.rfind('\n', 0, i)
		sys.exit(f'{path}: {message} at line {line}, column {column}!')

	while True:
		if (j := data.find('<?', i)) < 0: break
		template.add(data[i:j])
		i = j + 2
		if (j := data.find('>', i)) < 0: err('<? missing >')
		code = data[i:j]
		if code == 'end':
			template = template.parent
			if not template: err('Unexpected <?end>')
		elif code == 'else':
			template = template.parent
			if not template: err('Unexpected <?else>')
			block = template.blocks[-1]
			if block.else_template: err('Duplicate <?else>')
			block.else_template = Template()
			block.else_template.parent = template
			template = block.else_template
		elif pattern_var.fullmatch(code):
			template.add(Variable(code))
		elif pattern_cond.fullmatch(code):
			template = template.add(Conditional(code.split()[1]))
		elif pattern_loop.fullmatch(code):
			code = code.split()
			template = template.add(Loop(code[1], code[3]))
		else:
			err(f'Malformed <?{code}>')
		i = j + 1

	if template.parent:
		err('Missing <?end>')
	return template.add(data[i:])

def write(template, path, varmap):
	with open(path, 'w') as f:
		template.write(f, varmap)
