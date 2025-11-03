import os
import tempfile
from ..base import BaseCommandTemplate
from typing import TYPE_CHECKING
	
if TYPE_CHECKING:
	from .placeholders import ThumbnailSetterPlaceholders

class CommandTemplates(BaseCommandTemplate):

	def __init__(self, placeholders: 'ThumbnailSetterPlaceholders', parent=None):
		super().__init__(parent)
		self._placeholders = placeholders
		self._DEFAULT_CMD = [
			f'ffmpeg -y -loglevel warning -ss {self._placeholders.get_TIMESTAMP()} '
			f'-i "{self._placeholders.get_INFILE_FOLDER()}/{self._placeholders.get_INFILE_NAME()}.{self._placeholders.get_INFILE_EXT()}" '
			f'-frames:v 1 "{self._placeholders.get_THUMB_PATH()}"',

			f'ffmpeg -y -loglevel warning '
			f'-i "{self._placeholders.get_INFILE_FOLDER()}/{self._placeholders.get_INFILE_NAME()}.{self._placeholders.get_INFILE_EXT()}" '
			f'-i "{self._placeholders.get_THUMB_PATH()}" '
			f'-map 0 -map 1 -c copy -c:s copy -disposition:v:1 attached_pic '
			f'"{self._placeholders.get_OUTPUT_FOLDER()}/{self._placeholders.get_INFILE_NAME()}.{self._placeholders.get_INFILE_EXT()}"'
		]

		self._set_default_cmd()

	def generate_commands(self, 
					   input_file: str, 
					   output_folder: str, 
					   timestamp: str) -> tuple[list[str], str]:
		"""Creates the FFmpeg commands for extracting and embedding a thumbnail."""
		
		filename = os.path.basename(input_file)
		thumb_fd, thumb_path = tempfile.mkstemp(suffix=".jpg", prefix=f"{filename}_thumb_")
		os.close(thumb_fd)

		os.makedirs(output_folder, exist_ok=True)

		replacements = {
			self._placeholders.get_INFILE_FOLDER(): os.path.dirname(input_file),
			self._placeholders.get_INFILE_NAME(): os.path.splitext(filename)[0],
			self._placeholders.get_INFILE_EXT(): os.path.splitext(filename)[1][1:],
			self._placeholders.get_OUTPUT_FOLDER(): output_folder,
			self._placeholders.get_TIMESTAMP(): timestamp,
			self._placeholders.get_THUMB_PATH(): thumb_path,
		}
		
		command_templates = self.get_command_template()
		if not command_templates:
			return None, None
		commands = []
		for template in command_templates:
			cmd = self._placeholders.replace_placeholders(template, replacements)
			commands.append(cmd)
		
		return commands, thumb_path
	