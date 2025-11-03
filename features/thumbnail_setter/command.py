import os
import tempfile

class CommandTemplates:

	def __init__(self, parent=None):
		# super().__init__(parent)
		pass
	def generate_commands(self, 
					   input_file: str, 
					   output_folder: str, 
					   timestamp: str) -> tuple[list[str], str]:
		"""Creates the FFmpeg commands for extracting and embedding a thumbnail."""
		filename = os.path.basename(input_file)
		thumb_fd, thumb_path = tempfile.mkstemp(suffix=".jpg", prefix=f"{filename}_thumb_")
		os.close(thumb_fd)

		os.makedirs(output_folder, exist_ok=True)
		output_file_path = os.path.join(output_folder, filename)

		cmd1 = (f'ffmpeg -y -loglevel warning -ss {timestamp} -i "{input_file}" '
				f'-frames:v 1 "{thumb_path}"')

		cmd2 = (f'ffmpeg -y -loglevel warning -i "{input_file}" -i "{thumb_path}" '
				f'-map 0 -map 1 -c copy -disposition:v:1 attached_pic "{output_file_path}"')

		return [cmd1, cmd2], thumb_path