import os
from components import CommandInput, OutputPath

class CommandGenerator(object):
    def __init__(self, 
                 selected_files: list[tuple[str, str, str]], 
                 input_command: CommandInput,
                 output_path: OutputPath):

        self.selected_files = selected_files
        self.input_command = input_command
        self.output_path = output_path

    def create_concat_file(self):
        # create .temp directory in project root, same as main.py
        base_dir = os.path.dirname(os.path.abspath(os.path.join(__file__, "..")))
        temp_dir = os.path.join(base_dir, ".temp")
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)
        
        # create concat_list.txt content
        concat_content = []
        for _, fname, fpath in self.selected_files:
            full_path = os.path.join(fpath, fname)
            concat_content.append(f"file '{full_path}'")
        
        # write to concat_list.txt in .temp directory
        concat_file = os.path.join(temp_dir, "concat_list.txt")
        with open(concat_file, "w", encoding="utf-8") as f:
            f.write("\n".join(concat_content))
    
        return concat_file

    def generate_concat_command(self):
        if not self.selected_files:
            return None

        _, _, inputfile_folder = self.selected_files[0]

        concat_file = self.create_concat_file()
        output_dir = self.output_path.get_completed_output_path(inputfile_folder, "output")
        
        cmd = self.input_command.get_command()
        cmd = cmd.replace("{concat_list}", f'"{concat_file}"')
        cmd = cmd.replace("{output}", output_dir)

        return finalize_command(cmd)

    def generate_others_command(self, input_file):
        if not input_file:
            return None
        
        _, filename, inputfile_folder = input_file
        name, ext = os.path.splitext(filename)
        ext = ext.lstrip('.')

        output_dir = self.output_path.get_completed_output_path(inputfile_folder)

        cmd = self.input_command.get_command()
        cmd = cmd.replace("{input_path}", inputfile_folder)
        cmd = cmd.replace("{output_path}", output_dir)
        cmd = cmd.replace("{filename}", name)
        cmd = cmd.replace("{ext}", ext)

        return finalize_command(cmd)

def finalize_command(cmd):
    # -y to overwrite without asking
    if '-y' not in cmd:
        cmd = cmd.replace("ffmpeg ", "ffmpeg -y ")

    # set loglevel to warning if not specified
    if '-loglevel' not in cmd:
        cmd = cmd.replace("ffmpeg ", "ffmpeg -loglevel warning ")

    return cmd
