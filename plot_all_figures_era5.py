import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def load_era5_data():
    """Carrega os dados do ERA5 (pressupõe que o download_era5_cds.py já foi executado)"""
    try:
        ds_pl = xr.open_dataset('era5_pressure_levels_vcan_1995.nc')
        ds_sfc = xr.open_dataset('era5_surface_vcan_1995.nc')
        
        # Padroniza coordenadas para time e level
        rename_pl = {}
        if 'valid_time' in ds_pl.coords:
            rename_pl['valid_time'] = 'time'
        if 'pressure_level' in ds_pl.coords:
            rename_pl['pressure_level'] = 'level'
        if rename_pl:
            ds_pl = ds_pl.rename(rename_pl)
            
        if 'valid_time' in ds_sfc.coords:
            ds_sfc = ds_sfc.rename({'valid_time': 'time'})
            
        return ds_pl, ds_sfc
    except FileNotFoundError:
        print("Arquivos ERA5 não encontrados. Execute download_era5_cds.py primeiro.")
        return None, None

def plot_figure_6_slp_4panel(ds_sfc):
    """Recria a Figura 6 com 4 painéis (21/12, 22/12, 25/12 e 29/12 às 00 UTC)"""
    dates = ['1995-12-21T00:00', '1995-12-22T00:00', '1995-12-25T00:00', '1995-12-29T00:00']
    titles = ['(a) 21/12/1995 00Z', '(b) 22/12/1995 00Z', '(c) 25/12/1995 00Z', '(d) 29/12/1995 00Z']
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 11), subplot_kw={'projection': ccrs.PlateCarree()})
    
    for ax, date, title in zip(axes.flat, dates, titles):
        ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        
        # Pressão ao nível do mar convertida para hPa
        slp = ds_sfc['msl'].sel(time=date) / 100.0
        lon, lat = np.meshgrid(slp.longitude, slp.latitude)
        
        contours = ax.contour(lon, lat, slp, levels=np.arange(990, 1032, 4), colors='blue', linewidths=0.9, transform=ccrs.PlateCarree())
        ax.clabel(contours, inline=True, fontsize=7, fmt='%d')
        
        ax.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
        ax.set_title(title, fontsize=10, fontweight='bold')
    
    plt.suptitle('Figure 6: Mean Sea Level Pressure (hPa) - ERA5 Reanalysis', fontsize=12, y=0.94)
    plt.savefig('Figure_6_SLP_ERA5.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figura 6 (4 painéis) gerada: Figure_6_SLP_ERA5.png")

def plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-21T00:00'):
    """Recria a Figura 3 (VPI / Vento e Geopotencial em 400 hPa)"""
    fig = plt.figure(figsize=(9, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    level = 400
    u = ds_pl['u'].sel(time=date, level=level).values
    v = ds_pl['v'].sel(time=date, level=level).values
    z = ds_pl['z'].sel(time=date, level=level).values / 9.80665 # Geopotencial em gpm
    
    lon, lat = np.meshgrid(ds_pl.longitude, ds_pl.latitude)
    wspd = np.sqrt(u**2 + v**2)
    
    cf = ax.contourf(lon, lat, wspd, levels=np.arange(10, 60, 5), cmap='YlOrRd', transform=ccrs.PlateCarree())
    plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.06, label='Wind Speed (m/s)')
    
    cz = ax.contour(lon, lat, z, levels=np.arange(6800, 7600, 60), colors='black', linewidths=1.0, transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=7, fmt='%d')
    
    # Vetores de vento espaçados
    step = 4
    ax.quiver(lon[::step, ::step], lat[::step, ::step], u[::step, ::step], v[::step, ::step],
              transform=ccrs.PlateCarree(), scale=400, color='darkblue', width=0.002)
    
    ax.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
    plt.title(f'Figure 3: Geopotential Height (m) and Wind at 400 hPa - {date[:10]}', fontsize=11)
    plt.savefig(f'Figure_3_400hPa_{date[:10]}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura 3 gerada para {date[:10]}: Figure_3_400hPa_{date[:10]}.png")

def plot_cross_section(ds_pl, lat_slice=-27.5, date='1995-12-22T00:00'):
    """Recria cortes verticais de temperatura potencial (isentrópicas)"""
    fig, ax = plt.subplots(figsize=(9, 5))
    
    data = ds_pl.sel(time=date, latitude=lat_slice, method='nearest')
    lon = data.longitude.values
    levels = data.level.values
    t = data['t'].values
    
    # Temperatura potencial (theta)
    theta = t * (1000.0 / levels[:, None]) ** 0.286
    
    c = ax.contour(lon, levels, theta, levels=np.arange(280, 380, 4), colors='crimson', linewidths=1.0)
    ax.clabel(c, inline=True, fontsize=8, fmt='%d K')
    
    ax.invert_yaxis()
    ax.set_yscale('log')
    ax.set_yticks([1000, 850, 700, 500, 400, 300, 200, 100])
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylabel('Pressure (hPa)')
    ax.set_xlabel('Longitude (°W)')
    ax.set_title(f'Vertical Cross Section (Potential Temperature) at {lat_slice}°S - {date[:10]}', fontsize=11)
    
    out_name = f'Cross_Section_{date[:10]}_{lat_slice}S.png'
    plt.savefig(out_name, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Corte vertical gerado: {out_name}")

def plot_figure_10_barotropic(ds_pl):
    """
    Recria a Figura 10:
    (a) Parâmetro Qy = beta - d^2(u)/dy^2
    (b) Vento zonal médio u entre 300 e 100 hPa para o período de 22 a 28/12/1995.
    """
    # Média entre 300 e 100 hPa e período 22 a 28/12/1995
    u_subset = ds_pl['u'].sel(time=slice('1995-12-22', '1995-12-28'), level=slice(100, 300))
    u_mean = u_subset.mean(dim=['time', 'level'])
    
    lats = u_mean.latitude.values
    lons = u_mean.longitude.values
    
    # Constantes
    omega = 7.292115e-5
    a = 6.371e6
    phi = np.radians(lats)
    
    # beta = 2 * omega * cos(phi) / a
    beta = (2.0 * omega * np.cos(phi)) / a # 1D array
    
    # Derivada segunda de u em relação a y: d^2(u)/dy^2
    # dy em metros = a * dphi
    dphi = np.radians(np.abs(np.gradient(lats)))
    dy = a * dphi # 1D array
    
    # Gradiente em y (latitude)
    du_dy = np.gradient(u_mean.values, axis=0) / dy[:, None]
    d2u_dy2 = np.gradient(du_dy, axis=0) / dy[:, None]
    
    # Qy = beta - d2u/dy2
    Qy = beta[:, None] - d2u_dy2
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Painel (a): Qy
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    cq = ax1.contourf(lon2d, lat2d, Qy * 1e11, levels=np.linspace(-5, 5, 21), cmap='RdBu_r', transform=ccrs.PlateCarree(), extend='both')
    plt.colorbar(cq, ax=ax1, orientation='horizontal', pad=0.08, label=r'$Q_y \ (\times 10^{-11} \ \mathrm{m}^{-1}\mathrm{s}^{-1})$')
    ax1.contour(lon2d, lat2d, Qy, levels=[0], colors='black', linewidths=1.5, transform=ccrs.PlateCarree())
    ax1.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
    ax1.set_title(r'(a) Parameter $Q_y = \beta - \frac{d^2\bar{u}}{dy^2}$', fontsize=11)
    
    # Painel (b): Vento zonal médio u
    ax2.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax2.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    cu = ax2.contourf(lon2d, lat2d, u_mean.values, levels=np.arange(0, 45, 5), cmap='Purples', transform=ccrs.PlateCarree())
    plt.colorbar(cu, ax=ax2, orientation='horizontal', pad=0.08, label=r'$\bar{u}$ (m/s)')
    ax2.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
    ax2.set_title(r'(b) Mean Zonal Wind $\bar{u}$ (300-100 hPa)', fontsize=11)
    
    plt.suptitle('Figure 10: Barotropic Instability Analysis (22-28 Dec 1995)', fontsize=12, y=0.96)
    plt.savefig('Figure_10_Barotropic_ERA5.png', dpi=300, bbox_inches='tight')
    plt.close()
    print("Figura 10 gerada: Figure_10_Barotropic_ERA5.png")

def main():
    ds_pl, ds_sfc = load_era5_data()
    if ds_pl is not None and ds_sfc is not None:
        print("\n--- Gerando Figuras com dados ERA5 ---")
        plot_figure_6_slp_4panel(ds_sfc)
        plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-21T00:00')
        plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-22T00:00')
        plot_cross_section(ds_pl, lat_slice=-27.5, date='1995-12-21T00:00')
        plot_cross_section(ds_pl, lat_slice=-27.5, date='1995-12-22T00:00')
        plot_figure_10_barotropic(ds_pl)
        print("\nTodas as figuras ERA5 foram geradas com sucesso!")

if __name__ == '__main__':
    main()
