# coding: utf-8 -*-

'''
stats.py contains statistics utility functions
'''

__all__ = ['mstats', 'lregress', 'ttest', 'get_weights', 'get_weighted_mean',
           'get_linear_regression', 'bootstrap']

import numpy as _np
import pandas as _pd
from scipy.stats import t as _t
from sklearn.linear_model import LinearRegression


def mstats(x, verbose=True):
    '''
    Function that computes and displays
    various statistics of a variable.

    A better alternative is `scipy.stats.describe()`

    Args:
        x : (numpy array) numpy variable whose statistics are to
            be computed and displayed
        verbose : (boolean, default=True) Prints statistics if True

    Returns:
        OUT : (object) returns if verbose=False
    '''

    OUT = type('', (), {})

    OUT.MatrixSize = _np.shape(x)
    OUT.NElements = _np.prod(OUT.MatrixSize)
    OUT.Nnans = _np.sum(_np.isnan(x))
    OUT.NAnalyzedElements = OUT.NElements - OUT.Nnans

    datatype = x.dtype

    xf = x.flatten()
    xf = xf[~_np.isnan(xf)]
    absxf = _np.abs(xf)

    OUT.Mean = _np.mean(xf)
    OUT.Max = _np.max(xf)
    OUT.Min = _np.min(xf)
    OUT.Median = _np.median(xf)
    OUT.StDev = _np.std(xf, ddof=1)
    OUT.MeanAbs = _np.mean(absxf)
    OUT.MinAbs = _np.min(absxf[absxf > 0.0])
    OUT.FracZero = len(xf[xf == 0.0]) / OUT.NAnalyzedElements
    OUT.FracNan = OUT.Nnans / OUT.NElements

    if verbose:
        print('================= m s t a t s ==================')
        print('        MatrixSize: %s' % (str(OUT.MatrixSize)))
        print('         NElements: %d' % (OUT.NElements))
        print(' NAnalyzedElements: %d' % (OUT.NAnalyzedElements))
        if datatype in ['int', 'int8', 'int16', 'int32', 'int64',
                        'uint8', 'uint16', 'uint32', 'uint64',
                        'float', 'float16', 'float32', 'float64']:
            print('              Mean: %f' % (OUT.Mean))
            print('               Max: %f' % (OUT.Max))
            print('               Min: %f' % (OUT.Min))
            print('            Median: %f' % (OUT.Median))
            print('             StDev: %f' % (OUT.StDev))
            print('           MeanAbs: %f' % (OUT.MeanAbs))
            print('            MinAbs: %f' % (OUT.MinAbs))
        if datatype in ['complex', 'complex64', 'complex128']:
            print('              Mean: %f + %fi' % (OUT.Mean.real,
                                                    OUT.Mean.imag))
            print('               Max: %f + %fi' % (OUT.Max.real,
                                                    OUT.Max.imag))
            print('               Min: %f + %fi' % (OUT.Min.real,
                                                    OUT.Min.imag))
            print('            Median: %f + %fi' %
                  (OUT.Median.real, OUT.Median.imag))
            print('             StDev: %f + %fi' %
                  (OUT.StDev.real, OUT.StDev.imag))
            print('           MeanAbs: %f + %fi' %
                  (OUT.MeanAbs.real, OUT.MeanAbs.imag))
            print('            MinAbs: %f + %fi' %
                  (OUT.MinAbs.real, OUT.MinAbs.imag))
        print('          FracZero: %f' % (OUT.FracZero))
        print('           FracNaN: %f' % (OUT.FracNan))
        print('================================================')

        return

    else:

        return OUT


def lregress(x, y, ci=95.0):
    '''
    Function that computes the linear regression between two variables and
    returns the regression coefficient and statistical significance
    for a t-value at a desired confidence interval.

    Args:
        x : (array like) independent variable
        y : (array like) dependent variable
        ci : (float, optional, default=95) confidence interval percentage

    Returns:
        The linear regression coefficient (float),
        the standard error on the linear regression coefficient (float),
        and the statistical signficance of the linear regression
        coefficient (bool).
    '''

    # make sure the two samples are of the same size
    if (len(x) != len(y)):
        raise ValueError('samples x and y are not of the same size')
    else:
        nsamp = len(x)

    pval = 1.0 - (1.0 - ci / 100.0) / 2.0
    tcrit = _t.ppf(pval, 2 * len(x) - 2)

    covmat = _np.cov(x, y=y, ddof=1)
    cov_xx = covmat[0, 0]
    cov_yy = covmat[1, 1]
    cov_xy = covmat[0, 1]

    # regression coefficient (rc)
    rc = cov_xy / cov_xx
    # total standard error squared (se)
    se = (cov_yy - (rc**2) * cov_xx) * (nsamp - 1) / (nsamp - 2)
    # standard error on rc (sb)
    sb = _np.sqrt(se / (cov_xx * (nsamp - 1)))
    # error bar on rc
    eb = tcrit * sb

    ssig = True if (_np.abs(rc) - _np.abs(eb)) > 0.0 else False

    return rc, sb, ssig


def ttest(x, y=None, ci=95.0, paired=True, scale=False):
    '''
    Given two samples, perform the Student's t-test and return the errorbar.
    The test assumes the sample size be the same between x and y.
    Args:
        x: (numpy array) control
        y: (numpy array, optional, default=x )experiment
        ci: (float, optional, default=95) confidence interval percentage
        paired: (bool, optional, default=True) paired t-test
        scale: (bool, optional, default=False) normalize with mean(x) and
               return as a percentage

    Returns:
        The (normalized) difference in the sample means and
        the (normalized) errorbar with respect to control.

    To mask out statistically significant values:\n
    `diffmask = numpy.ma.masked_where(numpy.abs(diffmean)
                                      <=errorbar,diffmean).mask`
    '''

    nsamp = x.shape[0]

    if y is None:
        y = x.copy()

    pval = 1.0 - (1.0 - ci / 100.0) / 2.0
    tcrit = _t.ppf(pval, 2*(nsamp-1))

    xmean = _np.nanmean(x, axis=0)
    ymean = _np.nanmean(y, axis=0)

    diffmean = ymean - xmean

    if paired:
        # paired t-test
        std_err = _np.sqrt(_np.nanvar(y-x, axis=0, ddof=1) / nsamp)
    else:
        # unpaired t-test
        std_err = _np.sqrt((_np.nanvar(x, axis=0, ddof=1) +
                            _np.nanvar(y, axis=0, ddof=1)) / (nsamp-1.))

    errorbar = tcrit * std_err

    # normalize (rescale) the diffmean and errorbar
    if scale:
        scale_fac = 100.0 / xmean
        diffmean = diffmean * scale_fac
        errorbar = errorbar * scale_fac

    return diffmean, errorbar


def get_weights(lats):
    '''
    Get weights for latitudes to do weighted mean
    Args:
        lats: (array like) Latitudes
    Returns:
        An array of weights for latitudes
    '''
    return _np.cos((_np.pi / 180.0) * lats)


def get_weighted_mean(data, weights, axis=None):
    '''
    Given the weights for latitudes, compute weighted mean
    of data in that direction
    Note, `data` and `weights` must be same dimension
    Uses `numpy.average`
    Args:
        data: (numpy array) input data array
        weights: (numpy array) input weights
        axis: (int) direction to compute weighted average
    Returns:
        An array of data weighted mean by weights
    '''
    assert data.shape == weights.shape, (
        'data and weights mis-match array size')

    return _np.average(data, weights=weights, axis=axis)


def get_linear_regression(x, y):
    """
    Calculate linear regression between two sets of data.
    Fits a linear model with coefficients to minumize the
    residual sum of squares between the observed targets
    in the dataset, and the targets predicted by the linear
    approximation.

    Args:
        y, x : (array like) Data to calculate linear regression

    Returns:
        The predicted y values from calculation,
        the R squared value, the intercept of the line, and the
        slope of the line from the equation for the predicted
        y values.
    """
    x = x.reshape((-1, 1))
    model = LinearRegression().fit(x, y)
    r_sq = model.score(x, y)
    intercept = model.intercept_
    slope = model.coef_[0]
    # This is the same as if you calculated y_pred
    # by y_pred = slope * x + intercept
    y_pred = model.predict(x)
    return y_pred, r_sq, intercept, slope


def bootstrap(insample, level=.95, estimator='mean', nrepl=10000):
    """
    Generate emprical bootstrap confidence intervals.
    See https://ocw.mit.edu/courses/mathematics/
                18-05-introduction-to-probability-and-statistics-spring-2014/
                readings/MIT18_05S14_Reading24.pdf for more information.

    Args:
        insample: (array like) is the array from which the estimator (u)
                  was derived (x_1, x_2,....x_n).
        level: (float, default=0.95) desired confidence level for CI bounds
        estimator: (char, default='mean') type of statistic obtained from
                  the sample (mean or median)
        nrepl: (integer, default=1000) number of replicates

    Returns:
        Lower and upper bounds of confidence intervals
    """
    if any(_np.isnan(insample)):
        print('{:s}').format('bootstrap_ci.py: NaN detected. Dropping NaN(s) input prior to bootstrap...')
        sample = insample[~_np.isnan(insample)]
    else:
        sample = insample

    boot_dist = [_np.random.choice(sample, _np.size(sample)) for x in _np.arange(nrepl)]
    if estimator.lower() == 'mean':
        deltas = _np.sort(_np.mean(boot_dist, axis=1) - _np.mean(sample))
    elif estimator.lower() == 'median':
        deltas = _np.sort(_np.median(boot_dist, axis=1) - _np.median(sample))

    lower_pctile = 100*((1. - level)/2.)
    upper_pctile = 100. - lower_pctile
    ci_lower = _np.percentile(deltas, lower_pctile)
    ci_upper = _np.percentile(deltas, upper_pctile)

    return ci_lower, ci_upper


def spectrum_stats(df):
    '''
    Function to calculate major statistics for radiance data as a function of channel.
    Statisics are for observations that pass QC only.

    Args:
        df : (Pandas dataframe) A data frame containing raw radiance information as produced
             by the get_data method of Radiance.

    Returns:
        channel_stats : (Pandas dataframe) A data frame containing channel-by-channel statistics
    '''

    # Get channel numbers in dataframe
    sc = df.index.unique(level="Channel")

    # Initialise output dataframe
    channel_stats = _pd.DataFrame(index=sc,
                                  columns=["count", "omf_unadjusted_mean", "omf_adjusted_mean",
                                           "omf_unadjusted_stddev", "omf_adjusted_stddev"])

    # Sorting by channel increases efficiency and prevents a warning message
    dfs = df.sort_index()

    # Loop through channels and calculate stats
    for chan in sc:
        # Subset based on channel and QC indexes
        tmp = dfs.loc[(chan, 0.0)]
        # This next line makes sure that all rejected obs are avoided.
        # Using the inverse observation error is more reliable than the QC flag.
        tmp = tmp[(tmp['inverse_observation_error'] > 0.0)]
        channel_stats["count"].loc[chan] = tmp.size
        for var in ["omf_unadjusted", "omf_adjusted"]:
            channel_stats[var + '_mean'].loc[chan] = tmp[var].to_numpy().mean()
            channel_stats[var + '_stddev'].loc[chan] = tmp[var].to_numpy().std()

    return channel_stats
