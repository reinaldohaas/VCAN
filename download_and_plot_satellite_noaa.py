import urllib.request
import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def download_gridsat(year, month, day, hour):
    """
    Baixa os dados GridSat-B1 (satélites geoestacionários incluindo GOES-8)
    diretamente do repositório público da NOAA NCEI (EarthData).
    """
    filename = f"GRIDSAT-B1.{year}.{month:02d}.{day:02d}.{hour:02d}.v02r01.nc"
    url = f"https://www.ncei.noaa.gov/data/geostationary-ir-channel-brightness-temperature-gridsat-b1/access/{year}/{filename}"
    
    if not os.path.exists(filename):
        print(f"Baixando imagem de satélite da NOAA: {filename}...")
        urllib.request.urlretrieve(url, filename)
        print("Download concluído!")
    return filename

def plot_figure_1():
    """
    Recria a Figura 1:
    Imagens do canal infravermelho (IR) para 14/12/1995 e 19/12/1995 (GOES-8).
    """
    f1 = download_gridsat(1995, 12, 14, 18)
    f2 = download_gridsat(1995, 12, 19, 18)
    
    ds1 = xr.open_dataset(f1)
    ds2 = xr.open_dataset(f2)
    
    # Recorta para a América do Sul e oceanos adjacentes
    lat_slice = slice(-60, 0)
    lon_slice = slice(270, 330) # 90W a 30W em graus leste (ou -90 a -30)
    
    # Verifica sistema de coordenadas de longitude
    lons1 = ds1.lon.values
    if (lons1 > 180).any():
        lon_box = slice(270, 330)
    else:
        lon_box = slice(-90, -30)
        
    ir1 = ds1['irwin_cdr'].sel(lat=lat_slice, lon=lon_box).squeeze()
    ir2 = ds2['irwin_cdr'].sel(lat=lat_slice, lon=lon_box).squeeze()
    
    # Ajusta longitudes para [-180, 180] se necessário
    plot_lons1 = ir1.lon.values
    if (plot_lons1 > 180).any():
        plot_lons1 = np.where(plot_lons1 > 180, plot_lons1 - 360, plot_lons1)
        
    plot_lons2 = ir2.lon.values
    if (plot_lons2 > 180).any():
        plot_lons2 = np.where(plot_lons2 > 180, plot_lons2 - 360, plot_lons2)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Painel 1 (14/12/1995)
    ax1.add_feature(cfeature.COASTLINE, color='yellow', linewidth=0.9)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', color='yellow', linewidth=0.6)
    im1 = ax1.contourf(plot_lons1, ir1.lat.values, ir1.values, levels=np.linspace(190, 310, 50),
                       cmap='gray_r', transform=ccrs.PlateCarree())
    ax1.set_extent([-90, -30, -55, -5], crs=ccrs.PlateCarree())
    ax1.set_title('(a) GOES-8 IR - 14/12/1995 ~17:45 UTC\nFormação do VCAN no Pacífico', fontsize=11)
    
    # Painel 2 (19/12/1995)
    ax2.add_feature(cfeature.COASTLINE, color='yellow', linewidth=0.9)
    ax2.add_feature(cfeature.BORDERS, linestyle=':', color='yellow', linewidth=0.6)
    im2 = ax2.contourf(plot_lons2, ir2.lat.values, ir2.values, levels=np.linspace(190, 310, 50),
                       cmap='gray_r', transform=ccrs.PlateCarree())
    ax2.set_extent([-90, -30, -55, -5], crs=ccrs.PlateCarree())
    ax2.set_title('(b) GOES-8 IR - 19/12/1995 ~17:45 UTC\nVCAN formado a Oeste dos Andes', fontsize=11)
    
    plt.suptitle('Figure 1: Satellite Imagery (GOES-8 / NOAA GridSat-B1 IR)', fontsize=13, y=0.96)
    out_fig = 'Figure_1_GOES8_IR.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura 1 salva com sucesso em: {out_fig}")

if __name__ == '__main__':
    plot_figure_1()
