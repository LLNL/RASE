###############################################################################
# Copyright (c) 2018-2022 Lawrence Livermore National Security, LLC.
# Produced at the Lawrence Livermore National Laboratory
#
# Written by J. Brodsky, S. Czyz
# RASE-support@llnl.gov.
#
# LLNL-CODE-829509
#
# All rights reserved.
#
# This file is part of RASE.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED,INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
###############################################################################


import numpy as np
from .dynamic_models import SphericalCoordsTransformer, InverseR2TargetTransformer
from matplotlib import pyplot as plt
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D


class _PlotTools:

    def __init__(self):
        self.transformer = SphericalCoordsTransformer()

    def _position_and_points(self, spectra, bin):

        xyz = np.array([(spec.x, spec.y, spec.z) for spec in spectra])
        counts = np.array([spec.counts[bin] / spec.livetime * spec.sensitivity for spec in spectra])
        errors = np.array([np.sqrt(spec.counts[bin]) / spec.livetime for spec in spectra])
        t_position = self.transformer.transform(xyz)
        livetimes = np.array([spec.livetime/spec.sensitivity for spec in spectra])

        return xyz, counts, errors, t_position, livetimes


class Plot3D(_PlotTools):

    def __init__(self):
        super(Plot3D, self).__init__()
        self.func_dict = {
                            'plot_3D_model': self.plot_3D_model,
                            'plot_3D_train': self.plot_3D_points,
                            'plot_3D_test': self.plot_3D_points,
                            'plot_3D_train_colored_by_model': self.plot_3D_points_colored_by_model,
                            'plot_3D_test_colored_by_model': self.plot_3D_points_colored_by_model,
                            'plot_3D_path': self.plot_3D_path
                         }


    def init_plot(self, plot_def=None):
        self.plot_def = plot_def
        self._make_fig()
        self._create_plot_bounds()


    def _make_fig(self, num_subplots=0):
        if num_subplots > 0:
            pass  # for later
        else:
            self.fig = plt.figure(figsize=(9, 9), dpi=80)
            self.ax = self.fig.add_subplot(projection='3d')
            self.fig.tight_layout()

    def _create_plot_bounds(self):
        if self.plot_def and ('limits' in self.plot_def.keys()):
            if 'X' in self.plot_def['limits'].keys():
                assert len(self.plot_def['limits']['X']) == 2, f"Plot X limits ({self.plot_def['limits']['X']}) should be two numbers."
                [x_min, x_max] = self.plot_def['limits']['X']
            else:
                [x_min, x_max] = [-301, 301]

            if 'Y' in self.plot_def['limits'].keys():
                assert len(self.plot_def['limits']['Y']) == 2, f"Plot Y limits ({self.plot_def['limits']['Y']}) should be two numbers."
                [y_min, y_max] = self.plot_def['limits']['Y']
            else:
                [y_min, y_max] = [29, 301]
        else:
            [x_min, x_max] = [-301, 301]
            [y_min, y_max] = [29, 301]

        spacing_x = ((x_max + .2 * (x_max - x_min)) - (x_min - .2 * (x_max - x_min))) / 200
        spacing_y = ((y_max + .2 * (y_max - y_min)) - (y_min - .2 * (y_max - y_min))) / 200
        self.xx, self.yy, self.zz = np.meshgrid(np.arange(x_min - .2 * (x_max - x_min), x_max + .2 * (x_max - x_min),
                                                  spacing_x), np.arange(y_min, y_max + .2 * (y_max - y_min),
                                                                        spacing_y), 0)
        sphere_grid = SphericalCoordsTransformer.cart_to_sphere(np.stack((self.xx.ravel(), self.yy.ravel(),
                                                                               self.zz.ravel()), -1))
        self.rr = sphere_grid[:, 0]
        self.pp = sphere_grid[:, 1]
        self.tt = sphere_grid[:, 2]


    def plot_3D_model(self, model, plot_type):

        model_z = model.predict(np.c_[self.xx.ravel(), self.yy.ravel(), self.zz.ravel()],
                                return_model=(plot_type != 'real'))
        model_z = model_z.reshape((self.xx.shape[0], self.xx.shape[1]))
        #consider adding rcount=100, ccount=100 to make 3D plots smoother
        if plot_type == 'real':
            self.ax.plot_surface(self.xx[:, :, 0], self.yy[:, :, 0], model_z, cmap=cm.coolwarm, alpha=.5)
        else:
            self.ax.plot_surface(self.xx[:, :, 0], self.yy[:, :, 0], model_z, cmap=cm.coolwarm, alpha=.5, vmin=-1.2, vmax=0.2)
        try:
            self.ax.set_title(str(model.gp.kernel_),pad=-20)
        except AttributeError:
            self.ax.set_title('Blank Model')

    def plot_3D_points(self, spectra, plot_type, bin, model, plot_error):

        xyz, counts, errors, t_position, livetimes = self._position_and_points(spectra, bin)

        if plot_type == 'real' or (counts==0).all():
            self.ax.scatter3D(xyz[:, 0], xyz[:, 1], counts, edgecolor='k', facecolor='r', s=60)
            if plot_error:
                for pos, cnt, err in zip(xyz, counts, errors):
                    self.ax.plot([pos[0], pos[0]], [pos[1], pos[1]], [cnt + err, cnt - err], color='r', marker="_")

        else:
            self.ax.scatter3D(xyz[:, 0], xyz[:, 1], model.y_transformer.transform(np.reshape(t_position, (-1,3)), counts),
                              edgecolor='k', facecolor='r', s=60)
            if plot_error:
                tcounts = model.y_transformer.transform(np.reshape(t_position, (-1, 3)), counts)
                terrors = model.y_transformer.point_variances(np.reshape(t_position, (-1, 3)), counts, livetimes)**0.5
                for pos, tcnt, terr in zip(xyz, tcounts, terrors):
                    self.ax.plot([pos[0], pos[0]], [pos[1], pos[1]], [tcnt + terr, tcnt - terr], color='r', marker="_")


    def plot_3D_points_colored_by_model(self, spectra, plot_type, bin, model, plot_error):

        xyz, counts, errors, t_position,livetimes = self._position_and_points(spectra, bin)

        for pos, tpos, cnt, err, livetime in zip(xyz, t_position, counts, errors,livetimes):
            marker = 'o'
            if (cnt > 0) and (cnt - model.predict(np.c_[pos[0], pos[1], pos[2]])) / cnt < -0.05:
                color = 'b'
                if (cnt - model.predict(np.c_[pos[0], pos[1], pos[2]])) / cnt < -0.2:
                    marker = '^'
                if (cnt - model.predict(np.c_[pos[0], pos[1], pos[2]])) / cnt < -0.5:
                    marker = 's'
            elif (cnt > 0) and (cnt - model.predict(np.c_[pos[0], pos[1], pos[2]])) / cnt > 0.05:
                color = 'r'
                if (cnt - model.predict(np.c_[pos[0], pos[1], pos[2]])) / cnt > 0.2:
                    marker = '^'
                if (cnt - model.predict(np.c_[pos[0], pos[1], pos[2]])) / cnt > 0.5:
                    marker = 's'
            else:
                color = 'g'

            if plot_error:
                if (cnt > 0) and abs(err / cnt) > 0.05:
                    eclr = 'm'
                elif (cnt > 0) and abs(err / cnt) > 0.02:
                    eclr = 'c'
                else:
                    eclr = 'k'

            if plot_type == 'real' or (counts==0).all():
                self.ax.scatter3D(pos[0], pos[1], cnt, marker=marker, edgecolor='k', facecolor=color, s=60)
                if plot_error:
                    self.ax.plot([pos[0], pos[0]], [pos[1], pos[1]], [cnt + err, cnt - err], color=eclr, marker="_")
            else:
                self.ax.scatter3D(pos[0], pos[1], model.y_transformer.transform(np.reshape(tpos, (-1,3)), cnt),
                              marker=marker,  edgecolor='k', facecolor=color, s=60)
                if plot_error:
                    tcnt = model.y_transformer.transform(np.reshape(tpos, (-1, 3)), cnt)[0]
                    terr = model.y_transformer.point_variances(np.reshape(tpos, (-1, 3)), cnt, livetime)[0] **0.5
                    self.ax.plot([pos[0], pos[0]], [pos[1], pos[1]], [tcnt + terr, tcnt - terr], color=eclr, marker="_")

    def plot_3D_path(self):
        assert self.plot_def, "No plot_def defined."


class Plot2D(_PlotTools):

    def __init__(self):
        super(Plot2D, self).__init__()
        self.func_dict = {
                            'plot_2D_fixed_phi': self.plot_2D_fixed_phi,
                            'plot_2D_fixed_radius': self.plot_2D_fixed_radius,
                            'plot_2D_fixed_line': self.plot_2D_fixed_line
                         }


    def init_plot(self, plot_def=None):
        self.plot_def = plot_def
        self._make_fig()


    def _make_fig(self, num_subplots=0):
        if num_subplots > 0:
            pass  # for later
        else:
            self.fig = plt.figure(figsize=(9, 9), dpi=80)
            self.ax = self.fig.gca()
            # self.fig.tight_layout()


    def _set_2D_bounds_slice(self, t_position, t_point, index):

        if self.plot_def and 'limits' in self.plot_def.keys():
            t_limits = []
            for [x, y, z] in zip(self.plot_def['limits']['X'], self.plot_def['limits']['Y'],
                                 self.plot_def['limits']['Z']):
                t_limits.append(self.transformer.transform(np.reshape([x,y,z], (-1, 3)))[0])

            min_in_space = np.min(np.array(t_limits), axis=0)[index]
            if index == 0:
                min_in_space = max(min_in_space, 0)
            max_in_space = np.max(np.array(t_limits), axis=0)[index]

            assert min_in_space < max_in_space

        else:
            scale_bounds_factor = 1.1  # plot slightly further than bounds
            if index == 0:
                min_in_space = 0
            elif index == 2:
                scale_bounds_factor = 1
                min_in_space = min([t_pos[index] for t_pos in t_position]) * scale_bounds_factor
            else:
                raise ValueError('Plotting for phi not implemented')

            max_in_space = max([t_pos[index] for t_pos in t_position] + [t_point[index]]) * scale_bounds_factor

        self.plot_dimensions = np.linspace(min_in_space, max_in_space, 101)


    def _find_spec_counts_in_slice(self, spectra, xyz, t_position, t_point, bin, index):

        positions = [(c_pos, t_loc) for c_pos, t_loc in zip(xyz, t_position) if t_loc[index] == t_point[index]]

        if not positions:
            return [], []

        xyz_in_2D, t_pos_in_2D = zip(*positions)

        counts_to_plot = [spec.counts[bin] / spec.livetime for spec in spectra if
                            any(np.equal([spec.x, spec.y, spec.z], xyz_in_2D).all(1))]
        errors_to_plot = [np.sqrt(spec.counts[bin]) / spec.livetime for spec in spectra if
                            any(np.equal([spec.x, spec.y, spec.z], xyz_in_2D).all(1))]

        return t_pos_in_2D, counts_to_plot, errors_to_plot


    def _order_user_points_line(self, points):
        for index in range(3):
            if points[0, index] > points[1, index]:
                break
            elif points[1, index] < points[0, index]:
                temp = points[1]
                points[1] = points[0]
                points[0] = temp
                break
        return points


    def _set_2D_bounds_line(self, points):
        distance = np.linalg.norm(points[1] - points[0])
        self.plot_dimensions = np.linspace(0, distance, 101)


    def _find_spec_points_on_line(self, xyz, t_position, points):
        line_diffs = points[1] - points[0]

        positions = [(c_pos, t_pos) for c_pos, t_pos in zip(xyz, t_position) if
                               (np.cross(line_diffs, np.array(c_pos) - points[0]) == 0).all()]
        if not positions:
            return [], []

        xyz_in_2D_orig, t_pos_in_2D_orig = zip(*positions)

        xyz_in_2D = []
        t_pos_in_2D = []
        for pos, t_pos in zip(xyz_in_2D_orig, t_pos_in_2D_orig):
            passed = 0
            for i in range(len(pos)):
                if not (pos[i] <= max(points[:,i]) and pos[i] >= min(points[:,i])):
                    break
                passed += 1
            if passed == len(pos):
                xyz_in_2D.append(pos)
                t_pos_in_2D.append(t_pos)

        return xyz_in_2D, t_pos_in_2D


    def _sort_xyz_2D_line(self, xyz_in_2D, spec_t_pos, points):
        idx = np.argsort(np.linalg.norm(xyz_in_2D - points[0], axis=1))
        new_xyz_in_2D = list(np.array(xyz_in_2D)[idx])
        new_spec_t_pos = list(np.array(spec_t_pos)[idx])

        return new_xyz_in_2D, new_spec_t_pos


    def _set_2D_steps_line(self, points, xyz_in_2D):
        linspace_length = 100
        step_sizes = (points[1] - points[0]) / linspace_length
        steps_xyz = [points[0]]
        xyz_index = 0
        points_added = 0

        for step in range(linspace_length):
            new_step = steps_xyz[step + points_added] + step_sizes
            if xyz_index < len(xyz_in_2D):
                if np.linalg.norm(new_step - points[0]) > np.linalg.norm(xyz_in_2D[xyz_index] - points[0]):
                    steps_xyz.append(xyz_in_2D[xyz_index])
                    points_added += 1
                    xyz_index += 1
                elif np.linalg.norm(new_step - points[0]) == np.linalg.norm(xyz_in_2D[xyz_index] - points[0]):
                    xyz_index += 1
            steps_xyz.append(new_step)

        return np.array(steps_xyz)


    def _find_spec_counts_in_line(self, spectra, bin, xyz_in_2D):

        counts_to_plot = []
        errors_to_plot = []
        for pos in xyz_in_2D:
            for spec in spectra:
                if all(np.equal([spec.x, spec.y, spec.z], pos)):
                    counts_to_plot.append(spec.counts[bin] / spec.livetime)
                    errors_to_plot.append(np.sqrt(spec.counts[bin]) / spec.livetime)
                    break

        return np.array(counts_to_plot), np.array(errors_to_plot)


    def _plot_2D_fixed(self, spectra, train_xyz, point, plot_type, bin, model, plot_error, dimension_to_vary, dimension_to_fix):

        xyz, counts, errors, t_position = self._position_and_points(spectra, bin)
        t_point = self.transformer.transform(np.reshape(point, (-1, 3)))[0]

        spec_t_pos, spec_counts, spec_errs = self._find_spec_counts_in_slice(spectra, xyz, t_position, t_point, bin, index=dimension_to_fix)

        self._set_2D_bounds_slice(t_position, t_point, dimension_to_vary)

        if dimension_to_vary == 0:
            model_points = self.transformer.sphere_to_cart(np.vstack([self.plot_dimensions,
                                                                      np.ones(np.shape(self.plot_dimensions)) * t_point[1],
                                                                      np.ones(np.shape(self.plot_dimensions)) * t_point[2]]).T)
        elif dimension_to_vary == 2:
            model_points = self.transformer.sphere_to_cart(np.vstack([np.ones(np.shape(self.plot_dimensions)) * t_point[0],
                                                                      np.ones(np.shape(self.plot_dimensions)) * t_point[1],
                                                                      self.plot_dimensions]).T)

        model_curve = model.predict(model_points, return_model=(plot_type != 'real'))
        self.ax.plot(self.plot_dimensions, model_curve)
        x_label = ['Radius [cm]', 'Theta [rad]', 'Phi [rad]']
        self.ax.set_xlabel(x_label[dimension_to_vary], fontsize=15)
        if plot_type == 'real' or (counts == 0).all():
            self.ax.scatter(np.reshape(spec_t_pos, (-1, 3))[:, dimension_to_vary], spec_counts, color='r')
            if plot_error:
                for t_pos, cnt, err in zip(spec_t_pos, spec_counts, spec_errs):
                    self.ax.plot([t_pos[dimension_to_vary], t_pos[dimension_to_vary]], [cnt + err, cnt - err], color='r', marker="_")
            self.ax.set_ylabel('cps/bin', fontsize=15)
        else:
            self.ax.scatter(np.reshape(spec_t_pos, (-1, 3))[:, dimension_to_vary], model.y_transformer.transform(
                np.reshape(spec_t_pos, (-1, 3)), spec_counts), color='r')
            if plot_error:
                tcounts = model.y_transformer.transform(np.reshape(spec_t_pos, (-1, 3)), spec_counts)
                terrors = model.y_transformer.transform(np.reshape(spec_t_pos, (-1, 3)), spec_errs) + 1
                for t_pos, tcnt, terr in zip(spec_t_pos, tcounts, terrors):
                    self.ax.plot([t_pos[dimension_to_vary], t_pos[dimension_to_vary]], [tcnt + terr, tcnt - terr], color='r', marker="_")
            self.ax.set_ylabel('cps/bin, scaled by 1/r^2', fontsize=15)


    def plot_2D_fixed_phi(self, spectra, train_xyz, point, plot_type, bin, model, plot_error):
        assert len(point) == 3, "Provide 3D point for plotting."

        dimension_to_vary = 0
        dimension_to_fix = 2
        self._plot_2D_fixed(spectra, train_xyz, point, plot_type, bin, model, plot_error, dimension_to_vary, dimension_to_fix)


    def plot_2D_fixed_radius(self, spectra, train_xyz, point, plot_type, bin, model, plot_error):
        assert len(point) == 3, "Provide 3D point for plotting."

        dimension_to_vary = 2
        dimension_to_fix = 0
        self._plot_2D_fixed(spectra, train_xyz, point, plot_type, bin, model, plot_error, dimension_to_vary, dimension_to_fix)


    def plot_2D_fixed_line(self, spectra, train_xyz, points, plot_type, bin, model, plot_error):
        assert len(points) == 2, "Provide two points"
        assert len(points[0]) == 3, "Each point must be 3D"
        assert len(points[1]) == 3, "Each point must be 3D"
        assert points[0] != points[1], "A line required two different points"

        points = np.array(points)

        points = self._order_user_points_line(points)
        self._set_2D_bounds_line(points)

        xyz, _, _, t_position = self._position_and_points(spectra, bin)

        xyz_in_2D, spec_t_pos = self._find_spec_points_on_line(xyz, t_position, points)
        xyz_in_2D, spec_t_pos = self._sort_xyz_2D_line(xyz_in_2D, spec_t_pos, points)
        model_points = self._set_2D_steps_line(points, xyz_in_2D)
        spec_counts, spec_errs = self._find_spec_counts_in_line(spectra, bin, xyz_in_2D)

        model_curve = model.predict(model_points, return_model=(plot_type != 'real'))

        self.ax.plot(['[%s]' % ', '.join(map(str, ['{:.1f}'.format(p) for p in mp])) for mp in model_points], model_curve)

        for n, label in enumerate(self.ax.xaxis.get_ticklabels()):
            if n % int((len(model_points)-2) / 6) != 0:
                label.set_visible(False)
        for n, tick in enumerate(self.ax.xaxis.get_major_ticks()):
            if n % int((len(model_points)-2) / 6) != 0:
                tick.set_visible(0)

        if plot_type != 'real':
            spec_counts = model.y_transformer.transform(np.reshape(spec_t_pos, (-1, 3)), spec_counts)
            spec_errs = (model.y_transformer.transform(np.reshape(spec_t_pos, (-1, 3)), spec_errs) + 1)

        for pos, cnt, err in zip(xyz_in_2D, spec_counts, spec_errs):
            if any(np.equal(pos, train_xyz).all(1)):
                clr = 'r'
            else:
                clr = 'b'
            self.ax.scatter([str(list(pos))], cnt, color=clr)
            if plot_error:
                self.ax.plot([str(list(pos)), str(list(pos))], [cnt + err, cnt - err], color='k', marker="_")
