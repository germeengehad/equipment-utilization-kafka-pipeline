from moviepy.video.io.VideoFileClip import VideoFileClip

input_path = "data/raw/test_video.mp4"
output_path = "data/raw/test_clip.mp4"

start_time = 380   # 6:20
end_time = 420     # 7:00

clip = VideoFileClip(input_path).subclipped(start_time, end_time)
clip.write_videofile(output_path, codec="libx264", audio=False)