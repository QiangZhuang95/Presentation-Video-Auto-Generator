import tkinter as tk
from tkinter import filedialog, messagebox
import fitz  # PyMuPDF
import subprocess

class PDFSplitAndMergeVideosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Split & Merge Videos Tool")

        # Split PDF
        tk.Label(root, text="Select PDF File:").pack()
        self.entry_pdf = tk.Entry(root, width=50)
        self.entry_pdf.pack()
        tk.Button(root, text="Browse", command=self.select_pdf).pack()

        tk.Label(root, text="Select Output Folder for PDF Pages:").pack()
        self.entry_output_folder = tk.Entry(root, width=50)
        self.entry_output_folder.pack()
        tk.Button(root, text="Browse", command=self.select_output_folder).pack()

        tk.Button(root, text="Split PDF into Pages", command=self.split_pdf_into_pages).pack()

        # Merge Videos
        tk.Label(root, text="Select MP4 Files to Merge:").pack()
        self.listbox_videos = tk.Listbox(root, width=50, height=4)
        self.listbox_videos.pack()
        tk.Button(root, text="Add MP4 File", command=self.add_mp4_file).pack()
        tk.Button(root, text="Merge MP4 Files", command=self.merge_videos).pack()

    def select_pdf(self):
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        self.entry_pdf.delete(0, tk.END)
        self.entry_pdf.insert(0, file_path)

    def select_output_folder(self):
        folder_path = filedialog.askdirectory()
        self.entry_output_folder.delete(0, tk.END)
        self.entry_output_folder.insert(0, folder_path)

    def split_pdf_into_pages(self):
        pdf_path = self.entry_pdf.get()
        output_folder = self.entry_output_folder.get()
        doc = fitz.open(pdf_path)
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)  # Load the current page
            doc_new = fitz.open()  # Create a new PDF
            doc_new.insert_pdf(doc, from_page=page_num, to_page=page_num)  # Insert the current page into the new PDF
            output_file = f"{output_folder}/page_{page_num + 1}.pdf"
            doc_new.save(output_file)  # Save the new PDF
            doc_new.close()
        doc.close()
        messagebox.showinfo("Success", "PDF split into pages successfully.")

    def add_mp4_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("MP4 Files", "*.mp4")])
        if file_path:
            self.listbox_videos.insert(tk.END, file_path)

    def merge_videos(self):
        video_paths = [self.listbox_videos.get(idx) for idx in range(self.listbox_videos.size())]
        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4 Files", "*.mp4")])
        if output_path:
            with open("filelist.txt", "w") as filelist:
                for path in video_paths:
                    filelist.write(f"file '{path}'\n")
            subprocess.run(["ffmpeg", "-f", "concat", "-safe", "0", "-i", "filelist.txt", "-c", "copy", output_path])
            messagebox.showinfo("Success", "MP4 files merged successfully.")

if __name__ == "__main__":
    root = tk.Tk()
    app = PDFSplitAndMergeVideosApp(root)
    root.mainloop()
