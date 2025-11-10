import geopandas as gpd

# Membaca sumber data yang akan dilakukan geoprocessing dari data shapefile
gdf1 = gpd.read_file("C:/00_YASIN MANIK HAWA/KULIAH/SEMESTER 7/MAGANG KP TECHNOGIS/PYTHON-ADVANCED/data/polygon1.shp")        # shapefile utama clip intersect union
gdf2 = gpd.read_file("C:/00_YASIN MANIK HAWA/KULIAH/SEMESTER 7/MAGANG KP TECHNOGIS/PYTHON-ADVANCED/data/polygon2.shp")        # shapefile kedua clip intersect union
boundary = gpd.read_file("C:/00_YASIN MANIK HAWA/KULIAH/SEMESTER 7/MAGANG KP TECHNOGIS/PYTHON-ADVANCED/data/boundary_kec.shp") # shapefile untuk dissolve atau clip

# Cleansing data dengan menyamakan CRS
if gdf1.crs != gdf2.crs:
    gdf2 = gdf2.to_crs(gdf1.crs)
if gdf1.crs != boundary.crs:
    boundary = boundary.to_crs(gdf1.crs)

# Geoprocessing CLIP 
gdf_clip = gpd.clip(gdf1, boundary)

#Geoprocessing INTERSECT
gdf_inter = gpd.overlay(gdf1, gdf2, how="intersection")

#Geoprocessing Union 
gdf_union = gpd.overlay(gdf1, gdf2, how="union")

# Mengubah CRS ke dalam satuan meter agar luasan akurat untuk calculate geom, intersect, dan dissolve
gdf_inter = gdf_inter.to_crs(epsg=32750)
gdf_inter["area_m2"] = gdf_inter.area
gdf_inter["area_ha"] = gdf_inter["area_m2"] / 10000

# Geoprocessing Dissolve
if "WADMKK" in boundary.columns:
    gdf_diss = boundary.dissolve(by="WADMKK")
else:
    gdf_diss = boundary.copy()

# Menyimpan hasil Geoprocessing CLIP, INTERSECT, DISSOLVE, UNION dalam direktori folder 
gdf_clip.to_file("hasil_clip.shp")
gdf_inter.to_file("hasil_intersect.shp")
gdf_diss.to_file("hasil_dissolve.shp")
gdf_union.to_file("hasil_union.shp")

# Informasi tambahan
print("✅ Proses Geoprocessing selesai berikut adalah hasilnya yey, done ya sahabat !")
print(f"Hasil clip: {len(gdf_clip)} fitur")
print(f"Hasil intersect: {len(gdf_inter)} fitur")
print(f"Hasil dissolve: {len(gdf_diss)} fitur")
print(f"Hasil union: {len(gdf_union)} fitur")
print(f"Hasil intersect adalah : ", gdf_inter[["area_m2", "area_ha"]].head())
