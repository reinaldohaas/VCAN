import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import metpy.calc as mpcalc
from metpy.units import units

def load_era5_data():
    """Carrega os dados do ERA5 (pressupõe que o download_era5_cds.py já foi executado)"""
    try:
        ds_pl = xr.open_dataset('era5_pressure_levels_vcan_1995.nc')
        ds_sfc = xr.open_dataset('era5_surface_vcan_1995.nc')
        return ds_pl, ds_sfc
    except FileNotFoundError:
        print("Arquivos ERA5 não encontrados. Execute download_era5_cds.py primeiro.")
        return None, None

def plot_figure_6_slp(ds_sfc, date='1995-12-21T00:00'):
    """Recria a Figura 6 (Pressão ao Nível do Mar - SLP)"""
    fig = plt.figure(figsize=(8, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    ax.add_feature(cfeature.BORDERS)
    
    # Seleciona o tempo e converte Pa para hPa
    slp = ds_sfc['msl'].sel(time=date) / 100.0
    lon, lat = np.meshgrid(slp.longitude, slp.latitude)
    
    contours = ax.contour(lon, lat, slp, levels=np.arange(990, 1030, 2), colors='black', transform=ccrs.PlateCarree())
    ax.clabel(contours, inline=True, fontsize=8)
    
    plt.title(f'Figure 6: Mean Sea Level Pressure (hPa) - {date}')
    plt.savefig(f'Figure_6_SLP_{date[:10]}.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-21T00:00'):
    """Recria a Figura 3 (VPI, Vento e Geopotencial em 400 hPa)"""
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE)
    
    # Extrai os dados em 400 hPa
    level = 400
    u = ds_pl['u'].sel(time=date, level=level).values * units('m/s')
    v = ds_pl['v'].sel(time=date, level=level).values * units('m/s')
    t = ds_pl['t'].sel(time=date, level=level).values * units('K')
    z = ds_pl['z'].sel(time=date, level=level).values / 9.80665 # Converte geopotencial para altura (m)
    
    lon, lat = np.meshgrid(ds_pl.longitude, ds_pl.latitude)
    
    # Plota a magnitude do vento como shade (proxy visual)
    wspd = np.sqrt(u.m**2 + v.m**2)
    cf = ax.contourf(lon, lat, wspd, cmap='Blues', transform=ccrs.PlateCarree())
    plt.colorbar(cf, label='Wind Speed (m/s)')
    
    # Contornos de geopotencial
    cz = ax.contour(lon, lat, z, colors='black', transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=8)
    
    plt.title(f'Figure 3: Wind & Geopotential at 400 hPa - {date}')
    plt.savefig(f'Figure_3_400hPa_{date[:10]}.png', dpi=300, bbox_inches='tight')
    plt.close()

def plot_cross_section(ds_pl, lat_slice=-27.5, date='1995-12-22T00:00'):
    """Recria cortes verticais (Figuras 4, 5, 7, 9)"""
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # Seleciona uma latitude específica
    data = ds_pl.sel(time=date, latitude=lat_slice, method='nearest')
    
    lon = data.longitude.values
    levels = data.level.values
    t = data['t'].values * units.K
    
    # Calcula a temperatura potencial (theta)
    theta = t * (1000 / levels[:, None]) ** (287.05 / 1004.6)
    
    # Plota os contornos de theta (isentrópicas)
    c = ax.contour(lon, levels, theta.m, levels=np.arange(280, 360, 5), colors='brown')
    ax.clabel(c, inline=True, fontsize=8)
    
    ax.invert_yaxis()
    ax.set_yscale('log')
    ax.set_ylabel('Pressure (hPa)')
    ax.set_xlabel('Longitude')
    plt.title(f'Cross Section at {lat_slice}°S - {date}')
    plt.savefig(f'Cross_Section_{date[:10]}.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    ds_pl, ds_sfc = load_era5_data()
    if ds_pl is not None and ds_sfc is not None:
        print("Gerando Figura 6 (SLP)...")
        plot_figure_6_slp(ds_sfc, date='1995-12-21T00:00')
        
        print("Gerando Figura 3 (400 hPa)...")
        plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-21T00:00')
        
        print("Gerando Cortes Verticais...")
        plot_cross_section(ds_pl, lat_slice=-27.5, date='1995-12-22T00:00')
        
        print("Figuras geradas com sucesso usando ERA5!")

if __name__ == '__main__':
    main()
