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

from abc import ABC, abstractmethod
from sklearn.base import TransformerMixin, BaseEstimator, RegressorMixin
from sklearn.gaussian_process import GaussianProcessRegressor

from sklearn.linear_model import LinearRegression
from sklearn.gaussian_process.kernels import RBF
from dynamic.dynamic_kernels import SphericalKernel, NSRadialKernel, SphericalKernelChordal, SymmetricAngleKernel
from src.table_def import *
from tqdm import tqdm
import copy

from dynamic import dynamic_data_handling as ddh



class SphericalCoordsTransformer(TransformerMixin,BaseEstimator):
    def fit(self,X=None,y=None): #required by transformer mixin property
        return self
    def transform(self, X):
        return self.cart_to_sphere(X)
    @classmethod
    def cart_to_sphere(cls, xyz):
        ptsnew = np.zeros(xyz.shape)
        xy = xyz[:, 0] ** 2 + xyz[:, 1] ** 2
        ptsnew[:, 0] = np.sqrt(xy + xyz[:, 2] ** 2)
        ptsnew[:, 1] = np.arctan2(xyz[:, 2], np.sqrt(xy))  # for elevation angle defined from XY-plane up
        ptsnew[:, 2] = np.arctan2(xyz[:, 1], xyz[:, 0])
        return ptsnew

    @classmethod
    def sphere_to_cart(cls, rpt):
        xyznew = np.zeros(rpt.shape)
        xyznew[:, 0] = rpt[:, 0] * np.cos(rpt[:, 1]) * np.cos(rpt[:, 2])
        xyznew[:, 1] = rpt[:, 0] * np.cos(rpt[:, 1]) * np.sin(rpt[:, 2])
        xyznew[:, 2] = rpt[:, 0] * np.sin(rpt[:, 1])
        return xyznew


class InverseR2TargetTransformer(TransformerMixin,BaseEstimator):
    def __init__(self):
        self.r2_coeff=None
    def fit(self,X_sphere,y, y_weights):
        assert not (X_sphere[:, 0] == 0).any() , "Radius value of 0 included. This is incompatible with polar coordinate transform."
        x_r2: np.ndarray = X_sphere[:, 0] ** -2
        r2_weights = (np.clip(y,a_min=1,a_max=None)/y_weights)**0.5
        r2_model = LinearRegression(fit_intercept=False).fit(x_r2[:, np.newaxis], y, r2_weights)
        self.r2_coeff = r2_model.coef_[0]
        assert self.r2_coeff > 0 , f"Fit of r2 coordinate leading to value >0 ({self.r2_coeff}). This shouldn't be possible for thi"
        return self
    def transform(self,X_sphere,y):
        x_r2 = X_sphere[:, 0] ** -2
        return y / (x_r2 * self.r2_coeff) - 1
    def inverse_transform(self,X_sphere,yt):
        x_r2 = X_sphere[:, 0] ** -2
        return (yt+1) * (x_r2 * self.r2_coeff)
    def point_variances(self,X_sphere,y,y_weights): #y_weights should be livetimes
        #handling some zeros. Shouldn't be all zeros, due to zerobin check
        y_raw = y*y_weights
        y_min1 = np.clip(y_raw,a_min=1, a_max=None) # for purposes of pv, zero counts has same uncertainty as 1 count
        x_r2 = X_sphere[:, 0] ** -2
        pvs = y_min1 / (x_r2 * self.r2_coeff) ** 2 / y_weights**2
        return pvs


import warnings
from sklearn.exceptions import ConvergenceWarning
class SingleEnergyGP(RegressorMixin,BaseEstimator):
    #set kernel as class variable rather than instance variable

    transformer = SphericalCoordsTransformer()


    def __init__(self,):
        self.zerobin: bool = False
        self.r2_coeff = None
        self.gp: GaussianProcessRegressor = None
        self.y_transformer = InverseR2TargetTransformer()
        pass

    def kernel(self, X_cart, y, y_weights):
        radialkernel = RBF([1000, 1e99, 1e99], length_scale_bounds=(
            (25, 1e4), (1e98, 1e99), (1e98, 1e99)))
        anglekernel = SphericalKernelChordal(tau=(5, 10), tau_bounds=((4, 400,), (4, 400)))
        return (1+1*radialkernel) * (anglekernel)

    def fit(self,X_cart, y, y_weights):
        if (y==0).all(): #this bin was empty in all the training data, so we can't use it
            self.zerobin = True
            return

        np.seterr(invalid='ignore')  # prevent from printing excess amounts of true_divide errors
        X_sphere = self.transformer.transform(X_cart)
        yt = self.y_transformer.fit(X_sphere,y,y_weights).transform(X_sphere,y)
        pvs = self.y_transformer.point_variances(X_sphere,y,y_weights)

        kernel = self.kernel(X_cart,y,y_weights)
        with warnings.catch_warnings():
            warnings.filterwarnings('error',category=ConvergenceWarning)
            try:
                self.gp = GaussianProcessRegressor(kernel=kernel, alpha = pvs, n_restarts_optimizer=4).fit(X_sphere,yt)
            except Warning as warning:
                if "failed to converge" in str(warning):
                    if ((y*y_weights).max()>10):
                        warnings.warn(f"Failure of GP to converge. This is normal when there are <10 data counts at any location, but this time it happened with {(y*y_weights).max()} counts at one location.")
                    self.zerobin=True
                else:
                    warnings.filterwarnings('ignore', category=ConvergenceWarning)
                    self.gp = GaussianProcessRegressor(kernel=kernel, alpha = pvs, n_restarts_optimizer=4).fit(X_sphere,yt)

    def predict(self,X_cart,return_model=False):
        if self.zerobin:
            return np.zeros((X_cart.shape[0]))
        X_sphere = self.transformer.transform(X_cart)
        yt = self.gp.predict(X_sphere)
        if return_model:
            return yt
        return self.y_transformer.inverse_transform(X_sphere,yt)


class FitSymmetricKernelSingleEnergyGP(SingleEnergyGP):
    def kernel(self, X_cart, y, y_weights):
        X_sphere = self.transformer.transform(X_cart)
        medianphi = np.median(X_sphere[:, 2])
        radialkernel = RBF([1000, 1e99, 1e99], length_scale_bounds=(
            (25, 1e4), (1e98, 1e99), (1e98, 1e99)))
        symkernel = SymmetricAngleKernel.construct(tau=(4, 10), tau_bounds=((4, 400,), (4, 400)), thetaReflection=0,
                                                   phiReflection=medianphi,
                                                   # phiReflection=1.5,
                                                   thetaReflection_bounds=(0, 0),
                                                   phiReflection_bounds=(1, 2))
        anglekernel = 1 * SphericalKernel(tau=(4, 4), tau_bounds=((4, 400,), (4, 400))) + 1 * symkernel
        return (1 + 1 * radialkernel) * (anglekernel)

class FixedSymmetricKernelSingleEnergyGP(SingleEnergyGP):
    reflection_axis: np.ndarray
    def kernel(self, X_cart, y, y_weights):
        reflection = self.transformer.transform(np.atleast_2d(self.reflection_axis))[0]
        radialkernel = RBF([1000, 1e99, 1e99], length_scale_bounds=(
            (25, 1e4), (1e98, 1e99), (1e98, 1e99)))
        symkernel = SymmetricAngleKernel.construct(tau=(4, 10), tau_bounds=((4, 400,), (4, 400)), thetaReflection=reflection[1],
                                                   phiReflection=reflection[2],
                                                   # phiReflection=1.5,
                                                   thetaReflection_bounds=(reflection[1], reflection[1]),
                                                   phiReflection_bounds=(reflection[2], reflection[2]))
        anglekernel =  symkernel
        return (1 + 1 * radialkernel) * (anglekernel)


class DynamicGPModel(ABC):
    '''
    container for GP for a single material
    A scenario may glue a few materials together, including BG, but the scenario should be in charge of summing these.
    For the purposes of making listmode data, we want to query this model at many (or all) energy bins and one or more locations
    initialize with data object to give access to spectrum DB. Plus, specify detector name and material.
    Subclass this with one-GP-per-energy specific features
    Includes the ability to set a training set & test set for convenience, tho users may often not reserve any data for testing.
    '''
    hide_buildbars = False
    hide_querybars = True

    def __init__(self,detector_name,material_name:str, model_def):
        data = ddh.DynamicData.get()
        self.detector = data.get_detector(detector_name)
        self.material = data.get_material(material_name)
        self.model_def = model_def
        self.spectra:Sequence[BaseSpectrumXYZ] = data.get_spectra_xyz(detector_name,material_name)
        self.built=False


    def build(self,):  # wrapper, subclasses should specialize _build() and leave this alone
        self._build()
        self.built=True

    @abstractmethod
    def _build(self,):  # do the setup
        pass


    def query(self, xyz:np.ndarray , energies: Sequence = None  ):
        #return shape: array of (locations, energies)
        assert self.built, "Attempt to query model before it has been built."
        if not energies:
            energies = range(self.detector.chan_count)
        return self._query(xyz,energies)

    @abstractmethod
    def _query(self, xyz:np.ndarray , energies: Sequence  ):
        #return shape: array of (locations, energies)
        pass

    def getSpectra(self, xyzs:np.ndarray):
        spectra_list = []
        for xyz in xyzs:
            assert np.atleast_2d(xyz).shape[1] == 3 , f"Attempted to ask for spectra with non-3D list of coordinates. {xyz}"
            for spec in self.spectra:
                if xyz == [spec.x, spec.y, spec.z]:
                    spectra_list.append(spec)
                    break
        return spectra_list

    def setTrainSpectra(self):
        train_points = self.model_def.get('points')
        if train_points is None:
            train_points = [[spec.x,spec.y,spec.z] for spec in self.spectra]

        self.train_spectra = [spec for spec in self.spectra if [spec.x, spec.y, spec.z] in train_points]
        missing = set([tuple(x) for x in train_points]) - set([(spec.x, spec.y, spec.z) for spec in self.spectra])
        if missing:
            raise ValueError(f'Requested training point not available in data:{missing}')

        return train_points

class ManyGPsModel(DynamicGPModel):
    GPs: Sequence[SingleEnergyGP]

    def _build(self,):

        train_points = self.getTrainPoints()

        self.train_spectra = [spec for spec in self.spectra if [spec.x,spec.y,spec.z] in train_points]

        train_xyz = np.array([(spec.x,spec.y,spec.z) for spec in self.train_spectra])
        self.GPs = [SingleEnergyGP() for bin in range(self.detector.chan_count)]

        for bin, gp in enumerate(tqdm(self.GPs,disable=self.hide_buildbars)):
            train_counts = np.array([spec.counts[bin] for spec in self.train_spectra])
            weights = np.array([spec.livetime/spec.sensitivity for spec in self.train_spectra])
            gp.fit(train_xyz, train_counts/weights,weights)

        self.built = True

    def _query(self, xyz:np.ndarray , energies: Sequence[int] = None  ):
        xyz = np.atleast_2d(xyz) #(number of locations, 3)
        assert xyz.shape[1]==3 , "Attempt to query the model using non-3D list of coordinates."

        output = np.zeros((xyz.shape[0],len(energies)))
        for i,energy in enumerate(tqdm(energies,disable=self.hide_querybars)):
            try:
                output[:, i] = self.GPs[energy].predict(xyz)
            except KeyError:
                pass
        return output

class ManyGPsROIModel(ManyGPsModel):
    GPs: dict
    GPclass = SingleEnergyGP
    def _build(self,):
        self.setTrainSpectra()

        if 'roi' in self.model_def.keys():
            roi = self.model_def['roi'] #expecting a list of bins or a 'first', 'last' dict
        else:
            roi = [0, len(self.spectra[0].counts)]

        try:
            roi = list(range(roi['first'],roi['last']))
        except:
            pass

        train_xyz = np.array([(spec.x,spec.y,spec.z) for spec in self.train_spectra])
        self.GPs = {}
        for energy in roi:
            self.GPs[energy] = self.GPclass()

        for bin, gp in tqdm(self.GPs.items(), disable=self.hide_buildbars):
            train_counts = np.array([spec.counts[bin] for spec in self.train_spectra])
            weights = np.array([spec.livetime / spec.sensitivity for spec in self.train_spectra])
            gp.fit(train_xyz, train_counts / weights, weights)
        self.built=True


class ProxyModel(DynamicGPModel):
    proxy : dict
    anchor : BaseSpectrumXYZ
    proxy_at_anchor : np.ndarray
    def _build(self):
        data = ddh.DynamicData.get()

        for psource, pmodeldef in self.model_def['proxies'].items():
            assert pmodeldef['model_def']['roi'] == self.model_def['roi'], f"Proxy model and actual model do not have the same roi. Actual model roi: {self.model_def['roi']}. Proxy model roi: {pmodeldef['model_def']['roi']}."
            model_store = data.get_model(detector_name=self.detector.name, material_name=psource,
                                              model_name='ManyGPsROIModel', model_def=pmodeldef['model_def'])
            if model_store==None:
                model = ManyGPsROIModel(self.detector.name,psource,pmodeldef['model_def'])
                model.build()
                data.store_model(model)
            else:
                model = model_store.model
                if not model.built:
                    model.build()
                    data.store_model(model)
        self.setTrainSpectra()
        spectral_sums = [spectrum.counts.sum() for spectrum in self.train_spectra ]
        max_spectrum = np.argmax(spectral_sums)
        self.anchor = self.train_spectra[max_spectrum]

        proxy_at_anchor = np.zeros((self.detector.chan_count))
        for psource,pmodeldef in self.model_def['proxies'].items():
            pmodel = data.get_model(detector_name=self.detector.name, material_name=psource,
                                         model_name='ManyGPsROIModel', model_def=pmodeldef['model_def']).model
            assert pmodel.built, f"Attempt to use a proxy model that has not been built. detector_name={self.detector.name}, material_name={psource}, model_name='ManyGPsROIModel', model_def={pmodeldef['model_def']}"
            proxy_at_anchor += pmodeldef['weight'] * pmodel.query([[self.anchor.x,self.anchor.y,self.anchor.z],])[0]

        self.proxy_at_anchor = proxy_at_anchor



    def _query(self, xyz:np.ndarray , energies: Sequence = None  ):
        data = ddh.DynamicData.get()
        model_results = []
        for psource, pmodeldef in self.model_def['proxies'].items():
            pmodel = data.get_model(detector_name=self.detector.name, material_name=psource,
                                    model_name='ManyGPsROIModel', model_def=pmodeldef['model_def']).model
            assert pmodel.built, f"Attempt to use a proxy model that has not been built. detector_name={self.detector.name}, material_name={psource}, model_name='ManyGPsROIModel', model_def={pmodeldef['model_def']}"
            model_results.append(pmodel.query(xyz,energies)*pmodeldef['weight'])

        proxy_result = np.sum(model_results, axis=0)

        normalize = np.divide(self.anchor.counts[energies] / self.anchor.livetime , self.proxy_at_anchor[energies], out = np.zeros_like(self.proxy_at_anchor[energies]), where=(self.proxy_at_anchor[energies]>0))

        return proxy_result*normalize


class SymmetricMGRModel(ManyGPsROIModel):
    def _build(self,):
        axis= self.model_def['reflection_axis']
        self.GPclass=FixedSymmetricKernelSingleEnergyGP
        self.GPclass.reflection_axis=axis
        super()._build()


class RecreateModel(DynamicGPModel):

    def _build(self,):
        self.spec_xyz = np.array([(spec.x,spec.y,spec.z) for spec in self.spectra])
        self.model_spec = copy.deepcopy(self.spectra)
        for spec in self.model_spec:
            spec.counts /= spec.livetime/spec.sensitivity
        self.built = True

    def _query(self, xyz: np.ndarray, energies: Sequence[int] = None):
        xyz = np.atleast_2d(xyz)  # (number of locations, 3)
        assert xyz.shape[1] == 3  , "Attempted to query model at non-3D list of coordinates."

        required_positions = set([tuple(x) for x in xyz])
        available_positions = set([tuple(x) for x in self.spec_xyz])
        missing = list(required_positions - available_positions)
        assert len(missing)==0 , f"Attemped to query RecreateModel at a position ({missing}) for which no input data is available. RecreateModel can only literally recreate input data, and cannot interpolate/extrapolate."


        specs_on_path = self._specs_at_path_positions(xyz)

        output = np.empty((xyz.shape[0], len(energies)))
        for i, energy in enumerate(tqdm(xyz,disable=self.hide_querybars)):
            output[i, :] = specs_on_path[i].counts[energies]
        return output

    def _specs_at_path_positions(self, xyz):
        specs = []
        for pos in xyz:
            for index in range(self.spec_xyz.shape[0]):
                if np.all(pos == self.spec_xyz[index, :]):
                    specs.append(self.model_spec[index])
                    continue
        return specs
