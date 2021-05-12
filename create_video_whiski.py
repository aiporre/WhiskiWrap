"""
Copyright (c) 2009 HHMI. Free downloads and distribution are allowed for any
non-profit research and educational purposes as long as proper credit is given
to the author. All other rights reserved.
"""
import argparse
import os
import tables
import pandas
import cv2
import numpy as np
import matplotlib.pyplot as plt

from vtools import ImageToVideo

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas


# 1: Reading arguments:
parser = argparse.ArgumentParser(description='Generate whiski output from video.')
parser.add_argument('video_path',type=str, help='path to the video (video must have an extension e.g. video.avi).')
args = parser.parse_args()

# 2: working directory is always the script directory
wdir = os.getcwd()

# get video name from arguments
video_fname = os.path.basename(args.video_path)
video_name = ''.join(video_fname.split('.')[:-1])
print('Processing video: ', video_name)
# output_path has the same name of the video name plus whiki_
output_path = os.path.join(wdir,'whiski_'+video_name)
print('Output will saved in: ', output_path)

# 3: assert output path was generated by tracing
assert  os.path.exists(output_path), 'whiki output path does\'t exist. The script apply_whiki.py must run before.'

# 4: assert input video has been copied
input_video = os.path.join(output_path,video_fname)
assert os.path.exists(input_video), f'input video must be copied from source ({video_fname}) and placed in {output_path}'

# 5: assert the hdf5 file was generated i.e. apply_whiki.py ran before.
output_file = os.path.join(output_path,video_name+'.hdf5')
assert os.path.exists(output_path), 'hdf5 output file doesn\'t exists. The script apply_whiki.py must run before.'

# 6: format output video paths
input_video = os.path.expanduser(input_video)
output_file = os.path.expanduser(output_file)
output_video = os.path.join(output_path, video_name + '_detected.avi')

# 7: Reading the whiskers detection file
with tables.open_file(output_file) as fi:
    test_result = pandas.DataFrame.from_records(fi.root.summary.read())
    test_result['x'] = fi.root.pixels_x.read()
    test_result['y'] = fi.root.pixels_y.read()

# 8: Reading video input
def read_video(video_path):
    cap = cv2.VideoCapture(video_path)
    frameCount = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frameWidth = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frameHeight = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print('video props: (frameCount, frameHeight, frameWidth)=', (frameCount, frameHeight, frameWidth))
    buf = np.empty((frameCount, frameHeight, frameWidth, 3), np.dtype('uint8'))
    fc = 0
    ret = True
    while (fc < frameCount  and ret):
        ret, buf[fc] = cap.read()
        fc += 1
    cap.release()
    return buf
vid = read_video(input_video)

# 9: Generating video with whiskers plots
def get_whisker(results,time):
    frame = results[results.time == time]
    coords = []
    for i in range(len(frame)):
        coords.append((frame.tip_x.iloc[i],frame.tip_y.iloc[i],frame.fol_x.iloc[i],
                       frame.fol_y.iloc[i],frame.x.iloc[i],frame.y.iloc[i]))
    return coords


video_out = ImageToVideo(gray='n')

N,H,W,C = vid.shape
print('video shape is: ', vid.shape)

video_out.set_output(W, H, output_path = output_video)
plt.ioff()
print('Generating video with whiskers..')
for time_pos in range(N):
    print('time pos: ', time_pos)
    ws_coords = get_whisker(test_result,time_pos)
    fig = plt.figure( dpi = H/5,)
    fig.set_size_inches(5. * W / H, 5, forward = False)
    canvas = FigureCanvas(fig)
    ax = plt.Axes(fig, [0., 0., 1., 1.])
    ax.set_axis_off()
    fig.add_axes(ax)
    ax.imshow(vid[time_pos])
    for c in ws_coords:
        ax.plot(c[4],c[5],'r')
#         ax.plot([c[0],c[2]],[c[1],c[3]],'r')
    fig.canvas.draw()
    image = np.fromstring(canvas.tostring_rgb(), dtype='uint8')
    width, height = fig.get_size_inches() * fig.get_dpi()
    image = image.reshape(int(height), int(width), 3)
    print(image.shape)
    video_out.update(image)
    plt.close(fig)
video_out.close()

print("Done")