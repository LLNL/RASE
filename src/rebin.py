import numpy as np
import scipy.interpolate
import scipy.ndimage



def integral_rebin(a, old_range, newdim, new_range, highnoise=0, sample_highnoise=False):
    a_integral = np.concatenate(([0.,],np.cumsum(a)))
    a_points = np.linspace(start=old_range[0],stop=old_range[1],num=len(a)+1, endpoint=True)
    out_points = (np.linspace(start=new_range[0], stop=new_range[1], num=newdim + 1, endpoint=True))
    if highnoise:
        assert(highnoise>0)
        if sample_highnoise:
            extra_points = out_points[out_points>a_points[-1]]
            a_points= np.concatenate((a_points,extra_points))
            bin_expectation = highnoise/len(extra_points)
            noise_bins = np.random.poisson(bin_expectation,len(extra_points))
            noise_int = np.cumsum(noise_bins)+a_integral[-1]
            a_integral = np.concatenate((a_integral,noise_int))
        else:
            a_points=np.append(a_points,out_points[-1])
            a_integral= np.append(a_integral,a_integral[-1]+highnoise)
    interp = np.interp(x=out_points,xp=a_points,fp=a_integral)
    return np.rint(np.diff(interp)).astype(int)




def congrid(a, newdims, method='linear', centre=False, minusone=False):
    '''
    https://scipy-cookbook.readthedocs.io/items/Rebinning.html
    Arbitrary resampling of source array to new dimension sizes.
    Currently only supports maintaining the same number of dimensions.
    To use 1-D arrays, first promote them to shape (x,1).

    Uses the same parameters and creates the same co-ordinate lookup points
    as IDL''s congrid routine, which apparently originally came from a VAX/VMS
    routine of the same name.

    method:
    neighbour - closest value from original data
    nearest and linear - uses n x 1-D interpolations using
                         scipy.interpolate.interp1d
    (see Numerical Recipes for validity of use of n 1-D interpolations)
    spline - uses ndimage.map_coordinates

    centre:
    True - interpolation points are at the centres of the bins
    False - points are at the front edge of the bin

    minusone:
    For example- inarray.shape = (i,j) & new dimensions = (x,y)
    False - inarray is resampled by factors of (i/x) * (j/y)
    True - inarray is resampled by(i-1)/(x-1) * (j-1)/(y-1)
    This prevents extrapolation one element beyond bounds of input array.
    '''
    if not a.dtype in [np.float64, np.float32]:
        a = np.cast[float](a)

    m1 = np.cast[int](minusone)
    ofs = np.cast[int](centre) * 0.5
    old = np.array(a.shape)
    ndims = len(a.shape)
    if len(newdims) != ndims:
        print('''
        [congrid] dimensions error. 
        This routine currently only support 
        rebinning to the same number of dimensions''')
        return None
    newdims = np.asarray(newdims, dtype=float)
    dimlist = []

    if method == 'neighbour':
        for i in range(ndims):
            base = np.indices(newdims)[i]
            dimlist.append((old[i] - m1) / (newdims[i] - m1) \
                           * (base + ofs) - ofs)
        cd = np.array(dimlist).round().astype(int)
        newa = a[list(cd)]
        return newa

    elif method in ['nearest', 'linear']:
        # calculate new dims
        for i in range(ndims):
            base = np.arange(newdims[i])
            dimlist.append((old[i] - m1) / (newdims[i] - m1) \
                           * (base + ofs) - ofs)
        # specify old dims
        olddims = [np.arange(i, dtype=np.float) for i in list(a.shape)]

        # first interpolation - for ndims = any
        mint = scipy.interpolate.interp1d(olddims[-1], a, kind=method)
        newa = mint(dimlist[-1])

        trorder = [ndims - 1] + list(range(ndims - 1))
        for i in range(ndims - 2, -1, -1):
            newa = newa.transpose(trorder)

            mint = scipy.interpolate.interp1d(olddims[i], newa, kind=method)
            newa = mint(dimlist[i])

        if ndims > 1:
            # need one more transpose to return to original dimensions
            newa = newa.transpose(trorder)

        return newa
    elif method in ['spline']:
        oslices = [slice(0, j) for j in old]
        oldcoords = np.ogrid[oslices]
        nslices = [slice(0, j) for j in list(newdims)]
        newcoords = np.mgrid[nslices]

        newcoords_dims = range(np.rank(newcoords))
        # make first index last
        newcoords_dims.append(newcoords_dims.pop(0))
        newcoords_tr = newcoords.transpose(newcoords_dims)
        # makes a view that affects newcoords

        newcoords_tr += ofs

        deltas = (np.asarray(old) - m1) / (newdims - m1)
        newcoords_tr *= deltas

        newcoords_tr -= ofs

        newa = scipy.ndimage.map_coordinates(a, newcoords)
        return newa
    else:
        print('''
        Congrid error: Unrecognized interpolation type.
        Currently only 'neighbour', 'nearest\,'linear',
        and 'spline' are supported.
        ''')
        return None