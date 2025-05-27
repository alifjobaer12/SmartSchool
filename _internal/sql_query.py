import mysql.connector
from cryptography.fernet import Fernet
import os
from dotenv import dotenv_values
import keyring
from tkinter import messagebox
from customtkinter import *

# ✅ Step 1: Load encrypted env first
def load_encrypted_env(enc_file_path, encryption_key):
    with open(enc_file_path, "rb") as f:
        encrypted_data = f.read()

    fernet = Fernet(encryption_key)
    try:
        decrypted_data = fernet.decrypt(encrypted_data).decode()
    except:
        messagebox.showerror("Setup Error","Please complete the setup before launching the SmaartSchool App. If anything goes wrong after setup, just reach out to the owner—we’ve got your back." )
        sys.exit()


    with open("temp.env", "w") as f:
        f.write(decrypted_data)

    env_vars = dotenv_values("temp.env")
    for key, value in env_vars.items():
        os.environ[key] = value

    os.remove("temp.env")  # Cleanup

# ✅ Step 2: Call this at the top — before any env var usage
def try_load_encrypted_env():
    key = keyring.get_password("SmartSchool", "F_ENC_KEY")
    if not key:
        raise RuntimeError("❌ Encryption key not found in Windows Vault.")
    if not os.path.exists("SmartSchool.enc"):
        return
    load_encrypted_env("SmartSchool.enc", key.encode())

# ✅ Load before using env vars
try_load_encrypted_env()


# ✅ Step 3: Now safe to access env vars
def get_env_var(var_name):
    value = os.getenv(var_name)
    if value is None:
        raise EnvironmentError(f"❌ Required environment variable '{var_name}' is missing.")
    return value


class MySQLQuery:
    def __init__(self):
        try:
            self.db = mysql.connector.connect(
                host=get_env_var("HOST"),
                user=get_env_var("USER"),
                password=get_env_var("PASSWORD"),
                database=get_env_var("DATABASE"),
                port=int(get_env_var("PORT"))
            )
            self.cursor = self.db.cursor()
        except:
            messagebox.showerror("Internet Error","Please check your internet before launching the SmaartSchool App. If anything goes wrong, just reach out to the owner—we’ve got your back." )
            sys.exit()
        self.encript_key = get_env_var("ENC_KEY")
        self.fernet = Fernet(self.encript_key)

    def log_in(self, username):
        try:
            sql = "SELECT password, role FROM users WHERE username = %s"
            self.cursor.execute(sql, (username,))
            access = self.cursor.fetchone()

            if access is None:
                return False
            
            password, role = access

            try:
                decrypted_password = self.fernet.decrypt(password.encode()).decode()
            except Exception as e:
                print(f"Decryption failed: {e}")
                return False

            return (decrypted_password, role)
            
        except:
            return False


    def add_users(self, user_info: dict):
        try:
            sql = """INSERT INTO users (username, password, role, s_q_a)
            VALUES (%s, %s, %s, %s);"""

            user_info['pass'] = self.fernet.encrypt(user_info['pass'].encode())

            values = (user_info['username'], user_info['pass'], user_info['role'], user_info['qna'])
            
            self.cursor.execute(sql, values)
            self.db.commit()

            return True
        except mysql.connector.IntegrityError as e:
            return f"Error : {e}"
        except Exception as e:
            return f"Error : {e}"

    def ck_class_roll_section(self, student_data: dict):
        try:
            sql = """SELECT COUNT(*) AS total FROM students WHERE class = %s AND roll = %s AND section = %s GROUP BY class, roll, LOWER(section) HAVING COUNT(*) > 0;"""
            self.cursor.execute(sql, (student_data['class'], student_data['roll'], student_data['section']))
            ck = self.cursor.fetchone()
            if ck is None or ck[0] == 0:
                return True
            else:
                return False
        except mysql.connector.IntegrityError as e:
            print (f"Error : {e}")
            return False

    def ck_tec_class_sub_section(self, sub_info: dict):
        try:
            sql = """SELECT COUNT(*) AS total FROM subjects WHERE class = %s AND sub_name = %s AND section = %s AND class_start_time = %s AND class_end_time = %s GROUP BY class, LOWER(sub_name), LOWER(section), class_start_time, class_end_time HAVING COUNT(*) > 0;"""
            self.cursor.execute(sql, (sub_info['class'], sub_info['subject'], sub_info['section'], sub_info['start_t'], sub_info['end_t']))
            ck = self.cursor.fetchone()
            if ck is not None:
                return False
            else:
                return True
        except mysql.connector.IntegrityError as e:
            print (f"Error : {e}")
            return False

    # 1. Add Student
    def add_student(self, student_data: dict):
        try:
            sql = """INSERT INTO students (username, s_name, class, roll, section, grade, pn_number, address, tution_fee, paid_fee)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);"""

            values = (student_data['username'], student_data['s_name'], student_data['class'], student_data['roll'], student_data['section'], student_data['grade'], student_data['pn_number'], student_data['address'], student_data['tution_fee'], student_data['paid_fee'] )
            
            self.cursor.execute(sql, values)
            self.db.commit()

            return True
        except mysql.connector.IntegrityError as e:
            return f"Error : {e}"


    # 2. Find Student
    def find_student(self, username):
        sql = "SELECT * FROM students WHERE username = %s;"
        self.cursor.execute(sql, (username,))
        f_s = self.cursor.fetchone()
        return f_s
        


    # 3. Delete Student
    def delete_student(self, username):
        try:
            ck = self.find_student(username)

            while self.cursor.nextset():  # clear the cursor for next exicution
                pass

            if ck is None:
                return "❌ Student Not Found"

            # self.db.start_transaction()  # START TRANSACTION

            self.cursor.execute("DELETE FROM students WHERE username = %s;", (username,))
            self.cursor.execute("DELETE FROM users WHERE username = %s;", (username,))

            self.db.commit()  # COMMIT if all succeed
            return True

        except Exception as e:
            self.db.rollback()  # ROLLBACK if any fail
            return f"❌ [Error] Failed to delete student: {e}"

    # 4. All Students
    def all_students(self):
        sql = "SELECT * FROM students;"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    # 5. Student Routine
    def student_routine(self, username):
        try:
            sql = "SELECT class FROM students WHERE username = %s;"
            self.cursor.execute(sql, (username,))
            s_class = self.cursor.fetchone()
            # print(s_class)
            while self.cursor.nextset():  # clear the cursor for next exicution
                pass  

            sql = "SELECT sub_name, t_name, class_start_time, class_end_time FROM subjects WHERE class = %s;"
            self.cursor.execute(sql, (s_class[0],))
            # print(self.cursor.fetchall())
            return self.cursor.fetchall()
        except Exception as e:
            return f"❌ Error : {e}"

    # 6. Add Teacher
    def add_teacher(self, teacher_data: dict):
        
        try:
            sql = """INSERT INTO teacher (username, t_name, t_pn_number, t_address)
                     VALUES (%s, %s, %s, %s)"""
            values = (
                teacher_data['username'], teacher_data['name'],
                teacher_data['phone'], teacher_data['address']
            )
            self.cursor.execute(sql, values)
            self.db.commit()
            return True
        except mysql.connector.IntegrityError as e:
            return False
        except Exception as e:
            return False

    # 7. Find Teacher
    def find_teacher(self, username):
        sql = "SELECT * FROM teacher WHERE username = %s"
        self.cursor.execute(sql, (username,))
        f_t = self.cursor.fetchone()
        return f_t

    # 8. Delete Teacher
    def delete_teacher(self, username):
        try:
            ck = self.find_teacher(username)

            while self.cursor.nextset():  # clear the cursor for next execution
                pass
            
            if ck is None:
                return "❌ Teacher Not Found"
    
            # Start transaction
            # self.db.start_transaction()
    
            # Delete from all related tables
            self.cursor.execute("DELETE FROM teacher WHERE username = %s;", (username,))
            self.cursor.execute("DELETE FROM subjects WHERE username = %s;", (username,))
            self.cursor.execute("DELETE FROM users WHERE username = %s;", (username,))
    
            # Commit if all succeed
            self.db.commit()
            return True
    
        except Exception as e:
            self.db.rollback()  # Roll back if any delete fails
            return f"❌ [Error] Failed to delete Teacher: {e}"

    # 9. Teacher Info
    def teacher_info(self, username):
        try:
            sql = "SELECT t_name FROM teacher WHERE username = %s"
            self.cursor.execute(sql, (username,))
            name = self.cursor.fetchone()

            return name
        
        except Exception as e:
            return False

    def teacher_total_sub(self, username):
        try:
            sql = "SELECT COUNT(*) FROM subjects WHERE username = %s;"
            self.cursor.execute(sql, (username,))
            t_t_sub = self.cursor.fetchone()

            return t_t_sub
        
        except Exception as e:
            return False

    # 10. All Teachers
    def all_teachers(self):
        sql = "SELECT * FROM teacher;"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

        # 11. Teacher Routine
    def teacher_routine(self, username):
        try:
            while self.cursor.nextset():  # clear the cursor for next exicution
                pass            

            sql = "SELECT sub_name, class, section, class_start_time, class_end_time FROM subjects WHERE username = %s"
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchall()
        except mysql.connector.errors.InternalError as e:
            print("MySQL Error:", e)
            return []
    
    def add_subject(self, sub_info: dict):

        try:
            sql = """INSERT INTO subjects (sub_name, username, t_name, class, class_start_time, class_end_time, section)
                     VALUES (%s, %s, %s, %s, %s, %s, %s);"""
            values = (
                sub_info['subject'],sub_info['username'], sub_info['name'], 
                sub_info['class'], sub_info['start_t'], sub_info['end_t'],sub_info['section']
            )
            self.cursor.execute(sql, values)
            self.db.commit()
            return True
        except mysql.connector.IntegrityError as e:
            return False
        except Exception as e:
            return False

    def show_fees(self, username):
        try:
            sql = "SELECT tution_fee, paid_fee, (tution_fee - paid_fee) AS remaining_fee FROM students WHERE username = %s ;"
            self.cursor.execute(sql, (username,))
            return self.cursor.fetchone()
        except Exception as e:
            return f"❌ Error : {e}"

    def update_fees(self, username, tuition_fee, paid_fee):
        try:
            sql = "SELECT paid_fee, tution_fee FROM students WHERE username = %s"
            self.cursor.execute(sql, (username,))
            result = self.cursor.fetchone()
    
            if not result:
                return "❌ User not found."
    
            current_paid, current_tuition = result
    
            tuition_fee = int(tuition_fee) if tuition_fee else 0
            paid_fee = int(paid_fee) if paid_fee else 0
    
            new_paid = current_paid + paid_fee
            new_tuition = current_tuition + tuition_fee
    
            if tuition_fee > 0:
                sql = """UPDATE students SET tution_fee = %s, paid_fee = %s WHERE username = %s"""
                self.cursor.execute(sql, (new_tuition, new_paid, username))
            else:
                self.cursor.execute(
                    "UPDATE students SET paid_fee = %s WHERE username = %s",
                    (new_paid, username)
                )
    
            self.db.commit()
            return True
    
        except Exception as e:
            return f"❌ Error updating fees: {e}"

    def register(self, username, old_pass, new_pass, c_new_pass, qna):
        try:
            db_pass = self.log_in(username)  # Should return (password, role)
            if not db_pass:
                return "User not found"

            pswd, role = db_pass
            while self.cursor.nextset():   # clear the cursor for next exicution
                pass 

            if pswd != old_pass:
                return "Incorrect Default Password"

            if new_pass != c_new_pass:
                return "Password & Confirm Password do not match"

            new_pass = self.fernet.encrypt(new_pass.encode())

            sql = """UPDATE users SET password = %s, s_q_a = %s WHERE username = %s"""
            values = (new_pass, qna, username,)
            self.cursor.execute(sql, values)
            self.db.commit()  # Ensure changes are saved
            return True

        except mysql.connector.IntegrityError as e:
            return f"Integrity Error: {e}"

        except Exception as e:
            return f"Error: {e}"

    def forget_pass(self, username, qna, new_pass, c_new_pass):
        try:
            sql = """ SELECT s_q_a FROM users WHERE username = %s """
            self.cursor.execute(sql, (username,))
            access = self.cursor.fetchone()

            while self.cursor.nextset():  # clear the cursor for next exicution
                pass

            if access[0] != qna:
                return f"Security Question  do not match"
            
            if new_pass != c_new_pass:
                return f"New Password & Confirm New Password do not match"
            
            new_pass = self.fernet.encrypt(new_pass.encode())

            sql = """UPDATE users SET password = %s WHERE username = %s"""
            values = (new_pass, username,)
            self.cursor.execute(sql, values)
            self.db.commit()  # Ensure changes are saved
            return True

        except mysql.connector.IntegrityError as e:
            return f"Integrity Error: {e}"

        except Exception as e:
            return f"Error: {e}"


    def att_find_class(self, t_username):
        sql = """SELECT DISTINCT class FROM subjects WHERE username = %s;"""            
        self.cursor.execute(sql, (t_username,))
        class_list = self.cursor.fetchall()

        all_class_list = sorted([row[0] for row in class_list])
        return all_class_list

    def att_find_section(self, t_username, selected_class):
        sql = """select DISTINCT section from subjects where username = %s and class = %s;"""            
        self.cursor.execute(sql, (t_username, selected_class,))
        section_list = self.cursor.fetchall()

        all_sections_list = sorted([row[0] for row in section_list])
        return all_sections_list

    def att_find_subject(self, t_username, selected_class, selected_section):
        sql = """select DISTINCT sub_name from subjects where username = %s and class = %s and section = %s;"""            
        self.cursor.execute(sql, (t_username, selected_class, selected_section))
        subject_list = self.cursor.fetchall()

        all_subject_list = sorted([row[0] for row in subject_list])
        return all_subject_list

    def att_load_student(self, class_val, section_val):
        sql = """SELECT id, roll, s_name FROM students WHERE class=%s AND section=%s ORDER BY roll;"""
        self.cursor.execute(sql, (class_val, section_val,))
        student_list = self.cursor.fetchall()

        return student_list
    
    def att_std_present(self, sid):
        sql = """SELECT COUNT(*) FROM attendance WHERE student_id=%s AND status=1;"""
        self.cursor.execute(sql, (sid,))
        present_count = self.cursor.fetchone()[0]
        return present_count
    
    def att_std_absent(self, sid):
        sql = """SELECT COUNT(*) FROM attendance WHERE student_id=%s AND status=0;"""
        self.cursor.execute(sql, (sid,))
        absent_count = self.cursor.fetchone()[0]
        return absent_count
    
    def att_save_attendance(self, student_id, class_val, section_val, subject, today, status, t_username):
        try:
            sql = """INSERT INTO attendance (student_id, class, section, subject, date, status, t_username)
                    VALUES (%s, %s, %s, %s, %s, %s, %s);"""
            self.cursor.execute(sql, (student_id, class_val, section_val, subject, today, status, t_username,) )
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            return f"Error, Failed to save attendance.\n{e}"
            


    def close_db(self):
        try:
            self.cursor.close()
            self.db.close()
            return True
        except Exception as e:
            return f"Error : {e}"
