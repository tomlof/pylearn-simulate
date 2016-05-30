# -*- coding: utf-8 -*-
"""
Created on Mon May 12 15:46:47 2014

Copyright (c) 2013-2014, CEA/DSV/I2BM/Neurospin. All rights reserved.

@author:  Tommy Löfstedt
@email:   lofstedt.tommy@gmail.com
@license: BSD 3-clause.
"""
import abc

import numpy as np
import scipy.optimize

import utils

__all__ = ["SimulatedData", "LinearRegressionData"]


class SimulatedData(object):

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def load(self, beta):
        raise NotImplementedError('Abstract method "load" must be '
                                  'specialised!')


class LinearRegressionData(SimulatedData):
    """Returns simulated data for linear regression.

    The data is generated such that we know the exact solution to the equation
    system.

    The data generated by this function is fit to the Linear regression + Sum
    of Penalties function, i.e.:

        f(beta) = (1 / 2).|X.beta - y|²_2 + sum_{i=1}^N l_i.P_i(beta),

    where the P_i(.) are penalty functions.

    Parameters
    ----------
    penalties : list or tuple
        The penalties to add to the linear regression function.

    X0 : numpy array
        The array has shape (n-by-p). The initial matrix to use when
        building data. This matrix carries the desired correlation
        structure of the generated data. The generated data will be a
        column-scaled version of this matrix.

    e : numpy array
        The array has shape (n-by-1). The error vector e = Xb - y. This
        vector carries the desired distribution of the residual. Note that
        if intercept is True, then e will be centred.

    snr : float, optional
        Must be positive. The signal-to-noise ratio between model and
        residual.

    intercept : boolean, optional
        Whether or not to include an intercept variable. If intercept is
        True, the first column of X0 must be a column of ones. This
        variable is not penalised. Note that if intercept is True, then e
        will be centred.

    Returns
    -------
    X : numpy array
        The array has shape (n-by-p). The generated X matrix.

    y : numpy array
        The array has shape (n-by-1). The generated y vector.

    beta : numpy array
        The array has shape (p-by-1). The regression vector with the
        correct snr (if snr is given).
    """
    def __init__(self, penalties, X0, e, snr=None, intercept=False):

        super(LinearRegressionData, self).__init__()

        if isinstance(penalties, (list, tuple)):
            self.penalties = list(penalties)
        else:
            self.penalties = [penalties]
        self.X0 = X0
        self.intercept = bool(intercept)
        self.e = e - np.mean(e) if self.intercept else e
        self.snr = float(snr) if snr is not None else None

    def load(self, beta):
        """Generate the simulated data.

        Parameters
        ----------
        beta : numpy array
            The array has shape (p-by-1). The regression vector to
            generate data from.
        """
        if self.snr is not None:
            old_snr = self.snr
            self.snr = None
            try:
                def f(x):
                    X, y, _, _ = self.load(x * beta)

#                    print "snr = %.5f = %.5f = |X.b| / |e| = %.5f / %.5f" \
#                       % (old_snr, np.linalg.norm(np.dot(X, x * beta)) \
#                                                   / np.linalg.norm(self.e),
#                          np.linalg.norm(np.dot(X, x * beta)),
#                          np.linalg.norm(self.e))

                    return (np.linalg.norm(np.dot(X, x * beta))
                            / np.linalg.norm(self.e)) - old_snr

                low, high = utils.find_bisect_interval(f,
                                                       low=0.0, high=old_snr)
                snr = scipy.optimize.bisect(f, low, high)

            finally:
                self.snr = old_snr

            beta = beta * snr

        grad = 0.0
        for p in self.penalties:
            grad -= p.grad(beta[1:, :] if self.intercept else beta)

        Mte = np.dot(self.X0.T, self.e)
        if self.intercept:
            Mte = Mte[1:, :]

        alpha = np.divide(grad, Mte)

        p = beta.shape[0]

        start = 1 if self.intercept else 0
        X = np.ones(self.X0.shape)
        for i in xrange(start, p):
            X[:, i] = self.X0[:, i] * alpha[i - start, 0]

        y = np.dot(X, beta) - self.e

        return X, y, beta, self.e

if __name__ == "__main__":
    import doctest
    doctest.testmod()
