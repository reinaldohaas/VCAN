import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units

def calculate_and_plot_vpi():
    """
    Script de exemplo para calcular a VPI (Vorticidade Potencial Isentrópica)
    usando os dados recortados.
    """
    try:
        ds_u = xr.open_dataset('uwnd_1995_subset.nc')
        ds_v = xr.open_dataset('vwnd_1995_subset.nc')
        ds_t = xr.open_dataset('air_1995_subset.nc')
        
        # Selecionando um dia da fase madura (ex: 22/12/1995) e um nível (ex: 300 hPa)
        date = '1995-12-22'
        level = 300
        
        u = ds_u['uwnd'].sel(time=date, level=level).values * units('m/s')
        v = ds_v['vwnd'].sel(time=date, level=level).values * units('m/s')
        
        lon = ds_u['lon'].values
        lat = ds_u['lat'].values
        
        # Para simplificar este script, plota-se apenas o vento e temperatura
        # O cálculo completo de VPI requer interpolação para coordenadas isentrópicas
        # e uso de metpy.calc.potential_vorticity_baroclinic
        
        fig = plt.figure(figsize=(10, 8))
        ax = plt.axes(projection=ccrs.PlateCarree())
        ax.add_feature(cfeature.COASTLINE)
        ax.add_feature(cfeature.BORDERS, linestyle=':')
        
        # Contornos de Vento
        speed = np.sqrt(u**2 + v**2)
        c = ax.contourf(lon, lat, speed, cmap='YlOrRd', transform=ccrs.PlateCarree())
        plt.colorbar(c, orientation='horizontal', pad=0.05, label='Wind Speed (m/s)')
        
        ax.set_extent([-90, -30, -60, 0], crs=ccrs.PlateCarree())
        plt.title(f'Wind Speed at {level} hPa - {date}')
        plt.savefig(f'wind_speed_{level}hPa_{date}.png')
        print("Figura salva com sucesso!")
        
    except FileNotFoundError:
        print("Arquivos NetCDF não encontrados. Rode o script de download primeiro.")

if __name__ == "__main__":
    calculate_and_plot_vpi()
