from itertools import combinations_with_replacement
from collections import defaultdict
import tkinter as tk
from tkinter import filedialog, messagebox

import numpy as np
from numpy.linalg import inv
import cv2
import os

B, G, R = 0, 1, 2 

def boxfilter(I, r):
    M, N = I.shape
    dest = np.zeros((M, N))
    
    # cumulative sum over Y axis
    sumY = np.cumsum(I, axis=0)
    
    # difference over Y axis
    dest[:r + 1] = sumY[r:2*r + 1] # top r+1 lines
    dest[r + 1:M - r] = sumY[2*r + 1:] - sumY[:M - 2*r - 1]
    dest[-r:] = np.tile(sumY[-1], (r, 1)) - sumY[M - 2*r - 1:M - r - 1] # bottom r lines

    # cumulative sum over X axis
    sumX = np.cumsum(dest, axis=1)
    
    # difference over X axis
    dest[:, :r + 1] = sumX[:, r:2*r + 1] # left r+1 columns
    dest[:, r + 1:N - r] = sumX[:, 2*r + 1:] - sumX[:, :N - 2*r - 1]
    dest[:, -r:] = np.tile(sumX[:, -1][:, None], (1, r)) - sumX[:, N - 2*r - 1:N - r - 1] # right r columns

    return dest


def guided_filter(I, p, r=15, eps=1e-3):
    M, N = p.shape
    base = boxfilter(np.ones((M, N)), r) # this is needed for regularization
    
    # each channel of I filtered with the mean filter. this is myu.
    means = [boxfilter(I[:, :, i], r) / base for i in range(3)]
    
    # p filtered with the mean filter
    mean_p = boxfilter(p, r) / base

    # filter I with p then filter it with the mean filter
    means_IP = [boxfilter(I[:, :, i]*p, r) / base for i in range(3)]

    # covariance of (I, p) in each local patch
    covIP = [means_IP[i] - means[i]*mean_p for i in range(3)]

    # variance of I in each local patch: the matrix Sigma in ECCV10 eq.14
    var = defaultdict(dict)
    for i, j in combinations_with_replacement(range(3), 2):
        var[i][j] = boxfilter(I[:, :, i]*I[:, :, j], r) / base - means[i]*means[j]

    a = np.zeros((M, N, 3))
    for y, x in np.ndindex(M, N):
        Sigma = np.array([[var[B][B][y, x], var[B][G][y, x], var[B][R][y, x]],
                          [var[B][G][y, x], var[G][G][y, x], var[G][R][y, x]],
                          [var[B][R][y, x], var[G][R][y, x], var[R][R][y, x]]])
        cov = np.array([c[y, x] for c in covIP])
        a[y, x] = np.dot(cov, inv(Sigma + eps*np.eye(3)))  # eq 14

    # ECCV10 eq.15
    b = mean_p - a[:, :, R]*means[R] - a[:, :, G]*means[G] - a[:, :, B]*means[B]

    # ECCV10 eq.16
    q = (boxfilter(a[:, :, R], r)*I[:, :, R] + boxfilter(a[:, :, G], r)*I[:, :, G] + boxfilter(a[:, :, B], r)*I[:, :, B] + boxfilter(b, r)) / base

    return q


def get_illumination_channel(I, w):
    M, N, _ = I.shape
    padded = np.pad(I, ((int(w/2), int(w/2)), (int(w/2), int(w/2)), (0, 0)), 'edge')
    darkch = np.zeros((M, N))
    brightch = np.zeros((M, N))

    for i, j in np.ndindex(darkch.shape):
        darkch[i, j] = np.min(padded[i:i + w, j:j + w, :])
        brightch[i, j] = np.max(padded[i:i + w, j:j + w, :])

    return darkch, brightch

def get_atmosphere(I, brightch, p=0.1):
    M, N = brightch.shape
    flatI = I.reshape(M*N, 3)
    flatbright = brightch.ravel()

    searchidx = (-flatbright).argsort()[:int(M*N*p)]
    A = np.mean(flatI.take(searchidx, axis=0), dtype=np.float64, axis=0)
    return A

def get_initial_transmission(A, brightch):
    A_c = np.max(A)
    init_t = (brightch-A_c)/(1.-A_c)
    return (init_t - np.min(init_t))/(np.max(init_t) - np.min(init_t))

def get_corrected_transmission(I, A, darkch, brightch, init_t, alpha, omega, w):
    im3 = np.empty(I.shape, I.dtype);
    for ind in range(0, 3):
        im3[:, :, ind] = I[:, :, ind] / A[ind]
    dark_c, _ = get_illumination_channel(im3, w)
    dark_t = 1 - omega*dark_c
    corrected_t = init_t
    diffch = brightch - darkch

    for i in range(diffch.shape[0]):
        for j in range(diffch.shape[1]):
            if(diffch[i, j] < alpha):
                corrected_t[i, j] = dark_t[i, j] * init_t[i, j]

    return np.abs(corrected_t)

def get_final_image(I, A, refined_t, tmin):
    refined_t_broadcasted = np.broadcast_to(refined_t[:, :, None], (refined_t.shape[0], refined_t.shape[1], 3))
    J = (I-A) / (np.where(refined_t_broadcasted < tmin, tmin, refined_t_broadcasted)) + A

    return (J - np.min(J))/(np.max(J) - np.min(J))

def dehaze(I, tmin, w, alpha, omega, p, eps, reduce=False):
    m, n, _ = I.shape
    Idark, Ibright = get_illumination_channel(I, w)
    A = get_atmosphere(I, Ibright, p)

    init_t = get_initial_transmission(A, Ibright) 
    if reduce:
        init_t = reduce_init_t(init_t)
    corrected_t = get_corrected_transmission(I, A, Idark, Ibright, init_t, alpha, omega, w)

    normI = (I - I.min()) / (I.max() - I.min())
    refined_t = guided_filter(normI, corrected_t, w, eps)
    J_refined = get_final_image(I, A, refined_t, tmin)
    
    enhanced = (J_refined*255).astype(np.uint8)
    f_enhanced = cv2.detailEnhance(enhanced, sigma_s=10, sigma_r=0.15)
    f_enhanced = cv2.edgePreservingFilter(f_enhanced, flags=1, sigma_s=64, sigma_r=0.2)
    return f_enhanced

def reduce_init_t(init_t):
    init_t = (init_t*255).astype(np.uint8)
    xp = [0, 32, 255]
    fp = [0, 32, 48]
    x = np.arange(256)
    table = np.interp(x, xp, fp).astype('uint8')
    init_t = cv2.LUT(init_t, table)
    init_t = init_t.astype(np.float64)/255
    return init_t

def select_image():
    root = tk.Tk()
    root.withdraw()  
    file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")])
    root.destroy()
    return file_path

if __name__ == "__main__":
    image_path = select_image()
    if image_path:
        print(f"Processing image: {image_path}")
        im = cv2.imread(image_path)
        orig = im.copy()

        tmin = 0.1   
        w = 15       
        alpha = 0.4  
        omega = 0.75 
        p = 0.1      
        eps = 1e-3   

        I = np.asarray(im, dtype=np.float64) 
        I = I[:, :, :3] / 255

        messagebox.showinfo("Processing", "The photo is being processed, please wait...")

        f_enhanced = dehaze(I, tmin, w, alpha, omega, p, eps)
        f_enhanced2 = dehaze(I, tmin, w, alpha, omega, p, eps, True)
        
        messagebox.showinfo("Completed", "The photo has been processed successfully!")

        cv2.imshow('original', orig)
        cv2.imshow('F_enhanced', f_enhanced)
        cv2.imshow('F_enhanced2', f_enhanced2)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    else:
        print("No image selected.")
