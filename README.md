# PIG 'n' PIE &mdash; P's Image Gallery &amp; P's Image Editor

The first version of **pig** was written in May 2008, partly inspired by Max P's **lightbox**.

**pig** consists of two main components: **pig.py** and **pie.html**

**pig.py** is a Python script that will (1) create resized (and
cropped, rotated, normalized, etc.) copies of images (JPEGs and PNGs)
according to **spec.py** and (2) create HTML pages for a gallery /
photo album containing those images.

**pig.py** uses [ImageMagick](https://www.imagemagick.org/)'s
[convert](https://www.imagemagick.org/script/convert.php) utility to
create the copies of the original images. Thus both Python and
ImageMagick must be installed to run **pig.py**.

**pie.html** is a browser-based tool, written in JavaScript (with CSS
and HTML), originally intended only for rotating and precisely
cropping images while maintaining their original aspect ratio in order
to determine an image's crop geometry. The crop geometry can then be
copied and pasted into the **crop** list in **spec.py** so that it
will be passed to **convert** by **pig.py**.

However, **pie.html** (see
[https://nightjuggler.com/pie/](https://nightjuggler.com/pie/)) has
now become more of a tool for experimenting with sequences of filters
(such as contrast and brightness), applied to images or video. Each
filter can be applied to all three color channels (red, green, and
blue) or only selected ones, and a copy of the filtered image can also
be saved (if the original was not cross-origin).

Each filter available in **pie.html** is implemented in two different ways:
(1) with SVG and (2) with the Canvas API.
Basic filters (e.g. ```contrast(200%)``` on all color channels) can also be CSS only.
The SVG filters can be applied even to cross-origin images, animated GIFs
(see [example](https://nightjuggler.com/pie/?f=contrast,rgb,200/polar/blur-x,gb,8,1/depolar&c=400x335+0+0&cors&i=https://media.giphy.com/media/F3Q638k5euONa/giphy.gif)),
while playing video
(see [example](https://nightjuggler.com/pie/?i=MountMuir.mp4&c=640x480+0+0&f=convolve,rgb,10)
&mdash; press the space bar to play/pause the video),
or while dragging the cropped area of an image or video
(see [example](https://nightjuggler.com/pie/?f=contrast,rgb,160/polar,rg&c=1500x1000+1450+1300)).

The canvas filters can be applied only if the image or video is not cross-origin.
In the case of video, canvas filters are applied to the current frame.
Canvas filters are in some cases more precise, e.g. for the polar and reverse polar transforms
(see [example](https://nightjuggler.com/pie/?f=contrast,gb,160/convolve,rgb,2,1/polar,rg/blur-x,gb,6,1/depolar&c=2010x1340+1200+1200&o)),
and they allow a filtered image to be saved, via the canvas element's
[toDataURL()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toDataURL)
or [toBlob()](https://developer.mozilla.org/en-US/docs/Web/API/HTMLCanvasElement/toBlob)
methods.

The filters are implemented in **filter.js** which is included by
**pie.html**. **pie.html** also tries to load **cropList.js** which
can define a list of image (and video) files (and URLs) that will
appear in a drop-down menu in the control panel. **cropList.py** can
be used to generate **cropList.js** for all **.jpg** and **.png**
files in the **originals** subdirectory.
