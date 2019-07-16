# WhiskiWrap
WhiskiWrap provides tools for running whiski (http://whiskertracking.janelia.org) more easily and efficiently. 

My goal is to improve whiski in the following ways:

1. Make it more flexible about reading various input files. In my experience whiski has trouble reading certain input videos. Instead, WhiskiWrap uses your system's ffmpeg to read input files (because ffmpeg can typically read almost anything) and to generate simple tiff stacks which whiski can reliably read.
2. Make it faster, by calling many instances of `trace` in parallel on non-overlapping chunks of the input video.
3. Make it more cross-platform and memory-efficient, by converting whiski's output files into HDF5 files which can be read by multiple programs (Python, Matlab) on any operating system. Importantly, HDF5 files can also be read partially to avoid overflowing your system's memory.

## Example
Note: The current best pipeline for running trace is `interleaved_reading_and_trace`, but the command `pipeline_trace` is the only one configured to run measure.

First start the interactive python environment by typing ipython at the terminal.

Import WhiskiWrap so it can be used:

`import WhiskiWrap`

Set the path to the input file. There are some test videos in this repository that you can use. Usually it's best to copy this file to a new directory, because a lot of temporary files will be created in the same directory.
```
mkdir ~/whiski_wrap_session
cp ~/dev/WhiskiWrap/test_video2.mp4 ~/whiski_wrap_session/test_video2.mp4
input_video = '~/whiski_wrap_session/test_video2.mp4'
```

Choose where you want the output HDF5 file to be.

`output_file = 'output.hdf5'`

Run the trace. Here we use 4 parallel processes.

`WhiskiWrap.pipeline_trace(input_video, output_file, n_trace_processes=4)`

If you go to the session directory, you'll see a bunch of tiff stacks and whiskers files that were generated by every instance of trace. There's also a combined HDF5 file with all the data combined. You can read it into Python like so:
```
import tables
import pandas
with tables.open_file(output_file) as fi:`
  test_result = pandas.DataFrame.from_records(
    fi.root.summary.read())     
```
This just reads the "summary": the tip and follicle of every whisker in every frame. The HDF5 file also contains the x- and y-coordinates of every pixel in every whisker, but you probably don't want to read all of this in at once.

## More detail on how WhiskiWrap works
1. Split the entire video into _epochs_ of about 100K frames (~100MB of data). The entire epoch will be read into memory, so the epoch size cannot be too big.
2. For each epoch:
  1. Split it into _chunks_ of about 1000 frames, each of which will be traced separately. The frames can optionally be cropped at this point.
  2. Write each chunk to disk as a tiff stack (note: these files are quite large).
  3. Trace each chunk with parallel instances of `trace`. A `whiskers` file is generated for each chunk.
  4. Parse in order each chunk's `whiskers` file and append the results to an output HDF5 file.
  5. (Optional) delete the intermediate chunk files here.

The following parameters must be chosen:
* `n_trace_processes` - the number of parallel instances of `trace` to run at the same time. The most efficient choice is the number of CPUs on your system.
* `epoch_sz_frames` - the number of frames per epoch. It is most efficient to make this value as large as possible. However, it should not be so large that you run out of memory when reading in the entire epoch of video. 100000 is a reasonable choice.
* `chunk_sz_frames` - the size of each chunk. Ideally, this should be `epoch_size` / `n_trace_processes`, so that all the processes complete at about the same time. It could also be `epoch_size` / (N * `n_trace_processes`) where N is an integer.

You may also add optional parameters to run the measure command
* `measure=True` - run measure command, default is False
* `face='right'` - run measure with face on right side, can also specify to 'left' side

# Installation
WhiskiWrap is written in Python and relies on `ffmpeg` for reading input videos, `tifffile` for writing tiff stacks, `whiski` for tracing whiskers in the tiff stacks, and `pytables` for creating HDF5 files with all of the results.

## Installing `ffmpeg`
First install [`ffmpeg`](https://www.ffmpeg.org/) and ensure it is available on your system path -- that is, you should be able to type `ffmpeg` in the terminal and it should find it and run it.

## Installing `whiski`
Next install [`whiski`](http://whiskertracking.janelia.org). There are several ways to do this:

1. Download the pre-built binary. This is the easiest path because it doesn't require compiling anything. However, you still need to make a few changes to the Python code that is downloaded in order to make it work with `WhiskiWrap`.
2. Build `whiski` from source, using my lightly customized fork. This will probably require more trouble-shooting to make sure all of its parts are working.

To use the pre-built binary (preferred):

1. Download the [zipped binary](http://whiskertracking.janelia.org/wiki/display/MyersLab/Whisker+Tracking+Downloads) and unpack it or get the file whisk-1.1.0d-64bit-Linux.tar.gz from someone. Unpack with `tar -xzf whisk-1.1.0d-64bit-Linux.tar.gz`. Rename the unpacked directory to `~/dev/whisk`
2. Add the binaries to your system path so that you can run `trace` from the command line.
3. Add a few files to make `whiski`'s Python code work more nicely with other packages. (Technically, we need to make it a module, and avoid name collisions with the unrelated built-in module `trace`.)
4. `touch ~/dev/whisk/share/whisk/__init__.py`
5. `touch ~/dev/whisk/share/whisk/python/__init__.py`
6. Add these modules to your Python path.
7. `ln -s ~/dev/whisk/share/whisk/python ~/dev/whisk/python`
8. or `echo "~/whisk/share" >> "~/.local/lib/python2.7/site-packages/whiski_wrap.pth`
9. Test that everything worked by opening python or ipython and running `from whisk.python import traj, trace`

To build from source:

1. Install required dependencies (gl.h, etc)
2. Download the source from my lightly modified fork, which makes the `__init__` changes described above.
3. `cd ~/dev`
4. `git clone https://github.com/cxrodgers/whisk.git`
5. `cd whisk`
6. `mkdir build`
7. `cmake ..`
8. `make`
9. Copy a library into an expected location:
10. `cp ~/dev/whisk/build/libwhisk.so ~/dev/whisk/python`
11. Test that everything worked by opening python or ipython and running `from whisk.python import traj, trace`

## Installing Python modules
Here I outline the use of `conda` to manage and install Python modules. In the long run this is the easiest way. Unfortunately it doesn't work well with user-level `pip`. Specifically, you should not have anything on your `$PYTHONPATH`, and there shouldn't be any installed modules in your `~/.local`.

0. Clone my into ~/dev for video processing functions.
```
cd ~/dev
git clone https://github.com/cxrodgers/my.git
```

0.5. Install scipy.
`conda install scipy`

1. Create a new conda environment for WhiskiWrap.

`conda create -n whiski_wrap python=2.7 pip numpy matplotlib pyqt pytables pandas ipython`
2. Activate that environment and install `tifffile`
```
source activate whiski_wrap
pip install tifffile
```
If `source activate whiski_wrap` doesn't work, try `conda activate whiski_wrap`

3. Clone WhiskiWrap
```
cd ~/dev
git clone https://github.com/cxrodgers/WhiskiWrap.git
```
4. Make sure the development directory is on your Python path.

`echo "~/dev" >> ~/.local/lib/python2.7/site-packages/whiski_wrap.pth`



