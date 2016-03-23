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
function applyBlurFilter(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, radius, radius, channels, 'edge', 0);
}
function applyBlurXFilter(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, radius, 0, channels, 'edge', 0);
}
function applyBlurYFilter(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, 0, radius, channels, 'edge', 0);
}
function applyDBlurX(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, radius, 0, channels, 'edge', BlurFlags.xDirectional);
}
function applyDBlurY(context, imageData, radius, channels)
{
	return applyBlur(context, imageData, 0, radius, channels, 'edge', BlurFlags.yDirectional);
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
function setChannelFlags(info, channels)
{
	info.setR = false;
	info.setG = false;
	info.setB = false;
	info.setA = false;

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
