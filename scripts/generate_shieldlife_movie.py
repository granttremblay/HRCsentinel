#!/usr/bin/env python


import os
import glob

import numpy as np

import imageio


home_directory = os.path.expanduser("~")
frames_directory = home_directory + "/Dropbox/HRCOps/ShieldCloud/scs107_plots/wholemission/"

movie_file = frames_directory + "shieldlife_movie.gif"

# Create list of .png frames
frames = glob.glob(frames_directory + "*.png")

# The list won't be alphanumeric. Fix that. 
frames_sorted = sorted(frames)

gif_frames=[]

for pngfile in frames_sorted:
	print("Reading {}".format(pngfile.split("/")[-1]))
	gif_frames.append(imageio.imread(pngfile))

print("Writing movie. Hang tight.")
imageio.mimwrite(movie_file, gif_frames)

print("Done. Daved your movie to {}".format(movie_file))
