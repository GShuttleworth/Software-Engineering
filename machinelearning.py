#!/usr/bin/python
import numpy as np



xs = np.array([0.0, 1.0, 2.0, 3.0, 4.0, 5.0 ,6.0 ,7.0, 8.0, 9.0])
ys = np.array([100.0, 110.0, 125.0, 144.0, 167.0, 199.0, 251.0, 321.0, 460.0, 600.0])
degree = 1

coeff = np.polyfit(xs, ys, degree)

print ("%dx + %d" % (coeff[0], coeff[1]))
