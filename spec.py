title = ''
date = ''
sort_by_time = False
time_adjust = 0
width = 920
height = 690
thumb_width = 360
thumb_height = 270
thumb_cols = 2
thumb_rows = 60

skip = ()
rotate_left = ()
rotate_right = ()

filenameFormat = 'IMG_%04u.HEIC'

skip = [filenameFormat % n for n in skip]
rotate_left = [filenameFormat % n for n in rotate_left]
rotate_right = [filenameFormat % n for n in rotate_right]

crop = [
]
