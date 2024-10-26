import os
import shutil
from tkinter import Tk, Label, Button, filedialog, messagebox
from tkinter import Canvas, Scrollbar, Frame
from PIL import Image, ImageTk
from pillow_heif import register_heif_opener
from tkinter import PhotoImage
import datetime
import tkinter.font as tkFont

BACKGROUND_COLOR_1 = "#222222"
BACKGROUND_COLOR_2 = "#353535"
BACKGROUND_COLOR_3 = "#666666"
FOREGROUND_COLOR = "#FFFFFF"
FONT = ("Poppins", 11)


class ImageSelectorApp:
    def __init__(self, root):
        register_heif_opener()  # support for ".heic" files

        self.root = root
        self.root.configure(bg=BACKGROUND_COLOR_2)
        self.root.title("Selector imatges")
        self.selected_images = []

        # Create frame for displaying images
        self.canvas = Canvas(
            root, bg=BACKGROUND_COLOR_1, borderwidth=0, highlightthickness=0
        )
        self.scrollbar = Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = Frame(self.canvas, bg=BACKGROUND_COLOR_1)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Bind mouse scroll to the canvas
        self.canvas.bind_all("<MouseWheel>", self.on_mousewheel)  # Windows and Linux
        self.canvas.bind_all("<Button-4>", self.on_mousewheel)  # macOS scroll up
        self.canvas.bind_all("<Button-5>", self.on_mousewheel)  # macOS scroll down

        # Label to show number of selected images
        self.selected_count_label = Label(
            root,
            text="Seleccionades: 0",
            fg=FOREGROUND_COLOR,
            bg=BACKGROUND_COLOR_2,
            font=FONT,
        )
        self.selected_count_label.pack(pady=10)

        # Select folder button
        self.select_folder_button = Button(
            root,
            text="Obrir carpeta",
            command=self.browse_folder,
            borderwidth=0,
            bg=BACKGROUND_COLOR_3,
            fg=FOREGROUND_COLOR,
            activebackground=BACKGROUND_COLOR_2,
            font=FONT,
            width=13,
            height=1,
        )
        self.select_folder_button.pack(pady=10, padx=20)

        # Save images button
        self.save_images_button = Button(
            root,
            text="Acabar",
            command=self.send_images,
            borderwidth=0,
            relief="solid",
            bg="#22a14a",
            fg="white",
            activebackground="#AAAAAA",
            font=FONT,
            width=13,
            height=1,
        )
        self.save_images_button.pack(padx=20)

    def on_mousewheel(self, event):
        if event.num == 4 or event.delta > 0:
            self.canvas.yview_scroll(-1, "units")  # Scroll up
        elif event.num == 5 or event.delta < 0:
            self.canvas.yview_scroll(1, "units")  # Scroll down

    def browse_folder(self):
        folder_path = filedialog.askdirectory()
        if folder_path:
            self.load_images_from_folder(folder_path)

    def load_images_from_folder(self, folder_path):
        # Clear the canvas
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        self.selected_images = []
        self.update_selected_count()

        loading_label = Label(
            self.canvas,
            text="Carregant imatges...",
            font=("Poppins", 12),
            fg="white",
            bg=BACKGROUND_COLOR_1,
            padx=10,
        )
        loading_label.place(relx=0.5, rely=0.5, anchor="center")
        self.root.update()  # Force the GUI to update to display the label immediately

        self.images = []
        self.image_labels = []

        image_width = 250
        image_padding = 5

        self.canvas.update()
        max_width = self.canvas.winfo_width()

        x = 0  # Column index
        y = 0  # Row index

        # Get list of image files in the folder
        image_files = [
            file
            for file in os.listdir(folder_path)
            if file.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".heic"))
        ]
        total_images_number = len(image_files)

        for i, file in enumerate(image_files, start=1):
            image_path = os.path.join(folder_path, file)
            image = Image.open(image_path)
            image.thumbnail((image_width, image_width))

            img = ImageTk.PhotoImage(image)
            self.images.append(img)  # Store reference to avoid garbage collection

            label = Label(
                self.scrollable_frame,
                image=img,
                borderwidth=5,
                relief="flat",
                background="white",
            )
            label.bind(
                "<Button-1>",
                lambda e, img_path=image_path: self.toggle_selection(e, img_path),
            )

            # Check if we need to wrap to the next row
            if (x * (image_width + image_padding)) > (max_width - 300):
                x = 0  # Reset column index
                y += 1  # Move to the next row

            # Calculate the position
            label.grid(
                row=y,
                column=x,
                padx=image_padding,
                pady=image_padding,
            )

            # Increment the column index
            x += 1

            self.image_labels.append(label)

            loading_label.config(text=f"Carregant imatges... {i}/{total_images_number}")
            self.root.update()  # Update the GUI to reflect changes

        loading_label.place_forget()  # Remove "loading" label when images are loaded

    def toggle_selection(self, event, image_path):
        label = event.widget

        if image_path in self.selected_images:  # Deselect image
            self.selected_images.remove(image_path)
            label.config(borderwidth=5, relief="flat", background="white")
        else:  # Select image
            self.selected_images.append(image_path)
            label.config(
                borderwidth=5, relief="flat", background="blue"
            )  # Blue background for selected

        self.update_selected_count()

    def update_selected_count(self):
        self.selected_count_label.config(
            text=f"Seleccionades: {len(self.selected_images)}"
        )

    def send_images(self):
        if not self.selected_images:
            messagebox.showwarning("Advertencia", "No hi ha cap imatge seleccionada!")
            return

        # Get the user's desktop path
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
        folder_name = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_path = os.path.join(desktop_path, folder_name)

        try:
            os.makedirs(folder_path)
        except OSError:
            messagebox.showerror(
                "Error", f"No s'ha pogut crear la carpeta a {folder_path}"
            )
            return

        for image_path in self.selected_images:
            shutil.copy(image_path, folder_path)

        messagebox.showinfo(
            "Operació completada",
            f"Les imatges han sigut correctament copiades a {folder_path}",
        )
        self.selected_images = []
        self.update_selected_count()


if __name__ == "__main__":
    root = Tk()
    icon = PhotoImage(file="assets/logo.png")
    root.iconphoto(False, icon)
    app = ImageSelectorApp(root)

    root.state("zoomed")
    root.mainloop()