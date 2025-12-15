import tkinter as tk
from tkinter import ttk
import math

class InfusionPumpSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("Infusion Pump Interface (On-Screen Alerts)")
        self.root.geometry("500x750")
        self.root.configure(bg="#f0f0f0")

        # --- System Variables ---
        self.vtbi = 100.0  # Volume To Be Infused (mL)
        self.total_minutes = 60 # Default 1 hour
        self.rate = 100.0  # Flow Rate (mL/hr)
        self.infused_volume = 0.0
        
        self.is_infusing = False
        self.is_alarm = False
        self.sim_speed = 1.0 

        # --- UI Layout ---
        self.create_screen_display()
        self.create_controls()
        self.create_status_bar()

        # Initial calculation
        self.recalc_rate()
        self.update_display()

    def create_screen_display(self):
        """Creates the LCD-like display area."""
        # Main Screen Container
        self.screen_frame = tk.Frame(self.root, bg="black", bd=10, relief="sunken")
        self.screen_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # --- Normal Operation View (Container) ---
        self.normal_view = tk.Frame(self.screen_frame, bg="black")
        self.normal_view.pack(fill="both", expand=True)

        # Rate Display
        self.lbl_rate_title = tk.Label(self.normal_view, text="FLOW RATE (mL/hr)", bg="black", fg="white", font=("Arial", 10))
        self.lbl_rate_title.pack(anchor="w", pady=(10,0))
        self.lbl_rate = tk.Label(self.normal_view, text="100.0", bg="black", fg="#2fcd2f", font=("Digital-7", 45, "bold")) 
        self.lbl_rate.pack(anchor="e", padx=10)

        ttk.Separator(self.normal_view, orient='horizontal').pack(fill='x', pady=10)

        # Info Area
        self.lbl_vtbi = tk.Label(self.normal_view, text=f"VTBI: {self.vtbi} mL", bg="black", fg="white", font=("Arial", 14))
        self.lbl_vtbi.pack(anchor="w", padx=10)

        self.lbl_time = tk.Label(self.normal_view, text="TIME: 01:00", bg="black", fg="white", font=("Arial", 14))
        self.lbl_time.pack(anchor="w", padx=10)
        
        # Progress Bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.normal_view, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill="x", padx=10, pady=15)

        # Status Text (Running/Stopped)
        self.lbl_status = tk.Label(self.normal_view, text="STOPPED", bg="black", fg="yellow", font=("Arial", 12, "bold"))
        self.lbl_status.pack(side="bottom", pady=10)

        # --- Alert Overlay (Hidden by default) ---
        # This frame sits on top of everything else when an alarm happens
        self.alert_view = tk.Frame(self.screen_frame, bg="red")
        
        self.lbl_alert_title = tk.Label(self.alert_view, text="ALARM", bg="red", fg="white", font=("Arial", 16, "bold"))
        self.lbl_alert_title.pack(pady=(40, 10))
        
        self.lbl_alert_msg = tk.Label(self.alert_view, text="Message Here", bg="red", fg="white", font=("Arial", 12), wraplength=350)
        self.lbl_alert_msg.pack(pady=10)

        self.lbl_alert_hint = tk.Label(self.alert_view, text="Press STOP to Clear", bg="red", fg="white", font=("Arial", 10, "italic"))
        self.lbl_alert_hint.pack(side="bottom", pady=20)

    def create_controls(self):
        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(pady=10)

        # Volume Controls
        tk.Label(control_frame, text="Volume (mL)", bg="#f0f0f0", font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2)
        tk.Button(control_frame, text="-10", command=lambda: self.adjust_vtbi(-10), width=5).grid(row=1, column=0, padx=2, pady=2)
        tk.Button(control_frame, text="+10", command=lambda: self.adjust_vtbi(10), width=5).grid(row=1, column=1, padx=2, pady=2)

        # Time Controls
        tk.Label(control_frame, text="Time (HH:MM)", bg="#f0f0f0", font=("Arial", 10, "bold")).grid(row=0, column=2, columnspan=2)
        tk.Button(control_frame, text="-1 H", command=lambda: self.adjust_time(-60), width=5).grid(row=1, column=2, padx=2, pady=2)
        tk.Button(control_frame, text="+1 H", command=lambda: self.adjust_time(60), width=5).grid(row=1, column=3, padx=2, pady=2)
        tk.Button(control_frame, text="-10 M", command=lambda: self.adjust_time(-10), width=5).grid(row=2, column=2, padx=2, pady=2)
        tk.Button(control_frame, text="+10 M", command=lambda: self.adjust_time(10), width=5).grid(row=2, column=3, padx=2, pady=2)

        # Speed
        tk.Label(control_frame, text="Speed:", bg="#f0f0f0").grid(row=3, column=1, pady=10)
        self.speed_btn = tk.Button(control_frame, text="1x (Real)", command=self.toggle_speed, bg="lightblue")
        self.speed_btn.grid(row=3, column=2)

        # Action Buttons
        action_frame = tk.Frame(self.root, bg="#f0f0f0")
        action_frame.pack(pady=20)

        self.btn_start = tk.Button(action_frame, text="START", bg="#2fcd2f", fg="white", font=("Arial", 12, "bold"), width=10, command=self.start_infusion)
        self.btn_start.grid(row=0, column=0, padx=10)

        self.btn_stop = tk.Button(action_frame, text="STOP / SILENCE", bg="#f44336", fg="white", font=("Arial", 12, "bold"), width=14, command=self.stop_infusion)
        self.btn_stop.grid(row=0, column=1, padx=10)
        
        self.btn_reset = tk.Button(action_frame, text="RESET", bg="#FF9800", fg="white", font=("Arial", 12, "bold"), width=10, command=self.reset_system)
        self.btn_reset.grid(row=0, column=2, padx=10)

        # Error Simulation
        error_frame = tk.LabelFrame(self.root, text="Alarms", bg="#f0f0f0", padx=10, pady=5)
        error_frame.pack(pady=5)
        tk.Button(error_frame, text="Simulate Occlusion", command=self.trigger_occlusion, bg="grey", fg="white").pack()

    def create_status_bar(self):
        self.status_bar = tk.Label(self.root, text="System Ready", bd=1, relief="sunken", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

    # --- Display Logic ---

    def show_screen_alert(self, title, message, bg_color):
        """Switches the screen to the alert view."""
        # Update colors and text
        self.alert_view.config(bg=bg_color)
        self.lbl_alert_title.config(text=title, bg=bg_color)
        self.lbl_alert_msg.config(text=message, bg=bg_color)
        self.lbl_alert_hint.config(bg=bg_color)
        
        # Hide normal view, show alert view
        self.normal_view.pack_forget() 
        self.alert_view.pack(fill="both", expand=True)

    def clear_screen_alert(self):
        """Returns to the normal view."""
        self.alert_view.pack_forget()
        self.normal_view.pack(fill="both", expand=True)
        self.screen_frame.config(bg="black") # Reset border

    def format_time_hhmm(self, minutes):
        h = int(minutes // 60)
        m = int(minutes % 60)
        return f"{h:02d}:{m:02d}"

    # --- Operation Logic ---

    def recalc_rate(self):
        hours = self.total_minutes / 60.0
        if hours > 0:
            self.rate = round(self.vtbi / hours, 1)
        else:
            self.rate = 0.0

    def adjust_vtbi(self, amount):
        if self.is_infusing: return
        self.vtbi = max(0, round(self.vtbi + amount, 1))
        self.recalc_rate()
        self.update_display()

    def adjust_time(self, minutes_delta):
        if self.is_infusing: return
        self.total_minutes = max(1, self.total_minutes + minutes_delta)
        self.recalc_rate()
        self.update_display()

    def toggle_speed(self):
        if self.sim_speed == 1.0:
            self.sim_speed = 60.0
            self.speed_btn.config(text="60x (Fast)")
        else:
            self.sim_speed = 1.0
            self.speed_btn.config(text="1x (Real)")

    def start_infusion(self):
        # 1. Check for Setup Error
        if self.vtbi <= 0:
            self.show_screen_alert("SETUP ERROR", "Volume must be greater than 0.", "#FF9800") # Orange
            self.status_bar.config(text="Error: Check Settings")
            return
        
        # 2. Start if clear
        if not self.is_infusing and not self.is_alarm:
            self.clear_screen_alert() # Ensure screen is clear
            self.is_infusing = True
            self.status_bar.config(text="Pump Running...")
            self.lbl_status.config(text=">>> INFUSING >>>", fg="#2fcd2f")
            self.run_simulation_tick()

    def stop_infusion(self):
        # Acts as both Stop and Alarm Silence/Clear
        self.is_infusing = False
        self.is_alarm = False
        self.clear_screen_alert() # Go back to normal screen
        
        self.lbl_status.config(text="STOPPED", fg="yellow")
        self.lbl_rate.config(fg="yellow")
        self.status_bar.config(text="Pump Stopped / Silenced")

    def reset_system(self):
        self.stop_infusion()
        self.vtbi = 100.0
        self.total_minutes = 60
        self.infused_volume = 0.0
        self.recalc_rate()
        self.update_display()
        self.lbl_rate.config(fg="#2fcd2f")

    def trigger_occlusion(self):
        self.is_infusing = False
        self.is_alarm = True
        self.status_bar.config(text="ALARM: Line Blocked.")
        # Show on screen
        self.show_screen_alert("OCCLUSION", "Blockage detected in line.\nCheck patient access.", "#cc0000") # Red

    def complete_infusion(self):
        self.is_infusing = False
        self.status_bar.config(text="Therapy Finished.")
        # Show on screen
        self.show_screen_alert("COMPLETE", "Infusion Therapy Finished.\nVolume: 0 mL remaining.", "#0088cc") # Blue

    def run_simulation_tick(self):
        if self.is_infusing and self.vtbi > 0:
            time_passed_seconds = 0.1 * self.sim_speed
            time_passed_hours = time_passed_seconds / 3600.0
            step_volume = self.rate * time_passed_hours
            
            if step_volume > self.vtbi:
                step_volume = self.vtbi

            self.vtbi -= step_volume
            self.infused_volume += step_volume
            remaining_hours = self.vtbi / self.rate if self.rate > 0 else 0
            self.total_minutes = remaining_hours * 60
            
            if self.vtbi <= 0.01:
                self.vtbi = 0
                self.total_minutes = 0
                self.complete_infusion()
            
            self.update_display()
            self.root.after(100, self.run_simulation_tick)

    def update_display(self):
        self.lbl_rate.config(text=f"{self.rate:.1f}")
        self.lbl_vtbi.config(text=f"VTBI: {self.vtbi:.1f} mL")
        self.lbl_time.config(text=f"TIME: {self.format_time_hhmm(self.total_minutes)}")
        
        total = self.vtbi + self.infused_volume
        if total > 0:
            pct = (self.infused_volume / total) * 100
            self.progress_var.set(pct)

if __name__ == "__main__":
    root = tk.Tk()
    app = InfusionPumpSimulator(root)
    root.mainloop()