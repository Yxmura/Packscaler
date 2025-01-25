import os
import zipfile
from PIL import Image
import multiprocessing
import customtkinter as ctk
from tkinter import filedialog, messagebox
import shutil
import tempfile


class TexturePackUpscaler(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window setup
        self.title("Packscaler")
        self.geometry("500x450")
        self.iconbitmap('icon.ico')

        # File selection
        self.file_label = ctk.CTkLabel(self, text="No file selected")
        self.file_label.pack(pady=20)

        self.select_button = ctk.CTkButton(self, text="Select Texture Pack", command=self.select_texture_pack)
        self.select_button.pack(pady=10)

        # Mode selection
        self.mode_var = ctk.StringVar(value="upscale")
        self.mode_label = ctk.CTkLabel(self, text="Scaling Mode")
        self.mode_label.pack(pady=10)

        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=10)

        self.upscale_radio = ctk.CTkRadioButton(
            self.mode_frame,
            text="Upscale",
            variable=self.mode_var,
            value="upscale"
        )
        self.upscale_radio.pack(side="left", padx=10)

        self.downscale_radio = ctk.CTkRadioButton(
            self.mode_frame,
            text="Downscale",
            variable=self.mode_var,
            value="downscale"
        )
        self.downscale_radio.pack(side="left", padx=10)

        # Upscale factor slider
        self.scale_label = ctk.CTkLabel(self, text="Scale Factor: 2x")
        self.scale_label.pack(pady=10)

        self.scale_slider = ctk.CTkSlider(
            self,
            from_=1,
            to=4,
            number_of_steps=3,
            command=self.update_scale_label
        )
        self.scale_slider.set(2)
        self.scale_slider.pack(pady=10)

        # Upscale button
        self.upscale_button = ctk.CTkButton(self, text="Process Texture Pack", command=self.process_texture_pack)
        self.upscale_button.pack(pady=20)

        self.selected_file = None

    def select_texture_pack(self):
        self.selected_file = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if self.selected_file:
            self.file_label.configure(text=os.path.basename(self.selected_file))

    def update_scale_label(self, value):
        mode = self.mode_var.get()
        self.scale_label.configure(text=f"{mode.capitalize()} Factor: {int(value)}x")

    def process_texture_pack(self):
        if not self.selected_file:
            messagebox.showerror("Error", "Please select a texture pack")
            return

        scale_factor = int(self.scale_slider.get())
        mode = self.mode_var.get()
        output_zip = self.selected_file.replace('.zip', f'_{scale_factor}x_{mode}d.zip')

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                self.scale_texture_pack(self.selected_file, temp_dir, output_zip, scale_factor, mode)

            messagebox.showinfo("Success", f"Texture pack {mode}d and saved to:\n{output_zip}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    @staticmethod
    def scale_image(input_path, output_path, scale_factor, mode):
        try:
            with Image.open(input_path) as img:
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')

                if mode == "upscale":
                    new_size = (img.width * scale_factor, img.height * scale_factor)
                    scaled_img = img.resize(new_size, Image.NEAREST)
                else:  # downscale
                    new_size = (max(1, img.width // scale_factor), max(1, img.height // scale_factor))
                    scaled_img = img.resize(new_size, Image.LANCZOS)

                pixels = scaled_img.load()
                for x in range(scaled_img.width):
                    for y in range(scaled_img.height):
                        r, g, b, a = pixels[x, y]
                        if a < 255:
                            pixels[x, y] = (r, g, b, 255)

                scaled_img.save(output_path)
        except Exception as e:
            print(f"Error scaling {input_path}: {e}")

    def scale_texture_pack(self, zip_path, temp_dir, output_zip, scale_factor, mode):
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        image_extensions = ['.png', '.jpg', '.jpeg']
        image_paths = []

        for root, _, files in os.walk(temp_dir):
            for file in files:
                if os.path.splitext(file)[1].lower() in image_extensions:
                    image_paths.append(os.path.join(root, file))

        with multiprocessing.Pool() as pool:
            pool.starmap(self.scale_image,
                         [(path, path, scale_factor, mode) for path in image_paths])

        with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, temp_dir)
                    zipf.write(file_path, arcname=arcname)


def main():
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")

    app = TexturePackUpscaler()
    app.mainloop()


if __name__ == "__main__":
    main()