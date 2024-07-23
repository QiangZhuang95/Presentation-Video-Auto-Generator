import fitz  # PyMuPDF
import base64
import requests
import subprocess
import tkinter as tk
from tkinter import filedialog, scrolledtext
import openai

# 初始化全局变量
text_edit = None
label_status = None
entry_api = None
entry_output = None

# 分析图像
def analyze_image(api_key, image_base64, instruction_text, max_tokens):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": instruction_text  # 使用用户输入的指令文本
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": max_tokens  # 使用用户定义的max_tokens值
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    return response.json()


# 文本转语音
def text_to_speech(api_key, text, speech_file_path):
    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="echo",
        input=text
    )
    with open(speech_file_path, "wb") as file:
        file.write(response.content)

# 从图像和音频创建视频
def create_video_from_image_and_audio(image_path, audio_path, output_path):
    command = [
        'ffmpeg',
        '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]
    subprocess.run(command)

# 编码图像为Base64
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# 处理PDF转视频的主要流程
def process_pdf_to_video(pdf_path, output_folder, api_key):
    global text_edit, label_status
    global entry_instruction, entry_max_tokens

    # 在函数开头添加这两行，以从输入框获取用户输入的值
    instruction_text = entry_instruction.get()
    max_tokens = int(entry_max_tokens.get())  # 将字符串转换为整数

    num_pages = convert_pdf_to_images(pdf_path, output_folder)

    if num_pages > 0:
        for page_num in range(1, num_pages + 1):
            image_path = f"{output_folder}/page_{page_num}.png"
            base64_image = encode_image(image_path)
            # 在这里传递 instruction_text 和 max_tokens 给 analyze_image 函数
            analysis_result = analyze_image(api_key, base64_image, instruction_text, max_tokens)
            analysis_text = analysis_result['choices'][0]['message']['content']

            # 将结果保存至文本文件
            with open(f"{output_folder}/analysis_result.txt", "a") as file:
                file.write(f"Page {page_num}:\n{analysis_text}\n\n")

            # 假设你想将第一页的分析结果显示在text_edit中
            if page_num == 1:
                text_edit.delete(1.0, tk.END)
                text_edit.insert(tk.END, analysis_text)

        label_status.config(text="Analysis complete. Edit and confirm.")
    else:
        label_status.config(text="No pages to process.")


# PDF转图像
def convert_pdf_to_images(pdf_file, output_folder):
    doc = fitz.open(pdf_file)
    num_pages = len(doc)
    for page_num in range(num_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        output_file = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_file)
    doc.close()
    return num_pages

# GUI运行
def run_gui():
    global text_edit, label_status, entry_api, entry_output,instruction_text,max_tokens
    # 在 run_gui 函数顶部声明全局变量
    global entry_instruction, entry_max_tokens

    root = tk.Tk()
    root.title("PDF to Video Converter")

    # 创建GUI组件
    label_pdf = tk.Label(root, text="Select PDF File:")
    label_pdf.pack()
    entry_pdf = tk.Entry(root, width=50)
    entry_pdf.pack()
    button_pdf = tk.Button(root, text="Browse", command=lambda: select_file(entry_pdf, [('PDF Files', '*.pdf')]))
    button_pdf.pack()

    label_output = tk.Label(root, text="Select Output Folder:")
    label_output.pack()
    entry_output = tk.Entry(root, width=50)
    entry_output.pack()
    button_output = tk.Button(root, text="Browse", command=lambda: select_folder(entry_output))
    button_output.pack()

    label_api = tk.Label(root, text="Enter OpenAI API Key:")
    label_api.pack()
    entry_api = tk.Entry(root, width=50, show="*")
    entry_api.pack()

    text_edit = scrolledtext.ScrolledText(root, height=10, width=50)
    text_edit.pack()

    button_confirm_edit = tk.Button(root, text="Confirm Edit & Convert to Speech", command=lambda: confirm_edit_and_convert_to_speech(entry_api.get(), text_edit.get(1.0, tk.END).strip(), entry_output.get()))
    button_confirm_edit.pack()

    button_start = tk.Button(root, text="Start Process", command=lambda: process_pdf_to_video(entry_pdf.get(), entry_output.get(), entry_api.get()))
    button_start.pack()

    label_status = tk.Label(root, text="")
    label_status.pack()
    # 在run_gui函数中添加以下组件和逻辑
    label_image = tk.Label(root, text="Select Image File:")
    label_image.pack()
    entry_image = tk.Entry(root, width=50)
    entry_image.pack()
    button_image = tk.Button(root, text="Browse",
                             command=lambda: select_file(entry_image, [('Image Files', '*.png')]))
    button_image.pack()

    label_audio = tk.Label(root, text="Select Audio File:")
    label_audio.pack()
    entry_audio = tk.Entry(root, width=50)
    entry_audio.pack()
    button_audio = tk.Button(root, text="Browse", command=lambda: select_file(entry_audio, [('Audio Files', '*.mp3')]))
    button_audio.pack()

    button_create_video = tk.Button(root, text="Create Video from Image and Audio",
                                    command=lambda: create_video_from_image_and_audio(entry_image.get(),
                                                                                      entry_audio.get(),
                                                                                      f"{entry_output.get()}/output_video.mp4"))
    button_create_video.pack()
    # 创建指令文本的标签和输入框
    label_instruction = tk.Label(root, text="Instruction Text:")
    label_instruction.pack()
    entry_instruction = tk.Entry(root, width=50)
    entry_instruction.pack()
    # 设置默认文本
    entry_instruction.insert(0,
                             "Read the content in the picture and you, as the speaker, give a speech of conclusion within 1 min.")

    # 创建 max_tokens 的标签和输入框
    label_max_tokens = tk.Label(root, text="Max Tokens:")
    label_max_tokens.pack()
    entry_max_tokens = tk.Entry(root, width=50)
    entry_max_tokens.pack()
    # 设置默认值
    entry_max_tokens.insert(0, "300")

    root.mainloop()

def create_video_from_image_and_audio(image_path, audio_path, output_path):
    command = [
        'ffmpeg',
        '-loop', '1',
        '-i', image_path,
        '-i', audio_path,
        '-c:v', 'libx264',
        '-tune', 'stillimage',
        '-c:a', 'aac',
        '-b:a', '192k',
        '-vf', 'scale=1920:1080',
        '-pix_fmt', 'yuv420p',
        '-shortest',
        output_path
    ]
    subprocess.run(command)

# GUI辅助函数
def select_file(entry_widget, filetypes):
    file_path = filedialog.askopenfilename(filetypes=filetypes)
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, file_path)

def select_folder(entry_widget):
    folder_path = filedialog.askdirectory()
    entry_widget.delete(0, tk.END)
    entry_widget.insert(0, folder_path)

def confirm_edit_and_convert_to_speech(api_key, edited_text, output_folder):
    global label_status
    if edited_text:
        speech_file_path = f"{output_folder}/speech.mp3"
        text_to_speech(api_key, edited_text, speech_file_path)
        label_status.config(text="Speech converted to MP3 and saved.")
    else:
        label_status.config(text="No text to convert to speech.")

if __name__ == "__main__":
    run_gui()
