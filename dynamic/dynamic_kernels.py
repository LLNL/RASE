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
from sklearn.gaussian_process.kernels import Kernel, Hyperparameter, StationaryKernelMixin, NormalizedKernelMixin, \
    _check_length_scale, _approx_fprime
from scipy.spatial.distance import cdist, squareform, pdist
import numpy as np
import warnings


class SphericalKernel(StationaryKernelMixin, NormalizedKernelMixin, Kernel):
    """from https://epubs.siam.org/doi/pdf/10.1137/15M1032740
    greater tau scale = faster change
    Assumes the input is an array of (r,theta,phi) entries.
        Should also work if the input is in (r,theta) [2d]
        This kernel only applies to theta and phi; r is not touched at all. So, combine with a separate kernel for r.
    """

    def __init__(self, tau=100.0, tau_bounds=(4., 1e5)):
        self.tau = tau
        # assert (np.min(tau_bounds) >= 4)  # required by source paper.
        self.tau_bounds = tau_bounds

    @property
    def anisotropic(self):
        return np.iterable(self.tau) and len(self.tau) > 1

    @property
    def hyperparameter_tau(self):
        if self.anisotropic:
            return Hyperparameter("tau", "numeric",
                                  self.tau_bounds,
                                  len(self.tau))
        return Hyperparameter(
            "tau", "numeric", self.tau_bounds)

    def angle_delta(self, X,Y): #assume X, Y have radius stripped off
        pairwise_diffs = X[:, np.newaxis] - Y[np.newaxis]
        return np.arccos(np.cos(pairwise_diffs)) / np.pi

    def __call__(self, X, Y=None, eval_gradient=False):
        """Return the kernel k(X, Y) and optionally its gradient.

        Parameters
        ----------
        X : array, shape (n_samples_X, n_features)
            Left argument of the returned kernel k(X, Y)

        Y : array, shape (n_samples_Y, n_features), (optional, default=None)
            Right argument of the returned kernel k(X, Y). If None, k(X, X)
            if evaluated instead.

        eval_gradient : bool (optional, default=False)
            Determines whether the gradient with respect to the kernel
            hyperparameter is determined. Only supported when Y is None.

        Returns
        -------
        K : array, shape (n_samples_X, n_samples_Y)
            Kernel k(X, Y)

        K_gradient : array (opt.), shape (n_samples_X, n_samples_X, n_dims)
            The gradient of the kernel k(X, X) with respect to the
            hyperparameter of the kernel. Only returned when eval_gradient
            is True.
        """
        X = np.atleast_2d(X)
        tau = np.squeeze(self.tau).astype(float)
        angle_dim = X.shape[1] - 1  # assume first dimension is radius
        if angle_dim < 1 or angle_dim > 2:
            raise ValueError("Input data should be in form (r,theta,phi) or (r,theta)")
        if np.ndim(tau) > 1:
            raise ValueError("tau cannot be of dimension greater than 1")
        if np.ndim(tau) == 1 and angle_dim != tau.shape[0]:
            raise ValueError("Anisotropic tau kernel must have one fewer "
                             "dimensions than data (%d+1!=%d)"
                             % (tau.shape[0], X.shape[1]))
        if not self.anisotropic:
            tau = np.full((2,), tau)

        if Y is None:
            Y=X
            # DD = X[:, np.newaxis] - X[np.newaxis]  # pairwise subtraction


        angle_delta = self.angle_delta(X[:,1:], Y[:,1:])
        dt = angle_delta[:, :, 0]
        if angle_dim == 2:
            dp = angle_delta[:,:,1]
            Wp = (1 + tau[1] * dp) * ((1 - dp) ** tau[1])
        else:
            dp = np.zeros(dt.shape)
            Wp = np.ones(dt.shape)

        Wt = (1 + tau[0] * dt) * ((1 - dt) ** tau[0])

        K = Wp * Wt  # returned kernel matrix

        if eval_gradient:
            # gradients calculated using mathematica. No promises the math is right
            if self.hyperparameter_tau.fixed:
                # Hyperparameter l kept fixed
                return K, np.empty((X.shape[0], X.shape[0], 0))
            elif not self.anisotropic:
                z = tau[0]
                if angle_dim == 2:
                    derivative = (1 - dp) ** z * (1 - dt) ** z * \
                                 (dp + dt + 2 * dp * dt * z +
                                  (1 + dp * z) * (1 + dt * z) * np.log(1 - dp) +
                                  (1 + dp * z) * (1 + dt * z) * np.log(1 - dt)
                                  )
                else:
                    derivative = ((1 - dt) ** tau) * (dt + (1 + dt * tau) * np.log(1 - dt))
                K_gradient = derivative[:, :, np.newaxis]
                return K, K_gradient
            elif self.anisotropic:
                assert angle_dim == 2 , f"SphericalKernel set to anisotropic but also to use {angle_dim} dimensions. " \
                                        f"That doesn't make sense."
                dpm = np.minimum(1-1e-5,dp)
                dtm = np.minimum(1 - 1e-5, dt)
                deriv_t = ((1 - dt) ** tau[0]) * (dt + (1 + dt * tau[0]) * np.log(1 - dtm)) * Wp
                deriv_p = ((1 - dp) ** tau[1]) * (dp + (1 + dp * tau[1]) * np.log(1 - dpm)) * Wt
                K_gradient = np.stack((deriv_t, deriv_p), -1)
                return K, K_gradient
        else:
            return K

    def __repr__(self):
        if self.anisotropic:
            return "{0}(tau=[{1}])".format(
                self.__class__.__name__, ", ".join(map("{0:.3g}".format,
                                                       self.tau)))
        else:  # isotropic
            return "{0}(tau={1:.3g})".format(
                self.__class__.__name__, np.ravel(self.tau)[0])


class SphericalKernelChordal(SphericalKernel):
    def angle_delta(self, X,Y):
        pairwise_diffs = X[:, np.newaxis] - Y[np.newaxis]
        return np.abs(np.sin(pairwise_diffs/2))




class SymmetricAngleKernel(SphericalKernel):
    @classmethod
    def construct(self, tau=100.0, tau_bounds=(4., 1e5), thetaReflection=0, thetaReflection_bounds= (0,np.pi*2), phiReflection=0, phiReflection_bounds= (0,np.pi*2)):
        return SymmetricAngleKernel(tau=tau, tau_bounds=tau_bounds,
                                    thetaReflection=np.exp(thetaReflection), thetaReflection_bounds=np.exp(thetaReflection_bounds),
                                    phiReflection=np.exp(phiReflection),phiReflection_bounds=np.exp(phiReflection_bounds))

    def __init__(self, tau=100.0, tau_bounds=(4., 1e5), thetaReflection=np.exp(0), thetaReflection_bounds= np.exp((0,np.pi)), phiReflection=np.exp(0), phiReflection_bounds= np.exp((0,np.pi))):
        self.tau = tau
        if np.min(tau_bounds) < 4:
            warnings.warn("According to the paper this kernel was sourced from, tau must not be <4. Don't set the bounds for tau below 4.")
        self.tau_bounds = tau_bounds
        self.thetaReflection = thetaReflection
        self.thetaReflection_bounds = thetaReflection_bounds
        self.phiReflection = phiReflection
        self.phiReflection_bounds = phiReflection_bounds


    @property
    def hyperparameter_thetaReflection(self):
        return Hyperparameter(
            "thetaReflection", "numeric", self.thetaReflection_bounds)

    @property
    def hyperparameter_phiReflection(self):
        return Hyperparameter(
            "phiReflection", "numeric", self.phiReflection_bounds)

    def angle_delta(self, X,Y): ##dd is
        angle_dim = X.shape[1]  # assume first dimension is radius
        if angle_dim == 1:
            reflection =  np.log((self.thetaReflection, ))
        else:
            reflection = np.log((self.thetaReflection, self.phiReflection))
        X_distance_from_axis = np.arccos(np.cos(X-reflection))
        Y_distance_from_axis = np.arccos(np.cos(Y - reflection))
        pairwise_diffs = X_distance_from_axis[:, np.newaxis] - Y_distance_from_axis[np.newaxis]
        return np.arccos(np.cos(pairwise_diffs)) / np.pi

    def is_stationary(self):
        return False

    def __call__(self, X, Y=None, eval_gradient=False ):
        if not eval_gradient:
            return SphericalKernel.__call__(self,X, Y, eval_gradient)
        else:
            epsilon = 1e-8
            kernel, taugradient = SphericalKernel.__call__(self,X, Y, eval_gradient)
            origthetaRefl = self.thetaReflection
            self.thetaReflection += epsilon
            plusTK = SphericalKernel.__call__(self,X, Y)
            self.thetaReflection -= 2*epsilon
            minusTK = SphericalKernel.__call__(self, X, Y)
            # delta_thetaR = (SphericalKernel.__call__(self,X, Y) - kernel) / epsilon
            delta_thetaR = (plusTK - minusTK)/(2*epsilon)
            self.thetaReflection = origthetaRefl

            origphiRefl = self.phiReflection
            self.phiReflection += epsilon
            plusPK = SphericalKernel.__call__(self,X, Y)
            self.phiReflection -= 2*epsilon
            minusPK = SphericalKernel.__call__(self, X, Y)
            # delta_phiR = (SphericalKernel.__call__(self,X, Y) - kernel) / epsilon
            delta_phiR = (plusPK - minusPK)/(2*epsilon)
            self.phiReflection = origphiRefl

            allgradient = np.concatenate((delta_phiR[:,:,None], taugradient, delta_thetaR[:,:,None]), axis=2)
            return kernel, allgradient

    def __repr__(self):
        return f'{self.__class__.__name__} (tau = {self.tau}, thetaRefl = {np.log(self.thetaReflection)}, phiRefl = {np.log(self.phiReflection)})'


class NSRadialKernel(NormalizedKernelMixin, Kernel):

    def __init__(self, length_scale=1.0, length_scale_bounds=(1e-5, 1e5), scale_exponent = 1, scale_exponent_bounds=(1e-10,3)):
        self.length_scale = length_scale
        self.length_scale_bounds = length_scale_bounds
        self.scale_exponent = scale_exponent
        self.scale_exponent_bounds = scale_exponent_bounds

    def is_stationary(self):
        """Returns whether the kernel is stationary. """
        return False

    @property
    def hyperparameter_length_scale(self):

        return Hyperparameter(
            "length_scale", "numeric", self.length_scale_bounds)

    @property
    def hyperparameter_scale_exponent(self):
        return Hyperparameter(
            "scale_exponent", "numeric", self.scale_exponent_bounds)

    def safe_lengthscale(self,lengthscale):
        lengthscale[lengthscale==0] = lengthscale.min()
        return lengthscale


    def __call__(self, X, Y=None, eval_gradient=False):
        """Return the kernel k(X, Y) and optionally its gradient.

        Parameters
        ----------
        X : array, shape (n_samples_X, n_features)
            Left argument of the returned kernel k(X, Y)

        Y : array, shape (n_samples_Y, n_features), (optional, default=None)
            Right argument of the returned kernel k(X, Y). If None, k(X, X)
            if evaluated instead.

        eval_gradient : bool (optional, default=False)
            Determines whether the gradient with respect to the kernel
            hyperparameter is determined. Only supported when Y is None.

        Returns
        -------
        K : array, shape (n_samples_X, n_samples_Y)
            Kernel k(X, Y)

        K_gradient : array (opt.), shape (n_samples_X, n_samples_X, n_dims)
            The gradient of the kernel k(X, X) with respect to the
            hyperparameter of the kernel. Only returned when eval_gradient
            is True.
        """
        X = X[:,0,None]
        if Y is None:
            Y=X
        else:
            Y=Y[:,0,None]

        X = np.atleast_2d(X)
        length_scale = _check_length_scale(X, self.length_scale)
        if Y is None:
            length_scale= self.safe_lengthscale(length_scale*X**self.scale_exponent)
            dists = pdist(X/(np.sqrt(2)*length_scale) , metric='sqeuclidean')

            K = np.exp(-.5 * dists)
            # convert from upper-triangular matrix to square matrix
            K = squareform(K)
            np.fill_diagonal(K, 1)
        else:
            if eval_gradient and not np.array_equal(X,Y):
                raise ValueError(
                    "Gradient can only be evaluated when Y is None.")
            # length_scale = self.safe_lengthscale((length_scale*X**self.scale_exponent+length_scale*Y.ravel()**self.scale_exponent))
            dists = cdist(X , Y ,
                          metric='sqeuclidean')
            dists /= (self.safe_lengthscale((length_scale*X**self.scale_exponent))**2+ self.safe_lengthscale(length_scale*Y.ravel()**self.scale_exponent)**2)
            K = np.exp(-.5 * dists)

        if eval_gradient:

            if not self.hyperparameter_length_scale.fixed:
                def f(scale):  # helper function
                    old = self.length_scale
                    self.length_scale = scale
                    res = self(X, Y, eval_gradient=False)
                    self.length_scale=old
                    return res

                length_scale_gradient = _approx_fprime((self.length_scale,),f,1e-5)
            else:  # l is kept fixed
                length_scale_gradient = np.empty((K.shape[0], K.shape[1], 0))

            if not self.hyperparameter_scale_exponent.fixed:
                def f(expon):
                    old=self.scale_exponent
                    self.scale_exponent=expon
                    res=self(X,Y,eval_gradient=False)
                    self.scale_exponent=old
                    return res
                scale_exponent_gradient = _approx_fprime((self.scale_exponent,),f,1e-5)
            else:  # l is kept fixed
                scale_exponent_gradient = np.empty((K.shape[0], K.shape[1], 0))

            return K, np.dstack((length_scale_gradient, scale_exponent_gradient))
        else:
            return K

    def __repr__(self):
        return f"{self.__class__.__name__}({self.length_scale,self.scale_exponent})"