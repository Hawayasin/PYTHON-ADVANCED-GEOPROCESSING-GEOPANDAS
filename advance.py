import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.basemap import Basemap
import geopandas as gpd
import os
import warnings

warnings.filterwarnings('ignore')

class AdvanceGeoApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Advance Geoprocessing with Satellite Map')
        self.root.geometry('1400x800')
        # Data layers: Data 1, Data 2, Data 3
        self.gdf1 = None
        self.gdf2 = None
        self.gdf3 = None
        self.result = None
        # File path display
        self.data1_path = tk.StringVar(value="No data")
        self.data2_path = tk.StringVar(value="No data")
        self.data3_path = tk.StringVar(value="No data")
        self.init_ui()

    def init_ui(self):
        # Main container with left (tools) and right (map) panels
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ===== LEFT PANEL: TOOLS & CONTROLS =====
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)
        
        # Title
        title_label = ttk.Label(left_frame, text="🛠️ GEOPROCESSING TOOLS", font=("Arial", 12, "bold"))
        title_label.pack(pady=10, padx=10)
        
        # Data Upload Section
        upload_frame = ttk.LabelFrame(left_frame, text="📂 Upload Data", padding=10)
        upload_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # Data 1 button and label
        ttk.Label(upload_frame, text="Data 1 (Clip, Intersect, Union):", font=("Arial", 9)).pack(anchor=tk.W)
        ttk.Button(upload_frame, text="Upload Data 1", command=lambda: self.load_file(1)).pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data1_path, font=("Arial", 8), foreground="blue").pack(anchor=tk.W, padx=5)
        
        # Data 2 button and label
        ttk.Label(upload_frame, text="Data 2 (Intersect, Union):", font=("Arial", 9)).pack(anchor=tk.W, pady=(10,0))
        ttk.Button(upload_frame, text="Upload Data 2", command=lambda: self.load_file(2)).pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data2_path, font=("Arial", 8), foreground="blue").pack(anchor=tk.W, padx=5)
        
        # Data 3 button and label
        ttk.Label(upload_frame, text="Data 3 (Clip, Dissolve):", font=("Arial", 9)).pack(anchor=tk.W, pady=(10,0))
        ttk.Button(upload_frame, text="Upload Data 3", command=lambda: self.load_file(3)).pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data3_path, font=("Arial", 8), foreground="blue").pack(anchor=tk.W, padx=5)
        
        # Geoprocessing Operations
        ops_frame = ttk.LabelFrame(left_frame, text="⚙️ Operasi Geoprocessing", padding=10)
        ops_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(ops_frame, text="Clip (Data1 clip by Data3)", command=self.run_clip).pack(fill=tk.X, pady=5)
        ttk.Button(ops_frame, text="Intersect (Data1 ∩ Data2)", command=self.run_intersect).pack(fill=tk.X, pady=5)
        ttk.Button(ops_frame, text="Union (Data1 ∪ Data2)", command=self.run_union).pack(fill=tk.X, pady=5)
        ttk.Button(ops_frame, text="Dissolve (Data1)", command=self.run_dissolve).pack(fill=tk.X, pady=5)
        
        # Result & Export
        result_frame = ttk.LabelFrame(left_frame, text="📊 Hasil", padding=10)
        result_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(result_frame, text="Save Result", command=self.save_result).pack(fill=tk.X, pady=5)
        ttk.Button(result_frame, text="Clear All", command=self.clear_layers).pack(fill=tk.X, pady=5)
        
        # ===== RIGHT PANEL: MAP CANVAS =====
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=3)
        
        self.fig = plt.Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        self.draw_basemap()

    def draw_basemap(self):
        """Draw Basemap with Blue Marble and auto-zoom to data bounds if data exists."""
        self.ax.clear()
        
        # Determine map bounds based on uploaded data
        llcrnrlat, urcrnrlat, llcrnrlon, urcrnrlon = -80, 80, -180, 180
        
        if self.gdf1 is not None or self.gdf2 is not None or self.gdf3 is not None:
            # Collect all bounds from loaded data
            bounds_list = []
            for gdf in [self.gdf1, self.gdf2, self.gdf3]:
                if gdf is not None:
                    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
                    bounds_list.append(bounds)
            
            if bounds_list:
                # Calculate overall bounds with a small padding
                all_bounds = bounds_list[0]
                for bounds in bounds_list[1:]:
                    all_bounds = [min(all_bounds[0], bounds[0]), min(all_bounds[1], bounds[1]),
                                 max(all_bounds[2], bounds[2]), max(all_bounds[3], bounds[3])]
                
                pad = 0.1  # 10% padding
                width = all_bounds[2] - all_bounds[0]
                height = all_bounds[3] - all_bounds[1]
                pad_lon = width * pad if width > 0 else 1
                pad_lat = height * pad if height > 0 else 1
                
                llcrnrlon = max(-180, all_bounds[0] - pad_lon)
                llcrnrlat = max(-80, all_bounds[1] - pad_lat)
                urcrnrlon = min(180, all_bounds[2] + pad_lon)
                urcrnrlat = min(80, all_bounds[3] + pad_lat)
        
        # Create Basemap with computed bounds
        self.m = Basemap(projection='merc',
                        llcrnrlat=llcrnrlat, urcrnrlat=urcrnrlat,
                        llcrnrlon=llcrnrlon, urcrnrlon=urcrnrlon,
                        resolution='c', ax=self.ax)
        
        # Draw satellite imagery
        try:
            self.m.bluemarble(alpha=1.0)
        except Exception:
            self.m.fillcontinents(color='#2d5016', lake_color='#4d9ff2', alpha=0.6)
        
        # Draw vector features
        self.m.drawcoastlines(linewidth=0.5, color='yellow')
        self.m.drawcountries(linewidth=0.5, color='white')
        self.m.drawstates(linewidth=0.3, color='gray', linestyle='--')
        self.m.drawrivers(linewidth=0.3, color='cyan')
        self.m.drawmapboundary(fill_color='#000000', linewidth=1)
        
        # Styling
        self.fig.patch.set_facecolor('#1a1a1a')
        self.ax.patch.set_facecolor('#1a1a1a')
        self.ax.set_title('Visualisasi Geoprocessing', fontsize=14, color='white', pad=10)
        
        # Plot overlay layers
        self.plot_layers()
        self.canvas.draw()

    def load_file(self, data_num):
        """Load a shapefile for Data 1, 2, or 3."""
        file_path = filedialog.askopenfilename(filetypes=[('Shapefile', '*.shp'), ('GeoPackage', '*.gpkg')])
        if not file_path:
            return
        try:
            gdf = gpd.read_file(file_path)
            file_name = os.path.basename(file_path)
            
            if data_num == 1:
                self.gdf1 = gdf
                self.data1_path.set(file_name)
            elif data_num == 2:
                self.gdf2 = gdf
                self.data2_path.set(file_name)
            elif data_num == 3:
                self.gdf3 = gdf
                self.data3_path.set(file_name)
            
            self.draw_basemap()
            messagebox.showinfo('Success', f'Data {data_num} loaded: {file_name}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load file: {e}')

    def plot_layers(self):
        """Overlay Data 1, 2, 3 and result on the map."""
        colors = ['red', 'lime', 'cyan', 'magenta']
        layers_to_plot = [
            (self.gdf1, 'Data 1 (Red)', 'red'),
            (self.gdf2, 'Data 2 (Green)', 'lime'),
            (self.gdf3, 'Data 3 (Cyan)', 'cyan'),
            (self.result, 'Result (Magenta)', 'magenta')
        ]
        
        for gdf, label, color in layers_to_plot:
            if gdf is not None:
                try:
                    # Try to reproject to map CRS if needed (best-effort)
                    if hasattr(self, 'm') and hasattr(self.m, 'crs') and getattr(gdf, 'crs', None) is not None:
                        try:
                            # Use the same CRS as the GeoDataFrame if compatible
                            if gdf.crs != self.m.crs:
                                gdf = gdf.to_crs(gdf.crs)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Plot with z-order so result is always on top
                if color == 'magenta':
                    z = 5
                    a = 0.9
                    lw = 1.0
                else:
                    z = 3
                    a = 0.6
                    lw = 0.5

                gdf.plot(ax=self.ax, color=color, alpha=a, edgecolor='black', linewidth=lw, zorder=z)

        # Redraw canvas after plotting
        self.canvas.draw()

    def run_clip(self):
        """Clip Data 1 by Data 3."""
        if self.gdf1 is None or self.gdf3 is None:
            messagebox.showinfo('Info', 'Upload Data 1 and Data 3 for Clip.')
            return
        try:
            # Ensure same CRS
            gdf1 = self.gdf1.copy()
            gdf3 = self.gdf3.copy()
            if gdf1.crs != gdf3.crs:
                gdf3 = gdf3.to_crs(gdf1.crs)
            
            self.result = gpd.clip(gdf1, gdf3)
            self.draw_basemap()
            messagebox.showinfo('Success', f'Clip complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Clip failed: {e}')

    def run_intersect(self):
        """Intersect Data 1 and Data 2."""
        if self.gdf1 is None or self.gdf2 is None:
            messagebox.showinfo('Info', 'Upload Data 1 and Data 2 for Intersect.')
            return
        try:
            # Ensure same CRS
            gdf1 = self.gdf1.copy()
            gdf2 = self.gdf2.copy()
            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)
            
            self.result = gpd.overlay(gdf1, gdf2, how='intersection')
            self.draw_basemap()
            messagebox.showinfo('Success', f'Intersect complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Intersect failed: {e}')

    def run_union(self):
        """Union Data 1 and Data 2."""
        if self.gdf1 is None or self.gdf2 is None:
            messagebox.showinfo('Info', 'Upload Data 1 and Data 2 for Union.')
            return
        try:
            # Ensure same CRS
            gdf1 = self.gdf1.copy()
            gdf2 = self.gdf2.copy()
            if gdf1.crs != gdf2.crs:
                gdf2 = gdf2.to_crs(gdf1.crs)
            
            self.result = gpd.overlay(gdf1, gdf2, how='union')
            self.draw_basemap()
            messagebox.showinfo('Success', f'Union complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Union failed: {e}')

    def run_dissolve(self):
        """Dissolve Data 1."""
        if self.gdf1 is None:
            messagebox.showinfo('Info', 'Upload Data 1 for Dissolve.')
            return
        try:
            self.result = self.gdf1.dissolve()
            self.draw_basemap()
            messagebox.showinfo('Success', f'Dissolve complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Dissolve failed: {e}')

    def save_result(self):
        """Save result to a shapefile."""
        if self.result is None:
            messagebox.showinfo('Info', 'No result to save. Run a geoprocessing operation first.')
            return
        file_path = filedialog.asksaveasfilename(defaultextension='.shp', filetypes=[('Shapefile', '*.shp'), ('GeoPackage', '*.gpkg')])
        if not file_path:
            return
        try:
            self.result.to_file(file_path)
            messagebox.showinfo('Success', f'Result saved to {os.path.basename(file_path)}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to save: {e}')

    def clear_layers(self):
        """Clear all data layers."""
        self.gdf1 = None
        self.gdf2 = None
        self.gdf3 = None
        self.result = None
        self.data1_path.set("No data")
        self.data2_path.set("No data")
        self.data3_path.set("No data")
        self.draw_basemap()
        messagebox.showinfo('Success', 'All layers cleared')

if __name__ == '__main__':
    root = tk.Tk()
    app = AdvanceGeoApp(root)
    root.mainloop()
