# -*- coding: utf-8 -*-

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_auth
from dash.dependencies import Input, Output, State
import plotly.express as px
import numpy as np
import pandas as pd
from io import StringIO
import extra_vars as exva
import json
from flask import request
from datetime import datetime
import os

# Functions


def check_index(position, z_grid):
    p_index = np.where(z_grid >= position)[0][0]
    return(p_index)


def characterize(teh_type: int, short=False):
    if teh_type == 0:
        if short:
            nstring = 'origin'
        else:
            nstring = 'the origin of the beam'
    elif teh_type == 1:
        if short:
            nstring = 'lens'
        else:
            nstring = 'a lens'
    else:
        raise ValueError('Unknown optics type!')
    return(nstring)


def update_optics(optical_elements):
    optical_elements.sort_values('Position', inplace=True)
    optical_elements.reset_index(drop=True, inplace=True)
    return(optical_elements)


def scale_text(factor):
    if factor == 1:
        text = ' (mm)'
    elif factor == 1000:
        text = ' (m)'
    elif factor == 0.001:
        text = ' (μm)'
    else:
        text = ''
    return(text)


def calc_gaussian(settings, optical_elements):
    z_max = float(settings['z_max'])
    z_min = float(settings['z_min'])
    z_step = float(settings['z_step'])
    waist = float(settings['waist'])
    wavelength = float(settings['wavelength']) * 1e-6
    rayleigh = waist ** 2 * np.pi / wavelength
    z_origin = z_min
    z_grid = np.arange(z_min, z_max, z_step)
    report_text = ''
    optical_elements.at[0, 'Position'] = z_min
    optical_elements['z grid index'] = [check_index(
        pos, z_grid)-1 for pos in optical_elements['Position']]
    optical_elements.at[0, 'z grid index'] = 0
    w_z = waist + 0 * z_grid
    show_lenses = [[], []]
    num_elements = len(optical_elements)
    for o_index in range(num_elements):
        o_type = optical_elements.at[o_index, 'Type']
        el_number = optical_elements.at[o_index, 'Element']
        start_index = optical_elements.at[o_index, 'z grid index']
        report_text += (exva.elem_title.format(el_number,
                                               characterize(o_type)))
        if o_index == num_elements - 1:
            end_index = -1
        else:
            end_index = optical_elements.at[o_index + 1, 'z grid index']
        if o_type == 0:
            pass
        elif o_type == 1:
            f = optical_elements.at[o_index, 'FocalLength']
            z_temp = (z_grid[start_index] - z_origin)
            r = rayleigh / (z_temp - f)
            Mr = np.abs(f / (z_temp - f))
            M = Mr / (np.sqrt(1 + r ** 2))
            waist = waist * M
            z_origin = M ** 2 * ((z_temp) - f) + f + z_grid[start_index]
            rayleigh = M ** 2 * rayleigh
            show_lenses[0].append(str(el_number))
            show_lenses[1].append([z_grid[start_index], w_z[start_index - 1]])
        report_text += exva.report_entry.format(z_origin, z_origin -
                                                z_grid[start_index],
                                                'after' if z_origin -
                                                z_grid[start_index] > 0 else
                                                'before', waist)
        if rayleigh < 10000:
            report_text += exva.report_rayleigh.format(
                2 * rayleigh)
        else:
            report_text += exva.collimated_text.format(2 * rayleigh)
        w_z[start_index:end_index] = waist * np.sqrt(1 + ((z_grid[
            start_index:end_index] - z_origin) / rayleigh) ** 2)
        if end_index == -1:
            w_z[end_index] = waist * \
                np.sqrt(1 + ((z_grid[end_index] - z_origin) / rayleigh) ** 2)
    return(w_z, show_lenses, report_text)


input_file = 'assets/initial_lens.csv'
settings_loc = 'assets/default_settings.json'

# Settings loading goes here

with open(settings_loc, 'r') as settings_file:
    default_settings = json.loads(settings_file.read())
init_z_max = float(default_settings['z_max'])
init_z_min = float(default_settings['z_min'])
init_z_step = float(default_settings['z_step'])
init_z_grid = np.arange(init_z_min, init_z_max, init_z_step)
init_wavelength = float(default_settings['wavelength'])
init_waist = float(default_settings['waist'])

# Remake logfile on app startup... ?

use_logfile = True

if use_logfile:
    os.makedirs('aux', exist_ok = True)
    logfile_name = 'aux/logfile.txt'
    logfile = open(logfile_name, 'w')
    nowstr = datetime.now().isoformat(timespec='seconds', sep=' ')
    logstr = nowstr + ' Server restarted\n'
    logfile.write(logstr)
    logfile.close()

# Initial loading of optics (could probably be better tbh)

optical_elements = pd.read_csv(input_file)
optical_elements['z grid index'] = [
    check_index(pos, init_z_grid)
    for pos in optical_elements['Position']]
optical_elements.loc[-1] = [init_z_min, 0, 0, 0]
optical_elements = update_optics(optical_elements)
optical_elements['Element'] = optical_elements.index
optical_elements = optical_elements[
    ['Element', 'Position', 'Type', 'FocalLength']]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

tabs_styles = {
    'height': '51px'
}

tab_style = {
    'borderBottom': '1px solid #d6d6d6',
    'padding': '2px',
    'fontWeight': 'bold'
}

tab_selected_style = {
    'borderTop': '1px solid #ccccff',
    'borderBottom': '1px solid #ccccff',
    'backgroundColor': "#53C3F0",
    'color': 'white',
    'padding': '2px'
}

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

server = app.server

app.title = 'beampage'

# Optional: set password protection, in which case usr/pwd pairs are loaded
# from here

VALID_USERNAME_PASSWORD_PAIRS = {
    'foo': 'bar',
}

use_password = False

if use_password:
    auth = dash_auth.BasicAuth(
        app,
        VALID_USERNAME_PASSWORD_PAIRS
    )

app.layout = html.Div([
    dcc.Tabs(id="all-tabs-inline", value='tab-1', children=[
        dcc.Tab(label='Main', value='tab-1', style=tab_style,
                selected_style=tab_selected_style, children=[
                    dcc.Graph(id='main-graph'),
                    html.Div([
                        dcc.Dropdown(
                            id='element_select',
                            options=[{'label': i, 'value': i}
                                     for i in optical_elements.index[1:]],
                            value='1',
                            style={'min-width': '100px',
                                   'display': 'inline-block'},
                            clearable=False
                        ),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        html.Div(id='Infobox',
                                 style={'width': '120px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        html.Label(dcc.Markdown('**Position:** '),
                                   style={'display': 'inline-block',
                                          'position': 'relative',
                                          'vertical-align': 'top'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        dcc.Input(type='number', id='position', style={
                            'width': '90px', 'display': 'inline-block',
                            'position': 'relative',
                            'vertical-align': 'top'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        html.Label(dcc.Markdown('**Focal length:** '), style={
                            'display': 'inline-block', 'position': 'relative',
                            'vertical-align': 'top'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        dcc.Input(type='number', id='focal_length', style={
                            'width': '100px', 'display': 'inline-block',
                            'position': 'relative', 'vertical-align': 'top'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        html.Button(id='make-button', n_clicks=0,
                                    children='Create Element',
                                    style={'display': 'inline-block',
                                           'vertical-align': 'top'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        dcc.Textarea(
                            id='output_text',
                            placeholder='Enter a value...',
                            value='Element,Position,Type,FocalLength',
                            style={'min-width': '270px',
                                   'display': 'inline-block',
                                   'vertical-align': 'top'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block',
                                        'position': 'relative'}),
                        html.Button(id='load-button', n_clicks=0,
                                    children='Load Optics',
                                    style={'display': 'inline-block',
                                           'vertical-align': 'top'})
                    ], style={'columns': 1, 'display': 'table',
                              'overflow-x': 'auto', 'margin-left': 'auto',
                              'margin-right': 'auto'})
                ]),
        dcc.Tab(label='Report', value='report', style=tab_style,
                selected_style=tab_selected_style, children=[
                    html.Div(children=[
                        dcc.Markdown(exva.report_headline),
                        html.Div(id='report-body')
                    ], style={'max-width': '750px', 'margin-left': 'auto',
                              'margin-right': 'auto'})]),
        dcc.Tab(label='Settings', value='tab-2', style=tab_style,
                selected_style=tab_selected_style, children=[
                    html.Div(style={'min-height': '20px'}),
                    html.Div(children=[
                        html.Label('x plot scale: ',
                                   style={'width': '100px',
                                          'display': 'inline-block'}),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block'}),
                        html.Label('y plot scale: ',
                                   style={'width': '100px',
                                          'display': 'inline-block'}),
                        html.Div(),
                        dcc.Dropdown(
                            id='xscale-drop',
                            options=[{'label': 'Micrometers', 'value': 0.001},
                                     {'label': 'Millimeters', 'value': 1},
                                     {'label': 'Meters', 'value': 1000}, ],
                            value='1',
                            style={
                                'width': '100px',
                                'display': 'inline-block'},
                            clearable=False
                        ),
                        html.Div(style={'width': '10px',
                                        'display': 'inline-block'}),
                        dcc.Dropdown(
                            id='yscale-drop',
                            options=[{'label': 'Micrometers', 'value': 0.001},
                                     {'label': 'Millimeters', 'value': 1},
                                     {'label': 'Meters', 'value': 1000}, ],
                            value='1',
                            style={
                                'width': '100px',
                                'display': 'inline-block'},
                            clearable=False
                        ),
                        html.Label('Wavelength (nm): ', style={
                            'width': 'one-column'}),
                        dcc.Input(type='number', id='wavelength-box',
                                  value=init_wavelength, style={}),
                        html.Label('Starting waist (mm): ', style={
                            'width': 'one-column'}),
                        dcc.Input(type='number', id='waist-box',
                                  value=init_waist, style={}),
                        html.Div(),
                        html.Div(dcc.Markdown(exva.checkbox_labels), style={
                            'display': 'inline-block'}),
                        html.Div(style={'width': '20px',
                                        'display': 'inline-block'}),
                        dcc.Checklist(id='more-options', options=[
                            {'label': '', 'value': 'double_sided'},
                            {'label': '', 'value': 'reset_index'}],
                            style={'display': 'inline-block'},
                            value=['double_sided']),
                        html.Label(
                            'z min (mm): ', style={
                                'width': 'one-column'}),
                        dcc.Input(type='number', id='zmin-box',
                                  value=init_z_min,
                                  style={}),
                        html.Label(
                            'z max (mm): ', style={
                                'width': 'one-column'}),
                        dcc.Input(type='number', id='zmax-box',
                                  value=init_z_max,
                                  style={}),
                        html.Label(
                            'z step (mm): ', style={
                                'width': 'one-column'}),
                        dcc.Input(type='number', id='zstep-box',
                                  value=init_z_step,
                                  style={}),
                        html.Div(style={'height': '10px'})
                    ], style={'max-width': '750px', 'margin-left': 'auto',
                              'margin-right': 'auto', 'columns': 2,
                              'content-justification': 'center'}),
                    html.Div(style={'min-height': '20px'}),
                    html.Button(id='load-settings-button', n_clicks=0,
                                children='Save settings',
                                style={'width': '200px',
                                       'transform': ' translate(-70%, -0%)',
                                       'margin': 0, 'position': 'absolute',
                                       'left': '50%'})]),
        dcc.Tab(label='About', value='tab-3', style=tab_style,
                selected_style=tab_selected_style, children=[
                    html.Div(children=[
                        dcc.Markdown(exva.about_text)
                    ], style={'max-width': '750px', 'margin-left': 'auto',
                              'margin-right': 'auto'})]),
    ], style=tabs_styles,
        colors={
        "border": "#ccccff",
            "primary": "red",
            "background": "white"
    }),
    html.Div(id='optics-store', style={'display': 'none'},
             children=optical_elements.to_json()),
    html.Div(id='persistent-settings', style={'display': 'none'}, children=''),
    html.Div(id='load-butt-clicks', style={'display': 'none'}, children='0'),
    html.Div(id='make-butt-clicks', style={'display': 'none'}, children='0'),
    html.Div(id='auth', style={'display': 'none'}),
    html.Div(id='auth2', style={'display': 'none'}, children='')
])


@app.callback(
    [Output('auth', 'children')], [Input('auth2', 'children')])
def access_log(children):
    if use_logfile:
        if use_password:
            usr = request.authorization['username']
        else:
            usr = 'anonymous'
        nowstr = datetime.now().isoformat(timespec='seconds', sep=' ')
        logstr = nowstr + ' Connection by ' + usr + '\n'
        with open(logfile_name, 'a') as logfile:
            logfile.write(logstr)
    return([None])


@app.callback(
    [Output('Infobox', 'children'), Output('position', 'value'),
     Output('focal_length', 'value')],
    [Input('element_select', 'value')], [State('optics-store', 'children')])
def update_output_div(input_value, compressed_optics):
    chosen = int(input_value)
    optics = pd.read_json(compressed_optics)
    chosen_index = optics.loc[optics['Element'] == chosen].index[0]
    teh_type = optics.at[chosen_index, 'Type']
    teh_position = optics.at[chosen_index, 'Position']
    focal = optics.at[chosen_index, 'FocalLength']
    return ['Element {} is {}. '.format(input_value, characterize(teh_type)),
            teh_position, focal]


@app.callback(
    [Output('persistent-settings', 'children')],
    [Input('load-settings-button', 'n_clicks')],
    [State('xscale-drop', 'value'),
        State('yscale-drop', 'value'), State('wavelength-box', 'value'),
        State('waist-box', 'value'), State('zmin-box', 'value'),
        State('zmax-box', 'value'), State('zstep-box', 'value'),
        State('more-options', 'value')])
def update_settings(clicks, xscale, yscale, wl, waist, zmin, zmax, zstep,
                    options):
    # One thing to consider here is adding a "load/save settings" box
    # similar to that for the data.
    # In that case I'll add the same outputs as states.
    settings = {}
    settings['x_scale'] = xscale
    settings['y_scale'] = yscale
    settings['wavelength'] = wl
    settings['waist'] = waist
    settings['z_min'] = zmin
    settings['z_max'] = zmax
    settings['z_step'] = zstep
    settings['double_sided'] = 1
    if 'double_sided' in options:
        settings['double_sided'] = 1
    else:
        settings['double_sided'] = 0
    if 'reset_index' in options:
        settings['reset_index'] = 1
    else:
        settings['reset_index'] = 0
    return([json.dumps(settings)])


@app.callback(
    [Output('optics-store', 'children'),
        Output('load-butt-clicks', 'children'),
        Output('make-butt-clicks', 'children')],
    [Input('position', 'value'),
     Input('focal_length', 'value'), Input('load-button', 'n_clicks'),
     Input('make-button', 'n_clicks')],
    [State('optics-store', 'children'),
     State('load-butt-clicks', 'children'),
     State('make-butt-clicks', 'children'),
     State('output_text', 'value'),
     State('element_select', 'value'),
     State('persistent-settings', 'children')])
def move_lenses(posvalue, focal, load_clicks, make_clicks, compressed_optics,
                load_numclicks, make_numclicks, load_text, which_one,
                compressed_settings):
    optics = pd.read_json(compressed_optics)
    settings = json.loads(compressed_settings)
    l_clicks = int(load_numclicks)
    m_clicks = int(make_numclicks)
    old_load_clicks = int(load_clicks)
    old_make_clicks = int(make_clicks)
    last_optic = optics.tail(1)
    chosen = int(which_one)
    chosen_index = optics.loc[optics['Element'] == chosen].index[0]
    if l_clicks != old_load_clicks:
        try:
            optics = pd.read_csv(StringIO(load_text), dtype=exva.optics_dtypes)
        except ValueError:
            # If the user puts some useless data here we'll just reset the box
            pass
        if settings['reset_index']:
            optics['Element'] = optics.index
    elif m_clicks != old_make_clicks:
        last_place = float(last_optic['Position'])
        last_index = last_optic.index
        new_optic = pd.DataFrame({
            'Type': [1],
            'Position': [last_place+10],
            'FocalLength': [100],
            'Element': len(optical_elements)})
        optics = optics.append(new_optic)
    else:
        try:
            optics.at[chosen_index, 'Position'] = float(posvalue)
            optics.at[chosen_index, 'FocalLength'] = float(focal)
        except TypeError:
            pass
    optics = update_optics(optics)
    return([optics.to_json(), load_clicks, make_clicks])


@app.callback(
    [Output('main-graph', 'figure'), Output('output_text', 'value'),
     Output('element_select', 'options'), Output('report-body', 'children')],
    [Input('optics-store', 'children'),
     Input('persistent-settings', 'children')])
def update_figure(compressed_optics, compressed_settings):
    settings = json.loads(compressed_settings)
    optical_elements = pd.read_json(compressed_optics)
    w_z, show_lenses, report_text = calc_gaussian(settings, optical_elements)
    z_max = float(settings['z_max'])
    z_min = float(settings['z_min'])
    z_step = float(settings['z_step'])
    z_grid = np.arange(z_min, z_max, z_step)
    double_sided = int(settings['double_sided'])
    x_scaling_factor = float(settings['x_scale'])
    y_scaling_factor = float(settings['y_scale'])

    xlabel = 'z' + scale_text(x_scaling_factor)
    ylabel = 'Width' + scale_text(y_scaling_factor)

    fig = px.line(x=z_grid / x_scaling_factor, y=w_z / y_scaling_factor,
                  labels={'x': xlabel, 'y': ylabel})
    if double_sided:
        fig2 = px.line(x=z_grid / x_scaling_factor, y=-w_z / y_scaling_factor,
                       labels={'x': xlabel, 'y': ylabel})
        fig.add_trace(fig2.data[0])
    for element_name, element_position in zip(show_lenses[0], show_lenses[1]):
        if double_sided:
            fig.add_annotation(
                x=element_position[0] / x_scaling_factor,
                y=-element_position[1] / y_scaling_factor,
                text=element_name,
                ayref='y',
                ay=element_position[1] / (y_scaling_factor * 1.5))
        else:
            fig.add_annotation(
                x=element_position[0] / x_scaling_factor,
                y=element_position[1] / y_scaling_factor,
                text=element_name,
                ayref='y',
                ay=element_position[1] / (y_scaling_factor * 2))
    fig.update_annotations(dict(
        xref="x",
        yref="y",
        showarrow=True,
        arrowhead=7,
        ax=0,
    ))
    wherefocus = np.where(w_z == min(w_z))[0][0]
    minspot_text = exva.minspot.format(w_z[wherefocus],
                                       z_grid[wherefocus])
    options = [{'label': i, 'value': i}
               for i in optical_elements['Element'][1:]]
    nice_optics = optical_elements.loc[:, ['Element',
                                           'Type',
                                           'Position',
                                           'FocalLength']]
    nice_optics['Type'] = nice_optics.loc[:, 'Type'].apply(characterize,
                                                           short=True)
    i_am_the_table = nice_optics.to_markdown(
        index=False,
        headers=[
            'Element',
            'Type',
            'Position (mm)',
            'Focal length (mm)']) + '\n'

    total_report = html.Div(children=[
        dcc.Markdown(minspot_text),
        dcc.Markdown(exva.table_headline),
        dcc.Markdown(i_am_the_table),
        dcc.Markdown(report_text)
    ])
    return [
        fig,
        optical_elements.to_csv(
            columns=[
                'Element',
                'Position',
                'Type',
                'FocalLength'],
            index=False),
        options,
        total_report]


if __name__ == '__main__':
    app.run_server(debug=True)
