import matplotlib
matplotlib.use('TkAgg')
from mpl_toolkits.basemap import Basemap
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure(figsize=(12, 8))
ax = fig.add_subplot(111)

m = Basemap(projection='merc',
            llcrnrlat=-80,
            urcrnrlat=80,
            llcrnrlon=-180,
            urcrnrlon=180,
            resolution='c',
            ax=ax)

try:
    m.bluemarble(alpha=1.0)
except Exception:
    m.fillcontinents(color='#2d5016', lake_color='#4d9ff2', alpha=0.6)

# Draw vector overlays
m.drawcoastlines(linewidth=0.5, color='yellow')
m.drawcountries(linewidth=0.5, color='white')
m.drawstates(linewidth=0.3, color='gray', linestyle='--')
m.drawrivers(linewidth=0.3, color='cyan')
m.drawmapboundary(fill_color='#000000', linewidth=1)

# Graticules
parallels = np.arange(-90, 91, 30)
meridians = np.arange(-180, 180, 30)
m.drawparallels(parallels, labels=[1, 0, 0, 0], fontsize=8, color='white', linewidth=0.5)
m.drawmeridians(meridians, labels=[0, 0, 0, 1], fontsize=8, color='white', linewidth=0.5)

# Title
plt.title('Global Satellite Imagery (Blue Marble)', fontsize=14, fontweight='bold', pad=10, color='white')
fig.patch.set_facecolor('#1a1a1a')
ax.patch.set_facecolor('#1a1a1a')

plt.show()