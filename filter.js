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

	var delta = 4; // the number of data array elements to skip to get to the next pixel
	var vDelta = 4 * width;

	if (vertical) {
		delta = vDelta;
		vDelta = 4;

		width = height;
		height = inData.width;
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
			firstR = lastR = 0; sumR = 0;
			firstG = lastG = 0; sumG = 0;
			firstB = lastB = 0; sumB = 0;
			firstA = lastA = 0; sumA = 0;
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
function getBoxBlurSizes1(blurInfo, radiusType)
{
	// This function determines the sizes for 3 successive box blurs according to
	// https://www.w3.org/TR/filter-effects-1/#feGaussianBlurElement

	var radius = blurInfo[radiusType];

	var boxBlurSize = Math.floor(radius * 3 * Math.sqrt(2 * Math.PI) / 4 + 0.5);

	var suffixes = ['1Left', '1Right', '2Left', '2Right', '3Left', '3Right'];

	if (boxBlurSize & 1 === 1) {
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

	return blurInfo.inData;
}
function BlurInfo(context, inData, radius)
{
	this.inData = inData;
	this.outData = context.createImageData(inData);

	this.xRadius = radius;
	this.yRadius = radius;
	this.edgeMode = 1; // duplicate
	this.blurR = true;
	this.blurG = true;
	this.blurB = true;
	this.blurA = true;
}
function applyBlurFilter(context, imageData, radius)
{
	var blurInfo = new BlurInfo(context, imageData, radius);

	return blur(blurInfo);
}
function applyBlurRed(context, imageData, radius)
{
	var blurInfo = new BlurInfo(context, imageData, radius);

	blurInfo.blurG = false;
	blurInfo.blurB = false;
	blurInfo.blurA = false;

	return blur(blurInfo);
}
function applyBlurGreen(context, imageData, radius)
{
	var blurInfo = new BlurInfo(context, imageData, radius);

	blurInfo.blurR = false;
	blurInfo.blurB = false;
	blurInfo.blurA = false;

	return blur(blurInfo);
}
function applyBlurBlue(context, imageData, radius)
{
	var blurInfo = new BlurInfo(context, imageData, radius);

	blurInfo.blurR = false;
	blurInfo.blurG = false;
	blurInfo.blurA = false;

	return blur(blurInfo);
}
