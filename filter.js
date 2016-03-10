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

	for (var channel of channels)
		this['blur' + channel] = true;

	this.blurAll = this.blurR && this.blurG && this.blurB && this.blurA;
}
function applyBlur(context, imageData, xRadius, yRadius, channels, edgeMode)
{
	var blurInfo = new BlurInfo(context, imageData, xRadius, yRadius, channels, edgeMode);

	return blur(blurInfo);
}
function applyBlurFilter(context, imageData, radius)
{
	return applyBlur(context, imageData, radius, radius, 'RGBA', 1);
}
