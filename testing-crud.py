import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon
from shapely.ops import unary_union
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import pandas as pd
from pyproj import Transformer

class GISApp:
    def __init__(self, root):
        self.root = root
        self.root.title("GIS Spatial Operations - Interactive Drawing")
        self.root.geometry("1600x900")
        
        # Penyimpanan Data
        self.gdf = gpd.GeoDataFrame(columns=['id', 'type', 'geometry', 'area_m2', 'area_ha'], 
                                    geometry='geometry', crs="EPSG:4326")
        self.current_id = 0
        self.current_crs = "EPSG:4326"
        
        # Penggambaran Sementara
        self.drawing_mode = None  # 'point', 'line', 'polygon'
        self.temp_points = []
        self.is_drawing = False
        
        self.setup_ui()
        
    def setup_ui(self):
        # Konten utama
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Panel konten kiri menggunakan scrollbar (untuk overflow konten)
        left_container = tk.Frame(main_frame, width=200, relief=tk.RAISED, borderwidth=2)
        left_container.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 5))
        left_container.pack_propagate(False)
        
        # Panel kanan tampa scrollbar
        right_panel_container = tk.Frame(main_frame, width=350, relief=tk.RAISED, borderwidth=2)
        right_panel_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))
        right_panel_container.pack_propagate(False)
        
        # Panel kiri dengan scrollbar
        left_canvas = tk.Canvas(left_container, width=280)
        scrollbar = tk.Scrollbar(left_container, orient="vertical", command=left_canvas.yview)
        left_frame = tk.Frame(left_canvas)
        
        left_frame.bind(
            "<Configure>",
            lambda e: left_canvas.configure(scrollregion=left_canvas.bbox("all"))
        )
        
        left_canvas.create_window((0, 0), window=left_frame, anchor="nw")
        left_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Scrollar panel kanan 
        left_canvas.pack(side="left", fill="both", expand=True)
        
        # Fungsi untuk menghandle mouse wheel pada panel kiri, tkinter handling berkebalikan dengan perintah 
        def _on_mousewheel_left(event):
            left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        # Mouse whell akan binding ketika crusor di taruh di sebelah kiri
        left_canvas.bind("<Enter>", lambda e: left_canvas.bind_all("<MouseWheel>", _on_mousewheel_left))
        left_canvas.bind("<Leave>", lambda e: left_canvas.unbind_all("<MouseWheel>"))
        
        # Setting PANEL KANAN 
        right_panel = tk.Frame(right_panel_container)
        right_panel.pack(fill="both", expand=True)
        
        # Kontainer PANEL KANAN
        right_container = tk.Frame(main_frame)
        right_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Map panel (top right)
        map_frame = tk.Frame(right_container, relief=tk.SUNKEN, borderwidth=2)
        map_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Table panel (bottom right)
        table_frame = tk.Frame(right_container, height=200, relief=tk.SUNKEN, borderwidth=2)
        table_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, padx=(0, 0), pady=(5, 0))
        
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_panel)
        self.setup_map_panel(map_frame)
        self.setup_table_panel(table_frame)
        
    def setup_left_panel(self, parent):
        # CREATE Panel
        create_frame = tk.LabelFrame(parent, text="CREATE Feature", padx=10, pady=10, 
                                    font=('Arial', 10, 'bold'))
        create_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(create_frame, text="Click on map to draw:", font=('Arial', 9)).pack(anchor=tk.W, pady=(0, 5))
        
        btn_width = 22
        self.btn_point = tk.Button(create_frame, text="Draw Point", 
                                command=lambda: self.set_drawing_mode('point'),
                                bg="#4CAF50", fg="white", width=btn_width)
        self.btn_point.pack(pady=2)
        
        self.btn_line = tk.Button(create_frame, text="Draw Line", 
                                command=lambda: self.set_drawing_mode('line'),
                                bg="#2196F3", fg="white", width=btn_width)
        self.btn_line.pack(pady=2)
        
        self.btn_polygon = tk.Button(create_frame, text="Draw Polygon", 
                                    command=lambda: self.set_drawing_mode('polygon'),
                                    bg="#FF9800", fg="white", width=btn_width)
        self.btn_polygon.pack(pady=2)
        
        tk.Button(create_frame, text="Finish Drawing", 
                command=self.finish_drawing,
                bg="#9C27B0", fg="white", width=btn_width).pack(pady=5)
        
        tk.Label(create_frame, text="Status:", font=('Arial', 9, 'bold')).pack(anchor=tk.W, pady=(10, 0))
        self.status_label = tk.Label(create_frame, text="Ready", fg="green", 
                                    font=('Arial', 8), wraplength=250, justify=tk.LEFT)
        self.status_label.pack(anchor=tk.W)
        
        # READ Panel
        read_frame = tk.LabelFrame(parent, text="READ Data", padx=10, pady=10,
                                font=('Arial', 10, 'bold'))
        read_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(read_frame, text="Refresh Table", command=self.read_data,
                bg="#00BCD4", fg="white", width=btn_width).pack(pady=2)
        
        # Add Feature X,Y Panel
        coord_frame = tk.LabelFrame(parent, text="Add Feature X, Y", padx=10, pady=10,
                                    font=('Arial', 10, 'bold'))
        coord_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Label(coord_frame, text="X (Longitude):", font=('Arial', 8)).pack(anchor=tk.W)
        self.x_entry = tk.Entry(coord_frame, width=25)
        self.x_entry.pack(pady=2)
        
        tk.Label(coord_frame, text="Y (Latitude):", font=('Arial', 8)).pack(anchor=tk.W)
        self.y_entry = tk.Entry(coord_frame, width=25)
        self.y_entry.pack(pady=2)
        
        tk.Button(coord_frame, text="Add Point", command=self.add_point_xy,
                bg="#4CAF50", fg="white", width=20).pack(pady=5)
        
        # Calculate Geometry Panel
        calc_frame = tk.LabelFrame(parent, text="Calculate Geometry", padx=10, pady=10,
                                font=('Arial', 10, 'bold'))
        calc_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.calc_label = tk.Label(calc_frame, text="Luasan:\n- m²: 0\n- ha: 0", 
                                justify=tk.LEFT, fg="blue", font=('Arial', 9))
        self.calc_label.pack(anchor=tk.W)
        
        tk.Button(calc_frame, text="Calculate All Features", 
                command=self.calculate_geometry,
                bg="#009688", fg="white", width=20).pack(pady=5)
        
        # CRS Operations Panel
        crs_frame = tk.LabelFrame(parent, text="CRS Operations", padx=10, pady=10,
                                font=('Arial', 10, 'bold'))
        crs_frame.pack(fill=tk.X, padx=5, pady=5)
        
        tk.Button(crs_frame, text="WGS84 → UTM", 
                command=self.convert_to_utm,
                bg="#3F51B5", fg="white", width=20).pack(pady=2)
        
        self.crs_label = tk.Label(crs_frame, text=f"Current CRS:\n{self.current_crs}", 
                                fg="darkblue", font=('Arial', 8), justify=tk.LEFT)
        self.crs_label.pack(anchor=tk.W, pady=5)
        
        tk.Button(crs_frame, text="Clear All Data", 
                command=self.clear_all_data,
                bg="#F44336", fg="white", width=20).pack(pady=2)
    
    def setup_right_panel(self, parent):
        # Result Panel - NO SCROLLBAR for mouse wheel
        result_frame = tk.LabelFrame(parent, text="RESULT - Feature Attributes", padx=10, pady=10,
                                    font=('Arial', 10, 'bold'))
        result_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # ScrolledText for displaying results (scrollbar is there, but no mouse wheel binding)
        self.result_text = scrolledtext.ScrolledText(result_frame, 
                                                    wrap=tk.WORD, 
                                                    width=40, 
                                                    height=35,
                                                    font=('Courier', 9),
                                                    bg='#f9f9f9',
                                                    fg='#333333')
        self.result_text.pack(fill=tk.BOTH, expand=True)
        
        # Initial message
        self.result_text.insert(tk.END, "Click 'Refresh Table' to display feature attributes\n")
        self.result_text.insert(tk.END, "=" * 45 + "\n\n")
        self.result_text.config(state=tk.DISABLED)
        
    def setup_map_panel(self, parent):
        # Title
        title_label = tk.Label(parent, text="Interactive Map (Click to Draw)", 
                            font=('Arial', 11, 'bold'), bg='lightgray')
        title_label.pack(fill=tk.X, pady=(0, 5))
        
        # Matplotlib figure with Cartopy
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.ax = self.fig.add_subplot(111, projection=ccrs.PlateCarree())
        
        # Add map features
        self.ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
        self.ax.add_feature(cfeature.OCEAN, facecolor='#e6f2ff')
        self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        self.ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':')
        self.ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False, 
                        linewidth=0.5, alpha=0.5)
        
        # Set initial extent (Indonesia region)
        self.ax.set_extent([95, 141, -11, 6], crs=ccrs.PlateCarree())
        self.ax.set_title("Map View - EPSG:4326", fontsize=10)
        
        # Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, parent)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Connect mouse events
        self.canvas.mpl_connect('button_press_event', self.on_map_click)
        
        # Toolbar for pan/zoom
        toolbar = NavigationToolbar2Tk(self.canvas, parent)
        toolbar.update()
        
    def setup_table_panel(self, parent):
        # Title
        title_label = tk.Label(parent, text="Data Table", 
                            font=('Arial', 10, 'bold'), bg='lightgray')
        title_label.pack(fill=tk.X)
        
        # Create Treeview
        columns = ('ID', 'Type', 'Area (m²)', 'Area (ha)', 'Coordinates')
        self.tree = ttk.Treeview(parent, columns=columns, show='headings', height=8)
        
        # Define headings
        self.tree.heading('ID', text='ID')
        self.tree.heading('Type', text='Type')
        self.tree.heading('Area (m²)', text='Area (m²)')
        self.tree.heading('Area (ha)', text='Area (ha)')
        self.tree.heading('Coordinates', text='Coordinates')
        
        # Define column widths
        self.tree.column('ID', width=50, anchor=tk.CENTER)
        self.tree.column('Type', width=100, anchor=tk.CENTER)
        self.tree.column('Area (m²)', width=120, anchor=tk.CENTER)
        self.tree.column('Area (ha)', width=120, anchor=tk.CENTER)
        self.tree.column('Coordinates', width=400, anchor=tk.W)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
    def set_drawing_mode(self, mode):
        self.drawing_mode = mode
        self.temp_points = []
        self.is_drawing = True
        
        # Update button colors
        self.btn_point.config(bg="#4CAF50")
        self.btn_line.config(bg="#2196F3")
        self.btn_polygon.config(bg="#FF9800")
        
        if mode == 'point':
            self.btn_point.config(bg="#1B5E20")
            self.status_label.config(text="Click on map to add Point")
        elif mode == 'line':
            self.btn_line.config(bg="#0D47A1")
            self.status_label.config(text="Click on map to add Line vertices. Click 'Finish Drawing' when done.")
        elif mode == 'polygon':
            self.btn_polygon.config(bg="#E65100")
            self.status_label.config(text="Click on map to add Polygon vertices. Click 'Finish Drawing' when done.")
    
    def on_map_click(self, event):
        if not self.is_drawing or event.inaxes != self.ax:
            return
        
        x, y = event.xdata, event.ydata
        
        if self.drawing_mode == 'point':
            self.temp_points = [(x, y)]
            self.finish_drawing()
        elif self.drawing_mode in ['line', 'polygon']:
            self.temp_points.append((x, y))
            # Plot temporary point
            self.ax.plot(x, y, 'ro', markersize=5, transform=ccrs.PlateCarree())
            self.canvas.draw()
            self.status_label.config(text=f"Points added: {len(self.temp_points)}")
    
    def finish_drawing(self):
        if not self.temp_points:
            messagebox.showwarning("Warning", "No points to create geometry")
            return
        
        try:
            if self.drawing_mode == 'point':
                if len(self.temp_points) != 1:
                    raise ValueError("Point requires 1 coordinate")
                geom = Point(self.temp_points[0])
                geom_type = "Point"
                
            elif self.drawing_mode == 'line':
                if len(self.temp_points) < 2:
                    raise ValueError("Line requires at least 2 points")
                geom = LineString(self.temp_points)
                geom_type = "Line"
                
            elif self.drawing_mode == 'polygon':
                if len(self.temp_points) < 3:
                    raise ValueError("Polygon requires at least 3 points")
                geom = Polygon(self.temp_points)
                geom_type = "Polygon"
            else:
                return
            
            # Calculate area
            area_m2, area_ha = self.calculate_area(geom)
            
            # Add to GeoDataFrame
            new_row = gpd.GeoDataFrame({
                'id': [self.current_id],
                'type': [geom_type],
                'geometry': [geom],
                'area_m2': [area_m2],
                'area_ha': [area_ha]
            }, crs=self.current_crs)
            
            self.gdf = pd.concat([self.gdf, new_row], ignore_index=True)
            self.current_id += 1
            
            # Reset drawing state
            self.temp_points = []
            self.is_drawing = False
            self.drawing_mode = None
            
            # Reset button colors
            self.btn_point.config(bg="#4CAF50")
            self.btn_line.config(bg="#2196F3")
            self.btn_polygon.config(bg="#FF9800")
            
            self.status_label.config(text=f"{geom_type} created successfully!")
            self.update_map()
            self.read_data()
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create geometry: {str(e)}")
    
    def add_point_xy(self):
        try:
            x = float(self.x_entry.get())
            y = float(self.y_entry.get())
            
            geom = Point(x, y)
            area_m2, area_ha = self.calculate_area(geom)
            
            new_row = gpd.GeoDataFrame({
                'id': [self.current_id],
                'type': ["Point"],
                'geometry': [geom],
                'area_m2': [area_m2],
                'area_ha': [area_ha]
            }, crs=self.current_crs)
            
            self.gdf = pd.concat([self.gdf, new_row], ignore_index=True)
            self.current_id += 1
            
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)
            
            self.update_map()
            self.read_data()
            messagebox.showinfo("Success", "Point added successfully!")
            
        except ValueError:
            messagebox.showerror("Error", "Please enter valid X and Y coordinates")
    
    def calculate_area(self, geom):
        """Calculate area in m² and ha based on current CRS"""
        if geom.geom_type in ['Point', 'LineString']:
            return 0, 0
        
        if self.current_crs == "EPSG:4326":
            # Rough conversion for WGS84 (degrees to meters)
            area_m2 = geom.area * 111320 * 111320
        else:
            # For UTM, area is already in m²
            area_m2 = geom.area
        
        area_ha = area_m2 / 10000
        return area_m2, area_ha
    
    def calculate_geometry(self):
        if self.gdf.empty:
            messagebox.showinfo("Info", "No geometries available")
            return
        
        total_area_m2 = self.gdf['area_m2'].sum()
        total_area_ha = self.gdf['area_ha'].sum()
        
        calc_text = f"Total Luasan:\n- m²: {total_area_m2:.2f}\n- ha: {total_area_ha:.4f}"
        self.calc_label.config(text=calc_text)
    
    def read_data(self):
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Clear result text
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete(1.0, tk.END)
        
        if self.gdf.empty:
            self.result_text.insert(tk.END, "No features available\n")
            self.result_text.insert(tk.END, "=" * 45 + "\n")
            self.result_text.config(state=tk.DISABLED)
            return
        
        # Header for result
        self.result_text.insert(tk.END, "FEATURE ATTRIBUTES\n")
        self.result_text.insert(tk.END, "=" * 45 + "\n\n")
        
        # Populate table and result text
        for idx, row in self.gdf.iterrows():
            coords = str(row['geometry'].coords[:] if hasattr(row['geometry'], 'coords') else row['geometry'])
            if len(coords) > 50:
                coords_display = coords[:50] + "..."
            else:
                coords_display = coords
            
            # Add to table
            self.tree.insert('', tk.END, values=(
                row['id'],
                row['type'],
                f"{row['area_m2']:.2f}",
                f"{row['area_ha']:.4f}",
                coords_display
            ))
            
            # Add to result text
            self.result_text.insert(tk.END, f"Feature ID: {row['id']}\n")
            self.result_text.insert(tk.END, f"Type: {row['type']}\n")
            self.result_text.insert(tk.END, f"Area (m²): {row['area_m2']:.2f}\n")
            self.result_text.insert(tk.END, f"Area (ha): {row['area_ha']:.4f}\n")
            self.result_text.insert(tk.END, f"CRS: {self.current_crs}\n")
            
            # ENHANCED: Display ALL coordinates for polygons with 2+ vertices
            if hasattr(row['geometry'], 'coords'):
                coord_list = list(row['geometry'].coords)
                self.result_text.insert(tk.END, f"Coordinates ({len(coord_list)} points):\n")
                for i, coord in enumerate(coord_list):
                    self.result_text.insert(tk.END, f"  {i+1}. ({coord[0]:.6f}, {coord[1]:.6f})\n")
            elif row['geometry'].geom_type == 'Polygon':
                # For Polygon, get exterior coordinates
                coord_list = list(row['geometry'].exterior.coords)
                self.result_text.insert(tk.END, f"Polygon Coordinates ({len(coord_list)} vertices):\n")
                for i, coord in enumerate(coord_list):
                    self.result_text.insert(tk.END, f"  {i+1}. ({coord[0]:.6f}, {coord[1]:.6f})\n")
                
                # If polygon has interior rings (holes), display them too
                if len(row['geometry'].interiors) > 0:
                    self.result_text.insert(tk.END, f"\nInterior Rings (Holes): {len(row['geometry'].interiors)}\n")
                    for ring_idx, interior in enumerate(row['geometry'].interiors):
                        interior_coords = list(interior.coords)
                        self.result_text.insert(tk.END, f"  Ring {ring_idx+1} ({len(interior_coords)} points):\n")
                        for i, coord in enumerate(interior_coords):
                            self.result_text.insert(tk.END, f"    {i+1}. ({coord[0]:.6f}, {coord[1]:.6f})\n")
            else:
                self.result_text.insert(tk.END, f"Geometry: {row['geometry']}\n")
            
            self.result_text.insert(tk.END, "-" * 45 + "\n\n")
        
        # Ringkasan hasil read data 
        total_features = len(self.gdf)
        total_area_m2 = self.gdf['area_m2'].sum()
        total_area_ha = self.gdf['area_ha'].sum()
        
        self.result_text.insert(tk.END, "SUMMARY\n")
        self.result_text.insert(tk.END, "=" * 45 + "\n")
        self.result_text.insert(tk.END, f"Total Features: {total_features}\n")
        self.result_text.insert(tk.END, f"Total Area (m²): {total_area_m2:.2f}\n")
        self.result_text.insert(tk.END, f"Total Area (ha): {total_area_ha:.4f}\n")
        
        self.result_text.config(state=tk.DISABLED)
    
    def convert_to_utm(self):
        if self.gdf.empty:
            messagebox.showinfo("Info", "No data to convert")
            return
        
        try:
            if self.current_crs == "EPSG:4326":
                # Determine UTM zone from first geometry centroid
                first_geom = self.gdf.iloc[0]['geometry']
                lon = first_geom.centroid.x
                
                # Calculate UTM zone
                utm_zone = int((lon + 180) / 6) + 1
                # Determine hemisphere
                lat = first_geom.centroid.y
                epsg_code = 32600 + utm_zone if lat >= 0 else 32700 + utm_zone
                
                target_crs = f"EPSG:{epsg_code}"
                self.gdf = self.gdf.to_crs(target_crs)
                self.current_crs = target_crs
                
                # Recalculate areas
                for idx, row in self.gdf.iterrows():
                    area_m2, area_ha = self.calculate_area(row['geometry'])
                    self.gdf.at[idx, 'area_m2'] = area_m2
                    self.gdf.at[idx, 'area_ha'] = area_ha
                
                self.crs_label.config(text=f"Current CRS:\n{self.current_crs}")
                self.ax.set_title(f"Map View - {self.current_crs}", fontsize=10)
                self.update_map()
                self.read_data()
                messagebox.showinfo("Success", f"CRS converted to {target_crs}")
            else:
                messagebox.showinfo("Info", "Already in UTM projection")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to convert CRS: {str(e)}")
    
    def clear_all_data(self):
        if messagebox.askyesno("Confirm", "Are you sure you want to clear all data?"):
            self.gdf = gpd.GeoDataFrame(columns=['id', 'type', 'geometry', 'area_m2', 'area_ha'], 
                                         geometry='geometry', crs="EPSG:4326")
            self.current_id = 0
            self.current_crs = "EPSG:4326"
            self.temp_points = []
            self.is_drawing = False
            self.drawing_mode = None
            
            self.crs_label.config(text=f"Current CRS:\n{self.current_crs}")
            self.calc_label.config(text="Luasan:\n- m²: 0\n- ha: 0")
            self.status_label.config(text="Ready")
            
            # Clear result text
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(tk.END, "All data cleared\n")
            self.result_text.insert(tk.END, "=" * 45 + "\n")
            self.result_text.config(state=tk.DISABLED)
            
            # Reset button colors
            self.btn_point.config(bg="#4CAF50")
            self.btn_line.config(bg="#2196F3")
            self.btn_polygon.config(bg="#FF9800")
            
            self.update_map()
            self.read_data()
            messagebox.showinfo("Success", "All data cleared")
    
    def update_map(self):
        # Clear previous plots
        self.ax.clear()
        
        # Re-add map features
        self.ax.add_feature(cfeature.LAND, facecolor='#f0f0f0')
        self.ax.add_feature(cfeature.OCEAN, facecolor='#e6f2ff')
        self.ax.add_feature(cfeature.COASTLINE, linewidth=0.5)
        self.ax.add_feature(cfeature.BORDERS, linewidth=0.5, linestyle=':')
        self.ax.gridlines(draw_labels=True, dms=True, x_inline=False, y_inline=False,
                         linewidth=0.5, alpha=0.5)
        
        # Plot geometries
        if not self.gdf.empty:
            colors = {'Point': 'red', 'Line': 'blue', 'Polygon': 'green'}
            
            for idx, row in self.gdf.iterrows():
                geom_type = row['type']
                color = colors.get(geom_type, 'purple')
                alpha = 0.5
                
                geom = row['geometry']
                
                if geom.geom_type == 'Point':
                    self.ax.plot(geom.x, geom.y, 'o', color=color, markersize=8,
                               transform=ccrs.PlateCarree(), label=f"ID: {row['id']}")
                elif geom.geom_type == 'LineString':
                    x, y = geom.xy
                    self.ax.plot(x, y, color=color, linewidth=2,
                               transform=ccrs.PlateCarree(), label=f"ID: {row['id']}")
                elif geom.geom_type in ['Polygon', 'MultiPolygon']:
                    if geom.geom_type == 'Polygon':
                        x, y = geom.exterior.xy
                        self.ax.fill(x, y, color=color, alpha=alpha, 
                                   edgecolor='black', linewidth=1.5,
                                   transform=ccrs.PlateCarree(), label=f"ID: {row['id']}")
        
        self.ax.set_title(f"Map View - {self.current_crs}", fontsize=10)
        self.canvas.draw()

def main():
    root = tk.Tk()
    app = GISApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()