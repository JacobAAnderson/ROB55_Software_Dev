#!/usr/bin/env python2
# Jake Anderson
# ROB 599 Software Dev
# Homework 1
# Oct 19, 2020

# Find the plane of a wall
# Use laser scan data to do Total Least Squares
import rospy

import numpy as np

from sensor_msgs.msg        import LaserScan
from geometry_msgs.msg      import Pose, Point, PoseStamped, Quaternion
from tf.transformations     import quaternion_from_euler
from visualization_msgs.msg import Marker



def heading(yaw):
    """A helper function to getnerate quaternions from yaws."""
    q = quaternion_from_euler(0, 0, yaw)
    return Quaternion(*q)


def cross2d(a,b):

	n1 = np.sqrt(a[0]*a[0] + a[1]*a[1] )
	n2 = np.sqrt(b[0]*b[0] + b[1]*b[1] )

	ab = a[0] * b[0] + b[1] * a[1]

	a = ab/(n1*n2)

	return np.arccos(a)


def Text( frame_id, x_, y_, theta ):

	marker = Marker()
	marker.header.frame_id = frame_id
	marker.type = marker.TEXT_VIEW_FACING
	marker.action = marker.ADD
	marker.text = "Angle: {:.2f} [deg]".format(theta * 180/np.pi)
	marker.scale.x = 0.5
	marker.scale.y = 0.5
	marker.scale.z = 0.5
	marker.color.a = 1.0
	marker.color.r = 0.0
	marker.color.g = 1.0
	marker.color.b = 1.0
	marker.pose.orientation.w = 1.0
	marker.pose.position.x = x_ + 3 * np.cos(theta)
	marker.pose.position.y = y_ + 3 * np.sin(theta)
	marker.pose.position.z = 0.25

	return marker


def callback(lidar_msg):
	"""
	Callback function to create LaserScan markders.
	"""

	# Get X,Y Coordinates of the laser contacts
	x = []
	y = []

	angles = np.arange(lidar_msg.angle_min, lidar_msg.angle_max, lidar_msg.angle_increment)
	for r, a in zip(lidar_msg.ranges, angles):
		x.append(r * np.cos(a))
		y.append(r * np.sin(a))

	# Get the center of the wall and the covariance matrix
	x_  = np.mean(x)
	y_  = np.mean(y)
	cov = np.cov(x,y)

	# Use covariance matrix to find angle between the wall and robot
	W, V = np.linalg.eig(cov)

	# See which eigen vector should be used
	if W[0] < W[1]:
		theta = cross2d(V[:,1], [0,-1])        # Calculate angle between robot and the wall
	else:                                      #   0 is the robot is perpendiculare to the wall
		theta = cross2d(V[:,0], [0,-1])

	rospy.loginfo("Wall Angle: {0} [deg]".format(theta * 180 / np.pi))

	wall = PoseStamped()
	wall.header = lidar_msg.header
	wall.pose   = Pose(Point(x_, y_, 0), heading(theta))

	text  = Text( lidar_msg.header.frame_id, x_, y_, theta )

	pubW.publish(wall)
	pubT.publish(text)


if __name__ == '__main__':
	# Initialize the node.
	rospy.init_node('wall_finder')

	rospy.loginfo("Starting 'wall_finder' Node")

	# Set up a subscriber and publisher.
	sub  = rospy.Subscriber('base_scan_filterd', LaserScan, callback )
	pubW = rospy.Publisher( 'wall_pose', PoseStamped, queue_size=1 )
	pubT = rospy.Publisher( 'wall_angle_text', Marker, queue_size=1 )

	rospy.spin()
