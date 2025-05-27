from tkinter import messagebox
from customtkinter import *
from customtkinter import *
from animasion import SlideAnimation
from sql_query import MySQLQuery
import threading
from atendance import AttendanceForm
from pathlib import Path
from PIL import Image
import os


class teacher_panal:
    def __init__(self, tec_root_frame, t_username, anime_y, frame_main, login_window):
        def first():
            set_appearance_mode("light")
            set_default_color_theme("blue")

            self.sql = MySQLQuery()
            self.teacher_windo = tec_root_frame
            self.tec_username = t_username
            self.anime_y = anime_y 
            self.frame_main = frame_main
            self.login_window = login_window

            self.create_main_frame()
            self.create_info_frame()
            self.create_class_routine()
        threading.Thread(target=first, daemon=True).start()

    def logout(self, log_out_f) :
        confirm = messagebox.askyesno("Confirm Exit", "Are you sure you want to logout?")
        if confirm:
            animation = SlideAnimation(self.anime_y, self.frame_main, self.login_window)
            animation.slide_down()
            log_out_f.destroy()
            self.sql.close_db()

    def take_attendence(self):
        attendence = CTk()
        attendence.geometry("700x900")
        attendence.resizable(False, False)
        attendence.title("Attendance Sheet")
        def theading_attendence():
            AttendanceForm(attendence, self.tec_username)
        threading.Thread(target=theading_attendence, daemon=True).start()

        attendence.mainloop()


    def create_main_frame(self):
        # Teacher panel main frame
        self.tec_panal_frame = CTkFrame(self.teacher_windo, fg_color="#D7E6FF", width=700, height=400)
        self.tec_panal_frame.place(x=350, y=200, anchor="center")

        self.tec_h_label = CTkLabel(self.tec_panal_frame, text=f"Teacher\nHi! {self.tec_username}", width=1, height=1, fg_color="transparent", text_color="black", font=("Helvetica", 22, "bold"))
        self.tec_h_label.place(x=350, y=50, anchor="center")

        self.tec_logout = CTkButton(self.tec_panal_frame, text="⏻ Log Out", width=1, height=1, command=lambda:self.logout(self.tec_panal_frame), fg_color="transparent", text_color="black", font=("Helvetica", 16, "bold"), hover=False)
        self.tec_logout.place(x=640, y=50, anchor="center")
        self.tec_logout.bind("<Enter>", lambda event: self.hover_on(event, "red", self.tec_logout))
        self.tec_logout.bind("<Leave>", lambda event: self.hover_off(event, "black", self.tec_logout))

    def create_info_frame(self):
        # Info view frame inside the panel
        self.tec_info_view_frame = CTkFrame(self.tec_panal_frame, width=700, height=300, fg_color="transparent")
        self.tec_info_view_frame.place(x=350, y=230, anchor="center")

        # sql backend
        info = self.sql.teacher_info(self.tec_username)
        t_sub = self.sql.teacher_total_sub(self.tec_username)

        tec_name_label = CTkLabel(self.tec_info_view_frame, text_color="black", text="Username", font=("Helvetica", 15, "bold"), anchor="w")
        tec_name_label.place(x=120, y=20)
        tec_name_label = CTkLabel(self.tec_info_view_frame, text_color="black", text="Name", font=("Helvetica", 15, "bold"), anchor="w")
        tec_name_label.place(x=120, y=45)
        tec_tclass_label = CTkLabel(self.tec_info_view_frame, text_color="black", text="Total Class", font=("Helvetica", 15, "bold"), anchor="w")
        tec_tclass_label.place(x=120, y=70)

        BASE_DIR = Path(__file__).resolve().parent
        ICON_DIR = BASE_DIR / "image"
        attendence_icon = CTkImage(Image.open(ICON_DIR / "attendence.png"), size=(30, 30))

        atend_btn = CTkButton(self.tec_info_view_frame, text_color="#2c3e50", fg_color="transparent", hover_color="#d0e0f5", text="Take Attendance", image=attendence_icon, compound="top", command=self.take_attendence, font=("Helvetica",16, "bold"), hover=True)
        atend_btn.place(x=500, y=56, anchor="center")

        if (info and t_sub) is not None:

            name_value_label = CTkLabel(self.tec_info_view_frame, text=f":     {self.tec_username}", text_color="black", font=("Helvetica", 14, "bold"), anchor="w")
            name_value_label.place(x=230, y=20)

            if len(info[0]) >= 17:
                name = ' '.join(info[0].split()[:2])
                class_value_label = CTkLabel(self.tec_info_view_frame, text=f":     {name}", text_color="black", font=("Helvetica", 14, "bold"), anchor="w")
            else:
                class_value_label = CTkLabel(self.tec_info_view_frame, text=f":     {info[0]}", text_color="black", font=("Helvetica", 14, "bold"), anchor="w")
            class_value_label.place(x=230, y=45)

            class_value_label = CTkLabel(self.tec_info_view_frame, text=f":     {t_sub[0]}", text_color="black", font=("Helvetica", 14, "bold"), anchor="w")
            class_value_label.place(x=230, y=70)
        
        elif info is None:
            name_value_label = CTkLabel(self.tec_info_view_frame, text=f":     {self.tec_username}", text_color="black", font=("Helvetica", 14, "bold"), anchor="w")
            name_value_label.place(x=230, y=20)
            class_value_label = CTkLabel(self.tec_info_view_frame, text=f":     Not Found", text_color="red", font=("Helvetica", 14, "bold"), anchor="w")
            class_value_label.place(x=230, y=45)
            class_value_label = CTkLabel(self.tec_info_view_frame, text=f":     {t_sub[0]}", text_color="red", font=("Helvetica", 14, "bold"), anchor="w")
            class_value_label.place(x=230, y=70)


    def create_class_routine(self):

        # Class routine display
        results = self.sql.teacher_routine(self.tec_username)

        ruttin_label = CTkLabel(self.tec_info_view_frame, text="Class Routine", text_color="black", width=1, height=1, fg_color="transparent", font=("Helvetica", 13, "bold"))
        ruttin_label.place(x=350, y=140, anchor="center")

        subject_box = CTkTextbox(self.tec_info_view_frame, wrap="none", activate_scrollbars=True,
                                 width=500, height=160, fg_color="transparent",
                                 scrollbar_button_color="sky blue", font=("Helvetica", 13, "bold"))
        subject_box.place(x=360, y=240, anchor="center")

        subject_box.delete('0.0', 'end')
        header = "Subject\t\t\tClass\tSection\t   Start Time\t\tEnd Time\n"
        subject_box.insert('end', header)
        subject_box.insert('end', "-" * 115 + '\n')

        for info in results:
            line = f"{info[0]}\t\t\t  {info[1]}\t  {info[2]}\t     {info[3]}\t\t {info[4]}\n"
            subject_box.insert('end', line)
        subject_box.configure(state="disabled")

    def hover_on(self, event, color, btn_name):
        btn_name.configure(text_color=color)

    def hover_off(self, event, color, btn_name):
        btn_name.configure(text_color=color)

