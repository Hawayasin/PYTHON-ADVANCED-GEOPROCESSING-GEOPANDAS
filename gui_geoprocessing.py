import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import geopandas as gpd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import os
import warnings
import tempfile

warnings.filterwarnings('ignore')

class GeoprocessingGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Geoprocessing GUI - Data Spasial")
        self.root.geometry("1400x900")
        
        # Data storage
        self.gdf1 = None  # Data 1
        self.gdf2 = None  # Data 2
        self.gdf3 = None  # Data 3 (boundary/clip)
        self.result = None
        self.result_info = {"name": "", "features": 0}
        
        # File paths
        self.data1_path = tk.StringVar(value="Belum ada data")
        self.data2_path = tk.StringVar(value="Belum ada data")
        self.data3_path = tk.StringVar(value="Belum ada data")
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup UI dengan layout kiri (tools) dan kanan (peta)"""
        
        # Main container
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ============ PANEL KIRI - TOOLS & CONTROLS ============
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)
        
        # Judul
        title_label = ttk.Label(left_frame, text="🛠️ GEOPROCESSING TOOLS", 
                               font=("Arial", 12, "bold"))
        title_label.pack(pady=10, padx=10)
        
        # ---- Data Upload Section ----
        upload_frame = ttk.LabelFrame(left_frame, text="📂 Upload Data", padding=10)
        upload_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Data 1
        ttk.Label(upload_frame, text="Data 1 (Layer utama):", font=("Arial", 9)).pack(anchor=tk.W)
        data1_btn = ttk.Button(upload_frame, text="Upload Data 1", 
                              command=lambda: self.load_file(1))
        data1_btn.pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data1_path, 
                 font=("Arial", 8), foreground="blue").pack(anchor=tk.W, padx=5)
        
        # Data 2
        ttk.Label(upload_frame, text="Data 2 (Layer kedua):", font=("Arial", 9)).pack(anchor=tk.W, pady=(10,0))
        data2_btn = ttk.Button(upload_frame, text="Upload Data 2", 
                              command=lambda: self.load_file(2))
        data2_btn.pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data2_path, 
                 font=("Arial", 8), foreground="blue").pack(anchor=tk.W, padx=5)
        
        # Data 3 (Boundary/Clip)
        ttk.Label(upload_frame, text="Data 3 (Boundary/Clip):", font=("Arial", 9)).pack(anchor=tk.W, pady=(10,0))
        data3_btn = ttk.Button(upload_frame, text="Upload Data 3", 
                              command=lambda: self.load_file(3))
        data3_btn.pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data3_path, 
                 font=("Arial", 8), foreground="blue").pack(anchor=tk.W, padx=5)
        
        # ---- Geoprocessing Operations Section ----
        ttk.Separator(left_frame).pack(fill=tk.X, pady=10, padx=10)
        
        ops_frame = ttk.LabelFrame(left_frame, text="⚙️ Operasi Geoprocessing", padding=10)
        ops_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Clip Button
        clip_btn = ttk.Button(ops_frame, text="🔪 CLIP", 
                             command=self.run_clip)
        clip_btn.pack(fill=tk.X, pady=3)
        
        # Dissolve Button
        dissolve_btn = ttk.Button(ops_frame, text="🔗 DISSOLVE", 
                                 command=self.run_dissolve)
        dissolve_btn.pack(fill=tk.X, pady=3)
        
        # Intersect Button
        intersect_btn = ttk.Button(ops_frame, text="✂️ INTERSECT", 
                                  command=self.run_intersect)
        intersect_btn.pack(fill=tk.X, pady=3)
        
        # Union Button
        union_btn = ttk.Button(ops_frame, text="🔄 UNION", 
                              command=self.run_union)
        union_btn.pack(fill=tk.X, pady=3)
        
        # ---- Result Info Section ----
        ttk.Separator(left_frame).pack(fill=tk.X, pady=10, padx=10)
        
        info_frame = ttk.LabelFrame(left_frame, text="📊 Informasi Hasil", padding=10)
        info_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        self.result_text = tk.Text(info_frame, height=8, width=30, 
                                   font=("Courier", 9))
        self.result_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # ---- Save & Clear Section ----
        ttk.Separator(left_frame).pack(fill=tk.X, pady=10, padx=10)
        
        action_frame = ttk.Frame(left_frame)
        action_frame.pack(fill=tk.X, padx=10, pady=5)
        
        save_btn = ttk.Button(action_frame, text="💾 Simpan Hasil", 
                             command=self.save_result)
        save_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        clear_btn = ttk.Button(action_frame, text="🗑️ Bersihkan", 
                              command=self.clear_all)
        clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        
        # ============ PANEL KANAN - MAP VISUALIZATION ============
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=2)
        
        map_title = ttk.Label(right_frame, text="🗺️ Visualisasi Data", 
                             font=("Arial", 12, "bold"))
        map_title.pack(pady=10)
        
        # Setup matplotlib figure
        self.fig = Figure(figsize=(8, 7), dpi=100)
        self.ax = self.fig.add_subplot(111)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initial empty map message
        self.ax.text(0.5, 0.5, "Upload data untuk melihat visualisasi", 
                    ha='center', va='center', transform=self.ax.transAxes,
                    fontsize=12, color='gray')
        self.ax.set_axis_off()
        self.canvas.draw()
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, 
                              relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        
    def load_file(self, data_num):
        """Load shapefile atau GeoPackage"""
        file_path = filedialog.askopenfilename(
            title=f"Pilih Data {data_num}",
            filetypes=[
                ("Shapefile", "*.shp"),
                ("GeoPackage", "*.gpkg"),
                ("All GIS Files", "*.shp;*.gpkg"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            self.status_var.set(f"Membaca Data {data_num}...")
            self.root.update()
            
            # Read file with GeoPandas
            gdf = gpd.read_file(file_path)
            
            if gdf.empty:
                messagebox.showwarning("Warning", f"Data {data_num} kosong!")
                return
            
            # Store data
            if data_num == 1:
                self.gdf1 = gdf
                self.data1_path.set(os.path.basename(file_path))
            elif data_num == 2:
                self.gdf2 = gdf
                self.data2_path.set(os.path.basename(file_path))
            elif data_num == 3:
                self.gdf3 = gdf
                self.data3_path.set(os.path.basename(file_path))
            
            # Update map
            self.update_map()
            self.status_var.set(f"Data {data_num} berhasil dimuat ({len(gdf)} fitur)")
            messagebox.showinfo("Success", f"Data {data_num} berhasil dimuat!\n{len(gdf)} fitur ditemukan")
            
        except Exception as e:
            self.status_var.set(f"Error membaca Data {data_num}")
            messagebox.showerror("Error", f"Gagal membaca Data {data_num}:\n{str(e)}")
    
    def ensure_crs_match(self):
        """Samakan CRS semua data"""
        if self.gdf1 is not None:
            base_crs = self.gdf1.crs
            if self.gdf2 is not None and self.gdf2.crs != base_crs:
                self.gdf2 = self.gdf2.to_crs(base_crs)
            if self.gdf3 is not None and self.gdf3.crs != base_crs:
                self.gdf3 = self.gdf3.to_crs(base_crs)
    
    def run_clip(self):
        """Jalankan operasi CLIP"""
        if self.gdf1 is None or self.gdf3 is None:
            messagebox.showwarning("Warning", "Upload Data 1 dan Data 3 terlebih dahulu!")
            return
        
        try:
            self.status_var.set("Menjalankan CLIP...")
            self.root.update()
            
            self.ensure_crs_match()
            self.result = gpd.clip(self.gdf1, self.gdf3)
            self.result_info["name"] = "CLIP"
            
            if self.result.empty:
                messagebox.showwarning("Warning", "Hasil CLIP kosong! Cek geometri data.")
                return
            
            self.update_map()
            self.show_result_info()
            self.status_var.set(f"CLIP selesai ({len(self.result)} fitur)")
            messagebox.showinfo("Success", f"CLIP selesai!\n{len(self.result)} fitur dihasilkan")
            
        except Exception as e:
            self.status_var.set("Error CLIP")
            messagebox.showerror("Error", f"Gagal CLIP:\n{str(e)}")
    
    def run_dissolve(self):
        """Jalankan operasi DISSOLVE"""
        if self.gdf3 is None:
            messagebox.showwarning("Warning", "Upload Data 3 terlebih dahulu!")
            return
        
        try:
            self.status_var.set("Menjalankan DISSOLVE...")
            self.root.update()
            
            # Cari field untuk dissolve
            dissolve_field = None
            for field in ["WADMKK", "NAME", "ID", "CODE"]:
                if field in self.gdf3.columns:
                    dissolve_field = field
                    break
            
            if dissolve_field:
                self.result = self.gdf3.dissolve(by=dissolve_field)
                msg = f"DISSOLVE berdasarkan field '{dissolve_field}'"
            else:
                self.result = self.gdf3.dissolve()
                msg = "DISSOLVE tanpa field spesifik"
            
            self.result_info["name"] = "DISSOLVE"
            self.update_map()
            self.show_result_info()
            self.status_var.set(f"DISSOLVE selesai ({len(self.result)} fitur)")
            messagebox.showinfo("Success", f"{msg}\n{len(self.result)} fitur dihasilkan")
            
        except Exception as e:
            self.status_var.set("Error DISSOLVE")
            messagebox.showerror("Error", f"Gagal DISSOLVE:\n{str(e)}")
    
    def run_intersect(self):
        """Jalankan operasi INTERSECT"""
        if self.gdf1 is None or self.gdf2 is None:
            messagebox.showwarning("Warning", "Upload Data 1 dan Data 2 terlebih dahulu!")
            return
        
        try:
            self.status_var.set("Menjalankan INTERSECT...")
            self.root.update()
            
            self.ensure_crs_match()
            self.result = gpd.overlay(self.gdf1, self.gdf2, how="intersection")
            self.result_info["name"] = "INTERSECT"
            
            if self.result.empty:
                messagebox.showwarning("Warning", "Hasil INTERSECT kosong! Tidak ada overlap.")
                return
            
            # Hitung area
            self.result = self.result.to_crs(epsg=32750)  # UTM 50S
            self.result["area_m2"] = self.result.area
            self.result["area_ha"] = self.result["area_m2"] / 10000
            
            self.update_map()
            self.show_result_info()
            self.status_var.set(f"INTERSECT selesai ({len(self.result)} fitur)")
            messagebox.showinfo("Success", f"INTERSECT selesai!\n{len(self.result)} fitur dihasilkan")
            
        except Exception as e:
            self.status_var.set("Error INTERSECT")
            messagebox.showerror("Error", f"Gagal INTERSECT:\n{str(e)}")
    
    def run_union(self):
        """Jalankan operasi UNION"""
        if self.gdf1 is None or self.gdf2 is None:
            messagebox.showwarning("Warning", "Upload Data 1 dan Data 2 terlebih dahulu!")
            return
        
        try:
            self.status_var.set("Menjalankan UNION...")
            self.root.update()
            
            self.ensure_crs_match()
            self.result = gpd.overlay(self.gdf1, self.gdf2, how="union")
            self.result_info["name"] = "UNION"
            
            self.update_map()
            self.show_result_info()
            self.status_var.set(f"UNION selesai ({len(self.result)} fitur)")
            messagebox.showinfo("Success", f"UNION selesai!\n{len(self.result)} fitur dihasilkan")
            
        except Exception as e:
            self.status_var.set("Error UNION")
            messagebox.showerror("Error", f"Gagal UNION:\n{str(e)}")
    
    def update_map(self):
        """Update visualisasi peta"""
        self.ax.clear()
        
        try:
            # Plot semua layer
            if self.gdf1 is not None:
                self.gdf1.plot(ax=self.ax, alpha=0.3, color='blue', label='Data 1', edgecolor='black')
            
            if self.gdf2 is not None:
                self.gdf2.plot(ax=self.ax, alpha=0.3, color='green', label='Data 2', edgecolor='black')
            
            if self.gdf3 is not None:
                self.gdf3.plot(ax=self.ax, alpha=0.2, color='orange', label='Data 3', edgecolor='black', linewidth=2)
            
            # Plot result dengan warna merah
            if self.result is not None:
                self.result.plot(ax=self.ax, alpha=0.6, color='red', label='Hasil', edgecolor='darkred', linewidth=2)
            
            self.ax.set_title("Visualisasi Data Spasial", fontsize=12, fontweight='bold')
            self.ax.legend(loc='upper right', fontsize=9)
            self.ax.set_axis_off()
            
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Error: {str(e)}", 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=10, color='red')
        
        self.canvas.draw()
    
    def show_result_info(self):
        """Tampilkan informasi hasil di text widget"""
        info_text = f"""
╔═══════════════════════════════╗
║  INFORMASI HASIL              ║
╚═══════════════════════════════╝

Operasi: {self.result_info['name']}
Jumlah Fitur: {len(self.result)}

Kolom:
"""
        for i, col in enumerate(self.result.columns[:8]):
            info_text += f"  • {col}\n"
        
        if len(self.result.columns) > 8:
            info_text += f"  ... dan {len(self.result.columns) - 8} kolom lainnya\n"
        
        # Add geometry info
        geom_type = self.result.geometry.geom_type.unique()[0] if len(self.result) > 0 else "Unknown"
        info_text += f"\nTipe Geometri: {geom_type}"
        info_text += f"\nCRS: {self.result.crs}"
        
        # Add area info for intersect
        if "area_ha" in self.result.columns:
            total_area = self.result["area_ha"].sum()
            info_text += f"\nTotal Area (ha): {total_area:.2f}"
        
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", info_text)
    
    def save_result(self):
        """Simpan hasil ke file"""
        if self.result is None:
            messagebox.showwarning("Warning", "Tidak ada hasil untuk disimpan!")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".shp",
            filetypes=[
                ("Shapefile", "*.shp"),
                ("GeoPackage", "*.gpkg"),
                ("All files", "*.*")
            ]
        )
        
        if not save_path:
            return
        
        try:
            self.status_var.set("Menyimpan hasil...")
            self.root.update()
            
            self.result.to_file(save_path)
            self.status_var.set(f"Hasil disimpan ke {os.path.basename(save_path)}")
            messagebox.showinfo("Success", f"Hasil berhasil disimpan ke:\n{save_path}")
            
        except Exception as e:
            self.status_var.set("Error menyimpan")
            messagebox.showerror("Error", f"Gagal menyimpan:\n{str(e)}")
    
    def clear_all(self):
        """Bersihkan semua data"""
        if messagebox.askyesno("Konfirmasi", "Apakah Anda yakin ingin menghapus semua data?"):
            self.gdf1 = None
            self.gdf2 = None
            self.gdf3 = None
            self.result = None
            
            self.data1_path.set("Belum ada data")
            self.data2_path.set("Belum ada data")
            self.data3_path.set("Belum ada data")
            
            self.result_text.delete("1.0", tk.END)
            
            self.ax.clear()
            self.ax.text(0.5, 0.5, "Upload data untuk melihat visualisasi", 
                        ha='center', va='center', transform=self.ax.transAxes,
                        fontsize=12, color='gray')
            self.ax.set_axis_off()
            self.canvas.draw()
            
            self.status_var.set("Semua data dihapus")
            messagebox.showinfo("Info", "Semua data telah dihapus")

if __name__ == "__main__":
    root = tk.Tk()
    app = GeoprocessingGUI(root)
    root.mainloop()
