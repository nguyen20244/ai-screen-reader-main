"""
GUI interface for the AI Screen Reader
"""
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import queue
import logging
from datetime import datetime
from typing import Optional, List
from config import config
from question_detector import Question
from ai_integration import AIResponse
import pyttsx3

class ScreenReaderGUI:
    """Main GUI application for the AI Screen Reader"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # TTS engine
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty('rate', 150)
        self.tts_engine.setProperty('volume', 1.0)
        self._tts_lock = threading.Lock()
        
        # Initialize main window
        self.root = tk.Tk()
        self.root.title("AI Screen Reader")
        self.root.geometry(f"{config.window_width}x{config.window_height}")
        
        # Application state
        self.is_running = False
        self.current_text = ""
        self.current_questions = []
        self.current_responses = []
        
        # Create GUI components
        self.create_widgets()
        self._ui_queue = queue.Queue()
        self.root.after(100, self._pump_ui_queue)
        self.setup_logging_handler()
        
        # Configure styles
        self.setup_styles()
    
    def create_widgets(self):
        """Create and layout GUI widgets"""
        # Main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Control panel
        self.create_control_panel(main_frame)
        
        # Status panel
        self.create_status_panel(main_frame)
        
        # Content panels
        self.create_content_panels(main_frame)
        
        # Log panel
        self.create_log_panel(main_frame)
    
    def create_control_panel(self, parent):
        """Create control buttons and settings"""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="5")
        control_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop button
        self.start_button = ttk.Button(
            control_frame, 
            text="Start Reading", 
            command=self.toggle_reading,
            style="Accent.TButton"
        )
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Settings
        ttk.Label(control_frame, text="Interval (seconds):").grid(row=0, column=1, padx=(0, 5))
        self.interval_var = tk.StringVar(value=str(config.refresh_interval))
        interval_spin = ttk.Spinbox(
            control_frame, 
            from_=5, 
            to=300, 
            width=10, 
            textvariable=self.interval_var
        )
        interval_spin.grid(row=0, column=2, padx=(0, 10))
        
        # AI Provider selection
        ttk.Label(control_frame, text="AI Provider:").grid(row=0, column=3, padx=(0, 5))
        self.provider_var = tk.StringVar(value=config.default_ai_provider)
        provider_combo = ttk.Combobox(
            control_frame,
            textvariable=self.provider_var,
            values=['claude', 'openai', 'gemini'],
            state="readonly",
            width=10
        )
        provider_combo.grid(row=0, column=4, padx=(0, 10))
        
        # Settings button
        settings_button = ttk.Button(
            control_frame, 
            text="Settings", 
            command=self.open_settings
        )
        settings_button.grid(row=0, column=5, padx=(0, 10))

        # TTS toggle checkbox
        self.tts_var = tk.BooleanVar(value=True)
        tts_check = ttk.Checkbutton(
            control_frame,
            text="🔊 Đọc kết quả",
            variable=self.tts_var
        )
        tts_check.grid(row=0, column=6, padx=(0, 10))

        # TTS speed control
        ttk.Label(control_frame, text="Tốc độ:").grid(row=0, column=7, padx=(0, 5))
        self.tts_rate_var = tk.IntVar(value=150)
        tts_rate_spin = ttk.Spinbox(
            control_frame,
            from_=80,
            to=300,
            width=6,
            textvariable=self.tts_rate_var,
            command=self.update_tts_rate
        )
        tts_rate_spin.grid(row=0, column=8, padx=(0, 5))

        # Stop speech button
        stop_tts_button = ttk.Button(
            control_frame,
            text="⏹ Dừng đọc",
            command=self.stop_speaking
        )
        stop_tts_button.grid(row=0, column=9)
    
    def create_status_panel(self, parent):
        """Create status information panel"""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Status labels
        self.status_label = ttk.Label(status_frame, text="Status: Stopped", foreground="red")
        self.status_label.grid(row=0, column=0, padx=(0, 20))
        
        self.last_scan_label = ttk.Label(status_frame, text="Last scan: Never")
        self.last_scan_label.grid(row=0, column=1, padx=(0, 20))
        
        self.questions_label = ttk.Label(status_frame, text="Questions found: 0")
        self.questions_label.grid(row=0, column=2)
    
    def create_content_panels(self, parent):
        """Create content display panels"""
        # Create notebook for tabs
        notebook = ttk.Notebook(parent)
        notebook.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Extracted text tab
        text_frame = ttk.Frame(notebook)
        notebook.add(text_frame, text="Extracted Text")
        
        self.text_display = scrolledtext.ScrolledText(
            text_frame, 
            wrap=tk.WORD, 
            font=("Consolas", config.font_size),
            state=tk.DISABLED
        )
        self.text_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Questions tab
        questions_frame = ttk.Frame(notebook)
        notebook.add(questions_frame, text="Detected Questions")
        
        self.questions_display = scrolledtext.ScrolledText(
            questions_frame, 
            wrap=tk.WORD, 
            font=("Arial", config.font_size),
            state=tk.DISABLED
        )
        self.questions_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Answers tab
        answers_frame = ttk.Frame(notebook)
        notebook.add(answers_frame, text="AI Answers")

        # Nút đọc lại trong tab Answers
        btn_frame = ttk.Frame(answers_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        ttk.Button(
            btn_frame,
            text="🔊 Đọc lại kết quả",
            command=self.replay_answers
        ).pack(side=tk.LEFT)
        
        self.answers_display = scrolledtext.ScrolledText(
            answers_frame, 
            wrap=tk.WORD, 
            font=("Arial", config.font_size),
            state=tk.DISABLED
        )
        self.answers_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_log_panel(self, parent):
        """Create log display panel"""
        log_frame = ttk.LabelFrame(parent, text="Log", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.rowconfigure(0, weight=1)
        log_frame.columnconfigure(0, weight=1)
        
        self.log_display = scrolledtext.ScrolledText(
            log_frame, 
            height=8, 
            wrap=tk.WORD, 
            font=("Consolas", 8),
            state=tk.DISABLED
        )
        self.log_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def setup_styles(self):
        """Setup custom styles"""
        style = ttk.Style()
        style.configure("Accent.TButton", foreground="white")
    
    def setup_logging_handler(self):
        """Setup logging to display in GUI"""
        class GUILogHandler(logging.Handler):
            def __init__(self, text_widget):
                super().__init__()
                self.text_widget = text_widget
            
            def emit(self, record):
                msg = self.format(record)
                def append():
                    self.text_widget.config(state=tk.NORMAL)
                    self.text_widget.insert(tk.END, msg + '\n')
                    self.text_widget.see(tk.END)
                    self.text_widget.config(state=tk.DISABLED)
                self.text_widget.after(0, append)
        
        # Add GUI handler to root logger
        gui_handler = GUILogHandler(self.log_display)
        gui_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(gui_handler)
    
    # ------------------------------------------------------------------ #
    #  TTS helpers                                                         #
    # ------------------------------------------------------------------ #

    def speak(self, text: str):
        """Đọc text thành tiếng trong thread riêng để không block GUI"""
        if not self.tts_var.get():
            return
        def _run():
            with self._tts_lock:
                self.tts_engine.say(text)
                self.tts_engine.runAndWait()
        threading.Thread(target=_run, daemon=True).start()

    def stop_speaking(self):
        """Dừng đọc ngay lập tức"""
        try:
            self.tts_engine.stop()
        except Exception:
            pass

    def update_tts_rate(self):
        """Cập nhật tốc độ đọc theo spinbox"""
        try:
            self.tts_engine.setProperty('rate', self.tts_rate_var.get())
        except Exception:
            pass

    def replay_answers(self):
        """Đọc lại kết quả đang hiển thị"""
        if self.current_responses:
            answers = [r.answer for r in self.current_responses if r.answer and not r.error]
            if answers:
                self.speak(" ".join(answers))

    # ------------------------------------------------------------------ #

    def toggle_reading(self):
        """Toggle the screen reading process"""
        if self.is_running:
            self.stop_reading()
        else:
            self.start_reading()
    
    def start_reading(self):
        """Start the screen reading process"""
        self.is_running = True
        self.start_button.config(text="Stop Reading", style="")
        self.status_label.config(text="Status: Running", foreground="green")
        
        # Update config with current settings
        try:
            config.refresh_interval = int(self.interval_var.get())
        except ValueError:
            pass  # keep previous value
        config.default_ai_provider = self.provider_var.get()
        
        self.logger.info("Screen reading started")
        
        # Start reading in separate thread
        self.reading_loop()  # engine runs in its own worker thread
    
    def stop_reading(self):
        """Stop the screen reading process"""
        self.is_running = False
        self.start_button.config(text="Start Reading", style="Accent.TButton")
        self.status_label.config(text="Status: Stopped", foreground="red")
        self.logger.info("Screen reading stopped")
    
    def reading_loop(self):
        """Main reading loop (runs in separate thread)"""
        # This will be implemented in the automation engine
        pass
    
    def post_ui(self, fn, *args):
        """Thread-safe: may be called from any thread; fn runs later on the Tk main thread."""
        self._ui_queue.put((fn, args))

    def _pump_ui_queue(self):
        """Runs on the Tk main thread every 100 ms and applies queued UI updates."""
        try:
            while True:
                fn, args = self._ui_queue.get_nowait()
                try:
                    fn(*args)
                except Exception as e:
                    self.logger.error(f"UI update failed: {e}")
        except queue.Empty:
            pass
        self.root.after(100, self._pump_ui_queue)

    def update_text_display(self, text: str):
        """Update the extracted text display"""
        self.text_display.config(state=tk.NORMAL)
        self.text_display.delete(1.0, tk.END)
        self.text_display.insert(1.0, text)
        self.text_display.config(state=tk.DISABLED)
        self.current_text = text
    
    def update_questions_display(self, questions: List[Question]):
        """Update the questions display"""
        self.questions_display.config(state=tk.NORMAL)
        self.questions_display.delete(1.0, tk.END)
        
        for i, question in enumerate(questions, 1):
            self.questions_display.insert(tk.END, f"Question {i} ({question.question_type}):\n")
            self.questions_display.insert(tk.END, f"{question.text}\n")
            
            if question.options:
                self.questions_display.insert(tk.END, "Options:\n")
                for j, option in enumerate(question.options):
                    letter = chr(65 + j)
                    self.questions_display.insert(tk.END, f"  {letter}) {option}\n")
            
            self.questions_display.insert(tk.END, f"Confidence: {question.confidence:.2f}\n")
            self.questions_display.insert(tk.END, "-" * 50 + "\n\n")
        
        self.questions_display.config(state=tk.DISABLED)
        self.current_questions = questions
        
        # Update status
        self.questions_label.config(text=f"Questions found: {len(questions)}")
    
    def update_answers_display(self, responses: List[AIResponse]):
        """Update the answers display and read aloud via TTS"""
        self.answers_display.config(state=tk.NORMAL)
        self.answers_display.delete(1.0, tk.END)
        
        all_answers = []

        for i, response in enumerate(responses, 1):
            self.answers_display.insert(tk.END, f"Answer {i} ({response.provider}):\n")
            self.answers_display.insert(tk.END, f"{response.answer}\n")
            
            if response.processing_time > 0:
                self.answers_display.insert(tk.END, f"Processing time: {response.processing_time:.2f}s\n")
            
            if response.error:
                self.answers_display.insert(tk.END, f"Error: {response.error}\n")
            
            self.answers_display.insert(tk.END, "-" * 50 + "\n\n")

            if response.answer and not response.error:
                all_answers.append(response.answer)
        
        self.answers_display.config(state=tk.DISABLED)
        self.current_responses = responses

        # Đọc kết quả thành tiếng
        if all_answers:
            self.speak(" ".join(all_answers))
    
    def update_last_scan(self):
        """Update the last scan timestamp"""
        now = datetime.now().strftime("%H:%M:%S")
        self.last_scan_label.config(text=f"Last scan: {now}")
    
    def open_settings(self):
        """Open settings dialog"""
        messagebox.showinfo("Settings", "Settings dialog not implemented yet")
    
    def run(self):
        """Start the GUI application"""
        self.logger.info("Starting AI Screen Reader GUI")
        self.root.mainloop()
