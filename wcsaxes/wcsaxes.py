import numpy as np

from matplotlib.axes import Axes
from matplotlib.lines import Line2D
from matplotlib.transforms import Affine2D

from astropy.wcs import WCS

from .transforms import (WCSPixel2WorldTransform, WCSWorld2PixelTransform,
                         CoordinateTransform)
from .grid_helpers import SkyCoordinatesMap
from .utils import get_coordinate_system


class WCSAxes(Axes):

    def __init__(self, fig, rect, wcs=None, **kwargs):

        self.wcs = wcs

        super(WCSAxes, self).__init__(fig, rect, **kwargs)

        # Turn off spines and current axes

        for s in self.spines.values():
            s.set_visible(False)

        self.xaxis.set_visible(False)
        self.yaxis.set_visible(False)

        # Here determine all the coordinate axes that should be shown.

        self.coords = SkyCoordinatesMap(self, self.wcs)

    def _get_bounding_frame(self):
        """
        Return the bounding frame of the axes.
        """
        xmin, xmax = self.get_xlim()
        ymin, ymax = self.get_ylim()
        return [xmin, xmax, xmax, xmin, xmin], [ymin, ymin, ymax, ymax, ymin]

    def _sample_bounding_frame(self, n_samples):
        """
        Return n points equally spaced around the frame.
        """
        x, y = self._get_bounding_frame()
        p = np.linspace(0., 1., len(x))
        p_new = np.linspace(0., 1., n_samples)
        return np.interp(p_new, p, x), np.interp(p_new, p, y)

    def draw(self, renderer, inframe=False):

        super(WCSAxes, self).draw(renderer, inframe)

        x, y = self._get_bounding_frame()
        line = Line2D(x, y, transform=self.transData, color='purple')
        line.draw(renderer)

        # Here need to find out range of all coordinates, and update range for
        # each coordinate axis. For now, just assume it covers the whole sky.

        self.coords[0]._update_ticks(coord_range=[-180., 180.])
        self.coords[1]._update_ticks(coord_range=[-89.999, 89.999])

        self.coords[0].draw(renderer)
        self.coords[1].draw(renderer)

    def get_transform(self, frame, equinox=None, obstime=None):

        if self.wcs is None and frame != 'pixel':
            raise ValueError('No WCS specified, so only pixel coordinates are available')

        if isinstance(frame, WCS):

            coord_in = get_coordinate_system(frame)
            coord_out = get_coordinate_system(self.wcs)

            if coord_in == coord_out:

                return (WCSPixel2WorldTransform(frame)
                        + WCSWorld2PixelTransform(self.wcs)
                        + self.transData)

            else:

                return (WCSPixel2WorldTransform(frame)
                        + CoordinateTransform(coord_in, coord_out)
                        + WCSWorld2PixelTransform(self.wcs)
                        + self.transData)

        elif frame == 'pixel':

            return Affine2D() + self.transData

        else:

            from astropy.coordinates import FK5, Galactic

            world2pixel = WCSWorld2PixelTransform(self.wcs) + self.transData

            coord_class = get_coordinate_system(self.wcs)

            if frame == 'world':

                return world2pixel

            elif frame == 'fk5':

                if coord_class is FK5:
                    return world2pixel
                else:
                    return (CoordinateTransform(FK5, coord_class)
                            + world2pixel)

            elif frame == 'galactic':

                if coord_class is Galactic:
                    return world2pixel
                else:
                    return (CoordinateTransform(Galactic, coord_class)
                            + world2pixel)

            else:

                raise NotImplemented("frame {0} not implemented".format(frame))
