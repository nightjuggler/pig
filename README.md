# PIG &mdash; Pius' Image Gallery

The first version of **pig** was written in May 2008, partly inspired by Max P's **lightbox**.

**pig** consists of two main components: ```pig.py``` and ```crop.html```

```pig.py``` is a Python script that will create processed (e.g. cropped / rotated / resized / normalized) copies of images (JPEGs and PNGs) according to ```spec.py``` and create HTML pages for a gallery / photo album containing those images.

```pig.py``` uses [ImageMagick](https://www.imagemagick.org/)'s [convert](https://www.imagemagick.org/script/convert.php) utility to create the processed copies of the original images. So you must have both Python and ImageMagick installed to run ```pig.py```.

```crop.html``` is a browser-based tool for rotating and precisely cropping images while maintaining their original aspect ratio. It was originally intended only as a tool for determining the crop geometry for an image (which can then be copied and pasted into ```spec.py``` so that it will be passed to ImageMagick's convert utility by ```pig.py```), but it can now also be used to apply filters (e.g. contrast / brightness / sepia) and save images. See [https://nightjuggler.com/pig/crop.html](https://nightjuggler.com/pig/crop.html)
