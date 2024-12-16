import time
import torch
from transformers import AutoModel, AutoTokenizer
from huggingface_hub import InferenceClient
import chromadb
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import subprocess
import re
from serial.tools.list_ports import comports
from platform import system
import threading
from PIL import Image, ImageTk
import cv2
from groq import Groq
from tkinter import messagebox
import os
import tkinter as tk
from tkinter import ttk
import atexit
client = None
client12 = None
collection = None
embedding_model = None
tokenizer = None
documents = None
context_chunks= None
def IntegratedApi(a,b):
    APIKEY1 = a
    APIKEY2 = b
    global client,client12,collection,embedding_model,tokenizer, documents,context_chunks
    client = InferenceClient(api_key=APIKEY2,headers={"X-use-cache": "false"})
    client12= Groq(api_key=APIKEY1)
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name="my_collection")
    embedding_model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    documents = load_documents()
    context_chunks = split_documents(documents)
    add_documents_to_chroma(context_chunks) 
def USB_Port():
	ports = list(comports())
	usb_names = {
		"Windows": ["USB Serial Port"],
		"Linux": ["/dev/ttyUSB"],
		"Darwin": [
			"/dev/tty.usbserial",
			"/dev/tty.usbmodem",
			"/dev/tty.SLAB_USBtoUART",
			"/dev/tty.wchusbserial",
			"/dev/cu.usbserial",
		]
	}
	
	os_name = system()
	if ports:
		for port, desc, hwid in sorted(ports):
			if any(name in port or name in desc for name in usb_names.get(os_name, [])):
				print("bağlandı")
				return port
	return None


def load_documents():
    all_documents = []
    folder_path = "data"  
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        
        if os.path.isfile(file_path) and file_path.endswith(".txt"): 
            with open(file_path, 'r') as f:
                all_documents.append(Document(page_content=f.read()))
    
    return all_documents


def split_documents(documents):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=300, length_function=len, add_start_index=True)
    return text_splitter.split_documents(documents)
def get_embeddings(texts):
    inputs = tokenizer(texts, return_tensors='pt', padding=True, truncation=True)
    with torch.no_grad():
        embeddings = embedding_model(**inputs).last_hidden_state.mean(dim=1).numpy()
    return embeddings

def add_documents_to_chroma(chunks):
    for chunk in chunks:
        vector = get_embeddings([chunk.page_content])[0]
        collection.upsert(documents=[chunk.page_content], embeddings=[vector], ids=[str(hash(chunk.page_content))])

def query_chroma_db(query):
    query_embedding = get_embeddings([query])[0]
    results = collection.query(query_embeddings=[query_embedding], n_results=4)
    return results

def get_groq_response(prompt):
    usb_port = USB_Port()
    context = ""
    query_results = query_chroma_db(prompt)
    for result in query_results['documents'][0]:
        if isinstance(result, str):
            context += result + "\n"
    
    if len(context) == 0:
        return "No context found. Ask another question for more details."

    full_prompt = f"{context}\nQuestion: {prompt}\n"
    response = client12.chat.completions.create(
       model="llama-3.3-70b-versatile",
       messages=[
            {"role": "user", "content": full_prompt},
            {"role": "system", "content":
                "Answer only in the language used in the question.\n"
                "Rely solely on the ACROME SMD Python library documentation.\n\n"
                "Instructions:\n"
                "- Include code in a well-formatted code block.\n"
                "- Use the ACROME SMD library exclusively with correct syntax and dependencies.\n"
                "- Ensure proper module names (e.g., `smd-red`) and precise function parameters.\n"
                "- Ensure use Master.attach(Red(Smd_Id))\n"
                f"- The MASTER_PORT variable must use the value of {usb_port}.\n"
                "- Do not use USB_serial_port\n"
                "- For example you use velocity,Please follow the documentation"
                "Key Details:\n"
                "- For `get_joystick`, specify both SMD ID (first parameter) and Joystick Module ID (second parameter).\n"
                "- For motor RPM is 100 and CPR= 64\n"
                "Joystick Info:\n"
                "- Joystick has 3 variable= X-axis,Y-axis and button"
                "- X-axis: max 100, min -100; Y-axis: max 100, min -100.\n"
                "- Movement: Negative X = right, Positive X = left. Positive Y = down, Negative Y = up.\n"
                "- Dead Zones:\n"
                "   - X-axis: No movement detected if between -20 and +20.\n"
                "   - Y-axis: No movement detected if between -10 and +10.\n"
                "   - Movement is only recognized when outside these ranges.\n"
                "IDs:\n"
                "- Joystick_ID = 1 or 5\n"
                "- Buzzer_ID = 1\n"
                "- Distance_ID = 1\n"
                "- RGB_ID = 1\n"
                "- smd_ID=0\n"
                "- servo_id=1"
            }],
        temperature=0.70
    )
    content = response.choices[0].message.content
    return content
def get_hugging_response(prompt):     
    usb_port = USB_Port()
    context = ""
    query_results = query_chroma_db(prompt)  
    
    # Extract text from the query results
    for result in query_results['documents'][0]:
        if isinstance(result, str):
            context += result + "\n"
    
    # If no context is found, return a default message
    if len(context) == 0:
        return "No context found. Ask another question for more details."
    
    # Prepare the full prompt to be used in the model
    full_prompt = f"{context}\nQuestion: {prompt}\n"
    
    # Send the prompt to the model for a response
    response = client.chat.completions.create(
        model="Qwen/Qwen2.5-Coder-32B-Instruct",  # Model name
        messages = [
            {"role": "user", "content": full_prompt},  # User message
            {"role": "system", "content": f"""
Please provide Python code **ONLY** using the ACROME SMD Python library.
Make sure to use **only the functions** as defined in the ACROME SMD documentation.

### Key Instructions:
1. The **first parameter** should always be the `smd_id` (integer identifier for the device).
2. The **second parameter** should always be the `module_id` (e.g., joystick, distance, rgb, etc.).

Example usage for **get_joystick** function:
- `master.get_joystick(smd_id, joystick_id)` where `smd_id` is the first parameter (e.g., `0`), and `joystick_id` is the second parameter (e.g., `5`).

3. **Use the correct USB_PORT**: {usb_port}
4. **Avoid using USB_serial_port**.
5. **Import all smd.red modules**.
6. **Do not forget to use master.attach()!!! master.attach(Red(smd_id))**
7. **If you use other modules or libraries, Don't forget to integrate**.
8. **Use the functions carefully! For example: 
    - The `get_distance` function does not return a tuple. It should be called to get the distance value, returning int.
    - Similarly, other functions have specific input and output behaviors. Always refer to the documentation for the expected usage.**
    - Note: Don't make up functions as your wish. Follow the syntax in the documentation.
9. **If you use motor, do not forget to use Operation Mode.**
10. ** Do not use set_variables and set_user_indicator functions because you do not know how you use! Also, you do not use Index. because you cannot.**
11. ** Don't make up functions as you wish. Functions are important in documentation. Follow the functions in SMD.**
12. ** If you use another libraries, please import them in python code.**
13. ** Avoid using functions or libraries that directly or indirectly print output to the console, such as os, print, tabulate, or similar.**
### Key IDs:
- joystick_id = 1
- buzzer_id = 1
- distance_id = 1
- rgb_id = 1
- smd_id = 0
- servo_id = 1

### Joystick Instructions:
- Joystick has 3 variables: X-axis, Y-axis, and button.
- **X-axis**: [-100, 100], **Y-axis**: [-100, 100].
- Joystick movement:
  - Negative X = right
  - Positive X = left
  - Positive Y = down
  - Negative Y = up.
- Dead zones:
  - **X-axis**: [-20, 20]
  - **Y-axis**: [-10, 10]

Please do **not invent new functions**, and **do not use any external libraries or unknown terms**. Stick strictly to the functions and parameters provided in the ACROME SMD library documentation.
"""
        }
    ],
    max_tokens=2000,
    top_p=0.95,
    temperature=0.35  # Lower temperature for deterministic responses
    )

    # Extract content from the model's response
    content = response.choices[0].message.content
    return content
process= None
def terminate_process():
    if process is not None:
        process.kill()
atexit.register(terminate_process)
def save_and_execute_python_code(code):
    global process
    try:
        with open('generated_script.py', 'w') as file:
            file.write(code)
        if process is not None:
            if process.poll() is None:
                process.kill()
            process = None
        process = subprocess.Popen(["pythonw", "generated_script.py"],stdout=subprocess.PIPE, stderr=subprocess.PIPE)  
        
        stdout, stderr = process.communicate(timeout=5)
        if stderr:
            return stderr

    except subprocess.TimeoutExpired:
        return 

def remove_code_blocks(response):
    clean_response = re.sub(r"```python.*?```", "", response, flags=re.DOTALL)
    return clean_response.strip()

def extract_python_code(response):
    python_code = re.findall(r'```python(.*?)```', response, flags=re.DOTALL)
    if python_code:
        return python_code[0].strip()
    else:
        return "No Python code found"

def log_error(message):
    with open("error_log.txt", "a") as log_file:
        log_file.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")
class ApiKeyWindow(tk.Toplevel):
    def __init__(self, root, callback):
        super().__init__(root)
        self.callback = callback
        self.title("API Keys")
        self.geometry("400x300")
        self.config(bg="#FFFFFF")

        # API Key Input Fields
        self.label1 = tk.Label(self, text="Enter Groq Cloud API Key:", font=("Arial", 14, "bold"), bg="#FFFFFF", fg="black")
        self.entry1 = tk.Entry(self, font=("Arial", 14), show="*", width=30, borderwidth=2, relief="solid")
        self.label2 = tk.Label(self, text="Enter Hugging Face API Key:", font=("Arial", 14, "bold"), bg="#FFFFFF", fg="black")
        self.entry2 = tk.Entry(self, font=("Arial", 14), show="*", width=30, borderwidth=2, relief="solid")
        self.submit_button = tk.Button(self, text="Submit", font=("Arial", 14, "bold"), bg="#298CCE", fg="white", command=self.submit_keys)

        # Pack Widgets
        self.label1.pack(pady=10)
        self.entry1.pack(pady=5)
        self.label2.pack(pady=10)
        self.entry2.pack(pady=5)
        self.submit_button.pack(pady=10)

    def submit_keys(self):
        groq_key = self.entry1.get().strip()
        hugging_key = self.entry2.get().strip()

        if groq_key and hugging_key:
            with open('api.txt', 'w') as file:
                file.write(f"{groq_key}\n{hugging_key}")
            
            # Thread başlatma
            threading.Thread(target=self.execute_api_in_thread, args=(groq_key, hugging_key)).start()
            self.destroy()
        else:
            messagebox.showerror("Error", "Enter key values please")

    def execute_api_in_thread(self, groq_key, hugging_key):
        IntegratedApi(groq_key, hugging_key)
        self.callback()
class AskQuestionThread(threading.Thread):

    def __init__(self, input_text, a, result_callback):
        super().__init__()
        self.input_text = input_text
        self.a = a
        self.result_callback = result_callback

    def run(self):
        try:
            start_time = time.time()
            
            if self.a == 1:
                response = get_groq_response(self.input_text)
                end_time = time.time()
                elapsed_time1 = end_time - start_time
                self.result_callback(response, elapsed_time1)  
                get_hugging_response
            elif self.a == 2:
                response = get_hugging_response(self.input_text)
                clean_answer = remove_code_blocks(response)
                python_answer = extract_python_code(response)
                end_time = time.time()
                elapsed_time2 = end_time - start_time
                execution_result = save_and_execute_python_code(python_answer)
                self.result_callback(clean_answer, elapsed_time2,execution_result)

        except Exception as e:
            error_message = f"An error occurred: {str(e)}"
            log_error(error_message)
            self.result_callback("An error occurred.", "Error")  # Error mesajını ilet


class AcromeApp:
    
    def __init__(self, root):
        self.root = root
        self.root.title("Acrome SMD Chatbot and Writer")
        self.root.geometry("1366x720")
        self.root.config(bg="#643838")
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")
        self.c=0
        self.change_camera_value=False
        # Tabs
        self.create_chatbot_tab()
        self.create_writer_and_chatbot_tab()

        self.camera_label = tk.Label(root)  # This will show the camera feed
        self.camera_label.pack(pady=10)
        self.cap = None
        self.camera_active= False
        self.current_image_id = None  # Initialize current_image_id here
        self.stop_timer = None
        # self.response_time_label1 = tk.Label(root, text="Response time: 0.00", font=("Arial", 14), bg="#643838", fg="black")
        # self.response_time_label1.place(relx=0.9, rely=0.10, anchor='ne')
    def create_chatbot_tab(self):
        self.chatbot_frame = tk.Frame(self.notebook,bg="#FFFFFF")
        self.notebook.add(self.chatbot_frame, text="Chatbot")
        self.question_label = tk.Label(self.chatbot_frame, text="Enter Your Question:", font=("Arial", 16, "bold"),bg="#FFFFFF")
        self.question_box = tk.Entry(self.chatbot_frame, font=("Arial", 14), width=40, borderwidth=2, relief="solid")
        self.ask_button = tk.Button(self.chatbot_frame,text="Ask",font=("Arial", 14, "bold"), bg="#298CCE", fg="white", command=self.ask_question1, relief="flat", bd=4, highlightthickness=0, padx=20, pady=10)
        self.response_box = tk.Text(self.chatbot_frame, font=("Courier New", 14), width=100, height=80,wrap="word",padx=10, pady=10, bd=2, relief="solid",bg="#FFFFFF",fg="black",border=0,state='disabled')
        
        
        # Layout
        self.question_label.pack(pady=10)
        self.question_box.pack(pady=5)
        self.ask_button.pack(pady=10)
        self.response_box.pack(pady=5)
    
            
            
    def create_writer_and_chatbot_tab(self):
        self.writer_and_chatbot_frame = tk.Frame(self.notebook, bg="#FFFFFF")
        self.notebook.add(self.writer_and_chatbot_frame, text="Education Kit Control")
        self.writer_command_label = tk.Label(self.writer_and_chatbot_frame, text="Enter Your Command:", font=("Arial", 16, "bold"),bg="#FFFFFF")
        self.writer_question_box = tk.Entry(self.writer_and_chatbot_frame, font=("Arial", 14), width=40, borderwidth=2, relief="solid")
        self.writer_command_button = tk.Button(self.writer_and_chatbot_frame, text="Command", font=("Arial", 14, "bold"), bg="#298CCE", fg="white", command=self.ask_question2, relief="flat", bd=4, highlightthickness=0, padx=20, pady=10)
        self.video_canvas = tk.Canvas(self.writer_and_chatbot_frame, width=640, height=480, bg="#FFFFFF",bd=0,highlightthickness=0)
        self.Response_time = tk.Label(self.writer_and_chatbot_frame,)
        self.response_time_label2 = tk.Label(self.writer_and_chatbot_frame, text="Response time: 0.00", font=("Arial", 14), bg="#FFFFFF", fg="black")
        self.response_time_label2.place(relx=0.9, rely=0.10, anchor='ne')

        self.change_camera_button = tk.Button(
        self.writer_and_chatbot_frame,
        text="Change the Camera",
        font=("Arial", 12, "bold"),
        bg="#00A8C2",
        fg="black",
        command=self.change_camera,  
        relief="flat",
        padx=10,
        pady=5
    )
        self.show_camera_button = tk.Button(
        self.writer_and_chatbot_frame,
        text="Show the camera",
        font=("Arial", 12, "bold"),
        bg="#00A8C2",
        fg="black",
        command=self.show_camera,  
        relief="flat",
        padx=10,
        pady=5
    )
        self.change_camera_button.place(x=10, y=10)
        self.show_camera_button.place(x=10,y=60)
        self.writer_command_label.pack(pady=10)
        self.writer_question_box.pack(pady=5)
        self.writer_command_button.pack(pady=10)
        self.video_canvas.pack(pady=20)
    def show_camera(self):
        self.stop_camera()
        if self.change_camera_value:
            self.start_camera2()
        else:
            self.start_camera1()
        if self.stop_timer is not None:
            self.root.after_cancel(self.stop_timer)
        self.stop_timer = self.root.after(10000, self.stop_camera)
    def change_camera(self):
        
        self.stop_camera()
        
        
        self.change_camera_value = not self.change_camera_value
        
        
        if self.change_camera_value:
            self.start_camera2()
        else:
            self.start_camera1()
        
        
        if self.stop_timer is not None:
            self.root.after_cancel(self.stop_timer)

        self.stop_timer = self.root.after(10000, self.stop_camera)
    def ask_question1(self):
        self.ask_button.config(bg="white", fg="black")
        input_text = self.question_box.get().strip()
        a = 1
        self.question_box.delete(0, tk.END)
        self.writer_question_box.delete(0, tk.END)
        self.thread1 = AskQuestionThread(input_text, a, self.update_response1)  
        self.thread1.start()

    def ask_question2(self):
        self.writer_command_button.config(bg="white", fg="black")
        self.change_camera_button.config(state="disabled")
        input_text = self.writer_question_box.get().strip()
        a = 2
        self.writer_question_box.delete(0, tk.END)
        self.question_box.delete(0, tk.END)
        self.root.after(0,self.reset_response_time)
        self.thread2 = AskQuestionThread(input_text, a, self.update_response2)  
        self.thread2.start()
        self.stop_camera()
        if self.change_camera_value==False:
            self.start_camera1()
        if self.change_camera_value==True:
            self.start_camera2()

        
        
        
        if self.stop_timer is not None:
            self.root.after_cancel(self.stop_timer)

        self.stop_timer = self.root.after(60000, self.stop_camera)

        
    def update_response1(self, response, elapsed_time):

        self.response_box.config(state=tk.NORMAL)
        self.response_box.delete(1.0, tk.END)
        self.response_box.insert(tk.END, response)
        self.response_box.config(state=tk.DISABLED)
        

        self.ask_button.config(bg="#298CCE", fg="white")

        # self.response_time_label1.config(text=f"Response time: {elapsed_time:.2f}s")
    def update_response2(self, response, elapsed_time, execution_result):
        self.root.after(0, self._update_response2, response, elapsed_time, execution_result)
    def _update_response2(self, response, elapsed_time,execution_result):
        self.writer_command_button.config(bg="#298CCE", fg="white")
        self.change_camera_button.config(state="normal")
        elapsed_time=elapsed_time+5
        self.response_time_label2.config(text=f"Response time: {elapsed_time:.2f}s")
        if execution_result is not None:
            messagebox.showerror("Error",execution_result)

    def reset_response_time(self):
        self.response_time_label2.config(text=f"Response time: 0.0s")
        
        
    def stop_camera(self):
        if self.cap is not None and self.cap.isOpened():  # Kamera geçerli mi ve açık mı?
            try:
                self.camera_active = False
                self.cap.release()  # Kamerayı serbest bırak
                cv2.destroyAllWindows()  # OpenCV pencerelerini kapat
                self.cap = None  # Kamera referansını sıfırla
            except cv2.error as e:
                print(f"Error releasing the camera: {e}")
            self.video_canvas.delete('all')
            self.current_image_id=None
        # if hasattr(self, "current_image_id") and self.current_image_id is not None:
        #     self.video_canvas.delete('all')
        #     self.current_image_id = None  


    def start_camera1(self):
        if self.cap is None:
            if system() == "Windows":
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            elif system() == "Linux":
                self.cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
            elif system() == "Darwin":
                self.cap = cv2.VideoCapture(0, cv2.CAP_FFMPEG)
            else:
                self.cap = cv2.VideoCapture(0)  # Varsayılan yol
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Camera  is not available or not connected.")
                self.change_camera_value = not self.change_camera_value
                self.cap = None
                return
            self.camera_active = True
            self.camera_thread = threading.Thread(target=self.update_camera, daemon=True)
            self.camera_thread.start()

    def start_camera2(self):
        if self.cap is None:
            if system() == "Windows":
                self.cap = cv2.VideoCapture(1, cv2.CAP_DSHOW)
            elif system() == "Linux":
                self.cap = cv2.VideoCapture(1, cv2.CAP_V4L2)
            elif system() == "Darwin":
                self.cap = cv2.VideoCapture(1, cv2.CAP_FFMPEG)
            else:
                self.cap = cv2.VideoCapture(1)  # Varsayılan yol
            if not self.cap.isOpened():
                messagebox.showerror("Error", "Camera is not available or not connected.")
                self.cap = None
                return
            self.camera_active = True
            self.camera_thread = threading.Thread(target=self.update_camera, daemon=True)
            self.camera_thread.start()

    def update_camera(self):
        while self.camera_active and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                img = ImageTk.PhotoImage(Image.fromarray(frame))

                # Canvas üzerinde güncelleme yapıyoruz
                if self.current_image_id:
                    self.video_canvas.itemconfig(self.current_image_id, image=img)
                else:
                    self.current_image_id = self.video_canvas.create_image(0, 0, anchor=tk.NW, image=img)

                self.video_canvas.image = img  
            self.root.update_idletasks()


def main():
    root = tk.Tk()
    root.withdraw() 
    def open_app():
        root.deiconify()  
        AcromeApp(root)
        root.mainloop()
    
    
    if os.path.exists('api.txt'):
        with open('api.txt', 'r') as file:
            api_keys = file.readlines()
            APIKEY1 = api_keys[0].strip()
            APIKEY2 = api_keys[1].strip()
            IntegratedApi(APIKEY1, APIKEY2)  
        open_app()  
    else:
        api_window = ApiKeyWindow(root, open_app)  
        root.mainloop()
        

if __name__ == "__main__":
    main()