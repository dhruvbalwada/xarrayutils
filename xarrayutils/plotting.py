import numpy as np
import xarray as xr
import matplotlib.pyplot as plt
import gsw


def center_lim(ax, which='y'):
    if which == 'y':
        lim = np.array(ax.get_ylim())
        ax.set_ylim(np.array([-1, 1]) * abs(lim).max())
    elif which == 'x':
        lim = np.array(ax.get_xlim())
        ax.set_xlim(np.array([-1, 1]) * abs(lim).max())
    elif which in ['xy', 'yx']:
        center_lim(ax, 'x')
        center_lim(ax, 'y')
    else:
        raise ValueError('`which` is not in (`x,`y`, `xy`) found %s' % which)


def depth_logscale(ax, yscale=400, ticks=None):
    if ticks is None:
        ticks = [0, 100, 250, 500, 1000, 2500, 5000]
    ax.set_yscale('symlog', linthreshy=yscale)
    ticklabels = [str(a) for a in ticks]
    ax.set_yticks(ticks)
    ax.set_yticklabels(ticklabels)
    ax.invert_yaxis()


def plot_line_shaded_std(x, y, std_y, horizontal=True,
                         ax=None,
                         line_kwargs=dict(),
                         fill_kwargs=dict()):
    """Plot wrapper to draw line for y and shaded patch according to std_y.
    The shading represents one std on each side of the line...

    Parameters
    ----------
    x : numpy.array or xr.DataArray
        Coordinate.
    y : numpy.array or xr.DataArray
        line data.
    std_y : numpy.array or xr.DataArray
        std corresponding to y.
    horizontal : bool
        Determines if the plot is horizontal or vertical (e.g. x is plotted
        on the y-axis).
    ax : matplotlib.axes
        Matplotlib axes object to plot on (the default is plt.gca()).
    line_kwargs : dict
        optional parameters for line plot.
    fill_kwargs : dict
        optional parameters for std fill plot.

    Returns
    -------
    ?
        handle to line plot.

    """

    line_defaults = {}

    # Set plot defaults into the kwargs
    if not ax:
        ax = plt.gca()

    # Apply defaults but respect input
    line_defaults.update(line_kwargs)

    if horizontal:
        p = ax.plot(x, y, **line_defaults)
    else:
        p = ax.plot(y, x, **line_defaults)

    fill_defaults = {'color': p[-1].get_color(),
                     'alpha': 0.35}

    # Apply defaults but respect input
    fill_defaults.update(fill_kwargs)

    if horizontal:
        ax.fill_between(x, y-std_y, y+std_y, **fill_defaults)
    else:
        ax.fill_betweenx(x, y-std_y, y+std_y, **fill_defaults)
    return p


def box_plot(box, ax=None, split_detection='True', **kwargs):
    """plots box despite coordinate discontinuities.
    INPUT
    -----
    box: np.array
        Defines the box in the coordinates of the current axis.
        Describing the box corners [x1, x2, y1, y2]
    ax: matplotlib.axis
        axis for plotting. Defaults to plt.gca()
    kwargs: optional
        anything that can be passed to plot can be put as kwarg
    """

    if len(box) != 4:
        raise RuntimeError("'box' must be a 4 element np.array, \
            describing the box corners [x1, x2, y1, y2]")
    xlim = plt.gca().get_xlim()
    ylim = plt.gca().get_ylim()
    x_split = False
    y_split = False

    if ax is None:
        ax = plt.gca()

    if split_detection:
        if np.diff([box[0], box[1]]) < 0:
            x_split = True

        if np.diff([box[2], box[3]]) < 0:
            y_split = True

    if y_split and not x_split:
        ax.plot([box[0], box[0], box[1], box[1], box[0]],
                 [ylim[1], box[2], box[2], ylim[1], ylim[1]], **kwargs)

        ax.plot([box[0], box[0], box[1], box[1], box[0]],
                 [ylim[0], box[3], box[3], ylim[0], ylim[0]], **kwargs)

    elif x_split and not y_split:
        ax.plot([xlim[1], box[0], box[0], xlim[1], xlim[1]],
                 [box[2], box[2], box[3], box[3], box[2]], **kwargs)

        ax.plot([xlim[0], box[1], box[1], xlim[0], xlim[0]],
                 [box[2], box[2], box[3], box[3], box[2]], **kwargs)

    elif x_split and y_split:
        ax.plot([xlim[1], box[0], box[0]], [box[2], box[2], ylim[1]],
                 **kwargs)

        ax.plot([xlim[0], box[1], box[1]], [box[2], box[2], ylim[1]],
                 **kwargs)

        ax.plot([xlim[1], box[0], box[0]], [box[3], box[3], ylim[0]],
                 **kwargs)

        ax.plot([xlim[0], box[1], box[1]], [box[3], box[3], ylim[0]],
                 **kwargs)

    elif not x_split and not y_split:
        ax.plot([box[0], box[0], box[1], box[1], box[0]],
                 [box[2], box[3], box[3], box[2], box[2]], **kwargs)

def dict2box(di, xdim='lon', ydim='lat'):
    return np.array([di[xdim].start, di[xdim].stop,
                     di[ydim].start, di[ydim].stop])


def box_plot_dict(di, xdim='lon', ydim='lat', **kwargs):
    """plot box from xarray selection dict e.g.
    `{'xdim':slice(a, b), 'ydim':slice(c,d), ...}`"""

    # extract box from dict
    box  = dict2box(di, xdim=xdim, ydim=ydim)
    # plot
    box_plot(box, **kwargs)



def draw_dens_contours_teos10(sigma='sigma0', add_labels=True, ax=None,
                              density_grid=20, dens_interval=1.0,
                              salt_on_x=True, slim=None, tlim=None,
                              contour_kwargs={}, c_label_kwargs={}, **kwargs):
    """draws density contours on the current plot.
    Assumes that the salinity and temperature values are given as SA and CT.
    Needs documentation... """
    if ax is None:
        ax = plt.gca()

    if sigma not in ['sigma%i' % s for s in range(5)]:
        raise ValueError('Sigma function has to be one of `sigma0`...`sigma4` \
                         is: %s' % (sigma))

    # get salt (default: xaxis) and temp (default: yaxis) limits
    if salt_on_x:
        if not slim:
            slim = ax.get_xlim()
        if not tlim:
            tlim = ax.get_ylim()
        x = np.linspace(*slim, density_grid)
        y = np.linspace(*tlim, density_grid)
    else:
        if not tlim:
            tlim = ax.get_xlim()
        if not slim:
            slim = ax.get_ylim()
        x = np.linspace(*slim, density_grid)
        y = np.linspace(*tlim, density_grid)

    if salt_on_x:
        ss, tt = np.meshgrid(x, y)
    else:
        tt, ss = np.meshgrid(x, y)

    sigma_func = getattr(gsw, sigma)

    sig = sigma_func(ss, tt)

    levels = np.arange(np.floor(sig.min()), np.ceil(sig.max()), dens_interval)

    c_kwarg_defaults = dict(levels=levels, colors='0.4',
                            linestyles='--', linewidths=0.5)
    c_kwarg_defaults.update(kwargs)
    c_kwarg_defaults.update(contour_kwargs)

    c_label_kwarg_defaults = dict(fmt='%.02f')
    c_label_kwarg_defaults.update(kwargs)
    c_label_kwarg_defaults.update(c_label_kwargs)

    ch = ax.contour(x, y, sig, **c_kwarg_defaults)
    ax.clabel(ch, **c_label_kwarg_defaults)

    if add_labels:
        plt.text(0.05, 0.05, '$\sigma_{%s}$' % (sigma[-1]), fontsize=14,
                 verticalalignment='center',
                 horizontalalignment='center', transform=ax.transAxes,
                 color=c_kwarg_defaults['colors'])


def tsdiagram(salt, temp, color=None, size=None,
              lon=None, lat=None, pressure=None,
              convert_teos10=True, ts_kwargs={},
              ax=None, fig=None, draw_density_contours=True,
              draw_cbar=True, add_labels=True,
              **kwargs):
    if ax is None:
        ax = plt.gca()

    if fig is None:
        fig = plt.gcf()

    if convert_teos10:
        temp_label = 'Conservative Temperature [$^{\circ}C$]'
        salt_label = 'Absolute Salinity [$g/kg$]'
        if any([a is None for a in [lon, lat, pressure]]):
            raise ValueError('when converting to teos10 variables, \
                             input for lon, lat and pressure is needed')
        else:
            salt = gsw.SA_from_SP(salt, pressure, lon, lat)
            temp = gsw.CT_from_pt(salt, temp)
    else:
        temp_label = 'Potential Temperature [$^{\circ}C$]'
        salt_label = 'Practical Salinity [$g/kg$]'

    if add_labels:
        ax.set_xlabel(salt_label)
        ax.set_ylabel(temp_label)

    scatter_kw_defaults = dict(s=size, c=color)
    scatter_kw_defaults.update(kwargs)
    s = ax.scatter(salt, temp, **scatter_kw_defaults)
    if draw_density_contours:
        draw_dens_contours_teos10(ax=ax, **ts_kwargs)
    if draw_cbar and color is not None:
        if isinstance(color, str) or isinstance(color, tuple):
            pass
        elif isinstance(color, list) or isinstance(color, np.ndarray) or \
                isinstance(color, xr.DataArray):
            fig.colorbar(s, ax=ax)
        else:
            raise RuntimeError('`color` not recognized. %s' % type(color))
    return s
