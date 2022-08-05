import os
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor
import queue
import re

class FFMPEG:
	output_dir='compressed/'
	verbosity='-hide_banner -v info'
	tuning='-pix_fmt yuv420p  -c:v h264_nvenc   -profile high -preset p1 -b:v 3M'
	profile='-bsf:v h264_metadata=video_format=1:colour_primaries=9:transfer_characteristics=18:matrix_coefficients=9 '
	profile=''

class GPU:
	def __init__(self,gid,task_queue):
		self.gid=gid
		self.task_queue=task_queue
		self.commandstring=f'''ffmpeg -hwaccel_device {gid} -hwaccel nvdec  {FFMPEG.verbosity}  -i "#VIDEOFILE" {FFMPEG.tuning} {FFMPEG.profile} -y ../{FFMPEG.output_dir}"#VIDEOFILE"'''

	def start_worker(self):
		while not self.task_queue.empty():
			t0=time.time()
			filename=self.task_queue.get()
			finalcommand=re.sub(r'#VIDEOFILE',filename,self.commandstring)

			print(f'INFO: GPU{self.gid} is processing {filename}')
			subprocess.check_output(finalcommand)
			print(f'INFO: GPU{self.gid} took [{time.time()-t0}s] to process {filename}')
			


def get_videos_in_folder(dir='./'):
	includefilters=['.mp4','.mkv','.avi','.mov','.webm','.3gp']
	vids=[f for f in os.listdir(dir) for ext in includefilters if ext in f ]
	return vids


def convert_other_video_to_mp4():
	mp4FileSet={x for x in os.listdir() if x.endswith('.mp4')}
	nonmp4filelist=allVideos - mp4FileSet
	for v in nonmp4filelist:
		os.system(f'start ffmpeg -y -i "{v}" -vcodec libx265 "{v.split(".")[0]+".mp4"}" ')

def concat_all_mp4_videos():
	# mp4FileSet={x for x in os.listdir() if x.endswith('.mp4')}
	mp4files='\n'.join(sorted([f"file '{x}'" for x in os.listdir() if x.endswith('.mp4')]))
	print(mp4files)
	open('fileQueue','w').write(mp4files)
	
	COMMAND=f"start cmd /k \"ffmpeg -safe 0 -f concat  -i fileQueue -vcodec libx265 -crf 32 output.mp4\" "
	os.system(COMMAND)


def compress_all_videos(input_dir='input/',output_dir=FFMPEG.output_dir):
	TPOOL=ThreadPoolExecutor(max_workers=3,)
	# proclist=[]
	os.makedirs(output_dir, exist_ok=True)
	vids= get_videos_in_folder(input_dir)
	os.chdir(input_dir)
	print(os.getcwd(),vids)

	q = queue.Queue();[q.put(x) for x in vids]

	gpus=[GPU(0,q),GPU(2,q),GPU(1,q)]

	for gpu in gpus:
		TPOOL.submit(gpu.start_worker)
		print('workers started')



if __name__ == '__main__':
	# convert_other_video_to_mp4()
	# concat_all_mp4_videos()
	compress_all_videos()
