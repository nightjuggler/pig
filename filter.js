var svgNS = 'http://www.w3.org/2000/svg';
var svgFilterId = 0;
var svgFilterIdBin = [];
var channelMap = [['R', 1], ['G', 2], ['B', 4]];

function removeSVGFilter(id)
{
	var filterElement = document.getElementById('filter' + id);
	filterElement.parentNode.removeChild(filterElement);
	svgFilterIdBin.push(id);
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
	filterNode.appendChild(fe);

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
function createGaussianBlur(xRadius, yRadius)
{
	var fe = document.createElementNS(svgNS, 'feGaussianBlur');
	fe.setAttribute('stdDeviation', xRadius + ' ' + yRadius);
	return fe;
}
function createBlurXFilter(xRadius, channels)
{
	return createFilter(channels, createGaussianBlur(xRadius, 0));
}
function createBlurYFilter(yRadius, channels)
{
	return createFilter(channels, createGaussianBlur(0, yRadius));
}
function createBlurFilter(radius, channels)
{
	return createFilter(channels, createGaussianBlur(radius, radius));
}
function boxBlur(blurInfo, radiusType, vertical)
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

	if (vertical) {
		[width, height] = [height, width]; // Swap width and height
		[delta, vDelta] = [vDelta, delta]; // Swap delta and vDelta
	}

	var m = leftRadius + 1;
	var zDelta = (width - 1) * delta;
	vDelta -= zDelta + delta;
	width -= size;

	var edgeMode = blurInfo.edgeMode;
	var blurR = blurInfo.blurR;
	var blurG = blurInfo.blurG;
	var blurB = blurInfo.blurB;
	var blurA = blurInfo.blurA;

	var i = 0;
	for (var y = 0; y < height; ++y) {
		var j = i;
		var k = i;

		var firstR, sumR, lastR;
		var firstG, sumG, lastG;
		var firstB, sumB, lastB;
		var firstA, sumA, lastA;

		if (edgeMode === 0) {
			// edgeMode is "none"
			firstR = lastR = 0; sumR = firstR * m;
			firstG = lastG = 0; sumG = firstG * m;
			firstB = lastB = 0; sumB = firstB * m;
			firstA = lastA = 0; sumA = firstA * m;
		} else {
			// edgeMode is "duplicate"
			var z = i + zDelta;
			firstR = src[i  ]; sumR = firstR * m; lastR = src[z  ];
			firstG = src[i+1]; sumG = firstG * m; lastG = src[z+1];
			firstB = src[i+2]; sumB = firstB * m; lastB = src[z+2];
			firstA = src[i+3]; sumA = firstA * m; lastA = src[z+3];
		}

		for (var x = 0; x < rightRadius; ++x) {
			sumR += src[k  ];
			sumG += src[k+1];
			sumB += src[k+2];
			sumA += src[k+3];
			k += delta;
		}
		for (var x = 0; x <= leftRadius; ++x) {
			if (blurR) { sumR += src[k  ] - firstR; d[i  ] = sumR / size; }
			if (blurG) { sumG += src[k+1] - firstG; d[i+1] = sumG / size; }
			if (blurB) { sumB += src[k+2] - firstB; d[i+2] = sumB / size; }
			if (blurA) { sumA += src[k+3] - firstA; d[i+3] = sumA / size; }
			k += delta;
			i += delta;
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
			if (blurR) { sumR += lastR - src[j  ]; d[i  ] = sumR / size; }
			if (blurG) { sumG += lastG - src[j+1]; d[i+1] = sumG / size; }
			if (blurB) { sumB += lastB - src[j+2]; d[i+2] = sumB / size; }
			if (blurA) { sumA += lastA - src[j+3]; d[i+3] = sumA / size; }
			j += delta;
			i += delta;
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
	getBoxBlurSizes1(blurInfo, 'xRadius');
	getBoxBlurSizes1(blurInfo, 'yRadius');

	boxBlur(blurInfo, 'xRadius1', false);
	boxBlur(blurInfo, 'yRadius1', true);

	boxBlur(blurInfo, 'xRadius2', false);
	boxBlur(blurInfo, 'yRadius2', true);

	boxBlur(blurInfo, 'xRadius3', false);
	boxBlur(blurInfo, 'yRadius3', true);

	if (!blurInfo.blurAll && blurInfo.inData === blurInfo.newData)
		copyUnchangedData(blurInfo);

	return blurInfo.inData;
}
function BlurInfo(context, inData, xRadius, yRadius, channels, edgeMode)
{
	this.inData = inData;
	this.outData = context.createImageData(inData);
	this.newData = this.outData;

	this.xRadius = xRadius;
	this.yRadius = yRadius;
	this.edgeMode = edgeMode;
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
function applyBlur(context, imageData, xRadius, yRadius, channels, edgeMode)
{
	var blurInfo = new BlurInfo(context, imageData, xRadius, yRadius, channels, edgeMode);

	return blur(blurInfo);
}
function applyBlurFilter(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, radius, radius, channels, 1);
}
function applyBlurXFilter(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, radius, 0, channels, 1);
}
function applyBlurYFilter(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, 0, radius, channels, 1);
}
