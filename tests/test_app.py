import pytest
import app
import pandas as pd
import io
import numpy as np

simple_optics = '''
Element,Position,Type,FocalLength
0,-1000,0,0
1,-250,1,250
'''

test_settings = {"x_scale": "1", "y_scale": "1", "wavelength": 800, "waist": 5,
                 "z_min": -1000, "z_max": 2000, "z_step": 0.05,
                 "double_sided": 1}


class TestCharacterize:
    def test_long(self):
        n_string = app.characterize(0, short=False)
        assert n_string == 'the origin of the beam'

    def test_short(self):
        n_string = app.characterize(1, short=True)
        assert n_string == 'lens'

    def test_wrong_number(self):
        with pytest.raises(ValueError):
            app.characterize(23, short=False)

    def test_notnumber(self):
        with pytest.raises(ValueError):
            app.characterize('23', short=False)


class TestGaussian:
    def test_min_focus(self):
        optics = pd.read_csv(io.StringIO(simple_optics))
        settings = test_settings
        w_z, show_lenses, report_text = app.calc_gaussian(settings, optics)
        assert min(w_z) == pytest.approx(0.01273, 0.001)

    def test_change_wavelength(self):
        optics = pd.read_csv(io.StringIO(simple_optics))
        settings = test_settings
        w_z_800, show_lenses, report_text = app.calc_gaussian(settings, optics)
        settings['wavelength'] = 400
        w_z_400, show_lenses, report_text = app.calc_gaussian(settings, optics)
        assert min(w_z_800) == pytest.approx(2 * min(w_z_400))

    def test_where_focus(self):
        optics = pd.read_csv(io.StringIO(simple_optics))
        settings = test_settings
        z_max = float(settings['z_max'])
        z_min = float(settings['z_min'])
        z_step = float(settings['z_step'])
        z_grid = np.arange(z_min, z_max, z_step)
        w_z, show_lenses, report_text = app.calc_gaussian(settings, optics)
        wherefocus = z_grid[np.where(w_z == min(w_z))[0][0]]
        # Asserting the abs here, because it's hard
        # to do a relative error from 0...
        assert np.abs(wherefocus) < 1e-8

    def test_simple_show_lenses(self):
        optics = pd.read_csv(io.StringIO(simple_optics))
        settings = test_settings
        w_z, show_lenses, report_text = app.calc_gaussian(settings, optics)
        assert show_lenses[0][0] == '1'
