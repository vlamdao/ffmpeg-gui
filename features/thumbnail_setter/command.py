import os
import tempfile

class CommandTemplates:

	def __init__(self, video_path: str, output_folder: str, timestamp: str):
		self._video_path = video_path
		self._output_folder = output_folder
		self._timestamp = timestamp

	def generate_commands(self) -> tuple[list[str], str]:
		"""Creates the FFmpeg commands for extracting and embedding a thumbnail."""
		filename = os.path.basename(self._video_path)
		thumb_fd, thumb_path = tempfile.mkstemp(suffix=".jpg", prefix=f"{filename}_thumb_")
		os.close(thumb_fd)

		os.makedirs(self._output_folder, exist_ok=True)
		output_file_path = os.path.join(self._output_folder, filename)

		cmd1 = (f'ffmpeg -y -loglevel warning -ss {self._timestamp} -i "{self._video_path}" '
				f'-frames:v 1 "{thumb_path}"')

		cmd2 = (f'ffmpeg -y -loglevel warning -i "{self._video_path}" -i "{thumb_path}" '
				f'-map 0 -map 1 -c copy -disposition:v:1 attached_pic "{output_file_path}"')

		return [cmd1, cmd2], thumb_path