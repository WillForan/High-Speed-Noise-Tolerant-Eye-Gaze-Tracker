import cv2
import numpy as np
from Gradient import gradient
from matplotlib import pyplot as plt

class opticalFlow:
	def __init__(self, image1, image2, address):
	
		#Read two image first
		self.image1 = image1 
		self.image2 = image2
		self.address = address
		#Define kernal size for scanning
		self.op_flow()

	def op_flow(self):
		#Determine the kernal size
		size = 8
		#Gaussian blur the image(kernal height and width)
		image_1 = cv2.blur(self.image1,(15, 15))
		image_2 = cv2.blur(self.image2,(15, 15))

		cv2.imwrite("test.png", image_2)

		#Only get the size and width of image_1
		hi = image_1.shape[0]
		wi = image_1.shape[1]

		#Got the gradient of the image
		fs_x, fs_y = gradient(image_1)
		ss_x, ss_y = gradient(image_2)

		#Got the xx yy and xy for both images
		FI_xx = fs_x**2
		FI_yy = fs_y**2
		FI_xy = fs_x*fs_y

		# SI_xx = ss_x**2
		# SI_yy = ss_y**2
		# SI_xy = ss_x*ss_y
		# #Change in pixel gradient over time
		T = image_1-image_2
		# T = SI_xy - FI_xy
		# print(FI_xy)
		# print(SI_xy)
		# print(T)

		#See the formula 
		R_x = fs_x*T
		R_y = fs_y*T

		#Starting Wposition
		x_pos = []
		y_pos = []
		#Vector value for direction
		x_direct = []
		y_direct = []

		print(hi, wi)
		#Get A
		for i in range(size, hi):
		    for j in range(size, wi):
		        #add on the rectangular value
		        L_1 = np.sum(FI_xx[i - size:i+1+size, j-size:j+1+size])
		        L_2 = np.sum(FI_yy[i - size:i+1+size, j-size:j+1+size])
		        L12 = np.sum(FI_xy[i - size:i+1+size, j-size:j+1+size])

		        R_1 = -np.sum(R_x[i - size:i+1+size, j-size:j+1+size])
		        R_2 = -np.sum(R_y[i - size:i+1+size, j-size:j+1+size])
		        #Find A
		        A = [
		             [L_1, L12],
		             [L12, L_2],
		            ]

		        R = [
		             [R_1],
		             [R_2],
		            ]

		        # print(np.linalg.inv(A))

		        result = np.dot(np.linalg.inv(A), R)
		        x = result[0][0]
		        y = result[1][0]
		        
		        if x == 0 or y == 0: 
		            continue
		        # print(x,y)
		        # x = abs(x)
		        # y = 0

		        # print('\n')
		        
		        x_pos.append(j)
		        y_pos.append(i)
		        x_direct.append(x)
		        y_direct.append(-y)

		new_x_pos = []
		new_y_pos = []
		new_x_direct = []
		new_y_direct = []

		#Easier to see when printed this way
		for i in range(0, len(x_pos), 40):
		    new_x_pos.append(x_pos[i])
		    new_y_pos.append(y_pos[i])
		    new_x_direct.append(x_direct[i])
		    new_y_direct.append(y_direct[i])

		#Print the stuffs on the image
		fig, ax = plt.subplots()

		#Read in the background image only the first one
		img = plt.imread(self.address)
		ax.imshow(img)
		ax.quiver(new_x_pos,new_y_pos,new_x_direct,new_y_direct, color='r')
		plt.savefig('testing.png')


if __name__ == '__main__':
    #Later put into the user interface
    address1 = 'optical_flow_test/image126.png'
    address2 = 'optical_flow_test/image127.png'
    image1 = cv2.imread(address1)
    image2 = cv2.imread(address2)
    opticalFlow(image1, image2, address1)