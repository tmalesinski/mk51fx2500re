import imageio
import matplotlib.pyplot as plt
import numpy as np
import scipy.ndimage

def load_image():
    return imageio.imread("img/mk51_rom_die.jpg")

NROWS = 16 * 5
NCOLS = 16 * 22

R00 = (510, 197.5)
R10 = (3743.1, 202.0)
R01 = (494.6, 1108.5)

CX0 = 534.7
CX1 = 3712.7

def bit_pos(i, j):
    x = CX0 + (CX1 - CX0) * j / (16 * 22 - 1)
    y = (R00[1] + (R01[1] - R00[1]) * i / (16 * 5 - 1) +
         (x - R00[0]) / (R10[0] - R00[0]) * (R10[1] - R00[1]))
    return (x, y)


def get_area(gray, i, j, r):
    x, y = bit_pos(i, j)
    return scipy.ndimage.affine_transform(
        gray, [1, 1], offset=(y - r, x - r), output_shape=(2 * r, 2 * r),
        prefilter=False)


def get_random_bits(img):
    gray = np.mean(img, axis=-1)
    n = 500
    rows = np.random.randint(0, NROWS, n)
    cols = np.random.randint(0, NCOLS, n)
    res = []
    for r, c in zip(rows, cols):
        res.append(get_area(gray, r, c, 3).flatten())
    return np.array(res)


def pca_bits(bits):
    m = np.mean(bits, axis=0)
    b = bits - m
    u, s, v = np.linalg.svd(b)
    return v[0], v[1]


def get_pc(img):
    gray = np.mean(img, axis=-1)
    rbits = get_random_bits(img)
    plt.imshow(rbits); plt.show()
    c1, c2 = pca_bits(rbits)
    m = np.mean(rbits, axis=0)
    pr1 = np.dot(rbits - m, c1)
    plt.plot(range(len(pr1)), pr1, 'x'); plt.show()
    return m, c1

M = np.array([189.65874425, 163.90641334, 155.98414646, 158.16136599,
       158.93950686, 170.83007093, 193.29812701, 168.67812829,
       159.61633928, 161.34572598, 163.48869532, 175.59516817,
       198.06160232, 177.4694989 , 170.91687956, 173.10009711,
       173.81137047, 182.45741622, 200.59431612, 182.49109655,
       177.7909631 , 180.30738711, 179.89019102, 186.3467299 ,
       199.84203548, 179.961734  , 173.82122801, 176.15399925,
       176.89570041, 185.14422612, 195.66970369, 171.57461742,
       162.99096766, 164.95080829, 167.25632738, 179.27765334])
C1 = np.array([-0.04704893, -0.09579545, -0.22798194, -0.28930118, -0.18566232,
              -0.0665317 ,  0.0358345 ,  0.01878957, -0.1315961 , -0.20346627,
              -0.07541347,  0.04435633,  0.13190374,  0.2027167 ,  0.11167305,
              0.0523622 ,  0.14819832,  0.19398221,  0.17839499,  0.29460418,
              0.24172098,  0.19393085,  0.26916633,  0.27169814,  0.15971022,
              0.23307345,  0.14465973,  0.0929638 ,  0.19459791,  0.23811151,
              0.07380907,  0.05872097, -0.08331383, -0.1459898 , -0.01573018,
              0.10222208])
THR = 27

def read_bits(img):
    gray = np.mean(img, axis=-1)
    res = np.zeros((NROWS, NCOLS), dtype=bool)
    for i in range(NROWS):
        for j in range(NCOLS):
            ar = get_area(gray, i, j, 3).flatten()
            # TODO: classify 0/1 based on one example
            res[i, j] = np.dot(ar - M, C1) > THR
    return res

def dist_from_means(bits, m):
    d = []
    for i in range(2):
        d.append(np.sum(np.square(bits - m[i]), axis=-1))
    return np.array(d)

def kmeans(bits, m0, m1):
    m = [m0, m1]
    for step in range(10):
        d = dist_from_means(bits, m)
        closer = np.argmin(d, axis=0)
        m = []
        for i in range(2):
            m.append(np.mean(bits[closer == i], axis=0))
    return tuple(m)

def read_with_kmeans_on_rows(gray, start, limit):
    bits = []
    for i in range(start, limit):
        for j in range(NCOLS):
            bits.append(get_area(gray, i, j, 3).flatten())
    bits = np.array(bits)
    ex1 = get_area(gray, 1, 1, 3).flatten()
    ex0 = get_area(gray, 2, 1, 3).flatten()
    m = kmeans(bits, ex0, ex1)
    d = dist_from_means(bits, m)
    plt.plot(range(d.shape[1]), d[0] - d[1], 'o'); plt.show()
    return np.argmin(d, axis=0).reshape(limit - start, NCOLS)


def read_with_kmeans(img):
    gray = np.mean(img, axis=-1)
    return np.concatenate(
        (read_with_kmeans_on_rows(gray, 0, NROWS // 2),
         read_with_kmeans_on_rows(gray, NROWS // 2, NROWS)), axis=0)

def dump_str(read_bits):
    rows = []
    for i in range(16):
        for j in range(4):
            rows.append("".join([str(b) for b in read_bits[i * 5 + j]]))
    return "\n".join(rows)
