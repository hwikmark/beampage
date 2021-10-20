import numpy as np

optics_dtypes = {
    'Element': np.int16,
    'Position': np.float64,
    'Type': np.int16,
    'FocalLength': np.float64
}

report_headline = '## beampage report\n'

report_entry = '''
Focus position: {:3.4f} mm ({:3.4f} mm {})\n\nFocal spot size: {:3.4f} mm
'''

report_rayleigh = '\n\nDepth of focus: {: 3.4f} mm\n\n'

collimated_text = '''
\n\nDepth of focus: {:3.4f} mm (*Collimated beam*)\n\n
'''

minspot = '''
\n \n\n**Smallest spot:** {:3.4f} mm at _z_ = {:3.4f} mm\n\n
'''

table_headline = '###### Optics overview'

elem_title = '###### Element {}: {}\n\n'

checkbox_labels = '''
Double-sided plotting:

`LOAD OPTICS` button resets ID:
'''

about_text = '''

## beampage - Gaussian optics dashboard

### Introduction

This app uses
[Gaussian beam optics](https://en.wikipedia.org/wiki/Gaussian_beam)
to calculate the propagation of a monochromatic beam
through a number of optical elements.

Each element is defined by its type, position along the _z_ axis
(axis of propagation) and focal length.

##### Note on widths
This app uses the convention of 'width' as the width of the beam
at a given point _z_, and 'waist' only as the width in focus
(for the collimated starting beam these are essentially the same).
Both of these are given as the half width at 1/e^2 amplitude.

### How-to

There are two ways of manipulating the optical system, directly
and through the loading interface.

##### Direct controls
Using the drop down menu at the far left of the interface, you can select
an element.
Using the two boxes after this you can set the position and focal length
of the selected element.

![The leftmost app controls](assets/direct_manipulation.png)

By pressing the `CREATE ELEMENT` button, you can add an optical element.
It will have the highest ID number and by default be added
10 mm after the latest optic.

Note that the ID is not necessarily the same as the index
(i.e. in which order the elements appear in the _z_ direction),
as it is assigned in order of creation.

##### Loading interface
Whenever the system is changed with the direct controls, this is also reflected
in the text box to the right. It is possible to copy the text from this box
to save your system.
You can then paste into the box and press the `LOAD OPTICS` button when you
wish to load the system.

![The saving/loading interface](assets/matrix_loading.png)

It is also possible to manipulate the text directly.
The text is printed, and read, in a standard CSV format,
where the columns should be more or less self-explanatory other than `Type`.
In this column a type of 0 is the origin of the beam
and 1 corresponds to a lens.

To add an element in this interface, one simply has to add a row to the text.
Do not assign an element number that already exists
as this may lead to unpredictable behavior.

If you wish to reset the element ID's, check the option
"`LOAD OPTICS` resets ID"
in the settings and press the `LOAD OPTICS` button.
This will reassign ID's according to index (_z_ axis).
##### Report

The "Report" tab will give you a brief report on the beam's propagation
through the different elements.

![Parts 1 and 2 of the report](assets/report1.png)

The first part of the report gives the smallest spot found along the
_z_ vector, and where it was found. Note that this is a numerically found
value and thus may differ from what you see in the next part. The next part
shows the input optics in a slightly easier-to-read format.

![Part 3 of the report](assets/report2.png)

The last part gives a breakdown of propagation for each optical element,
showing the focal spot size and depth of focus as calculated at the element.

##### Settings

The 'settings' tab enables you to change various things about the app such as
the plot scale, wavelength, and resolution.

![The 'settings' tab](assets/settings.png)

### Credits and acknowledgements
Made by [Hampus Wikmark Kreuger](https://github.com/hwikmark) in 2020-2021.
Dedicated to Knut.

Many thanks to Bahaa E. A. Saleh & Malvin Carl Teich for
"Fundamentals of Photonics", which greatly influenced this work.

beampage uses [Dash](http://dash.plotly.com/),
[Numpy](https://numpy.org/),
[Pandas](https://pandas.pydata.org/) and core libraries.
CSS layout by [chriddyp](https://codepen.io/chriddyp) /
[Dave Gamache](https://github.com/dhg).
'''
