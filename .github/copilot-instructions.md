## What this repo is (big picture)

This is a tiny Flask-based geo-processing demo: a front-end HTML page (`index.html`) triggers a backend endpoint (`/run-clip`) implemented in `app.py` which uses GeoPandas to clip one vector dataset by another and writes the result to disk.

Key files:
- `app.py` — Flask app and the geoprocessing logic (reads files with GeoPandas, clips, writes output with ESRI Shapefile driver).
- `index.html` — simple single-page UI that POSTs to `http://127.0.0.1:5000/run-clip` and shows status messages.

## Architectural notes agents should know (why/how)

- The app runs as a local Flask server. The file IO paths used by the clip logic are hard-coded in `app.py` (e.g. `file_to_clip_path`, `clipping_mask_path`, `output_path`). Agents modifying processing should look for these variables at the top of the route handler.
- GeoPandas is the primary dependency for GIS operations. The code checks and aligns CRS via `to_crs` before calling `gpd.clip`.
- Output is written with `clipped_gdf.to_file(output_path, driver="ESRI Shapefile")`. The runtime environment must have write permissions to `output_path` and enough disk space.

## Developer workflows and commands (explicit)

- Run the Flask app during development (PowerShell):

```powershell
$env:FLASK_APP = "app.py"; flask run
```

- Or run directly with Python (this uses `app.run(debug=True)` in `__main__`):

```powershell
python app.py
```

- The frontend expects the backend at `http://127.0.0.1:5000`. If you open `index.html` from the filesystem (file://), you may face cross-origin issues — either serve `index.html` from the same host (e.g., a simple static server) or enable CORS in Flask when testing.

## Project-specific conventions & patterns (concrete)

- Single-route processing: `@app.route('/run-clip', methods=['POST'])` contains the whole pipeline (read, clip, write, jsonify). When adding features, follow the same pattern of small, focused POST routes that return JSON status objects with `status` and `message` keys.
- Error handling: exceptions are caught in the route and returned as JSON with HTTP 500. Non-overlap clipping is returned as a 400 with a message `Poligon tidak tumpang tindih` (Indonesian); preserve message shape when adding new error cases.
- Logging/prints: the code uses `print()` for runtime messages. For more complex agents, prefer adding structured logging but preserve existing print statements if you edit the handler (tests or UI may rely on them during debugging).

## Integration points & external dependencies

- GeoPandas and its ecosystem (Fiona, Shapely, pyproj) are required for the clipping logic. Expect typical install time and binary wheels; if you add CI, remember system-level deps may be needed (GDAL).
- Frontend → Backend: `index.html` POSTs to `/run-clip`. The frontend expects a JSON object: `{status: 'success'|'error', message: '...'}` and uses that to show user feedback. Keep JSON shape compatible.

## Small, discoverable examples to copy when coding

- Align CRS before operations (from `app.py`):

```python
if gdf_to_clip.crs != gdf_mask.crs:
    gdf_mask = gdf_mask.to_crs(gdf_to_clip.crs)
```

- Clip with warnings suppressed (keep this structure if non-fatal warnings occur):

```python
with warnings.catch_warnings():
    warnings.simplefilter("ignore", UserWarning)
    clipped_gdf = gpd.clip(gdf_to_clip, gdf_mask)
```

## Things NOT to change without tests / manual verification

- The file IO formats and drivers. `to_file(..., driver="ESRI Shapefile")` implies multiple files (.shp, .shx, .dbf). Ensure consumers expect that shape.
- Hard-coded network addresses in `index.html` (`http://127.0.0.1:5000/run-clip`). If you change the backend port/origin, update the frontend or enable CORS explicitly.

## Quick checklist for PR reviewers / agents

- Verify route returns JSON with `status` and `message` for all paths (success, user error, exception).
- Confirm any new file paths are writable by the target environment and consider making paths configurable via env vars.
- When changing GeoPandas code, add a small manual test (run the Flask route locally with representative zipped shapefiles) — there are no automated tests in this repo yet.

---

If you'd like, I can (1) add a small README with exact install requirements (example `requirements.txt`) and a quick dev-run script, or (2) make the `output_path` configurable via an environment variable and wire a minimal CORS allow-list so `index.html` can be opened from the filesystem during testing. Which would you prefer? Please point out any unclear areas in the instructions above to iterate.
