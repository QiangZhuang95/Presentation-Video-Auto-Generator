import fitz
import base64
import requests
from pathlib import Path
import openai
import subprocess
import tkinter as tk
from tkinter import filedialog

def run_gui(process_function):
    root = tk.Tk()
    root.title("PDF to Video Converter")

    def select_pdf():
        file_path = filedialog.askopenfilename(filetypes=[("PDF Files", "*.pdf")])
        entry_pdf.delete(0, tk.END)
        entry_pdf.insert(0, file_path)

    def select_output_folder():
        folder_path = filedialog.askdirectory()
        entry_output.delete(0, tk.END)
        entry_output.insert(0, folder_path)

    def start_process():
        pdf_path = entry_pdf.get()
        output_folder = entry_output.get()
        api_key = entry_api.get()
        process_function(pdf_path, output_folder, api_key)  # 现在传递API密钥
        label_status.config(text="Processing Complete")
        # API密钥输入框

    label_api = tk.Label(root, text="Enter OpenAI API Key:")
    label_api.pack()
    entry_api = tk.Entry(root, width=50, show="*")  # 星号表示隐藏文本
    entry_api.pack()

    label_pdf = tk.Label(root, text="Select PDF File:")
    label_pdf.pack()
    entry_pdf = tk.Entry(root, width=50)
    entry_pdf.pack()
    button_pdf = tk.Button(root, text="Browse", command=select_pdf)
    button_pdf.pack()

    label_output = tk.Label(root, text="Select Output Folder:")
    label_output.pack()
    entry_output = tk.Entry(root, width=50)
    entry_output.pack()
    button_output = tk.Button(root, text="Browse", command=select_output_folder)
    button_output.pack()

    button_start = tk.Button(root, text="Start Process", command=start_process)
    button_start.pack()

    label_status = tk.Label(root, text="")
    label_status.pack()

    root.mainloop()

# 使用示例

# PDF转图片
def convert_pdf_to_images(pdf_file, output_folder):
    doc = fitz.open(pdf_file)
    num_pages = len(doc)  # 获取总页数
    for page_num in range(num_pages):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        output_file = f"{output_folder}/page_{page_num + 1}.png"
        pix.save(output_file)
    doc.close()
    return num_pages  # 返回总页数

# 编码图片
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

# OpenAI GPT-Vision API分析图片
def analyze_image(api_key, image_base64):
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
                        #"text": "What’s in this image?"
                        "text": "Read the content in the picture and you, as the speaker, give a speech of conclusion within 1 min."
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
        "max_tokens": 300
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    print(response.json())
    return response.json()

# ChatGPT TTS API
def text_to_speech(api_key, text, speech_file_path):
    client = openai.OpenAI(api_key=api_key)
    response = client.audio.speech.create(
        model="tts-1",
        voice="shimmer",
        input=text
    )
    response.stream_to_file(speech_file_path)

# 合并图片和音频为视频
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

# 主函数
def main(pdf_path, output_folder, api_key):
    num_pages = convert_pdf_to_images(pdf_path, output_folder)  # 获取总页数

    for page_num in range(num_pages):
        image_path = f"{output_folder}/page_{page_num + 1}.png"
        base64_image = encode_image(image_path)
        analysis_result = analyze_image(api_key, base64_image)
        analysis_text = analysis_result['choices'][0]['message']['content']  # 获取分析文本

        speech_file_path = f"{output_folder}/speech_{page_num + 1}.mp3"
        text_to_speech(api_key, analysis_text, speech_file_path)

        output_video_path = f"{output_folder}/output_{page_num + 1}.mp4"
        create_video_from_image_and_audio(image_path, speech_file_path, output_video_path)

if __name__ == "__main__":
    run_gui(main)