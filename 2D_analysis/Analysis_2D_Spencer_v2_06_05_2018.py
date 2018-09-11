'''
Created on 05/21/2018
v1 Finished on 05/22/2018
v2 Finished on 06/05/2018
		- slight modification from v1 by improving the function that changes the interslice angle (Theta)
		- remove error check for input file
		- external line load computed for each slice

@author: Enok C.

2D LEM Slope Analysis - Spencer (1967)
'''

'''
purpose: Compute 2D FS using Spencer's method (1967) 
Input: slice geometry, shear strength,  external load, seismic load, water, tension crack, center point, 
Output: FS, Theta (interslice force angle)

Spencer's 2D LEM slope stability analysis method (1967) assumes:
1. equilibrium in vertical, horizontal and moment
2. relationship between interslice shear and normal forces are constant
'''

'''Input'''
# import slice
'''
description of the input file - subjected to change

## Input file column legend for very first row 1 
0(A) - 2D or 3D analysis (2 = 2D; 3 = 3D)
1(B) - id of analysis (id links to a specific model)
2(C) - total number of slip surfaces

## Input file column legend for row 1 
0(A) - 2D or 3D analysis (2 = 2D; 3 = 3D)
1(B) - id of analysis (id links to a specific model)
2(C) - id of slip surface (id links to a particular slip surface)
3(D) - number of slices 
4(E) - Direction of slope movement (0 = right to left; 1 = left to right) 
5(F) - X coordinate of center of rotation (Pt0x)
6(G) - Y coordinate of center of rotation (Pt0y)
7(H) - seismic coefficient for horizontal force (k)
8(I) - resultant water forces - from tension crack or submersion (A)
9(J) - perpendicular distance from the resultant water force to the center of rotation (a)
10(K) - shear strength id (each id links to certain shear strength:
			1 = Mohr-Coulomb
			2 = undrained (Su)
			3 = stress-(c & phi') relationship 
			4 = stress-shear relationship
			
## Input file column legend for row 2 and below
0(A) - slice number
1(B) - slice horizontal width (b)
2(C) - slice base length (l)
3(D) - slice base angle from horizontal (alpha)
4(E) - slice top angle from horizontal (beta)
5(F) - radius (R) 
6(G) - perpendicular offset from center of rotation(f)
7(H) - horizontal distance from slice to the center of rotation (x)
8(I) - vertical distance from C.G. of slice to the center of rotation (e)
9(J) - slice total weight force (W) 
10(K) - pore-water force at the top of slice (U_t)
11(L) - pore-water force at normal to the base of slice (U_b)
12(M) - pore-water force at the left side of slice (U_l)
13(N) - pore-water force at the right side of slice (U_r)
14(O) - external load - line load (L)
15(P) - line load orientation from horizontal (omega)
16(Q) - perpendicular distance from the line load to the center of rotation (L-d)
17(R) - resultant maximum tensile force from support (T) 
18(S) - angle of support force from horizontal (i) 
19(T) - Soil Shear Strength force (Sm)
20(U) - Mohr-Coulomb shear strength - cohesion (c')
21(V) - Mohr-Coulomb shear strength - angle for friction (phi')
22(W) - tension crack coefficient 
			1 = no tension crack
			0 = all base tension cracked
			in-between = partial tension crack on the base length 
'''

'''change the interslice angle theta based on the difference of FS for v2'''
def changeIntersliceTheta_Spencer(thetaInter, FS_moment_f, FS_force_f, tolaranceFS):
	# create total number of change criteria based on decimal points   
	if tolaranceFS >= 1:
		decimalPoint = 1
	elif tolaranceFS < 0.0001:
		dpListed = list(str(tolaranceFS))
		idx = dpListed.index('-')
		dPstring = ''.join(dpListed[idx+1:])
		decimalPoint = int(dPstring)
	else:
		decimalPoint = len(list(str(tolaranceFS)))-2	

	if decimalPoint >= 5:
		decimalPoint = 5
		tolaranceFS = 0.00001
		
	dFSLimList = [1]
	for loop1 in range(decimalPoint):
		if loop1 == decimalPoint-1:
			dFSLimList.append(tolaranceFS)
		elif tolaranceFS >= 0.0001 and loop1 == decimalPoint-2:
			dFSLimList.append(tolaranceFS*5)
		else:
			dFSLimList.append(0.1*float('1E-'+str(loop1)))

	# change the interslice force angle
	completeValueChangeSet = [10, 5, 1, 0.1, 0.01]
	valueChangeList = completeValueChangeSet[-(decimalPoint):]

	# changing thetaInter higher or lower value
	if FS_moment_f>FS_force_f:
		UorD = 1
	else:
		UorD = -1

	absDiffFS = abs(FS_moment_f - FS_force_f)
	for loop2 in range(decimalPoint):
		if absDiffFS <= tolaranceFS:
			valueChange = valueChangeList[-1]
			break
		elif absDiffFS <= dFSLimList[loop2] and absDiffFS > dFSLimList[loop2+1]:
			valueChange = valueChangeList[loop2]
			break
			
	thetaInter += valueChange*UorD

	return thetaInter

'''main function - Spencer Method 2D LEM slope stability analysis'''
def analysis2DSpencer(inputFileName, tolaranceFS, iterationNMax):
	# import function from Math Library
	#import numpy as np
	import math
	import making_list_with_floats as makeList  # functions from making_list_with_floats.py
	import Analysis_2D_Ordinary_V4_06_09_2018 as ordinary
 
	# take the inputfile and convert it into list
	analysisInput = makeList.csv2list(inputFileName)

	# initial trial of FS
	FS_initials = ordinary.ordinary_method(inputFileName) 

	totalSlipSurface = int(analysisInput[0][2])	# total number of slip surfaces

	# cut into separate files
	results2DLEMSpencer = []
	for loopSlip in range(totalSlipSurface):
		# starting and ending row numbers
		if loopSlip == 0:
			startingRowN = 1
		else:
			startingRowN = endingRowN+1
		endingRowN = startingRowN + int(analysisInput[startingRowN][3])

		analysisInfo = analysisInput[startingRowN]
		sliceInfo = analysisInput[startingRowN+1:endingRowN+1]
		
		# trial interslice angle (theta)
		thetaInter = 0
		iterationNN = 1
		iteration1 = True

		while iteration1:

			FS_force_i = FS_initials[loopSlip]		# inital trial value of FS for force equilibrium
			FS_moment_i = FS_initials[loopSlip]			# inital trial value of FS for moment equilibrium
			iterationN = 1
			dE_list = []
			iteration2 = True
			
			while iteration2:
				
				# FS for force calculated
				FS_force = 0
				FS_f_nom = 0
				FS_f_de = analysisInfo[8] 	# A 

				# FS for moment calculated
				FS_moment = 0
				FS_m_nom = 0
				FS_m_de = analysisInfo[8]*analysisInfo[9] # A*a

				# iterate trough slice
				for loopSlice in range(len(sliceInfo)):			
					# net pore-water pressure
					u_net_base = sliceInfo[loopSlice][11] - sliceInfo[loopSlice][10]
					u_net_side = abs(sliceInfo[loopSlice][12] - sliceInfo[loopSlice][13])

					# interslice assumption for first analysis
					if iterationN == 1:
						dX_f = math.tan(math.radians(thetaInter))*u_net_side
						dX_m = math.tan(math.radians(thetaInter))*u_net_side	   # change in vertical interslice force (dX = X_L-X_R)
					# using FS from previous calculation dX is calculated
					else:
						dX_f = math.tan(math.radians(thetaInter))*dE_list[loopSlice][0]
						dX_m = math.tan(math.radians(thetaInter))*dE_list[loopSlice][1]

					# actual resisting base length = base length * tension crack coefficient
					b_len_r = sliceInfo[loopSlice][2]*sliceInfo[loopSlice][22]
					
					if analysisInfo[10] == 1:
						# calculate normal force (P) for force equilibrium
						ma_force = math.cos(math.radians(sliceInfo[loopSlice][3])) + math.sin(math.radians(sliceInfo[loopSlice][3]))*math.tan(math.radians(sliceInfo[loopSlice][21]))/FS_force_i
						P_force = (sliceInfo[loopSlice][9] + sliceInfo[loopSlice][10] - dX_f - (sliceInfo[loopSlice][20])*b_len_r*math.sin(math.radians(sliceInfo[loopSlice][3]))/FS_force_i + u_net_base*math.tan(math.radians(sliceInfo[loopSlice][21]))*math.sin(math.radians(sliceInfo[loopSlice][3]))/FS_force_i)/ma_force
						
						# calculate normal force (P) for moment equilibrium
						ma_moment = math.cos(math.radians(sliceInfo[loopSlice][3])) + math.sin(math.radians(sliceInfo[loopSlice][3]))*math.tan(math.radians(sliceInfo[loopSlice][21]))/FS_moment_i
						P_moment = (sliceInfo[loopSlice][9] + sliceInfo[loopSlice][10] - dX_m - (sliceInfo[loopSlice][20])*b_len_r*math.sin(math.radians(sliceInfo[loopSlice][3]))/FS_moment_i + u_net_base*math.tan(math.radians(sliceInfo[loopSlice][21]))*math.sin(math.radians(sliceInfo[loopSlice][3]))/FS_moment_i)/ma_moment
					
						# calculate shear strength
						shear_strength_f = (sliceInfo[loopSlice][21]*b_len_r + (P_force - u_net_base)*math.tan(math.radians(sliceInfo[loopSlice][21])))
						shear_strength_m = (sliceInfo[loopSlice][21]*b_len_r + (P_moment - u_net_base)*math.tan(math.radians(sliceInfo[loopSlice][21])))

					elif analysisInfo[10] != 1:
						# calculate normal force (P) for force equilibrium
						P_force = (sliceInfo[loopSlice][9] + sliceInfo[loopSlice][10] - dX_f - sliceInfo[loopSlice][19]*math.sin(math.radians(sliceInfo[loopSlice][3]))/FS_force_i)/math.cos(math.radians(sliceInfo[loopSlice][3]))
						
						# calculate normal force (P) for moment equilibrium
						P_moment = (sliceInfo[loopSlice][9] + sliceInfo[loopSlice][10] - dX_m - sliceInfo[loopSlice][19]*math.sin(math.radians(sliceInfo[loopSlice][3]))/FS_moment_i)/math.cos(math.radians(sliceInfo[loopSlice][3]))

						# calculate shear strength
						shear_strength_f = sliceInfo[loopSlice][19]
						shear_strength_m = sliceInfo[loopSlice][19]

					# calcualte FS for force 
					FS_f_nom += math.cos(math.radians(sliceInfo[loopSlice][3]))*shear_strength_f
					FS_f_de += P_force*math.sin(math.radians(sliceInfo[loopSlice][3])) + analysisInfo[7]*(sliceInfo[loopSlice][9]+sliceInfo[loopSlice][10]) - sliceInfo[loopSlice][14]*math.cos(math.radians(sliceInfo[loopSlice][15]))

					# calcualte FS for moment 
					FS_m_nom += sliceInfo[loopSlice][5]*shear_strength_m
					FS_m_de += (sliceInfo[loopSlice][9]+sliceInfo[loopSlice][10])*sliceInfo[loopSlice][7] - P_moment*sliceInfo[loopSlice][6] + analysisInfo[5]*sliceInfo[loopSlice][9]*sliceInfo[loopSlice][8] + sliceInfo[loopSlice][14]*sliceInfo[loopSlice][16]
					
					# calculate dE for next iteration
					# dE = change in horizontal interslice force (dE = E_L-E_R)
					dE_f = u_net_side + P_force*math.sin(math.radians(sliceInfo[loopSlice][3])) - (math.cos(math.radians(sliceInfo[loopSlice][3]))*shear_strength_f/FS_force_i) + analysisInfo[7]*sliceInfo[loopSlice][9] 
					dE_m = u_net_side + P_moment*math.sin(math.radians(sliceInfo[loopSlice][3])) - (math.cos(math.radians(sliceInfo[loopSlice][3]))*shear_strength_m/FS_moment_i) + analysisInfo[7]*sliceInfo[loopSlice][9] 

					if iterationN == 1:
						dE_list.append([dE_f, dE_m])
					else:
						dE_list[loopSlice] = [dE_f, dE_m]

				# calculated FS
				FS_force = FS_f_nom/FS_f_de
				FS_moment = FS_m_nom/FS_m_de
				
				if iterationN >= iterationNMax:
					print('too many iterations - check code or increase maximum iteration number')
					iteration2 = False
				elif abs(FS_force_i - FS_force) > tolaranceFS or abs(FS_moment_i - FS_moment) > tolaranceFS:
					FS_force_i = FS_force
					FS_moment_i = FS_moment
					FS_force = 0
					FS_moment = 0
					iterationN += 1
				else:
					FS_force_i = FS_force
					FS_moment_i = FS_moment
					iteration2 = False

			FS_force_f = FS_force_i
			FS_moment_f = FS_moment_i
			
			if iterationN >= iterationNMax or iterationNN >= iterationNMax:
				print('too many iterations - check code or increase maximum iteration number')
				iteration1 = False
				FS_final = 'None'
			elif abs(FS_moment_f - FS_force_f) > tolaranceFS:
				iterationNN += 1
				thetaInter = changeIntersliceTheta_Spencer(thetaInter, FS_moment_f, FS_force_f, tolaranceFS)
			else:
				FS_final = FS_force_f
				iteration1 = False
		
		results2DLEMSpencer.append([analysisInfo[0:3], [FS_final, thetaInter]])

	return results2DLEMSpencer
	
'''Output Check'''
import time
time_start = time.clock()

iterationNMax = 500
inputFileName = 'test inputs for analysis.csv'	# test sample of csv file used for the analysis
tolaranceFS = 0.001
FS = analysis2DSpencer(inputFileName, tolaranceFS, iterationNMax)
print(FS)

time_elapsed = (time.clock() - time_start)
print(time_elapsed)  # tells us the computation time in seconds