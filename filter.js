var svgNS = 'http://www.w3.org/2000/svg';
var xlinkNS = 'http://www.w3.org/1999/xlink';
var svgFilterId = 0;
var svgFilterIdBin = [];
var channelMap = [['R', 1], ['G', 2], ['B', 4]];
var divWidth, divHeight;
var photoLeft, photoTop;
var userSpaceFilters = [];
var filterMarginX;
var filterMarginY;

function removeSVGFilter(id)
{
	if (id <= 0) return;
	var idStr = 'filter' + id;
	var filterElement = document.getElementById(idStr);
	filterElement.parentNode.removeChild(filterElement);
	svgFilterIdBin.push(id);

	for (var i = 0, len = userSpaceFilters.length; i < len; ++i)
		if (userSpaceFilters[i][0][0].id === idStr) {
			userSpaceFilters.splice(i, 1);
			break;
		}
}
function setUserSpaceElement(f)
{
	if (filterMarginX === undefined) return;

	var x = Math.round(-photoLeft);
	var y = Math.round(-photoTop);

	var xValues = [x, x - filterMarginX, x + divWidth - 1, x + divWidth];
	var yValues = [y, y - filterMarginY, y + divHeight - 1, y + divHeight];

	var widths = [divWidth, divWidth + 2 * filterMarginX, filterMarginX];
	var heights = [divHeight, divHeight + 2 * filterMarginY, filterMarginY];

	var [fe, x, y, w, h] = f;

	if (x >= 0) fe.setAttribute('x', xValues[x]);
	if (y >= 0) fe.setAttribute('y', yValues[y]);
	if (w >= 0) fe.setAttribute('width', widths[w]);
	if (h >= 0) fe.setAttribute('height', heights[h]);
}
function addUserSpaceFilter(id, i, feList)
{
	var fe = document.getElementById('filter' + id);
	fe.setAttribute('filterUnits', 'userSpaceOnUse');
	var f = [fe, i, i, i, i];
	feList.unshift(f);
	setUserSpaceElement(f);
	userSpaceFilters.push(feList);
}
function updateUserSpaceFilters()
{
	var x = Math.round(-photoLeft);
	var y = Math.round(-photoTop);

	var xValues = [x, x - filterMarginX, x + divWidth - 1, x + divWidth];
	var yValues = [y, y - filterMarginY, y + divHeight - 1, y + divHeight];

	for (var f of userSpaceFilters)
		for (var [fe, x, y, w, h] of f)
		{
			if (x >= 0) fe.setAttribute('x', xValues[x]);
			if (y >= 0) fe.setAttribute('y', yValues[y]);
		}
}
function resetUserSpaceFilters()
{
	var x = Math.round(-photoLeft);
	var y = Math.round(-photoTop);

	filterMarginX = Math.round(divWidth / 10);
	filterMarginY = Math.round(divHeight / 10);

	var xValues = [x, x - filterMarginX, x + divWidth - 1, x + divWidth];
	var yValues = [y, y - filterMarginY, y + divHeight - 1, y + divHeight];

	var widths = [divWidth, divWidth + 2 * filterMarginX, filterMarginX];
	var heights = [divHeight, divHeight + 2 * filterMarginY, filterMarginY];

	for (var f of userSpaceFilters)
		for (var [fe, x, y, w, h] of f)
		{
			if (x >= 0) fe.setAttribute('x', xValues[x]);
			if (y >= 0) fe.setAttribute('y', yValues[y]);
			if (w >= 0) fe.setAttribute('width', widths[w]);
			if (h >= 0) fe.setAttribute('height', heights[h]);
		}
}
function createChannelMask(channels, unfiltered)
{
	var fe = document.createElementNS(svgNS, 'feComponentTransfer');

	if (unfiltered)
		fe.setAttribute('in', 'SourceGraphic');
	else
		fe.setAttribute('result', 'filtered');

	for (var [letter, flag] of channelMap)
		if ((channels & flag) === flag)
		{
			var feFunc = document.createElementNS(svgNS, 'feFunc' + letter);
			feFunc.setAttribute('type', 'linear');
			feFunc.setAttribute('slope', '0');
			fe.appendChild(feFunc);
		}

	return fe;
}
function createFilter(channels, fe)
{
	var filterId = svgFilterIdBin.length === 0 ? ++svgFilterId : svgFilterIdBin.pop();

	var filterNode = document.createElementNS(svgNS, 'filter');
	filterNode.setAttribute('id', 'filter' + filterId);
	filterNode.setAttribute('color-interpolation-filters', 'sRGB');

	if (Array.isArray(fe))
		for (var i = 0; i < fe.length; ++i)
			filterNode.appendChild(fe[i]);
	else
		for (var i = 1; i < arguments.length; ++i)
			filterNode.appendChild(arguments[i]);

	if (channels > 0 && channels < 7)
	{
		filterNode.appendChild(createChannelMask(7 - channels, false));
		filterNode.appendChild(createChannelMask(channels, true));

		fe = document.createElementNS(svgNS, 'feComposite');
		fe.setAttribute('in2', 'filtered');
		fe.setAttribute('operator', 'arithmetic');
		fe.setAttribute('k2', '1');
		fe.setAttribute('k3', '1');
		filterNode.appendChild(fe);
	}

	var svgNode = document.getElementById('svgRoot');
	svgNode.firstChild.appendChild(filterNode);
	return filterId;
}
function matrixRow(a)
{
	return a[0].toFixed(6) + ' ' + a[1].toFixed(6) + ' ' + a[2].toFixed(6);
}
function createColorMatrix(channels, a0, a1, a2)
{
	a0 = (channels & 1) === 1 ? matrixRow(a0) : '1 0 0';
	a1 = (channels & 2) === 2 ? matrixRow(a1) : '0 1 0';
	a2 = (channels & 4) === 4 ? matrixRow(a2) : '0 0 1';

	var values = a0 + ' 0 0 ' + a1 + ' 0 0 ' + a2 + ' 0 0 0 0 0 1 0';

	var fe = document.createElementNS(svgNS, 'feColorMatrix');
	fe.setAttribute('type', 'matrix');
	fe.setAttribute('values', values);
	return fe;
}
function createSVGBrightness(amount, channels)
{
	var fe = document.createElementNS(svgNS, 'feComponentTransfer');

	amount = amount.toFixed(6);

	for (var [letter, flag] of channelMap)
		if ((channels & flag) === flag)
		{
			var feFunc = document.createElementNS(svgNS, 'feFunc' + letter);
			feFunc.setAttribute('type', 'linear');
			feFunc.setAttribute('slope', amount);
			fe.appendChild(feFunc);
		}

	return createFilter(7, fe);
}
function createSVGContrast(amount, channels)
{
	var fe = document.createElementNS(svgNS, 'feComponentTransfer');

	var intercept = (0.5 - 0.5 * amount).toFixed(6);
	amount = amount.toFixed(6);

	for (var [letter, flag] of channelMap)
		if ((channels & flag) === flag)
		{
			var feFunc = document.createElementNS(svgNS, 'feFunc' + letter);
			feFunc.setAttribute('type', 'linear');
			feFunc.setAttribute('slope', amount);
			feFunc.setAttribute('intercept', intercept);
			fe.appendChild(feFunc);
		}

	return createFilter(7, fe);
}
function createSVGGrayscale(amount, channels)
{
	var s = 1 - amount;

	return createFilter(7, createColorMatrix(channels,
		[0.2126 + 0.7874*s, 0.7152 - 0.7152*s, 0.0722 - 0.0722*s],
		[0.2126 - 0.2126*s, 0.7152 + 0.2848*s, 0.0722 - 0.0722*s],
		[0.2126 - 0.2126*s, 0.7152 - 0.7152*s, 0.0722 + 0.9278*s]));
}
function createSVGHueRotate(amount, channels)
{
	var fe = document.createElementNS(svgNS, 'feColorMatrix');
	fe.setAttribute('type', 'hueRotate');
	fe.setAttribute('values', amount);
	return createFilter(channels, fe);
}
function createSVGInvert(amount, channels)
{
	var fe = document.createElementNS(svgNS, 'feComponentTransfer');

	var tableValues = amount.toFixed(6) + ' ' + (1 - amount).toFixed(6);

	for (var [letter, flag] of channelMap)
		if ((channels & flag) === flag)
		{
			var feFunc = document.createElementNS(svgNS, 'feFunc' + letter);
			feFunc.setAttribute('type', 'table');
			feFunc.setAttribute('tableValues', tableValues);
			fe.appendChild(feFunc);
		}

	return createFilter(7, fe);
}
function createSVGSaturate(amount, channels)
{
	var fe = document.createElementNS(svgNS, 'feColorMatrix');
	fe.setAttribute('type', 'saturate');
	fe.setAttribute('values', amount.toFixed(6));
	return createFilter(channels, fe);
}
function createSVGSepia(amount, channels)
{
	var s = 1 - amount;

	return createFilter(7, createColorMatrix(channels,
		[0.393 + 0.607*s, 0.769 - 0.769*s, 0.189 - 0.189*s],
		[0.349 - 0.349*s, 0.686 + 0.314*s, 0.168 - 0.168*s],
		[0.272 - 0.272*s, 0.534 - 0.534*s, 0.131 + 0.869*s]));
}
function createSVGThreshold(amount, channels)
{
	var feFunc;

	var fe1 = document.createElementNS(svgNS, 'feComponentTransfer');
	var fe2 = document.createElementNS(svgNS, 'feComponentTransfer');

	amount = (-(amount - 1)/255).toFixed(6);

	for (var [letter, flag] of channelMap)
		if ((channels & flag) === flag)
		{
			feFunc = document.createElementNS(svgNS, 'feFunc' + letter);
			feFunc.setAttribute('type', 'linear');
			feFunc.setAttribute('intercept', amount);
			fe1.appendChild(feFunc);
			feFunc = document.createElementNS(svgNS, 'feFunc' + letter);
			feFunc.setAttribute('type', 'linear');
			feFunc.setAttribute('slope', '255');
			fe2.appendChild(feFunc);
		}

	return createFilter(7, fe1, fe2);
}
function createConvolveElement(kernel, order, inName, outName)
{
	var fe = document.createElementNS(svgNS, 'feConvolveMatrix');
	if (inName)
		fe.setAttribute('in', inName);
	if (outName)
		fe.setAttribute('result', outName);
	fe.setAttribute('preserveAlpha', 'true');
	fe.setAttribute('order', order);
	fe.setAttribute('kernelMatrix', kernel);
	return fe;
}
function addFilters(name1, name2, outName)
{
	var fe = document.createElementNS(svgNS, 'feComposite');
	if (name1)
		fe.setAttribute('in', name1);
	fe.setAttribute('in2', name2);
	if (outName)
		fe.setAttribute('result', outName);
	fe.setAttribute('operator', 'arithmetic');
	fe.setAttribute('k2', '1');
	fe.setAttribute('k3', '1');
	return fe;
}
function addConvolveFilters(feList, kernel1, kernel2, name1, name2, outName)
{
	feList.push(createConvolveElement(kernel2, '3 3', 'SourceGraphic', name2));
	feList.push(createConvolveElement(kernel1, '3 3', 'SourceGraphic', name1));
	feList.push(addFilters(name1, name2, outName));
	return feList;
}
function addConvolveReverse(feList, kernel, name2, name1)
{
	var reverseKernel = kernel.split(' ').reverse().join(' ');
	return addConvolveFilters(feList, kernel, reverseKernel, name1, name2, name1);
}
function addConvolutions(channels, kernelX, kernelY, abs)
{
	var feList = [];
	if (abs) {
		addConvolveReverse(feList, kernelX, 'x2', 'x');
		addConvolveReverse(feList, kernelY, 'y2', 'y');
		feList.push(addFilters('x', 'y'));
	} else
		addConvolveFilters(feList, kernelX, kernelY, 'x', 'y');

	return createFilter(channels, feList);
}
function createSVGConvolve(value, channels, abs)
{
	var convolution = Convolutions[value - 1].forSVG;

	if (typeof convolution === 'function')
		return convolution(channels, abs);
	if (abs)
		return createFilter(channels, addConvolveReverse([], convolution, 'c2'));

	return createFilter(channels, createConvolveElement(convolution, '3 3'));
}
function createSVGPolar(value, channels, edgeMode, reverse)
{
	var info = {
		radius: Polar.Radii[value],
		reverse: reverse ? true : false,
		width: divWidth,
		height: divHeight,
	};

	createPolarDisplacementMap(info);

	var fe, feList = [];

	fe = document.createElementNS(svgNS, 'feImage');
	fe.setAttributeNS(xlinkNS, 'href', info.url1);
	fe.setAttribute('result', 'map1');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feDisplacementMap');
	fe.setAttribute('in', 'SourceGraphic');
	fe.setAttribute('in2', 'map1');
	fe.setAttribute('scale', info.scale1);
	fe.setAttribute('xChannelSelector', 'R');
	fe.setAttribute('yChannelSelector', 'G');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feComposite');
	fe.setAttribute('in2', 'map1');
	fe.setAttribute('result', 'r1');
	fe.setAttribute('operator', 'in');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feImage');
	fe.setAttributeNS(xlinkNS, 'href', info.url2);
	fe.setAttribute('result', 'map2');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feDisplacementMap');
	fe.setAttribute('in', 'SourceGraphic');
	fe.setAttribute('in2', 'map2');
	fe.setAttribute('scale', info.scale2);
	fe.setAttribute('xChannelSelector', 'R');
	fe.setAttribute('yChannelSelector', 'G');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feComposite');
	fe.setAttribute('in2', 'map2');
	fe.setAttribute('result', 'r2');
	fe.setAttribute('operator', 'in');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feComposite');
	fe.setAttribute('in2', 'r1');
	feList.push(fe);

	var id = createFilter(channels, feList);
	addUserSpaceFilter(id, 0, []);
	return id;
}
function createSVGReversePolar(value, channels, edgeMode)
{
	return createSVGPolar(value, channels, edgeMode, true);
}
function dup(feList, mergeList, userSpace, result, f1, f2)
{
	var fe;
	var [x, y, w, h] = f1;

	fe = document.createElementNS(svgNS, 'feOffset');
	fe.setAttribute('in', 'SourceGraphic');
	if (x >= 0) fe.setAttribute('width', 1);
	if (y >= 0) fe.setAttribute('height', 1);
	feList.push(fe);

	f1.unshift(fe);
	setUserSpaceElement(f1);
	userSpace.push(f1);

	fe = document.createElementNS(svgNS, 'feTile');
	fe.setAttribute('result', result);
	feList.push(fe);

	f2.unshift(fe);
	setUserSpaceElement(f2);
	userSpace.push(f2);

	mergeList.push(result);
}
function dupTop(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupTop', [-1, 0, -1, -1], [-1, -1, -1, 2]);
}
function dupBottom(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupBottom', [-1, 2, -1, -1], [-1, 3, -1, 2]);
}
function dupLeft(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupLeft', [0, -1, -1, -1], [-1, -1, 2, -1]);
}
function dupRight(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupRight', [2, -1, -1, -1], [3, -1, 2, -1]);
}
function dupTopLeft(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupTopLeft', [0, 0, -1, -1], [-1, -1, 2, 2]);
}
function dupTopRight(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupTopRight', [2, 0, -1, -1], [3, -1, 2, 2]);
}
function dupBottomLeft(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupBottomLeft', [0, 2, -1, -1], [-1, 3, 2, 2]);
}
function dupBottomRight(feList, mergeList, userSpace)
{
	dup(feList, mergeList, userSpace, 'dupBottomRight', [2, 2, -1, -1], [3, 3, 2, 2]);
}
function createMerge(feList, mergeList, userSpaceElements)
{
	var fe = document.createElementNS(svgNS, 'feOffset');
	fe.setAttribute('in', 'SourceGraphic');
	fe.setAttribute('result', 'image');
	feList.push(fe);

	fe = [fe, 0, 0, 0, 0];
	setUserSpaceElement(fe);
	userSpaceElements.push(fe);
	mergeList.push('image');

	var feMerge = document.createElementNS(svgNS, 'feMerge');

	for (var inName of mergeList)
	{
		var feMergeNode = document.createElementNS(svgNS, 'feMergeNode');
		feMergeNode.setAttribute('in', inName);
		feMerge.appendChild(feMergeNode);
	}

	feList.push(feMerge);
}
function createSVGDBlur(radius, channels, edgeMode, isX)
{
	var isLeft, targetAttribute, targetValue, order;

	if (radius < 0) {
		isLeft = true;
		radius = -radius;
		targetValue = radius;
	} else {
		isLeft = false;
		targetValue = 0;
	}
	if (isX) {
		targetAttribute = 'targetX';
		order = (radius + 1) + ' 1';
	} else {
		targetAttribute = 'targetY';
		order = '1 ' + (radius + 1);
	}

	var fe, feList = [], userSpaceElements = [];

	if (edgeMode === 'duplicate' || edgeMode === 'mirror')
	{
		var mergeList = [];

		(isX ? (isLeft ? dupLeft : dupRight)
			: (isLeft ? dupTop : dupBottom))(feList, mergeList, userSpaceElements);

		createMerge(feList, mergeList, userSpaceElements);
	}
	else if (edgeMode === 'wrap')
	{
		fe = document.createElementNS(svgNS, 'feOffset');
		feList.push(fe);

		fe = [fe, 0, 0, 0, 0];
		setUserSpaceElement(fe);
		userSpaceElements.push(fe);

		fe = document.createElementNS(svgNS, 'feTile');
		feList.push(fe);
	}

	var kernel = [1];
	for (var i = 0; i < radius; ++i) kernel.push(1);
	kernel = kernel.join(' ');

	for (var i = 0; i < 3; ++i)
	{
		fe = document.createElementNS(svgNS, 'feConvolveMatrix');
		fe.setAttribute('preserveAlpha', 'true');
		fe.setAttribute('order', order);
		fe.setAttribute('kernelMatrix', kernel);
		fe.setAttribute(targetAttribute, targetValue);
		if (edgeMode === 'duplicate' || edgeMode === 'wrap' || edgeMode === 'none')
			fe.setAttribute('edgeMode', edgeMode);
		feList.push(fe);
	}

	var id = createFilter(channels, feList);
	if (userSpaceElements.length > 0)
		addUserSpaceFilter(id, 1, userSpaceElements);
	return id;
}
function createSVGDBlurX(radius, channels, edgeMode)
{
	return createSVGDBlur(radius, channels, edgeMode, true);
}
function createSVGDBlurY(radius, channels, edgeMode)
{
	return createSVGDBlur(radius, channels, edgeMode, false);
}
function createGaussianBlur(xRadius, yRadius, channels, edgeMode)
{
	var fe, feList = [], userSpaceElements = [];

	if (edgeMode === 'duplicate' || edgeMode === 'mirror')
	{
		var mergeList = [];
		if (xRadius > 0) {
			dupLeft(feList, mergeList, userSpaceElements);
			dupRight(feList, mergeList, userSpaceElements);
		}
		if (yRadius > 0) {
			dupTop(feList, mergeList, userSpaceElements);
			dupBottom(feList, mergeList, userSpaceElements);
		}
		if (xRadius > 0 && yRadius > 0) {
			dupTopLeft(feList, mergeList, userSpaceElements);
			dupTopRight(feList, mergeList, userSpaceElements);
			dupBottomLeft(feList, mergeList, userSpaceElements);
			dupBottomRight(feList, mergeList, userSpaceElements);
		}
		createMerge(feList, mergeList, userSpaceElements);
	}
	else if (edgeMode === 'wrap')
	{
		fe = document.createElementNS(svgNS, 'feOffset');
		feList.push(fe);

		fe = [fe, 0, 0, 0, 0];
		setUserSpaceElement(fe);
		userSpaceElements.push(fe);

		fe = document.createElementNS(svgNS, 'feTile');
		feList.push(fe);
	}

	fe = document.createElementNS(svgNS, 'feGaussianBlur');
	fe.setAttribute('stdDeviation', xRadius + ' ' + yRadius);
	if (edgeMode === 'duplicate' || edgeMode === 'wrap' || edgeMode === 'none')
		fe.setAttribute('edgeMode', edgeMode);
	feList.push(fe);

	var id = createFilter(channels, feList);
	if (userSpaceElements.length > 0)
		addUserSpaceFilter(id, 1, userSpaceElements);
	return id;
}
function createBlurXFilter(xRadius, channels, edgeMode)
{
	return createGaussianBlur(xRadius, 0, channels, edgeMode);
}
function createBlurYFilter(yRadius, channels, edgeMode)
{
	return createGaussianBlur(0, yRadius, channels, edgeMode);
}
function createBlurFilter(radius, channels, edgeMode)
{
	return createGaussianBlur(radius, radius, channels, edgeMode);
}
function createTiltShift(blurRadius, channels)
{
	var maskSVG =
		'<svg xmlns="http://www.w3.org/2000/svg"' +
			' width="100" height="100" viewBox="0 0 100 100">' +
		'<defs>' +
		'<linearGradient id="gradient" x2="0%" y2="100%">' +
			'<stop offset="20%" stop-color="black" stop-opacity="1"></stop>' +
			'<stop offset="50%" stop-color="black" stop-opacity="0"></stop>' +
			'<stop offset="80%" stop-color="black" stop-opacity="1"></stop>' +
		'</linearGradient>' +
		'</defs>' +
		'<rect x="0%" y="0%" width="100%" height="100%" fill="url(#gradient)"></rect>' +
		'</svg>';

	var maskURI = 'data:image/svg+xml;charset=utf-8,' + encodeURIComponent(maskSVG);

	var fe, feList = [];
	var mergeList = [], userSpaceElements = [];

	dupTop(feList, mergeList, userSpaceElements);
	dupLeft(feList, mergeList, userSpaceElements);
	dupRight(feList, mergeList, userSpaceElements);
	dupBottom(feList, mergeList, userSpaceElements);
	dupTopLeft(feList, mergeList, userSpaceElements);
	dupTopRight(feList, mergeList, userSpaceElements);
	dupBottomLeft(feList, mergeList, userSpaceElements);
	dupBottomRight(feList, mergeList, userSpaceElements);
	createMerge(feList, mergeList, userSpaceElements);

	fe = document.createElementNS(svgNS, 'feGaussianBlur');
	fe.setAttribute('stdDeviation', blurRadius);
	fe.setAttribute('edgeMode', 'duplicate');
	fe.setAttribute('result', 'blur');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feImage');
	fe.setAttributeNS(xlinkNS, 'href', maskURI);
	fe.setAttribute('preserveAspectRatio', 'none');
	fe.setAttribute('result', 'mask');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feComposite');
	fe.setAttribute('in', 'blur');
	fe.setAttribute('in2', 'mask');
	fe.setAttribute('operator', 'in');
	feList.push(fe);

	fe = document.createElementNS(svgNS, 'feComposite');
	fe.setAttribute('in2', 'SourceGraphic');
	feList.push(fe);

	var id = createFilter(channels, feList);
	addUserSpaceFilter(id, 1, userSpaceElements);
	return id;
}
function svgCannotImplement(amount, channels)
{
	return -1;
}
var BlurFlags = {
	xDirectional: 0b00000001,
	yDirectional: 0b00000010,
};
function boxBlur(blurInfo, radiusType)
{
	var leftRadius = blurInfo[radiusType + 'Left'];
	var rightRadius = blurInfo[radiusType + 'Right'];

	var size = leftRadius + rightRadius + 1;
	if (size < 2) return;

	var inData = blurInfo.inData;
	var src = inData.data;
	var d = blurInfo.outData.data;

	var width = inData.width;
	var height = inData.height;

	// delta = the number of data array elements to skip to get to the next pixel in the X direction
	// vDelta = the number of data array elements to skip to get to the next pixel in the Y direction

	var delta = 4;
	var vDelta = delta * width;

	if (radiusType.charAt(0) === 'y') {
		[width, height] = [height, width]; // Swap width and height
		[delta, vDelta] = [vDelta, delta]; // Swap delta and vDelta
	}

	var zDelta = (width - 1) * delta;
	vDelta -= zDelta + delta;
	width -= size;
	if (width < 0) return;

	var edgeMode = blurInfo.edgeMode;
	var blurR = blurInfo.blurR;
	var blurG = blurInfo.blurG;
	var blurB = blurInfo.blurB;
	var blurA = blurInfo.blurA;

	var edge = src;

	var eFirst      = 0;
	var eLast       = 0;
	var eFirstStart = 0;
	var eLastStart  = 0;
	var eDelta      = 0;

	if (edgeMode === 0) // "black" or "none"
	{
		edge = [0, 0, 0, 0];
	}
	else if (edgeMode === 1) // "tile" or "wrap"
	{
		eFirstStart = zDelta - (leftRadius - 1) * delta;
		eDelta = delta;
	}
	else if (edgeMode === 2) // "edge" or "duplicate"
	{
		eLastStart = zDelta;
	}
	else if (edgeMode === 3) // "mirror"
	{
		eFirstStart = (leftRadius - 1) * delta;
		eLastStart = zDelta;
		eDelta = -delta;
	}

	var i = 0;
	for (var y = 0; y < height; ++y) {
		var j = i;
		var k = i;

		var sumR = 0;
		var sumG = 0;
		var sumB = 0;
		var sumA = 0;

		if (edgeMode !== 0) {
			eFirst = i + eFirstStart;
			eLast = i + eLastStart;
		}
		var eFirstSaved = eFirst;
		for (var x = 0; x < leftRadius; ++x) {
			sumR += edge[eFirst  ];
			sumG += edge[eFirst+1];
			sumB += edge[eFirst+2];
			sumA += edge[eFirst+3];
			eFirst += eDelta;
		}
		eFirst = eFirstSaved;
		for (var x = 0; x <= rightRadius; ++x) {
			sumR += src[k  ];
			sumG += src[k+1];
			sumB += src[k+2];
			sumA += src[k+3];
			k += delta;
		}
		if (blurR) d[i  ] = sumR / size;
		if (blurG) d[i+1] = sumG / size;
		if (blurB) d[i+2] = sumB / size;
		if (blurA) d[i+3] = sumA / size;
		i += delta;
		for (var x = 0; x < leftRadius; ++x) {
			if (blurR) { sumR += src[k  ] - edge[eFirst  ]; d[i  ] = sumR / size; }
			if (blurG) { sumG += src[k+1] - edge[eFirst+1]; d[i+1] = sumG / size; }
			if (blurB) { sumB += src[k+2] - edge[eFirst+2]; d[i+2] = sumB / size; }
			if (blurA) { sumA += src[k+3] - edge[eFirst+3]; d[i+3] = sumA / size; }
			k += delta;
			i += delta;
			eFirst += eDelta;
		}
		for (var x = width; x > 0; --x) {
			if (blurR) { sumR += src[k  ] - src[j  ]; d[i  ] = sumR / size; }
			if (blurG) { sumG += src[k+1] - src[j+1]; d[i+1] = sumG / size; }
			if (blurB) { sumB += src[k+2] - src[j+2]; d[i+2] = sumB / size; }
			if (blurA) { sumA += src[k+3] - src[j+3]; d[i+3] = sumA / size; }
			j += delta;
			k += delta;
			i += delta;
		}
		for (var x = 0; x < rightRadius; ++x) {
			if (blurR) { sumR += edge[eLast  ] - src[j  ]; d[i  ] = sumR / size; }
			if (blurG) { sumG += edge[eLast+1] - src[j+1]; d[i+1] = sumG / size; }
			if (blurB) { sumB += edge[eLast+2] - src[j+2]; d[i+2] = sumB / size; }
			if (blurA) { sumA += edge[eLast+3] - src[j+3]; d[i+3] = sumA / size; }
			j += delta;
			i += delta;
			eLast += eDelta;
		}
		i += vDelta;
	}

	blurInfo.inData = blurInfo.outData;
	blurInfo.outData = inData;
}
function printBlurRadii(blurInfo)
{
	var prefixes = ['xRadius', 'yRadius'];
	var suffixes = ['1Left', '1Right', '2Left', '2Right', '3Left', '3Right'];

	for (var prefix of prefixes)
		for (var suffix of suffixes)
			console.log(prefix + suffix + " = " + blurInfo[prefix + suffix]);
}
function getBoxBlurSizes1(blurInfo, radiusType)
{
	// This function determines the sizes for 3 successive box blurs according to
	// https://www.w3.org/TR/filter-effects-1/#feGaussianBlurElement

	var radius = blurInfo[radiusType];

	var boxBlurSize = Math.floor(radius * 3 * Math.sqrt(2 * Math.PI) / 4 + 0.5);

	var suffixes = ['1Left', '1Right', '2Left', '2Right', '3Left', '3Right'];

	if ((boxBlurSize & 1) === 1) {
		// If boxBlurSize is odd:
		// Use three box blurs of size boxBlurSize centered on the output pixel.

		radius = (boxBlurSize - 1) / 2;

		for (var suffix of suffixes)
			blurInfo[radiusType + suffix] = radius;
	} else {
		// If boxBlurSize is even:
		// Use two box blurs of size boxBlurSize (the first one centered on the pixel boundary
		// between the output pixel and the one to the left, the second one centered on the
		// pixel boundary between the output pixel and the one to the right) and one box blur
		// of size boxBlurSize+1 centered on the output pixel.

		radius = boxBlurSize / 2;

		blurInfo[radiusType + '1Left' ] = radius;
		blurInfo[radiusType + '1Right'] = radius - 1;
		blurInfo[radiusType + '2Left' ] = radius - 1;
		blurInfo[radiusType + '2Right'] = radius;
		blurInfo[radiusType + '3Left' ] = radius;
		blurInfo[radiusType + '3Right'] = radius;
	}
}
function getBoxBlurSizes2(blurInfo, radiusType)
{
	// This function determines the sizes for 3 successive box blurs according to
	// http://www.peterkovesi.com/papers/FastGaussianSmoothing.pdf

	var radius = blurInfo[radiusType];

	var n = 3;
	var w = Math.floor(Math.sqrt(12*radius*radius/n + 1));

	if ((w & 1) === 0) w -= 1; // If w is even, subtract 1 to make it odd.

	var m = Math.round((12*radius*radius - n*w*w - 4*n*w - 3*n) / (-4*w - 4));

	radius = (w - 1) / 2;

	var i = 1;
	for (; i <= m; ++i) {
		blurInfo[radiusType + i + 'Left'] = radius;
		blurInfo[radiusType + i + 'Right'] = radius;
	}
	for (; i <= n; ++i) {
		blurInfo[radiusType + i + 'Left'] = radius + 1;
		blurInfo[radiusType + i + 'Right'] = radius + 1;
	}
}
function getBoxBlurSizes(blurInfo, radiusType)
{
	var directional = (blurInfo.flags & BlurFlags[radiusType + 'Directional']) !== 0;

	radiusType += 'Radius';

	if (!directional) {
		getBoxBlurSizes1(blurInfo, radiusType);
		return;
	}

	var radius = blurInfo[radiusType];
	var radiusLeft = 0;
	var radiusRight = 0;

	if (radius < 0)
		radiusLeft = -radius;
	else
		radiusRight = radius;

	for (var i = 1; i <= 3; ++i) {
		blurInfo[radiusType + i + 'Left'] = radiusLeft;
		blurInfo[radiusType + i + 'Right'] = radiusRight;
	}
}
function copyUnchangedData(blurInfo)
{
	var copyR = !blurInfo.blurR;
	var copyG = !blurInfo.blurG;
	var copyB = !blurInfo.blurB;
	var copyA = !blurInfo.blurA;

	var src = blurInfo.outData.data;
	var d = blurInfo.inData.data;

	for (var i = 0; i < d.length; i += 4)
	{
		if (copyR) d[i  ] = src[i  ];
		if (copyG) d[i+1] = src[i+1];
		if (copyB) d[i+2] = src[i+2];
		if (copyA) d[i+3] = src[i+3];
	}
}
function blur(blurInfo)
{
	getBoxBlurSizes(blurInfo, 'x');
	getBoxBlurSizes(blurInfo, 'y');

	boxBlur(blurInfo, 'xRadius1');
	boxBlur(blurInfo, 'yRadius1');

	boxBlur(blurInfo, 'xRadius2');
	boxBlur(blurInfo, 'yRadius2');

	boxBlur(blurInfo, 'xRadius3');
	boxBlur(blurInfo, 'yRadius3');

	if (!blurInfo.blurAll && blurInfo.inData === blurInfo.newData)
		copyUnchangedData(blurInfo);

	return blurInfo.inData;
}
function BlurInfo(context, inData, xRadius, yRadius, channels, edgeMode, flags)
{
	this.inData = inData;
	this.outData = context.createImageData(inData);
	this.newData = this.outData;

	this.xRadius = xRadius;
	this.yRadius = yRadius;
	this.flags = flags;

	if (edgeMode === 'black' || edgeMode === 'none')
		this.edgeMode = 0;
	else if (edgeMode === 'tile' || edgeMode === 'wrap')
		this.edgeMode = 1;
	else if (edgeMode === 'mirror')
		this.edgeMode = 3;
	else // (edgeMode === 'edge' || edgeMode === 'duplicate')
		this.edgeMode = 2;

	this.blurR = false;
	this.blurG = false;
	this.blurB = false;
	this.blurA = false;

	if (typeof channels === 'number') {
		if ((channels & 1) === 1) this.blurR = true;
		if ((channels & 2) === 2) this.blurG = true;
		if ((channels & 4) === 4) this.blurB = true;
		if ((channels & 8) === 8) this.blurA = true;
	} else if (typeof channels === 'string') {
		for (var channel of channels)
			switch (channel) {
				case 'A': this.blurA = true; break;
				case 'B': this.blurB = true; break;
				case 'G': this.blurG = true; break;
				case 'R': this.blurR = true; break;
			}
	} else if (typeof channels === 'undefined') {
		this.blurR = true;
		this.blurG = true;
		this.blurB = true;
	}

	this.blurAll = this.blurR && this.blurG && this.blurB && this.blurA;
}
function applyBlur(context, imageData, xRadius, yRadius, channels, edgeMode, flags)
{
	var blurInfo = new BlurInfo(context, imageData, xRadius, yRadius, channels, edgeMode, flags);

	return blur(blurInfo);
}
function applyBlurFilter(context, imageData, radius, channels, edgeMode)
{
	return applyBlur(context, imageData, radius, radius, channels, edgeMode, 0);
}
function applyBlurXFilter(context, imageData, radius, channels, edgeMode)
{
	return applyBlur(context, imageData, radius, 0, channels, edgeMode, 0);
}
function applyBlurYFilter(context, imageData, radius, channels, edgeMode)
{
	return applyBlur(context, imageData, 0, radius, channels, edgeMode, 0);
}
function applyDBlurX(context, imageData, radius, channels, edgeMode)
{
	return applyBlur(context, imageData, radius, 0, channels, edgeMode, BlurFlags.xDirectional);
}
function applyDBlurY(context, imageData, radius, channels, edgeMode)
{
	return applyBlur(context, imageData, 0, radius, channels, edgeMode, BlurFlags.yDirectional);
}
var Polar = {
	RadiusHalfDiagonal: function(w,h) {return Math.sqrt(w*w + h*h)/2;},
	RadiusHalfWidth:    function(w,h) {return w/2;},
	RadiusHalfHeight:   function(w,h) {return h/2;},
	RadiusHeight:       function(w,h) {return h;},
	EdgeBlack:          new Uint8ClampedArray([0, 0, 0, 255]),
	EdgeTransparent:    new Uint8ClampedArray([0, 0, 0, 0]),
	EdgeDuplicate:      null,
};
Polar.Radii = [
	Polar.RadiusHalfDiagonal,
	Polar.RadiusHalfWidth,
	Polar.RadiusHalfHeight,
	Polar.RadiusHeight,
];
Polar.EdgeModes = [
	Polar.EdgeDuplicate,
	Polar.EdgeBlack,
	Polar.EdgeTransparent,
];
function setChannelFlags(info, channels)
{
	info.setR = false;
	info.setG = false;
	info.setB = false;
	info.setA = true;

	if (typeof channels === 'number') {
		if ((channels & 1) === 1) info.setR = true;
		if ((channels & 2) === 2) info.setG = true;
		if ((channels & 4) === 4) info.setB = true;
		if ((channels & 8) === 8) info.setA = true;
	} else if (typeof channels === 'string') {
		for (var channel of channels)
			switch (channel) {
				case 'A': info.setA = true; break;
				case 'B': info.setB = true; break;
				case 'G': info.setG = true; break;
				case 'R': info.setR = true; break;
			}
	} else if (typeof channels === 'undefined') {
		info.setR = true;
		info.setG = true;
		info.setB = true;
		info.setA = true;
	}
}
var polarMapCache = {};
function createPolarDisplacementMap(info)
{
	var width = info.width;
	var height = info.height;
	info.scale1 = 2 * Math.max(width, height);
	info.scale2 = info.scale1 / 3;
	var scale1 = info.scale1;
	var scale2 = info.scale2;
	var halfScale2 = scale2 / 2;

	var reverse = (typeof info.reverse === 'boolean') ? info.reverse : false;
	var radius = ((typeof info.radius === 'function') ? info.radius : Polar.RadiusHalfDiagonal)(width, height);
	var radiusScale = radius / height;

	var minAngle = -180 * Math.PI/180;
	var maxAngle =  180 * Math.PI/180;
	var angleScale = (maxAngle - minAngle) / (width - 1);

	var cacheKey = [width, height, radius, reverse].join('_');
	var cachedInfo = polarMapCache[cacheKey];
	if (cachedInfo) {
		info.url1 = cachedInfo.url1;
		info.url2 = cachedInfo.url2;
		return;
	}

	var hiddenCanvas = document.createElement("canvas");
	hiddenCanvas.width = width;
	hiddenCanvas.height = height;

	var context = hiddenCanvas.getContext("2d");
	var map1 = context.createImageData(width, height);
	var map2 = context.createImageData(width, height);
	var map1Data = map1.data;
	var map2Data = map2.data;

	var centerX = Math.round(width / 2);
	var centerY = Math.round(height / 2);

	var x, y, hypot, angle;
	var scale, d, d2, di = 0;

	for (var j = 0; j < height; ++j)
		for (var i = 0; i < width; ++i)
		{
			if (reverse) {
				var deltaY = j - centerY;
				var deltaX = i - centerX;

				hypot = Math.sqrt(deltaX*deltaX + deltaY*deltaY);
				angle = Math.atan2(deltaY, deltaX);

				y = Math.round(hypot / radiusScale);
				x = Math.round((angle - minAngle) / angleScale);
			} else {
				hypot = j * radiusScale;
				angle = minAngle + i * angleScale;

				x = centerX + Math.round(hypot * Math.cos(angle));
				y = centerY + Math.round(hypot * Math.sin(angle));
			}

			var edge = false;
			if (x < 0) {
				edge = true; x = 0;
			} else if (x >= width) {
				edge = true; x = width - 1;
			}
			if (y < 0) {
				edge = true; y = 0;
			} else if (y >= height) {
				edge = true; y = height - 1;
			}

			if (Math.abs(x - i) < halfScale2 && Math.abs(y - j) < halfScale2) {
				d = map2Data;
				d2 = map1Data;
				scale = scale2;
			} else {
				d = map1Data;
				d2 = map2Data;
				scale = scale1;
			}

			d[di  ] = 255 * ((x - i)/scale + 0.5);
			d[di+1] = 255 * ((y - j)/scale + 0.5);
			d[di+2] = 0;
			d[di+3] = 255;

			d2[di  ] = 128;
			d2[di+1] = 128;
			d2[di+2] = 0;
			d2[di+3] = 0;

			x = Math.round(i + scale * (d[di  ]/255 - 0.5));
			y = Math.round(j + scale * (d[di+1]/255 - 0.5));

			if (x < 0) d[di  ] += 1; else if (x >= width)  d[di  ] -= 1;
			if (y < 0) d[di+1] += 1; else if (y >= height) d[di+1] -= 1;

			di += 4;
		}

	context.putImageData(map1, 0, 0);
	info.url1 = hiddenCanvas.toDataURL("image/png");

	context.putImageData(map2, 0, 0);
	info.url2 = hiddenCanvas.toDataURL("image/png");

	polarMapCache[cacheKey] = info;
}
function polarTransform(context, inData, channels, info)
{
	if (info === undefined)
		info = {};

	var width = inData.width;
	var height = inData.height;

	var reverse = (typeof info.reverse === 'boolean') ? info.reverse : false;
	var radius = ((typeof info.radius === 'function') ? info.radius : Polar.RadiusHalfDiagonal)(width, height);
	var radiusScale = radius / height;

	var edgePixel = (info.edgePixel instanceof Uint8ClampedArray
		&& info.edgePixel.length === 4) ? info.edgePixel : null;

	// Multiply degrees by pi/180 to convert to radians.
	// Note that when doing a reverse polar transform, Math.atan2() will always return an angle
	// between -pi and pi (-180 and 180 degrees). Thus minAngle should be >= -180, and maxAngle
	// should be <= 180.

	var minAngle = (typeof info.minAngle === 'number' ? info.minAngle : -180) * Math.PI/180;
	var maxAngle = (typeof info.maxAngle === 'number' ? info.maxAngle :  180) * Math.PI/180;
	var angleScale = (maxAngle - minAngle) / (width - 1);

	var centerX = Math.round(width / 2);
	var centerY = Math.round(height / 2);

	var outData = context.createImageData(inData);
	var s = inData.data;
	var d = outData.data;

	setChannelFlags(info, channels);
	var setR = info.setR;
	var setG = info.setG;
	var setB = info.setB;
	var setA = info.setA;

	var x, y, hypot, angle;

	for (var j = 0; j < height; ++j)
		for (var i = 0; i < width; ++i)
		{
			if (reverse) {
				var deltaY = j - centerY;
				var deltaX = i - centerX;

				hypot = Math.sqrt(deltaX*deltaX + deltaY*deltaY);
				angle = Math.atan2(deltaY, deltaX);

				y = Math.round(hypot / radiusScale);
				x = Math.round((angle - minAngle) / angleScale);
			} else {
				hypot = j * radiusScale;
				angle = minAngle + i * angleScale;

				x = centerX + Math.round(hypot * Math.cos(angle));
				y = centerY + Math.round(hypot * Math.sin(angle));
			}

			var di = (j * width + i) * 4;

			var edge = false;
			if (x < 0) {
				edge = true; x = 0;
			} else if (x >= width) {
				edge = true; x = width - 1;
			}
			if (y < 0) {
				edge = true; y = 0;
			} else if (y >= height) {
				edge = true; y = height - 1;
			}

			if (edge && edgePixel !== null) {
				d[di  ] = setR ? edgePixel[0] : s[di  ];
				d[di+1] = setG ? edgePixel[1] : s[di+1];
				d[di+2] = setB ? edgePixel[2] : s[di+2];
				d[di+3] = setA ? edgePixel[3] : s[di+3];
			} else {
				var si = (y * width + x) * 4;
				d[di  ] = setR ? s[si  ] : s[di  ];
				d[di+1] = setG ? s[si+1] : s[di+1];
				d[di+2] = setB ? s[si+2] : s[di+2];
				d[di+3] = setA ? s[si+3] : s[di+3];
			}
		}

	return outData;
}
function applyPolarTransform(context, imageData, value, channels, edgeMode)
{
	var info = {
		radius: Polar.Radii[value],
		edgePixel: Polar.EdgeModes[edgeMode],
	};
	return polarTransform(context, imageData, channels, info);
}
function applyReversePolarTransform(context, imageData, value, channels, edgeMode)
{
	var info = {
		reverse: true,
		radius: Polar.Radii[value],
		edgePixel: Polar.EdgeModes[edgeMode],
	};
	return polarTransform(context, imageData, channels, info);
}
function applyFilterMatrix(d, channels, a0, a1, a2)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	var dLen = d.length;
	for (var i = 0; i < dLen; i += 4)
	{
		var r = d[i];
		var g = d[i + 1];
		var b = d[i + 2];

		if (setR) d[i]     = a0[0] * r + a0[1] * g + a0[2] * b;
		if (setG) d[i + 1] = a1[0] * r + a1[1] * g + a1[2] * b;
		if (setB) d[i + 2] = a2[0] * r + a2[1] * g + a2[2] * b;
	}
}
function applyBrightnessFilter(d, amount, channels)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	var dLen = d.length;
	for (var i = 0; i < dLen; i += 4)
	{
		if (setR) d[i]     *= amount;
		if (setG) d[i + 1] *= amount;
		if (setB) d[i + 2] *= amount;
	}
}
function applyContrastFilter(d, amount, channels)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	// V' = C * (V - 0.5) + 0.5
	// where C = amount of contrast, V = current channel value, and V' = new channel value
	// Thus V' = V*C + 0.5 - 0.5*C

	var intercept = 255 * (0.5 - 0.5 * amount);

	var dLen = d.length;
	for (var i = 0; i < dLen; i += 4)
	{
		if (setR) d[i]     = d[i]     * amount + intercept;
		if (setG) d[i + 1] = d[i + 1] * amount + intercept;
		if (setB) d[i + 2] = d[i + 2] * amount + intercept;
	}
}
function applyGrayscaleFilter(d, amount, channels)
{
	var s = 1 - amount;

	applyFilterMatrix(d, channels,
		[0.2126 + 0.7874*s, 0.7152 - 0.7152*s, 0.0722 - 0.0722*s],
		[0.2126 - 0.2126*s, 0.7152 + 0.2848*s, 0.0722 - 0.0722*s],
		[0.2126 - 0.2126*s, 0.7152 - 0.7152*s, 0.0722 + 0.9278*s]);
}
function applyHueRotateFilter(d, amount, channels)
{
	amount *= Math.PI / 180; // Convert degrees to radians

	var c = Math.cos(amount);
	var s = Math.sin(amount);

	applyFilterMatrix(d, channels,
		[0.213 + 0.787*c - 0.213*s, 0.715 - 0.715*c - 0.715*s, 0.072 - 0.072*c + 0.928*s],
		[0.213 - 0.213*c + 0.143*s, 0.715 + 0.285*c + 0.140*s, 0.072 - 0.072*c - 0.283*s],
		[0.213 - 0.213*c - 0.787*s, 0.715 - 0.715*c + 0.715*s, 0.072 + 0.928*c + 0.072*s]);
}
function applyInvertFilter(d, amount, channels)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	var m = 1.0 - amount - amount;
	var c = 255 * amount;

	var dLen = d.length;
	for (var i = 0; i < dLen; i += 4)
	{
		if (setR) d[i]     = d[i]     * m + c;
		if (setG) d[i + 1] = d[i + 1] * m + c;
		if (setB) d[i + 2] = d[i + 2] * m + c;
	}
}
function applySaturateFilter(d, amount, channels)
{
	var s = amount;

	applyFilterMatrix(d, channels,
		[0.213 + 0.787*s, 0.715 - 0.715*s, 0.072 - 0.072*s],
		[0.213 - 0.213*s, 0.715 + 0.285*s, 0.072 - 0.072*s],
		[0.213 - 0.213*s, 0.715 - 0.715*s, 0.072 + 0.928*s]);
}
function applySepiaFilter(d, amount, channels)
{
	var s = 1 - amount;

	applyFilterMatrix(d, channels,
		[0.393 + 0.607*s, 0.769 - 0.769*s, 0.189 - 0.189*s],
		[0.349 - 0.349*s, 0.686 + 0.314*s, 0.168 - 0.168*s],
		[0.272 - 0.272*s, 0.534 - 0.534*s, 0.131 + 0.869*s]);
}
function applyThreshold(d, amount, channels)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	var dLen = d.length;
	for (var i = 0; i < dLen; i += 4)
	{
		if (setR) d[i]     = (d[i    ] < amount ? 0 : 255);
		if (setG) d[i + 1] = (d[i + 1] < amount ? 0 : 255);
		if (setB) d[i + 2] = (d[i + 2] < amount ? 0 : 255);
	}
}
function convolve3x3(context, inData, channels, kernel, abs)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	var outData = context.createImageData(inData);
	var s = inData.data;
	var d = outData.data;

	var width = inData.width;
	var height = inData.height;

	sumOfWeights = 0;
	for (var weight of kernel)
		sumOfWeights += weight;
	if (sumOfWeights === 0)
		sumOfWeights = 1;

	// edgeMode is 'duplicate'

	var yDelta = width * 4;
	var i0, i1, i2, i3, i5, i6, i7, i8;

	var k0 = kernel[0], k1 = kernel[1], k2 = kernel[2];
	var k3 = kernel[3], k4 = kernel[4], k5 = kernel[5];
	var k6 = kernel[6], k7 = kernel[7], k8 = kernel[8];

	var i = 0;
	for (var y = 0; y < height; ++y)
	{
		var yUp = y === 0 ? 0 : -yDelta;
		var yDn = y === height - 1 ? 0 : yDelta;

		for (var x = 0; x < width; ++x)
		{
			var xLft = x === 0 ? 0 : -4;
			var xRgt = x === width - 1 ? 0 : 4;
/*
	"The values in the kernel matrix are applied such that the kernel matrix is rotated 180 degrees
	relative to the source and destination images in order to match convolution theory as described
	in many computer graphics textbooks."
	(https://www.w3.org/TR/filter-effects-1/#feConvolveMatrixElement)
*/
			// 8 7 6
			// 5 4 3
			// 2 1 0

			i7 = i + yUp;
			i8 = i7 + xLft;
			i6 = i7 + xRgt;
			i5 = i + xLft;
			i3 = i + xRgt;
			i1 = i + yDn;
			i2 = i1 + xLft;
			i0 = i1 + xRgt;

			var r = k8*s[i8] + k7*s[i7] + k6*s[i6] +
				k5*s[i5] + k4*s[i ] + k3*s[i3] +
				k2*s[i2] + k1*s[i1] + k0*s[i0];
			var g = k8*s[i8+1] + k7*s[i7+1] + k6*s[i6+1] +
				k5*s[i5+1] + k4*s[i +1] + k3*s[i3+1] +
				k2*s[i2+1] + k1*s[i1+1] + k0*s[i0+1];
			var b = k8*s[i8+2] + k7*s[i7+2] + k6*s[i6+2] +
				k5*s[i5+2] + k4*s[i +2] + k3*s[i3+2] +
				k2*s[i2+2] + k1*s[i1+2] + k0*s[i0+2];
			if (abs) {
				r = Math.abs(r);
				g = Math.abs(g);
				b = Math.abs(b);
			}
			d[i  ] = setR ? r : s[i  ];
			d[i+1] = setG ? g : s[i+1];
			d[i+2] = setB ? b : s[i+2];
			d[i+3] = s[i+3];
			i += 4;
		}
	}

	return outData;
}
function addImages(image1, image2, channels)
{
	var setR = ((channels & 1) === 1);
	var setG = ((channels & 2) === 2);
	var setB = ((channels & 4) === 4);

	var d1 = image1.data;
	var d2 = image2.data;
	var dLen = d1.length;

	for (var i = 0; i < dLen; i += 4)
	{
		if (setR) d2[i]     += d1[i];
		if (setG) d2[i + 1] += d1[i + 1];
		if (setB) d2[i + 2] += d1[i + 2];
	}

	return image2;
}
function reverseIsOpposite(kernel)
{
	var i = 0, j = kernel.length - 1;

	for (; i <= j; ++i, --j)
		if (kernel[i] !== -kernel[j]) return false;

	return true;
}
function Convolution(name, kernel)
{
	this.name = name;
	if (kernel !== undefined) {
		this.forCanvas = kernel;
		this.forSVG = kernel.join(' ');
		this.allowAbs = reverseIsOpposite(kernel);
	}
}
var Convolutions = [
new Convolution('sharpen',       [ 0, -1,  0, -1,  5, -1,  0, -1,  0]),
new Convolution('sobel x+y'),
new Convolution('sobel x',       [-1,  0,  1, -2,  0,  2, -1,  0,  1]),
new Convolution('sobel y',       [-1, -2, -1,  0,  0,  0,  1,  2,  1]),
new Convolution('prewitt x+y'),
new Convolution('prewitt x',     [-1,  0,  1, -1,  0,  1, -1,  0,  1]),
new Convolution('prewitt y',     [-1, -1, -1,  0,  0,  0,  1,  1,  1]),
new Convolution('edge detect 1', [-1, -1, -1, -1,  8, -1, -1, -1, -1]),
new Convolution('edge detect 2', [ 0,  1,  0,  1, -4,  1,  0,  1,  0]),
new Convolution('emboss 1',      [ 1,  0,  0,  0,  0,  0,  0,  0, -1]),
new Convolution('emboss 2',      [-2, -1,  0, -1,  1,  1,  0,  1,  2]),
new Convolution('emboss 3',      [-2, -2,  0, -2,  6,  0,  0,  0,  0]),
];
function createXYConvolutionFunctions(i)
{
	var c = Convolutions[i];
	var cx = Convolutions[i + 1];
	var cy = Convolutions[i + 2];

	c.forCanvas = function(context, imageData, channels, abs)
	{
		var gX = convolve3x3(context, imageData, channels, cx.forCanvas, abs);
		var gY = convolve3x3(context, imageData, channels, cy.forCanvas, abs);
		return addImages(gX, gY, channels);
	}
	c.forSVG = function(channels, abs)
	{
		return addConvolutions(channels, cx.forSVG, cy.forSVG, abs);
	}
	c.allowAbs = cx.allowAbs && cy.allowAbs;
}
createXYConvolutionFunctions(1); // sobel x+y
createXYConvolutionFunctions(4); // prewitt x+y
function applyConvolution(context, imageData, value, channels, useAbsoluteValue)
{
	var convolution = Convolutions[value - 1].forCanvas;

	if (typeof convolution === 'function')
		return convolution(context, imageData, channels, useAbsoluteValue);

	return convolve3x3(context, imageData, channels, convolution, useAbsoluteValue);
}
function applyTiltShift(context, imageData, blurRadius, channels)
{
	var d = imageData.data;
	var width = imageData.width;
	var height = imageData.height;

	var blurData = context.createImageData(imageData);
	blurData.data.set(d);
	blurData = applyBlur(context, blurData, blurRadius, blurRadius, channels, 'duplicate', 0);
	var b = blurData.data;

	var setR = (channels & 1) === 1;
	var setG = (channels & 2) === 2;
	var setB = (channels & 4) === 4;
	var setA = (channels & 8) === 8;

	var halfHeight = height / 2;
	var gradientSize = 0.3;
	var gradientHeight = gradientSize * height;

	for (var y = 0, i = 0; y < height; ++y)
	{
		var maskAlpha = Math.abs(y - halfHeight) / gradientHeight;
		if (maskAlpha >= 1) {
			for (var x = 0; x < width; ++x, i += 4)
			{
				if (setR) d[i  ] = b[i  ];
				if (setG) d[i+1] = b[i+1];
				if (setB) d[i+2] = b[i+2];
				if (setA) d[i+3] = b[i+3];

				// d[i  ] = 0;
				// d[i+1] = 0;
				// d[i+2] = 0;
				// d[i+3] = 255;
			}
		} else {
			var sourceAlpha = 1 - maskAlpha;
			for (var x = 0; x < width; ++x, i += 4)
			{
				if (setR) d[i  ] = b[i  ]*maskAlpha + d[i  ]*sourceAlpha;
				if (setG) d[i+1] = b[i+1]*maskAlpha + d[i+1]*sourceAlpha;
				if (setB) d[i+2] = b[i+2]*maskAlpha + d[i+2]*sourceAlpha;
				if (setA) d[i+3] = b[i+3]*maskAlpha + d[i+3]*sourceAlpha;

				// d[i  ] = 255*sourceAlpha;
				// d[i+1] = 255*sourceAlpha;
				// d[i+2] = 255*sourceAlpha;
				// d[i+3] = 255;
			}
		}
	}
	return imageData;
}
