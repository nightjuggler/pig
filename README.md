# PIG &amp; PIE

This project consists of two main components that can be used
independently of each other: **pig.py** (PIG) and **pie.html** (PIE).
The first version of **pig.py** was written in May 2008, partly
inspired by Max P's **lightbox**.

## PIG (P's Image Gallery)

**pig.py** is a Python script that will (1) create resized (and
cropped, rotated, normalized, etc.) copies of images (JPEGs and PNGs)
according to **spec.py** and (2) create HTML pages for a gallery /
photo album containing those images. **index_template.html** and
**page_template.html** are used as templates for the HTML pages.
[ImageMagick](https://imagemagick.org/) is
used to create the copies of the original images. Thus both Python and
ImageMagick must be installed to run **pig.py**.

### temple.py

**temple.py** defines a **parse** function that parses a string and returns an instance
of the **Template** class. The input string can contain processing directives for simple
conditionals (&lt;?if **variable**&gt; ... &lt;?else&gt; ... &lt;?end&gt;), loops
(&lt;?for **loop-variable** in **sequence-variable**&gt; ... &lt;?end&gt;), and variable
substitutions (&lt;?**variable**&gt;). Instances of **Template** can then be evaluated
and written to any object that has a **write** method, like a file object. This allows
for all of the HTML for the image gallery to be contained in the HTML template files.

```
>>> import io
>>> import temple
>>> template = temple.parse('''<ul>
... <?for person in people><li><?person.name>'s age is <?if person.age><?person.age><?else>unknown<?end>.
... <?end></ul>''')
>>> people = [{'name': 'Alice', 'age': 28}, {'name': 'Bob'}]
>>> with io.StringIO() as output:
...   template.write(output, locals())
...   print(output.getvalue())
...
<ul>
<li>Alice's age is 28.
<li>Bob's age is unknown.
</ul>
>>>
```

## PIE (P's Image Editor)

**pie.html**, on the other hand, is a browser-based tool, written in
JavaScript (with CSS and HTML), originally intended only for rotating
and precisely cropping images while maintaining their original aspect
ratio in order to determine the crop geometry
(**width**x**height**+**x**+**y**) for an image. The crop geometry can
be copied and pasted into the **crop** list defined in **spec.py** so
that it will be passed to **magick** by **pig.py**.

However, **pie.html** (see
[https://nightjuggler.com/pie/](https://nightjuggler.com/pie/)) has
now become more of a tool for experimenting with sequences of filters
(such as contrast and brightness) applied to images or videos. Each
filter can be applied to all three color channels (red, green, and
blue) or only to selected channels, and a copy of the filtered image
can be saved (if the original was not cross-origin).

Each filter available in **pie.html** is implemented in two different ways:
(1) with SVG and (2) with the Canvas API.
In **HTML &lt;img&gt;** and **HTML &lt;video&gt;** modes (see more about modes below),
basic filters (such as contrast or brightness applied to all color channels) can be
CSS-only instead of SVG.
The SVG (and CSS-only) filters can be applied even to cross-origin images, animated GIFs
(see [example](https://nightjuggler.com/pie/?f=contrast,rgb,200/polar/blur-x,gb,8,1/depolar&c=400x335+0+0&cors&i=https://media.giphy.com/media/F3Q638k5euONa/giphy.gif)),
while playing video
(see [example](https://nightjuggler.com/pie/?i=MountMuir.mp4&c=640x480+0+0&f=convolve,rgb,10);
press the space bar to play/pause the video),
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
can define a list of image (and/or video) files (and/or URLs) that
will appear in a drop-down menu in the control panel. **cropList.py**
can be used to generate **cropList.js** for all **.jpg** and **.png**
files in the **originals** subdirectory.

### Different modes for embedding images and applying filters

Because some browsers behave differently depending on how an image is embedded
in the web page and depending on how filters are applied to an image, **pie.html**
allows different modes for embedding images and applying filters. Images can be
embedded using a stand-alone HTML &lt;img&gt; element, an SVG &lt;image&gt; element,
or an HTML &lt;img&gt; element inside of an SVG &lt;foreignObject&gt; element.
Video is embedded with an HTML &lt;video&gt; element, either stand-alone or inside
an SVG &lt;foreignObject&gt; element. If a stand-alone &lt;img&gt; or &lt;video&gt;
element is used, filters are applied via the CSS
[filter](https://developer.mozilla.org/en-US/docs/Web/CSS/filter)
property, either as a sequence of CSS filter and url() functions (one function for
each user-specified filter) or as a single url() function referencing a single SVG
&lt;filter&gt; element which combines all of the user-specified filters.
If an SVG &lt;image&gt; or &lt;foreignObject&gt; element is used, filters are applied
via that element's
[filter](https://developer.mozilla.org/en-US/docs/Web/SVG/Attribute/filter)
attribute, referencing a single SVG &lt;filter&gt; element which combines all of the
user-specified filters.

<table>
<tr>
<td>Mode</td>
<td>Filters applied via CSS filter property</td>
<td>Filters applied via SVG filter attribute</td>
<td>User-specified filters combined into one SVG &lt;filter&gt;</td>
</tr>
<tr>
<td>SVG &lt;image&gt;</td>
<td>&nbsp;</td>
<td>&#x2713;</td>
<td>&#x2713;</td>
</tr>
<tr>
<td>HTML &lt;img&gt;
<br>HTML &lt;video&gt;</td>
<td>&#x2713;</td>
<td>&nbsp;</td>
<td>&nbsp;</td>
</tr>
<tr>
<td>HTML &lt;img&gt; + 1 SVG &lt;filter&gt;
<br>HTML &lt;video&gt; + 1 SVG &lt;filter&gt;</td>
<td>&#x2713;</td>
<td>&nbsp;</td>
<td>&#x2713;</td>
</tr>
<tr>
<td>&lt;foreignObject&gt; + &lt;img&gt;
<br>&lt;foreignObject&gt; + &lt;video&gt;</td>
<td>&nbsp;</td>
<td>&#x2713;</td>
<td>&#x2713;</td>
</tr>
</table>
