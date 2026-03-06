import tkinter as tk
from tkinter import filedialog, messagebox, ttk, colorchooser
from tkinter import LEFT, RIGHT, TOP, BOTTOM, BOTH, X, Y, W, E, N, S, NW
from PIL import Image, ImageTk, ImageDraw, ImageOps
import os
import json
import ctypes
from datetime import datetime

class MotionQuill:
    def __init__(self, root):
        self.root = root
        self.root.title("MotionQuill - Pixel Animation Studio")
        self.root.geometry("1400x800")
        self.root.configure(bg='#2b2b2b')
        
        # Устанавливаем иконку для панели задач
        self.set_taskbar_icon()
        
        # Устанавливаем иконку для окна
        self.set_window_icon()
        
        # Загружаем иконки инструментов
        self.load_tool_icons()
        
        # Переменные для анимации
        self.frames = []
        self.current_frame_index = -1
        self.fps = 12
        self.frame_duration = 1000 // 12
        self.is_playing = False
        self.animation_after_id = None
        self.selected_tool = "pencil"
        self.show_previous_frame = False
        self.previous_opacity = 0.3
        self.current_file = None
        self.modified = False
        self.show_grid = False
        
        # Переменные для рисования
        self.pixel_size = 10
        self.last_x = None
        self.last_y = None
        self.drawing = False
        self.clipboard = None
        
        # Для фигур
        self.shape_start_x = None
        self.shape_start_y = None
        self.temp_shape_id = None
        
        # История
        self.history = []
        self.history_index = -1
        
        # Цветовая схема
        self.colors = {
            'bg': '#2b2b2b',
            'fg': '#ffffff',
            'accent': '#0078d4',
            'accent_light': '#2b88d8',
            'panel': '#333333',
            'panel_light': '#404040',
            'border': '#555555',
            'success': '#28a745',
            'warning': '#ffc107',
            'error': '#dc3545'
        }
        
        # Настройка UI
        self.setup_menu()
        self.setup_ui()
        
        # Добавляем первый пустой кадр
        self.add_frame()
        
        # Привязка горячих клавиш
        self.setup_hotkeys()
        
        # Переменные для отображения
        self.time_label = None
        self.duration_label = None
        
    def load_tool_icons(self):
        """Загрузка иконок для инструментов"""
        self.tool_icons = {}
        icon_size = (24, 24)  # Размер иконок
        
        tools = ['pencil', 'eraser', 'filling', 'pipette']
        
        for tool in tools:
            try:
                # Путь к иконке
                icon_path = os.path.join('resources', 'tools', f'{tool}.png')
                
                if os.path.exists(icon_path):
                    # Загружаем и изменяем размер
                    img = Image.open(icon_path)
                    img = img.resize(icon_size, Image.Resampling.LANCZOS)
                    
                    # Конвертируем в PhotoImage
                    photo = ImageTk.PhotoImage(img)
                    
                    # Сохраняем
                    self.tool_icons[tool] = photo
                    print(f"Иконка загружена: {tool}")
                else:
                    print(f"Иконка не найдена: {icon_path}")
                    self.tool_icons[tool] = None
                    
            except Exception as e:
                print(f"Ошибка загрузки иконки {tool}: {e}")
                self.tool_icons[tool] = None
                
    def set_taskbar_icon(self):
        """Установка иконки для панели задач Windows"""
        try:
            # Для Windows - устанавливаем иконку в панели задач
            if os.name == 'nt':
                # Путь к иконке
                icon_path = os.path.join('resources', 'icon', 'icon.png')
                if os.path.exists(icon_path):
                    # Конвертируем PNG в ICO на лету
                    img = Image.open(icon_path)
                    img = img.resize((64, 64), Image.Resampling.LANCZOS)
                    
                    # Сохраняем временный ICO файл
                    temp_ico = os.path.join(os.environ['TEMP'], 'motionquill_temp.ico')
                    img.save(temp_ico, format='ICO')
                    
                    # Устанавливаем иконку через ctypes
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('motionquill.app')
                    
                    # Загружаем иконку
                    self.root.iconbitmap(default=temp_ico)
                    
                    # Удаляем временный файл
                    try:
                        os.remove(temp_ico)
                    except:
                        pass
                    
                    print(f"Иконка для панели задач загружена")
        except Exception as e:
            print(f"Ошибка при установке иконки для панели задач: {e}")
        
    def set_window_icon(self):
        """Установка иконки для окна"""
        try:
            # Путь к иконке
            icon_path = os.path.join('resources', 'icon', 'icon.png')
            
            # Проверяем существует ли файл
            if os.path.exists(icon_path):
                # Загружаем иконку
                icon_image = Image.open(icon_path)
                icon_image = icon_image.resize((32, 32), Image.Resampling.LANCZOS)
                icon_photo = ImageTk.PhotoImage(icon_image)
                
                # Устанавливаем иконку для окна
                self.root.iconphoto(True, icon_photo)
                
                # Сохраняем ссылку чтобы не удалилась сборщиком мусора
                self.icon_photo = icon_photo
                
                print(f"Иконка окна загружена: {icon_path}")
            else:
                print(f"Иконка не найдена по пути: {icon_path}")
                
        except Exception as e:
            print(f"Ошибка при загрузке иконки окна: {e}")
            
    def setup_menu(self):
        """Создание главного меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню Файл
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel'], fg='white')
        menubar.add_cascade(label="Файл", menu=file_menu)
        
        file_menu.add_command(label="Новый проект", command=self.new_project, accelerator="Ctrl+N")
        file_menu.add_command(label="Открыть проект", command=self.load_project, accelerator="Ctrl+O")
        file_menu.add_command(label="Сохранить", command=self.save_project, accelerator="Ctrl+S")
        file_menu.add_command(label="Сохранить как...", command=self.save_project_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Импорт изображения", command=self.load_image, accelerator="Ctrl+I")
        file_menu.add_command(label="Экспорт в GIF", command=self.export_gif)
        file_menu.add_command(label="Экспорт в PNG", command=self.export_png_sequence)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit_app, accelerator="Alt+F4")
        
        # Меню Правка
        edit_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel'], fg='white')
        menubar.add_cascade(label="Правка", menu=edit_menu)
        
        edit_menu.add_command(label="Отменить", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Повторить", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Копировать кадр", command=self.copy_frame, accelerator="Ctrl+C")
        edit_menu.add_command(label="Вставить кадр", command=self.paste_frame, accelerator="Ctrl+V")
        edit_menu.add_command(label="Удалить кадр", command=self.delete_current_frame, accelerator="Del")
        
        # Меню Вид
        view_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel'], fg='white')
        menubar.add_cascade(label="Вид", menu=view_menu)
        
        view_menu.add_command(label="Показать сетку", command=self.toggle_grid, accelerator="Ctrl+G")
        view_menu.add_command(label="Показать предыдущий кадр", command=self.toggle_previous_frame, accelerator="Ctrl+P")
        
        # Меню Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel'], fg='white')
        menubar.add_cascade(label="Инструменты", menu=tools_menu)
        
        # Подменю размера пикселя
        pixel_menu = tk.Menu(tools_menu, tearoff=0, bg=self.colors['panel'], fg='white')
        tools_menu.add_cascade(label="Размер пикселя", menu=pixel_menu)
        for size in [1, 2, 5, 10, 20, 50]:
            pixel_menu.add_command(label=f"{size}px", command=lambda s=size: self.set_pixel_size(s))
        
        tools_menu.add_separator()
        tools_menu.add_command(label="Очистить кадр", command=self.clear_frame)
        tools_menu.add_command(label="Заливка", command=self.fill_frame)
        
        # Меню Анимация
        anim_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel'], fg='white')
        menubar.add_cascade(label="Анимация", menu=anim_menu)
        
        # Подменю FPS
        fps_menu = tk.Menu(anim_menu, tearoff=0, bg=self.colors['panel'], fg='white')
        anim_menu.add_cascade(label="Скорость (FPS)", menu=fps_menu)
        for fps in [8, 12, 15, 24, 30, 60]:
            fps_menu.add_command(label=f"{fps} FPS", command=lambda f=fps: self.set_fps(f))
        
        # Меню Справка
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['panel'], fg='white')
        menubar.add_cascade(label="Справка", menu=help_menu)
        
        help_menu.add_command(label="О программе", command=self.show_about)
        help_menu.add_command(label="Горячие клавиши", command=self.show_shortcuts)
        
    def setup_hotkeys(self):
        """Горячие клавиши"""
        self.root.bind('<Control-n>', lambda e: self.new_project())
        self.root.bind('<Control-o>', lambda e: self.load_project())
        self.root.bind('<Control-s>', lambda e: self.save_project())
        self.root.bind('<Control-Shift-S>', lambda e: self.save_project_as())
        self.root.bind('<Control-i>', lambda e: self.load_image())
        self.root.bind('<Control-g>', lambda e: self.toggle_grid())
        self.root.bind('<Control-p>', lambda e: self.toggle_previous_frame())
        self.root.bind('<Control-z>', lambda e: self.undo())
        self.root.bind('<Control-y>', lambda e: self.redo())
        self.root.bind('<Control-c>', lambda e: self.copy_frame())
        self.root.bind('<Control-v>', lambda e: self.paste_frame())
        self.root.bind('<Delete>', lambda e: self.delete_current_frame())
        self.root.bind('<space>', lambda e: self.toggle_playback())
        self.root.bind('<Left>', lambda e: self.prev_frame())
        self.root.bind('<Right>', lambda e: self.next_frame())
        
    def setup_ui(self):
        # Главный контейнер
        main_container = tk.Frame(self.root, bg=self.colors['bg'])
        main_container.pack(fill=BOTH, expand=True)
        
        # Верхняя панель инструментов
        self.setup_toolbar(main_container)
        
        # Основная рабочая область
        workspace = tk.Frame(main_container, bg=self.colors['bg'])
        workspace.pack(fill=BOTH, expand=True, pady=5)
        
        # Левая панель - инструменты
        self.setup_tools_panel(workspace)
        
        # Центральная область - холст
        self.setup_canvas_area(workspace)
        
        # Правая панель - кадры
        self.setup_frames_panel(workspace)
        
        # Нижняя панель - таймлайн
        self.setup_timeline(main_container)
        
        # Статус бар
        self.setup_statusbar(main_container)
        
    def setup_toolbar(self, parent):
        """Верхняя панель"""
        toolbar = tk.Frame(parent, bg=self.colors['panel'], height=50)
        toolbar.pack(fill=X, pady=(0, 5))
        toolbar.pack_propagate(False)
        
        buttons = [
            ('📄 Новый', self.new_project),
            ('📂 Открыть', self.load_project),
            ('💾 Сохранить', self.save_project),
            ('📷 Импорт', self.load_image),
        ]
        
        for text, command in buttons:
            btn = tk.Button(toolbar, text=text, command=command,
                          bg=self.colors['panel_light'],
                          fg='white',
                          relief=tk.FLAT,
                          padx=10,
                          pady=5,
                          font=('Arial', 10),
                          bd=0)
            btn.pack(side=LEFT, padx=2)
            
        # Разделитель
        sep = tk.Frame(toolbar, bg=self.colors['border'], width=2)
        sep.pack(side=LEFT, padx=10, fill=Y)
        
        # Кнопки воспроизведения
        self.play_btn = tk.Button(toolbar, text='▶', command=self.toggle_playback,
                                 bg=self.colors['panel_light'], fg='white',
                                 relief=tk.FLAT, padx=15, font=('Arial', 12), bd=0)
        self.play_btn.pack(side=LEFT, padx=2)
        
        self.stop_btn = tk.Button(toolbar, text='⏹', command=self.stop_playback,
                                 bg=self.colors['panel_light'], fg='white',
                                 relief=tk.FLAT, padx=15, font=('Arial', 12), bd=0)
        self.stop_btn.pack(side=LEFT, padx=2)
        
        # Метка режима
        self.mode_label = tk.Label(toolbar, text='✏️ Карандаш',
                                  bg=self.colors['panel'], fg=self.colors['accent'],
                                  font=('Arial', 10, 'bold'))
        self.mode_label.pack(side=LEFT, padx=20)
        
        # FPS
        fps_frame = tk.Frame(toolbar, bg=self.colors['panel'])
        fps_frame.pack(side=RIGHT, padx=10)
        
        tk.Label(fps_frame, text='FPS:', bg=self.colors['panel'],
                fg='white').pack(side=LEFT)
        
        self.fps_var = tk.StringVar(value='12')
        self.fps_entry = tk.Entry(fps_frame, textvariable=self.fps_var,
                                 width=4, bg=self.colors['panel_light'],
                                 fg='white', bd=0, justify='center')
        self.fps_entry.pack(side=LEFT, padx=2)
        self.fps_entry.bind('<Return>', self.update_fps)
        
    def setup_tools_panel(self, parent):
        """Панель инструментов с иконками"""
        tools_panel = tk.Frame(parent, bg=self.colors['panel'], width=200)
        tools_panel.pack(side=LEFT, fill=Y, padx=(0, 5))
        tools_panel.pack_propagate(False)
        
        # Заголовок
        tk.Label(tools_panel, text='ИНСТРУМЕНТЫ', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Основные инструменты с иконками
        tools = [
            ('pencil', '✏️ Карандаш'),
            ('eraser', '🧽 Ластик'),
            ('filling', '🪣 Заливка'),
            ('pipette', '👁 Пипетка'),
        ]
        
        self.tool_var = tk.StringVar(value='pencil')
        
        for tool_key, tool_name in tools:
            frame = tk.Frame(tools_panel, bg=self.colors['panel'])
            frame.pack(fill=X, pady=2, padx=5)
            
            # Создаем радиокнопку
            rb = tk.Radiobutton(frame, variable=self.tool_var, value=tool_key,
                               bg=self.colors['panel'],
                               fg='white',
                               selectcolor=self.colors['accent'],
                               font=('Arial', 10),
                               command=self.change_tool)
            rb.pack(side=LEFT)
            
            # Добавляем иконку если есть
            if tool_key in self.tool_icons and self.tool_icons[tool_key]:
                icon_label = tk.Label(frame, image=self.tool_icons[tool_key],
                                    bg=self.colors['panel'])
                icon_label.pack(side=LEFT, padx=5)
            
            # Добавляем текст
            tk.Label(frame, text=tool_name,
                    bg=self.colors['panel'],
                    fg='white').pack(side=LEFT)
        
        # Разделитель
        tk.Frame(tools_panel, bg=self.colors['border'], height=2).pack(fill=X, pady=10)
        
        # Фигуры
        tk.Label(tools_panel, text='ФИГУРЫ', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        shapes = [
            ('line', '📏 Линия'),
            ('rectangle', '⬜ Прямоугольник'),
            ('circle', '⚪ Круг'),
        ]
        
        for shape_key, shape_name in shapes:
            frame = tk.Frame(tools_panel, bg=self.colors['panel'])
            frame.pack(fill=X, pady=2, padx=5)
            
            rb = tk.Radiobutton(frame, variable=self.tool_var, value=shape_key,
                               bg=self.colors['panel'],
                               fg='white',
                               selectcolor=self.colors['accent'],
                               font=('Arial', 10),
                               command=self.change_tool)
            rb.pack(side=LEFT)
            
            tk.Label(frame, text=shape_name,
                    bg=self.colors['panel'],
                    fg='white').pack(side=LEFT, padx=25)
        
        # Разделитель
        tk.Frame(tools_panel, bg=self.colors['border'], height=2).pack(fill=X, pady=10)
        
        # Палитра
        tk.Label(tools_panel, text='ПАЛИТРА', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        palette_frame = tk.Frame(tools_panel, bg=self.colors['panel'])
        palette_frame.pack(pady=5)
        
        # Основные цвета
        colors = [
            '#000000', '#ffffff', '#ff0000', '#00ff00', '#0000ff',
            '#ffff00', '#ff00ff', '#00ffff', '#ff8800', '#8800ff',
        ]
        
        self.color_var = tk.StringVar(value='#000000')
        
        color_grid = tk.Frame(palette_frame, bg=self.colors['panel'])
        color_grid.pack()
        
        for i, color in enumerate(colors):
            row = i // 5
            col = i % 5
            btn = tk.Button(color_grid, bg=color, width=3, height=1,
                          command=lambda c=color: self.set_color(c),
                          relief=tk.RAISED, bd=1)
            btn.grid(row=row, column=col, padx=1, pady=1)
        
        # Предпросмотр цвета
        preview_frame = tk.Frame(palette_frame, bg=self.colors['panel'])
        preview_frame.pack(fill=X, pady=5)
        
        self.color_preview = tk.Label(preview_frame, bg='#000000',
                                     width=10, height=1, relief=tk.SUNKEN)
        self.color_preview.pack(side=LEFT, padx=2)
        
        tk.Button(preview_frame, text='Выбрать', command=self.choose_color,
                bg=self.colors['panel_light'], fg='white',
                relief=tk.FLAT, bd=0).pack(side=LEFT, expand=True, fill=X)
        
        # Размер
        tk.Label(tools_panel, text='РАЗМЕР', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 10, 'bold')).pack(pady=(10,5))
        
        size_frame = tk.Frame(tools_panel, bg=self.colors['panel'])
        size_frame.pack(fill=X, padx=10)
        
        self.size_var = tk.IntVar(value=10)
        size_slider = tk.Scale(size_frame, from_=1, to=50,
                              variable=self.size_var,
                              orient=tk.HORIZONTAL,
                              bg=self.colors['panel'],
                              fg='white',
                              highlightbackground=self.colors['panel'],
                              command=self.update_size)
        size_slider.pack(fill=X)
        
        self.size_label = tk.Label(size_frame, text='10px',
                                  bg=self.colors['panel'], fg='white')
        self.size_label.pack()
        
        # Настройки фигур
        tk.Frame(tools_panel, bg=self.colors['border'], height=2).pack(fill=X, pady=10)
        
        tk.Label(tools_panel, text='НАСТРОЙКИ', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        self.fill_var = tk.BooleanVar(value=False)
        tk.Checkbutton(tools_panel, text='Заливка',
                      variable=self.fill_var,
                      bg=self.colors['panel'],
                      fg='white',
                      selectcolor=self.colors['panel']).pack(anchor=W, padx=10)
        
        # Толщина
        outline_frame = tk.Frame(tools_panel, bg=self.colors['panel'])
        outline_frame.pack(fill=X, padx=10, pady=5)
        
        tk.Label(outline_frame, text='Толщина:',
                bg=self.colors['panel'], fg='white').pack(anchor=W)
        
        self.outline_var = tk.IntVar(value=2)
        tk.Spinbox(outline_frame, from_=1, to=20,
                  textvariable=self.outline_var,
                  width=10,
                  bg=self.colors['panel_light'],
                  fg='white',
                  bd=0).pack(anchor=W)
        
        # История
        tk.Frame(tools_panel, bg=self.colors['border'], height=2).pack(fill=X, pady=10)
        
        tk.Label(tools_panel, text='ИСТОРИЯ', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 10, 'bold')).pack(pady=5)
        
        history_frame = tk.Frame(tools_panel, bg=self.colors['panel'])
        history_frame.pack(fill=X, padx=10)
        
        tk.Button(history_frame, text='↩ Отменить',
                 command=self.undo,
                 bg=self.colors['panel_light'],
                 fg='white', bd=0, pady=5).pack(fill=X, pady=2)
        
        tk.Button(history_frame, text='↪ Повторить',
                 command=self.redo,
                 bg=self.colors['panel_light'],
                 fg='white', bd=0, pady=5).pack(fill=X, pady=2)
        
    def setup_canvas_area(self, parent):
        """Область холста"""
        canvas_frame = tk.Frame(parent, bg=self.colors['bg'])
        canvas_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        # Информационная панель
        info_frame = tk.Frame(canvas_frame, bg=self.colors['panel'])
        info_frame.pack(fill=X, pady=(0, 5))
        
        self.frame_info = tk.Label(info_frame, text='Кадр: 1/1',
                                  bg=self.colors['panel'],
                                  fg='white', font=('Arial', 10))
        self.frame_info.pack(side=LEFT, padx=10, pady=5)
        
        # Индикатор предыдущего кадра
        self.prev_frame_indicator = tk.Label(info_frame, text='👁',
                                            bg=self.colors['panel'],
                                            fg=self.colors['accent'],
                                            font=('Arial', 12))
        
        # Навигация
        nav_frame = tk.Frame(info_frame, bg=self.colors['panel'])
        nav_frame.pack(side=LEFT, padx=20)
        
        tk.Button(nav_frame, text='◀', command=self.prev_frame,
                 bg=self.colors['panel_light'], fg='white',
                 relief=tk.FLAT, bd=0, width=3).pack(side=LEFT, padx=2)
        tk.Button(nav_frame, text='▶', command=self.next_frame,
                 bg=self.colors['panel_light'], fg='white',
                 relief=tk.FLAT, bd=0, width=3).pack(side=LEFT, padx=2)
        
        # Координаты
        self.coord_label = tk.Label(info_frame, text='X: 0, Y: 0',
                                   bg=self.colors['panel'],
                                   fg='white')
        self.coord_label.pack(side=RIGHT, padx=10)
        
        # Холст
        canvas_container = tk.Frame(canvas_frame, bg=self.colors['panel'])
        canvas_container.pack(fill=BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_container, width=800, height=600,
                               bg='white', highlightthickness=1,
                               highlightbackground=self.colors['border'])
        self.canvas.pack(expand=True)
        
        # Сетка
        self.grid_items = []
        
        # События мыши
        self.canvas.bind("<B1-Motion>", self.paint)
        self.canvas.bind("<Button-1>", self.start_paint)
        self.canvas.bind("<ButtonRelease-1>", self.reset_paint)
        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-3>", self.pick_color)
        
    def setup_frames_panel(self, parent):
        """Панель кадров"""
        frames_panel = tk.Frame(parent, bg=self.colors['panel'], width=250)
        frames_panel.pack(side=RIGHT, fill=Y, padx=(5, 0))
        frames_panel.pack_propagate(False)
        
        tk.Label(frames_panel, text='КАДРЫ', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 12, 'bold')).pack(pady=10)
        
        # Контейнер для миниатюр
        thumb_container = tk.Frame(frames_panel, bg=self.colors['panel'])
        thumb_container.pack(fill=BOTH, expand=True, padx=10)
        
        self.thumb_canvas = tk.Canvas(thumb_container, bg=self.colors['panel'],
                                     highlightthickness=0)
        self.thumb_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        thumb_scroll = tk.Scrollbar(thumb_container, orient=tk.VERTICAL,
                                   command=self.thumb_canvas.yview)
        thumb_scroll.pack(side=RIGHT, fill=Y)
        
        self.thumb_canvas.configure(yscrollcommand=thumb_scroll.set)
        
        self.thumb_frame = tk.Frame(self.thumb_canvas, bg=self.colors['panel'])
        self.thumb_canvas.create_window((0, 0), window=self.thumb_frame,
                                       anchor=NW)
        
        self.thumb_frame.bind('<Configure>', 
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox('all')))
        
        # Кнопки
        btn_frame = tk.Frame(frames_panel, bg=self.colors['panel'])
        btn_frame.pack(fill=X, pady=10)
        
        tk.Button(btn_frame, text='➕ Добавить', command=self.add_frame,
                 bg=self.colors['success'], fg='white',
                 relief=tk.FLAT, bd=0).pack(side=LEFT, expand=True, fill=X, padx=2)
        
        tk.Button(btn_frame, text='🗑 Удалить', command=self.delete_current_frame,
                 bg=self.colors['error'], fg='white',
                 relief=tk.FLAT, bd=0).pack(side=LEFT, expand=True, fill=X, padx=2)
        
        copy_frame = tk.Frame(frames_panel, bg=self.colors['panel'])
        copy_frame.pack(fill=X, pady=(0,10), padx=10)
        
        tk.Button(copy_frame, text='📋 Копировать', command=self.copy_frame,
                 bg=self.colors['panel_light'], fg='white',
                 relief=tk.FLAT, bd=0).pack(side=LEFT, expand=True, fill=X, padx=2)
        
        tk.Button(copy_frame, text='📌 Вставить', command=self.paste_frame,
                 bg=self.colors['panel_light'], fg='white',
                 relief=tk.FLAT, bd=0).pack(side=LEFT, expand=True, fill=X, padx=2)
        
    def setup_timeline(self, parent):
        """Таймлайн"""
        timeline = tk.Frame(parent, bg=self.colors['panel'], height=80)
        timeline.pack(fill=X, pady=(5, 0))
        timeline.pack_propagate(False)
        
        title_frame = tk.Frame(timeline, bg=self.colors['panel'])
        title_frame.pack(fill=X, padx=10, pady=5)
        
        tk.Label(title_frame, text='ТАЙМЛАЙН', 
                bg=self.colors['panel'], fg='white',
                font=('Arial', 10, 'bold')).pack(side=LEFT)
        
        self.duration_label = tk.Label(title_frame, text='Длительность: 0.0с',
                                      bg=self.colors['panel'],
                                      fg='#888888', font=('Arial', 9))
        self.duration_label.pack(side=RIGHT)
        
        # Таймлайн
        timeline_container = tk.Frame(timeline, bg=self.colors['panel_light'])
        timeline_container.pack(fill=BOTH, expand=True, padx=10, pady=(0,10))
        
        self.timeline_canvas = tk.Canvas(timeline_container, height=40,
                                        bg=self.colors['panel_light'],
                                        highlightthickness=0)
        self.timeline_canvas.pack(fill=X)
        
        self.timeline_canvas.bind('<Button-1>', self.on_timeline_click)
        
        # Метка времени
        self.time_label = tk.Label(timeline_container, text='00:00 / 00:00',
                                  bg=self.colors['panel_light'],
                                  fg='white', font=('Arial', 8))
        self.time_label.pack()
        
    def setup_statusbar(self, parent):
        """Статус бар"""
        statusbar = tk.Frame(parent, bg=self.colors['panel'], height=25)
        statusbar.pack(fill=X, side=BOTTOM)
        
        self.status_label = tk.Label(statusbar, text='MotionQuill готов к работе',
                                    bg=self.colors['panel'],
                                    fg='#888888', font=('Arial', 9))
        self.status_label.pack(side=LEFT, padx=10)
        
        self.size_status = tk.Label(statusbar, text='800x600',
                                   bg=self.colors['panel'],
                                   fg='#888888', font=('Arial', 9))
        self.size_status.pack(side=RIGHT, padx=10)
        
    # ========== ФУНКЦИИ РИСОВАНИЯ ==========
    
    def change_tool(self):
        """Смена инструмента"""
        self.selected_tool = self.tool_var.get()
        tool_names = {
            'pencil': '✏️ Карандаш',
            'eraser': '🧽 Ластик',
            'filling': '🪣 Заливка',
            'pipette': '👁 Пипетка',
            'line': '📏 Линия',
            'rectangle': '⬜ Прямоугольник',
            'circle': '⚪ Круг'
        }
        self.mode_label.config(text=tool_names.get(self.selected_tool, '✏️ Карандаш'))
        self.update_status(f"Инструмент: {tool_names.get(self.selected_tool, 'Карандаш')}")
        
    def set_color(self, color):
        """Установить цвет"""
        self.color_var.set(color)
        self.color_preview.config(bg=color)
        
    def choose_color(self):
        """Выбрать цвет"""
        color = colorchooser.askcolor(title="Выберите цвет", 
                                      initialcolor=self.color_var.get())
        if color and color[1]:
            self.set_color(color[1])
            
    def update_size(self, *args):
        """Обновить размер"""
        size = self.size_var.get()
        self.size_label.config(text=f'{size}px')
        
    def set_pixel_size(self, size):
        """Установить размер пикселя"""
        self.size_var.set(size)
        self.update_status(f"Размер: {size}px")
        
    def toggle_grid(self):
        """Включить/выключить сетку"""
        self.show_grid = not self.show_grid
        if self.show_grid:
            self.draw_grid()
        else:
            self.clear_grid()
            
    def draw_grid(self):
        """Нарисовать сетку"""
        self.clear_grid()
        cell_size = self.size_var.get()
        
        for x in range(0, 801, cell_size):
            line = self.canvas.create_line(x, 0, x, 600, fill='#cccccc', width=1)
            self.grid_items.append(line)
            
        for y in range(0, 601, cell_size):
            line = self.canvas.create_line(0, y, 800, y, fill='#cccccc', width=1)
            self.grid_items.append(line)
            
    def clear_grid(self):
        """Очистить сетку"""
        for item in self.grid_items:
            self.canvas.delete(item)
        self.grid_items.clear()
        
    def toggle_previous_frame(self):
        """Показать предыдущий кадр"""
        self.show_previous_frame = not self.show_previous_frame
        if self.show_previous_frame:
            self.prev_frame_indicator.pack(side=LEFT, padx=5)
        else:
            self.prev_frame_indicator.pack_forget()
        self.display_current_frame()
        
    def start_paint(self, event):
        """Начать рисование"""
        if self.current_frame_index < 0:
            return
            
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
        
        tool = self.tool_var.get()
        
        if tool in ['pencil', 'eraser']:
            self.save_to_history()
            self.paint_pixel(event.x, event.y, tool)
        elif tool in ['line', 'rectangle', 'circle']:
            self.shape_start_x = event.x
            self.shape_start_y = event.y
        elif tool == 'filling':
            self.bucket_fill(event.x, event.y)
        elif tool == 'pipette':
            self.pick_color(event)
            
    def paint(self, event):
        """Рисование"""
        if not self.drawing or self.current_frame_index < 0:
            return
            
        x, y = event.x, event.y
        
        if x < 0 or x > 800 or y < 0 or y > 600:
            return
        
        tool = self.tool_var.get()
        
        if tool in ['pencil', 'eraser']:
            # Рисуем линию из пикселей
            self.draw_line(self.last_x, self.last_y, x, y, tool)
        elif tool in ['line', 'rectangle', 'circle']:
            # Предпросмотр фигуры
            self.draw_shape_preview(event)
            
        self.last_x = x
        self.last_y = y
        
    def paint_pixel(self, x, y, tool):
        """Нарисовать один пиксель"""
        size = self.size_var.get()
        color = self.color_var.get() if tool != 'eraser' else '#ffffff'
        
        half = size // 2
        x1, y1 = max(0, x - half), max(0, y - half)
        x2, y2 = min(800, x + half), min(600, y + half)
        
        # Рисуем на холсте
        self.canvas.create_rectangle(x1, y1, x2, y2,
                                   fill=color, outline=color)
        
        # Рисуем на изображении
        draw = ImageDraw.Draw(self.frames[self.current_frame_index])
        draw.rectangle([x1, y1, x2, y2], fill=color)
        
    def draw_line(self, x1, y1, x2, y2, tool):
        """Нарисовать линию из пикселей (алгоритм Брезенхема)"""
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        
        while True:
            self.paint_pixel(x1, y1, tool)
            
            if x1 == x2 and y1 == y2:
                break
                
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
                
    def bucket_fill(self, x, y):
        """Заливка"""
        if self.current_frame_index < 0:
            return
            
        self.save_to_history()
        
        # Простая заливка квадратом
        size = self.size_var.get() * 5
        color = self.color_var.get()
        
        x1, y1 = max(0, x - size), max(0, y - size)
        x2, y2 = min(800, x + size), min(600, y + size)
        
        draw = ImageDraw.Draw(self.frames[self.current_frame_index])
        draw.rectangle([x1, y1, x2, y2], fill=color)
        
        self.canvas.create_rectangle(x1, y1, x2, y2,
                                   fill=color, outline=color)
        
        self.display_current_frame()
        
    def pick_color(self, event):
        """Выбрать цвет пипеткой"""
        if self.current_frame_index < 0:
            return
            
        x, y = event.x, event.y
        if 0 <= x < 800 and 0 <= y < 600:
            frame = self.frames[self.current_frame_index]
            pixels = frame.load()
            color = pixels[x, y]
            
            if isinstance(color, tuple) and len(color) >= 3:
                hex_color = '#{:02x}{:02x}{:02x}'.format(color[0], color[1], color[2])
                self.set_color(hex_color)
                self.update_status(f"Цвет выбран: {hex_color}")
            
    def draw_shape_preview(self, event):
        """Предпросмотр фигуры"""
        if self.shape_start_x is None or self.shape_start_y is None:
            return
            
        if self.temp_shape_id:
            self.canvas.delete(self.temp_shape_id)
            
        x1, y1 = self.shape_start_x, self.shape_start_y
        x2, y2 = event.x, event.y
        color = self.color_var.get()
        
        tool = self.tool_var.get()
        
        if tool == 'line':
            self.temp_shape_id = self.canvas.create_line(x1, y1, x2, y2,
                                                       fill=color,
                                                       width=self.outline_var.get(),
                                                       dash=(4, 4))
        elif tool == 'rectangle':
            # Нормализуем координаты для прямоугольника
            x1_norm, x2_norm = min(x1, x2), max(x1, x2)
            y1_norm, y2_norm = min(y1, y2), max(y1, y2)
            
            if self.fill_var.get():
                self.temp_shape_id = self.canvas.create_rectangle(x1_norm, y1_norm, x2_norm, y2_norm,
                                                                 outline=color,
                                                                 width=self.outline_var.get(),
                                                                 fill=color,
                                                                 stipple='gray50')
            else:
                self.temp_shape_id = self.canvas.create_rectangle(x1_norm, y1_norm, x2_norm, y2_norm,
                                                                 outline=color,
                                                                 width=self.outline_var.get(),
                                                                 dash=(4, 4))
        elif tool == 'circle':
            # Нормализуем координаты для круга
            x1_norm, x2_norm = min(x1, x2), max(x1, x2)
            y1_norm, y2_norm = min(y1, y2), max(y1, y2)
            
            if self.fill_var.get():
                self.temp_shape_id = self.canvas.create_oval(x1_norm, y1_norm, x2_norm, y2_norm,
                                                            outline=color,
                                                            width=self.outline_var.get(),
                                                            fill=color,
                                                            stipple='gray50')
            else:
                self.temp_shape_id = self.canvas.create_oval(x1_norm, y1_norm, x2_norm, y2_norm,
                                                            outline=color,
                                                            width=self.outline_var.get(),
                                                            dash=(4, 4))
                                                            
    def reset_paint(self, event):
        """Завершить рисование"""
        if self.drawing and self.current_frame_index >= 0:
            tool = self.tool_var.get()
            
            if tool in ['line', 'rectangle', 'circle'] and self.shape_start_x is not None:
                self.save_to_history()
                self.draw_shape(event)
                
            if self.temp_shape_id:
                self.canvas.delete(self.temp_shape_id)
                self.temp_shape_id = None
                
            self.shape_start_x = None
            self.shape_start_y = None
            
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
    def draw_shape(self, event):
        """Нарисовать фигуру"""
        if self.shape_start_x is None or self.shape_start_y is None:
            return
            
        x1, y1 = self.shape_start_x, self.shape_start_y
        x2, y2 = event.x, event.y
        
        # Нормализуем координаты (для прямоугольника и круга нужно x1 <= x2, y1 <= y2)
        if self.tool_var.get() in ['rectangle', 'circle']:
            x1, x2 = min(x1, x2), max(x1, x2)
            y1, y2 = min(y1, y2), max(y1, y2)
        
        draw = ImageDraw.Draw(self.frames[self.current_frame_index])
        color = self.color_var.get()
        outline_width = self.outline_var.get()
        
        tool = self.tool_var.get()
        
        if tool == 'line':
            self.canvas.create_line(x1, y1, x2, y2,
                                   fill=color, width=outline_width)
            draw.line([x1, y1, x2, y2], fill=color, width=outline_width)
            
        elif tool == 'rectangle':
            if self.fill_var.get():
                self.canvas.create_rectangle(x1, y1, x2, y2,
                                           fill=color, outline=color,
                                           width=outline_width)
                draw.rectangle([x1, y1, x2, y2], fill=color, outline=color, width=outline_width)
            else:
                self.canvas.create_rectangle(x1, y1, x2, y2,
                                           outline=color, width=outline_width)
                draw.rectangle([x1, y1, x2, y2], outline=color, width=outline_width)
                
        elif tool == 'circle':
            if self.fill_var.get():
                self.canvas.create_oval(x1, y1, x2, y2,
                                      fill=color, outline=color,
                                      width=outline_width)
                draw.ellipse([x1, y1, x2, y2], fill=color, outline=color, width=outline_width)
            else:
                self.canvas.create_oval(x1, y1, x2, y2,
                                      outline=color, width=outline_width)
                draw.ellipse([x1, y1, x2, y2], outline=color, width=outline_width)
        
        self.display_current_frame()
        
    # ========== УПРАВЛЕНИЕ КАДРАМИ ==========
    
    def add_frame(self):
        """Добавить кадр"""
        img = Image.new('RGB', (800, 600), 'white')
        self.frames.append(img)
        self.current_frame_index = len(self.frames) - 1
        self.modified = True
        self.update_frames_display()
        self.display_current_frame()
        self.update_timeline()
        
    def delete_current_frame(self):
        """Удалить кадр"""
        if self.current_frame_index >= 0 and len(self.frames) > 1:
            if messagebox.askyesno("Подтверждение", "Удалить текущий кадр?"):
                del self.frames[self.current_frame_index]
                if self.current_frame_index >= len(self.frames):
                    self.current_frame_index = len(self.frames) - 1
                self.modified = True
                self.update_frames_display()
                self.display_current_frame()
                self.update_timeline()
        elif len(self.frames) <= 1:
            messagebox.showwarning("Предупреждение", "Нельзя удалить последний кадр")
                
    def copy_frame(self):
        """Копировать кадр"""
        if self.current_frame_index >= 0:
            self.clipboard = self.frames[self.current_frame_index].copy()
            self.update_status("Кадр скопирован")
            
    def paste_frame(self):
        """Вставить кадр"""
        if self.clipboard:
            new_frame = self.clipboard.copy()
            self.frames.insert(self.current_frame_index + 1, new_frame)
            self.current_frame_index += 1
            self.modified = True
            self.update_frames_display()
            self.display_current_frame()
            self.update_timeline()
            
    def select_frame(self, index):
        """Выбрать кадр"""
        if 0 <= index < len(self.frames):
            self.current_frame_index = index
            self.update_frames_display()
            self.display_current_frame()
            self.update_timeline()
            
    def prev_frame(self):
        """Предыдущий кадр"""
        if self.frames and self.current_frame_index > 0:
            self.current_frame_index -= 1
            self.update_frames_display()
            self.display_current_frame()
            self.update_timeline()
            
    def next_frame(self):
        """Следующий кадр"""
        if self.frames and self.current_frame_index < len(self.frames) - 1:
            self.current_frame_index += 1
            self.update_frames_display()
            self.display_current_frame()
            self.update_timeline()
            
    def update_frames_display(self):
        """Обновить миниатюры"""
        for widget in self.thumb_frame.winfo_children():
            widget.destroy()
            
        for i, frame in enumerate(self.frames):
            container = tk.Frame(self.thumb_frame, 
                               bg=self.colors['accent'] if i == self.current_frame_index else self.colors['panel'],
                               bd=2)
            container.pack(fill=X, pady=2, padx=5)
            
            thumb = frame.copy()
            thumb.thumbnail((80, 60))
            photo = ImageTk.PhotoImage(thumb)
            
            inner = tk.Frame(container, bg=self.colors['panel'])
            inner.pack(fill=BOTH, expand=True, padx=1, pady=1)
            
            label = tk.Label(inner, image=photo, bg=self.colors['panel'])
            label.image = photo
            label.pack(side=LEFT, padx=5, pady=5)
            
            info = tk.Frame(inner, bg=self.colors['panel'])
            info.pack(side=LEFT, fill=BOTH, expand=True, pady=5)
            
            tk.Label(info, text=f'Кадр {i+1}', 
                    bg=self.colors['panel'],
                    fg='white').pack(anchor=W)
                    
            tk.Button(info, text='Выбрать',
                     command=lambda idx=i: self.select_frame(idx),
                     bg=self.colors['accent'],
                     fg='white',
                     relief=tk.FLAT,
                     font=('Arial', 8),
                     bd=0).pack(anchor=W, pady=2)
            
        if self.frames:
            self.frame_info.config(text=f'Кадр: {self.current_frame_index + 1}/{len(self.frames)}')
            
    def display_current_frame(self):
        """Отобразить текущий кадр"""
        if self.current_frame_index >= 0 and self.frames:
            display_img = self.frames[self.current_frame_index].copy()
            
            if self.show_previous_frame and self.current_frame_index > 0:
                prev_img = self.frames[self.current_frame_index - 1].copy()
                display_img = Image.blend(display_img, prev_img, self.previous_opacity)
            
            self.photo = ImageTk.PhotoImage(display_img)
            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor=NW, image=self.photo)
            
            if self.show_grid:
                self.draw_grid()
        else:
            self.canvas.delete("all")
            self.canvas.create_rectangle(0, 0, 800, 600, fill='white')
            
    def update_timeline(self):
        """Обновить таймлайн"""
        self.timeline_canvas.delete("all")
        if self.frames:
            width = 30
            spacing = 5
            
            for i in range(len(self.frames)):
                x = i * (width + spacing) + 10
                color = self.colors['accent'] if i == self.current_frame_index else self.colors['panel']
                
                self.timeline_canvas.create_rectangle(x, 5, x + width, 35,
                                                    fill=color,
                                                    outline=self.colors['border'])
                self.timeline_canvas.create_text(x + width//2, 20,
                                               text=str(i+1),
                                               fill='white',
                                               font=('Arial', 9))
            
            # Время
            total_time = len(self.frames) * self.frame_duration / 1000
            current_time = (self.current_frame_index + 1) * self.frame_duration / 1000
            
            def format_time(seconds):
                mins = int(seconds // 60)
                secs = seconds % 60
                return f"{mins:02d}:{secs:04.1f}"
            
            if self.time_label:
                self.time_label.config(text=f"{format_time(current_time)} / {format_time(total_time)}")
            if self.duration_label:
                self.duration_label.config(text=f"Длительность: {total_time:.1f}с")
                
    def on_timeline_click(self, event):
        """Клик по таймлайну"""
        if not self.frames:
            return
            
        width = 30
        spacing = 5
        frame_index = int((event.x - 10) / (width + spacing))
        
        if 0 <= frame_index < len(self.frames):
            self.select_frame(frame_index)
            
    def on_mouse_move(self, event):
        """Движение мыши"""
        self.coord_label.config(text=f'X: {event.x}, Y: {event.y}')
        
    # ========== ИСТОРИЯ ==========
    
    def save_to_history(self):
        """Сохранить в историю"""
        if self.current_frame_index >= 0:
            self.history = self.history[:self.history_index + 1]
            self.history.append(self.frames[self.current_frame_index].copy())
            self.history_index += 1
            
            if len(self.history) > 50:
                self.history = self.history[-50:]
                self.history_index = min(self.history_index, len(self.history) - 1)
                
    def undo(self):
        """Отменить"""
        if self.history_index > 0:
            self.history_index -= 1
            self.frames[self.current_frame_index] = self.history[self.history_index].copy()
            self.display_current_frame()
            self.modified = True
            self.update_status("Отмена")
            
    def redo(self):
        """Повторить"""
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.frames[self.current_frame_index] = self.history[self.history_index].copy()
            self.display_current_frame()
            self.modified = True
            self.update_status("Повтор")
            
    # ========== АНИМАЦИЯ ==========
    
    def toggle_playback(self):
        """Воспроизведение"""
        if not self.frames or len(self.frames) < 2:
            messagebox.showinfo("Анимация", "Добавьте больше кадров для воспроизведения")
            return
            
        if self.is_playing:
            self.stop_playback()
        else:
            self.is_playing = True
            self.play_btn.config(text='⏸')
            self.play_animation()
            
    def play_animation(self):
        """Анимация"""
        if self.is_playing and self.frames:
            self.current_frame_index = (self.current_frame_index + 1) % len(self.frames)
            self.display_current_frame()
            self.update_frames_display()
            self.update_timeline()
            self.animation_after_id = self.root.after(self.frame_duration, self.play_animation)
            
    def stop_playback(self):
        """Остановить"""
        self.is_playing = False
        self.play_btn.config(text='▶')
        if self.animation_after_id:
            self.root.after_cancel(self.animation_after_id)
            self.animation_after_id = None
            
    def update_fps(self, event=None):
        """Обновить FPS"""
        try:
            new_fps = int(self.fps_var.get())
            if 1 <= new_fps <= 60:
                self.fps = new_fps
                self.frame_duration = 1000 // self.fps
                self.update_timeline()
                self.update_status(f"FPS: {self.fps}")
        except:
            self.fps_var.set(str(self.fps))
            
    def set_fps(self, fps):
        """Установить FPS из меню"""
        self.fps = fps
        self.fps_var.set(str(fps))
        self.frame_duration = 1000 // fps
        self.update_timeline()
        self.update_status(f"FPS: {fps}")
            
    def fill_frame(self):
        """Залить кадр"""
        if self.current_frame_index >= 0:
            self.save_to_history()
            color = self.color_var.get()
            draw = ImageDraw.Draw(self.frames[self.current_frame_index])
            draw.rectangle([0, 0, 800, 600], fill=color)
            self.display_current_frame()
            self.update_status("Кадр залит цветом")
            
    def clear_frame(self):
        """Очистить кадр"""
        if self.current_frame_index >= 0:
            self.save_to_history()
            self.frames[self.current_frame_index] = Image.new('RGB', (800, 600), 'white')
            self.display_current_frame()
            self.update_status("Кадр очищен")
            
    def update_status(self, message):
        """Обновить статус"""
        self.status_label.config(text=message)
        
    # ========== ФАЙЛОВЫЕ ОПЕРАЦИИ ==========
    
    def new_project(self):
        """Новый проект"""
        if self.modified:
            if messagebox.askyesno("Новый проект", "Сохранить изменения?"):
                self.save_project()
                
        self.frames = []
        self.current_frame_index = -1
        self.history = []
        self.history_index = -1
        self.current_file = None
        self.modified = False
        self.add_frame()
        self.update_status("Новый проект создан")
        
    def save_project(self):
        """Сохранить"""
        if self.current_file:
            self.save_to_file(self.current_file)
        else:
            self.save_project_as()
            
    def save_project_as(self):
        """Сохранить как"""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения")
        if folder:
            self.save_to_file(folder)
            
    def save_to_file(self, folder):
        """Сохранить в папку"""
        try:
            for i, frame in enumerate(self.frames):
                frame.save(os.path.join(folder, f'frame_{i:04d}.png'))
                
            metadata = {
                'fps': self.fps,
                'frame_count': len(self.frames),
                'date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'name': 'MotionQuill Project'
            }
            
            with open(os.path.join(folder, 'project.json'), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
            self.current_file = folder
            self.modified = False
            self.update_status(f"Сохранено в {os.path.basename(folder)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
            
    def load_project(self):
        """Загрузить проект"""
        if self.modified:
            if not messagebox.askyesno("Загрузка", "Сохранить изменения?"):
                return
            self.save_project()
            
        folder = filedialog.askdirectory(title="Выберите папку с проектом")
        if folder:
            try:
                files = sorted([f for f in os.listdir(folder) 
                              if f.startswith('frame_') and f.endswith('.png')])
                self.frames = []
                
                for file in files:
                    img = Image.open(os.path.join(folder, file))
                    img = img.resize((800, 600), Image.Resampling.LANCZOS)
                    self.frames.append(img)
                    
                meta_file = os.path.join(folder, 'project.json')
                if os.path.exists(meta_file):
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                        self.fps = metadata.get('fps', 12)
                        self.fps_var.set(str(self.fps))
                        self.frame_duration = 1000 // self.fps
                        
                if self.frames:
                    self.current_frame_index = 0
                    self.current_file = folder
                    self.modified = False
                    self.history = []
                    self.history_index = -1
                    self.update_frames_display()
                    self.display_current_frame()
                    self.update_timeline()
                    self.update_status(f"Загружено {len(self.frames)} кадров")
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
                
    def load_image(self):
        """Импорт изображения"""
        file_path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.png *.jpg *.jpeg *.gif *.bmp")]
        )
        if file_path:
            try:
                img = Image.open(file_path)
                img = img.resize((800, 600), Image.Resampling.LANCZOS)
                self.frames.append(img)
                self.current_frame_index = len(self.frames) - 1
                self.modified = True
                self.update_frames_display()
                self.display_current_frame()
                self.update_timeline()
                self.update_status(f"Импортировано: {os.path.basename(file_path)}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось загрузить: {e}")
                
    def export_gif(self):
        """Экспорт GIF"""
        if len(self.frames) < 2:
            messagebox.showwarning("Экспорт", "Нужно минимум 2 кадра для GIF")
            return
            
        file_path = filedialog.asksaveasfilename(defaultextension=".gif",
                                                filetypes=[("GIF files", "*.gif")])
        if file_path:
            try:
                self.frames[0].save(file_path,
                                   save_all=True,
                                   append_images=self.frames[1:],
                                   duration=self.frame_duration,
                                   loop=0,
                                   optimize=False)
                self.update_status(f"GIF сохранен: {os.path.basename(file_path)}")
                messagebox.showinfo("Успех", "GIF сохранен!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить GIF: {e}")
                
    def export_png_sequence(self):
        """Экспорт PNG"""
        if not self.frames:
            return
            
        folder = filedialog.askdirectory(title="Выберите папку для сохранения PNG")
        if folder:
            try:
                for i, frame in enumerate(self.frames):
                    frame.save(os.path.join(folder, f'frame_{i:04d}.png'))
                self.update_status(f"Сохранено {len(self.frames)} PNG")
                messagebox.showinfo("Успех", "PNG последовательность сохранена!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
                
    def quit_app(self):
        """Выход"""
        if self.modified:
            if messagebox.askyesno("Выход", "Сохранить изменения перед выходом?"):
                self.save_project()
        self.root.quit()
        
    def show_about(self):
        """О программе"""
        about_text = """MotionQuill v1.0
       
Программа для создания покадровой анимации
с поддержкой пиксельного рисования.

Горячие клавиши:
Ctrl+N - Новый проект
Ctrl+O - Открыть проект
Ctrl+S - Сохранить
Ctrl+Z - Отменить
Ctrl+Y - Повторить
Пробел - Воспроизведение
← → - Навигация по кадрам"""
        
        messagebox.showinfo("О программе MotionQuill", about_text)
        
    def show_shortcuts(self):
        """Горячие клавиши"""
        shortcuts = """ГОРЯЧИЕ КЛАВИШИ:

Файл:
Ctrl+N - Новый проект
Ctrl+O - Открыть проект
Ctrl+S - Сохранить
Ctrl+Shift+S - Сохранить как
Ctrl+I - Импорт изображения

Правка:
Ctrl+Z - Отменить
Ctrl+Y - Повторить
Ctrl+C - Копировать кадр
Ctrl+V - Вставить кадр
Del - Удалить кадр

Вид:
Ctrl+G - Сетка
Ctrl+P - Предыдущий кадр

Навигация:
← → - Предыдущий/следующий кадр
Пробел - Воспроизведение/Пауза"""
        
        messagebox.showinfo("Горячие клавиши", shortcuts)

if __name__ == "__main__":
    root = tk.Tk()
    app = MotionQuill(root)
    root.mainloop()