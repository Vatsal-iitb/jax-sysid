# -*- coding: utf-8 -*-
"""
jax-sysid: A Python package for linear and nonlinear system identification and nonlinear regression using Jax.

Utility functions.

(C) 2024 A. Bemporad, March 6, 2024
"""

import numpy as np


def lbfgs_options(iprint, iters, lbfgs_tol, memory):
    """
    Create a dictionary of options for the L-BFGS-B optimization algorithm.

    Parameters
    ----------
    iprint : int
        Verbosity level for printing optimization progress.
    iters : int
        Maximum number of iterations.
    lbfgs_tol : float
        Tolerance for convergence.
    memory : int
        Number of previous iterations to store for computing the next search direction.

    Returns
    -------
    dict
        A dictionary of options for the L-BFGS-B algorithm.
    """
    options = {'iprint': iprint, 'maxls': 20, 'gtol': lbfgs_tol, 'eps': 1.e-8,
               'ftol': lbfgs_tol, 'maxfun': iters, 'maxcor': memory}
    return options


def standard_scale(X):
    """
    Standardize the input data by subtracting the mean and dividing by the standard deviation.
    Note that in the case of multi-output systems, scaling outputs changes the relative weight 
    of output errors.

    Parameters
    ----------
    X : ndarray
        Input data array of shape (n_samples, n_features).

    Returns
    -------
    standardized_data : ndarray
        The standardized data array of shape (n_samples, n_features).
    mean : ndarray
        The mean values of each feature.
    gain : ndarray
        The gain values used for scaling each feature (=inverse of std, if nonzero, otherwise 1).
    """
    xmean = np.mean(X, 0)
    xstd = np.std(X, 0)
    nX = xmean.shape[0]
    xgain = np.ones(nX)
    for i in range(nX):
        if xstd[i] > 1.e-6:  # do not change gain in case std is approximately 0
            xgain[i] = 1./xstd[i]
    return (X - xmean) * xgain, xmean, xgain


def unscale(Xs, offset, gain):
    """
    Unscale scaled signal.

    Parameters
    ----------
    Xs : ndarray
        Scaled data array of shape (n_samples, n_features).
    offset : ndarray
        Offset to be added to each row of X.
    gain : ndarray
        Gain to be multiplied to each row of X.

    Returns
    -------
    X : ndarray
        Unscaled array X = Xs/gain + offset
    """
    return Xs/gain+offset


def compute_scores(Y_train, Yhat_train, Y_test, Yhat_test, fit='R2'):
    """Compute R2-score, best fit rate, or accuracy score on (possibly multi-dimensional) 
       training and test output data

    (C) 2024 A. Bemporad

    Parameters
    ----------
    Y_train : ndarray
        Reference output data for training, with shape (n_samples_training, n_outputs)
    Yhat_train : ndarray
        Predicted output data for training, with shape (n_samples_training, n_outputs)
    Y_test : ndarray
        Reference output data for testing, with shape (n_samples_test, n_outputs)
    Yhat_test : ndarray
        Predicted output data for testing, with shape (n_samples_test, n_outputs)
    fit : str, optional
        Metrics used: 'R2' (default), or 'BFR', or 'Accuracy'

    Returns
    -------
    score_train: array
        Score on training data (one entry per output)
    score_test : array
        Score on test data (one entry per output)
    msg : string
        Printout summarizing computed performance results
        """

    ny = np.atleast_2d(Y_train).shape[1]
    score_train = np.zeros(ny)
    score_test = np.zeros(ny)
    msg = ''
    isR2 = fit.lower() == 'r2'
    isBFR = fit.lower() == 'bfr'
    isAcc = fit.lower()[0:3] == 'acc'
    if not (isR2 or isBFR or isAcc):
        raise ValueError(
            "Invalid fit metric, only 'R2', 'BFR', and 'Accuracy' are supported.")

    if isAcc:
        unit = "%"
    else:
        unit = ""

    if ny > 1:
        for i in range(ny):
            if isR2 or isBFR:
                nY_train2 = np.sum((Y_train[:, i] - np.mean(Y_train[:, i]))**2)
                nY_test2 = np.sum((Y_test[:, i] - np.mean(Y_test[:, i]))**2)
            text = f"y{i+1}: "
            if isR2:
                score_train[i] = 100. * \
                    (1. - np.sum((Yhat_train[:, i] -
                     Y_train[:, i]) ** 2) / nY_train2)
                score_test[i] = 100. * \
                    (1. - np.sum((Yhat_test[:, i] -
                     Y_test[:, i]) ** 2) / nY_test2)
            elif isBFR:
                score_train[i] = 100. * (1. - np.linalg.norm(
                    Yhat_train[:, i] - Y_train[:, i]) / np.sqrt(nY_train2))
                score_test[i] = 100. * (1. - np.linalg.norm(
                    Yhat_test[:, i] - Y_test[:, i]) / np.sqrt(nY_test2))
            elif isAcc:
                score_train[i] = np.mean(Yhat_train[:, i] == Y_train[:, i])*100
                score_test[i] = np.mean(Yhat_test[:, i] == Y_test[:, i])*100
            text += f"{fit.capitalize()} score: training = {score_train[i]: 5.4f}{unit}, test = {score_test[i]: 5.4f}{unit}"
            msg += '\n' + text
            # print(text)
        msg += "\n-----\nAverage "
    else:
        nY_train2 = np.sum((Y_train-np.mean(Y_train))**2)
        nY_test2 = np.sum((Y_test - np.mean(Y_test))**2)
        if isR2:
            score_train = 100. * \
                (1. - np.sum((Yhat_train - Y_train) ** 2) / nY_train2)
            score_test = 100. * \
                (1. - np.sum((Yhat_test - Y_test) ** 2) / nY_test2)
        elif isBFR:
            score_train = 100. * \
                (1. - np.linalg.norm(Yhat_train-Y_train) / np.sqrt(nY_train2))
            score_test = 100. * (1. - np.linalg.norm(Yhat_test -
                                                     Y_test) / np.sqrt(nY_test2))
        elif isAcc:
            score_train = np.mean(Yhat_train == Y_train)*100
            score_test = np.mean(Yhat_test == Y_test)*100
    msg += f"{fit.capitalize()} score:  training = {np.sum(score_train) / ny: 5.4f}{unit}, test = {np.sum(score_test) / ny: 5.4f}{unit}"
    return score_train, score_test, msg


def print_eigs(A):
    """Print the eigenvalues of a given square matrix.

    (C) 2023 A. Bemporad

    Parameters
    ----------
    A : array
        Input matrix
    """
    print("Eigenvalues of A:")
    eigs = np.linalg.eig(A)[0]
    for i in range(A.shape[0]):
        print("%5.4f" % np.real(eigs[i]), end="")
        im = np.imag(eigs[i])
        if not im == 0.0:
            print(" + j%5.4f" % im)
        else:
            print("")
    return


def unscale_model(A, B, C, D, ymean, ygain, umean, ugain):
    """ Unscale linear state-space model after training on scaled inputs and outputs.

    Given the scaled state-space matrices A,B,C,D, and the scaling factors ymean,ygain,umean,ugain,
    transforms the model to receive unscaled inputs and produce unscaled outputs:

        x(k+1) = Ax(k)+B(u(k) - umean)*ugain 
               = Ax(k)+B*diag(ugain)*(u(k) - umean)
         ys(k) = Cx(k)+D(u(k) - umean)*ugain 
               = (y(k) - ymean)*ygain
         y(k)  = ys(k)/ygain + ymean  
               = diag(1./ygain)*Cx(k)+diag(1./ygain)*D*diag(ugain)*(u(k) - umean)+ymean

    Parameters
    ----------
    A : ndarray
        A matrix
    B : ndarray
        B matrix
    C : ndarray
        C matrix
    D : ndarray
        D matrix
    ymean : array
        Mean value of the output
    ygain : array   
        Inverse of output's standard deviation
    umean : array
        Mean value of the input
    ugain : array
        Inverse of input's standard deviation

    Returns
    -------
    A : ndarray
        unscaled A matrix
    B : ndarray
        unscaled B matrix
    C : ndarray
        unscaled C matrix
    D : ndarray
        unscaled D matrix
    ymean : array
        offset = mean value of the output
    umean : array
        offset = mean value of the input
    """
    B = B*ugain
    C = (C.T/ygain).T
    D = D*ugain
    D = (D.T/ygain).T
    return A, B, C, D, ymean, umean
