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

TARGET_CRS = 'EPSG:4326'

class AdvanceGeoApp:
    def __init__(self, root):
        self.root = root
        self.root.title('Advance Geoprocessing with Satellite Map')
        self.root.geometry('1400x800')
        # Data layers
        self.gdf1 = None
        self.gdf2 = None
        self.gdf3 = None
        self.result = None
        # file path vars
        self.data1_path = tk.StringVar(value='No data')
        self.data2_path = tk.StringVar(value='No data')
        self.data3_path = tk.StringVar(value='No data')
        self.init_ui()

    def init_ui(self):
        main_container = ttk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_container.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Left panel
        left_frame = ttk.Frame(main_container)
        main_container.add(left_frame, weight=1)

        title_label = ttk.Label(left_frame, text='🛠️ GEOPROCESSING TOOLS', font=('Arial', 12, 'bold'))
        title_label.pack(pady=10, padx=10)

        upload_frame = ttk.LabelFrame(left_frame, text='📂 Upload Data', padding=10)
        upload_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Label(upload_frame, text='Data 1 (Clip, Intersect, Union):', font=('Arial', 9)).pack(anchor=tk.W)
        ttk.Button(upload_frame, text='Upload Data 1', command=lambda: self.load_file(1)).pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data1_path, font=('Arial', 8), foreground='blue').pack(anchor=tk.W, padx=5)

        ttk.Label(upload_frame, text='Data 2 (Intersect, Union):', font=('Arial', 9)).pack(anchor=tk.W, pady=(10,0))
        ttk.Button(upload_frame, text='Upload Data 2', command=lambda: self.load_file(2)).pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data2_path, font=('Arial', 8), foreground='blue').pack(anchor=tk.W, padx=5)

        ttk.Label(upload_frame, text='Data 3 (Clip, Dissolve):', font=('Arial', 9)).pack(anchor=tk.W, pady=(10,0))
        ttk.Button(upload_frame, text='Upload Data 3', command=lambda: self.load_file(3)).pack(fill=tk.X, pady=2)
        ttk.Label(upload_frame, textvariable=self.data3_path, font=('Arial', 8), foreground='blue').pack(anchor=tk.W, padx=5)

        ops_frame = ttk.LabelFrame(left_frame, text='⚙️ Operasi Geoprocessing', padding=10)
        ops_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(ops_frame, text='Clip (Data1 clip by Data3)', command=self.run_clip).pack(fill=tk.X, pady=5)
        ttk.Button(ops_frame, text='Intersect (Data1 ∩ Data2)', command=self.run_intersect).pack(fill=tk.X, pady=5)
        ttk.Button(ops_frame, text='Union (Data1 ∪ Data2)', command=self.run_union).pack(fill=tk.X, pady=5)
        ttk.Button(ops_frame, text='Dissolve (Data3)', command=self.run_dissolve).pack(fill=tk.X, pady=5)

        result_frame = ttk.LabelFrame(left_frame, text='📊 Hasil', padding=10)
        result_frame.pack(fill=tk.X, padx=10, pady=10)

        ttk.Button(result_frame, text='Save Result', command=self.save_result).pack(fill=tk.X, pady=5)
        ttk.Button(result_frame, text='Clear All', command=self.clear_layers).pack(fill=tk.X, pady=5)

        # Right panel
        right_frame = ttk.Frame(main_container)
        main_container.add(right_frame, weight=3)

        self.fig = plt.Figure(figsize=(10, 8), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.draw_basemap()

    def draw_basemap(self):
        """Draw Basemap using 'cyl' projection and zoom to data bounds in EPSG:4326."""
        self.ax.clear()
        # default world bounds
        llcrnrlat, urcrnrlat, llcrnrlon, urcrnrlon = -80, 80, -180, 180

        # collect bounds in EPSG:4326
        bounds_list = []
        for gdf in (self.gdf1, self.gdf2, self.gdf3):
            if gdf is not None:
                try:
                    b = gdf.to_crs(TARGET_CRS).total_bounds
                    bounds_list.append(b)
                except Exception:
                    pass

        if bounds_list:
            all_bounds = bounds_list[0].copy()
            for b in bounds_list[1:]:
                all_bounds[0] = min(all_bounds[0], b[0])
                all_bounds[1] = min(all_bounds[1], b[1])
                all_bounds[2] = max(all_bounds[2], b[2])
                all_bounds[3] = max(all_bounds[3], b[3])

            pad = 0.1
            width = all_bounds[2] - all_bounds[0]
            height = all_bounds[3] - all_bounds[1]
            pad_lon = width * pad if width > 0 else 1
            pad_lat = height * pad if height > 0 else 1

            llcrnrlon = max(-180, all_bounds[0] - pad_lon)
            llcrnrlat = max(-80, all_bounds[1] - pad_lat)
            urcrnrlon = min(180, all_bounds[2] + pad_lon)
            urcrnrlat = min(80, all_bounds[3] + pad_lat)

        # Basemap with cylindrical projection so lon/lat align with axes
        self.m = Basemap(projection='cyl', llcrnrlat=llcrnrlat, urcrnrlat=urcrnrlat,
                         llcrnrlon=llcrnrlon, urcrnrlon=urcrnrlon, resolution='c', ax=self.ax)

        try:
            self.m.bluemarble(alpha=1.0)
        except Exception:
            self.m.fillcontinents(color='#2d5016', lake_color='#4d9ff2', alpha=0.6)

        self.m.drawcoastlines(linewidth=0.5, color='yellow')
        self.m.drawcountries(linewidth=0.5, color='white')
        self.m.drawstates(linewidth=0.3, color='gray', linestyle='--')
        self.m.drawrivers(linewidth=0.3, color='cyan')
        self.m.drawmapboundary(fill_color='#000000', linewidth=1)

        self.fig.patch.set_facecolor('#1a1a1a')
        self.ax.patch.set_facecolor('#1a1a1a')
        self.ax.set_title('Visualisasi Geoprocessing', fontsize=14, color='white', pad=10)

        self.plot_layers()
        self.canvas.draw()

    def ensure_crs(self, gdf):
        if gdf is None:
            return None
        if getattr(gdf, 'crs', None) is None:
            try:
                gdf = gdf.set_crs(TARGET_CRS, allow_override=True)
            except Exception:
                try:
                    gdf = gdf.set_crs('EPSG:4326', allow_override=True)
                except Exception:
                    pass
        try:
            gdf = gdf.to_crs(TARGET_CRS)
        except Exception:
            return gdf
        return gdf

    def load_file(self, data_num):
        file_path = filedialog.askopenfilename(filetypes=[('Shapefile', '*.shp')])
        if not file_path:
            return
        try:
            gdf = gpd.read_file(file_path)
            gdf = self.ensure_crs(gdf)
            name = os.path.basename(file_path)
            if data_num == 1:
                self.gdf1 = gdf
                self.data1_path.set(name)
            elif data_num == 2:
                self.gdf2 = gdf
                self.data2_path.set(name)
            else:
                self.gdf3 = gdf
                self.data3_path.set(name)
            self.draw_basemap()
            messagebox.showinfo('Success', f'Data {data_num} loaded: {name}')
        except Exception as e:
            messagebox.showerror('Error', f'Failed to load file: {e}')

    def plot_layers(self):
        layers = [
            (self.gdf1, 'Data1', 'red'),
            (self.gdf2, 'Data2', 'lime'),
            (self.gdf3, 'Data3', 'cyan'),
            (self.result, 'Result', 'magenta')
        ]

        for gdf, label, color in layers:
            if gdf is None:
                continue
            try:
                g = self.ensure_crs(gdf)
            except Exception:
                g = gdf
            # plot with zorder: result on top
            z = 5 if color == 'magenta' else 3
            a = 0.9 if color == 'magenta' else 0.6
            lw = 1.0 if color == 'magenta' else 0.5
            try:
                g.plot(ax=self.ax, color=color, alpha=a, edgecolor='black', linewidth=lw, zorder=z)
            except Exception:
                pass

    def run_clip(self):
        if self.gdf1 is None or self.gdf3 is None:
            messagebox.showinfo('Info', 'Upload Data 1 and Data 3 for Clip.')
            return
        try:
            a = self.ensure_crs(self.gdf1.copy())
            b = self.ensure_crs(self.gdf3.copy())
            self.result = gpd.clip(a, b)
            self.draw_basemap()
            messagebox.showinfo('Success', f'Clip complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Clip failed: {e}')

    def run_intersect(self):
        if self.gdf1 is None or self.gdf2 is None:
            messagebox.showinfo('Info', 'Upload Data 1 and Data 2 for Intersect.')
            return
        try:
            a = self.ensure_crs(self.gdf1.copy())
            b = self.ensure_crs(self.gdf2.copy())
            self.result = gpd.overlay(a, b, how='intersection')
            self.draw_basemap()
            messagebox.showinfo('Success', f'Intersect complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Intersect failed: {e}')

    def run_union(self):
        if self.gdf1 is None or self.gdf2 is None:
            messagebox.showinfo('Info', 'Upload Data 1 and Data 2 for Union.')
            return
        try:
            a = self.ensure_crs(self.gdf1.copy())
            b = self.ensure_crs(self.gdf2.copy())
            self.result = gpd.overlay(a, b, how='union')
            self.draw_basemap()
            messagebox.showinfo('Success', f'Union complete: {len(self.result)} features')
        except Exception as e:
            messagebox.showerror('Error', f'Union failed: {e}')

    def run_dissolve(self):
        if self.gdf3 is None:
            messagebox.showwarning('Warning', 'Upload Data 3 terlebih dahulu!')
            return

        try:
            # Ensure CRS and work on a copy
            gdf = self.ensure_crs(self.gdf3.copy())

            # Try to find a reasonable field to dissolve by; otherwise dissolve all geometries
            dissolve_field = None
            for field in ["WADMKK", "NAME", "ID", "CODE", "id", "name"]:
                if field in gdf.columns:
                    dissolve_field = field
                    break

            if dissolve_field:
                res = gdf.dissolve(by=dissolve_field)
                # make the dissolve field a column again if possible
                try:
                    res = res.reset_index()
                except Exception:
                    pass
                msg = f"Dissolve berdasarkan field '{dissolve_field}'"
            else:
                res = gdf.dissolve()
                try:
                    res = res.reset_index(drop=True)
                except Exception:
                    pass
                msg = "Dissolve tanpa field spesifik"

            # Set result and refresh map
            self.result = res
            self.draw_basemap()
            messagebox.showinfo('Success', f'{msg}\\n{len(self.result)} fitur dihasilkan')

        except Exception as e:
            messagebox.showerror('Error', f'Dissolve failed: {e}')

    def save_result(self):
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
        self.gdf1 = None
        self.gdf2 = None
        self.gdf3 = None
        self.result = None
        self.data1_path.set('No data')
        self.data2_path.set('No data')
        self.data3_path.set('No data')
        self.draw_basemap()
        messagebox.showinfo('Success', 'All layers cleared')


if __name__ == '__main__':
    root = tk.Tk()
    app = AdvanceGeoApp(root)
    root.mainloop()
