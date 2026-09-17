import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def load_era5_data():
    """Carrega os dados do ERA5 e orografia"""
    try:
        ds_pl = xr.open_dataset('era5_pressure_levels_vcan_1995.nc')
        ds_sfc = xr.open_dataset('era5_surface_vcan_1995.nc')
        
        try:
            ds_orog = xr.open_dataset('era5_surface_orography.nc')
        except FileNotFoundError:
            ds_orog = None
        
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
            
        return ds_pl, ds_sfc, ds_orog
    except FileNotFoundError:
        print("Arquivos ERA5 não encontrados. Execute download_era5_cds.py primeiro.")
        return None, None, None

def plot_figure_6_slp_4panel(ds_sfc):
    """
    Recria a Figura 6 com 4 painéis (21/12, 22/12, 25/12 e 29/12 às 00 UTC).
    Figura estritamente plana: apenas SLP, linhas de costa e fronteiras (sem relevo).
    """
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
    print("Figura 6 (4 painéis, plano limpo) gerada: Figure_6_SLP_ERA5.png")

def calculate_ertel_vpi(ds_pl, date):
    """Calcula a VPI de Ertel (UVP) no Hemisfério Sul (q = -P * 1e6)"""
    levels = ds_pl.level.values * 100.0 # Pa
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    
    omega = 7.292115e-5
    g = 9.80665
    a = 6.371e6
    
    phi = np.radians(lats)
    f = (2.0 * omega * np.sin(phi))[:, None]
    
    dphi = np.radians(np.abs(np.gradient(lats)))
    dlam = np.radians(np.abs(np.gradient(lons)))
    dx = a * np.cos(phi[:, None]) * dlam[None, :]
    dy = a * dphi[:, None]
    
    t_data = ds_pl['t'].sel(time=date).values
    u_data = ds_pl['u'].sel(time=date).values
    v_data = ds_pl['v'].sel(time=date).values
    
    theta = t_data * (100000.0 / levels[:, None, None]) ** 0.286
    dtheta_dp = np.gradient(theta, levels, axis=0)
    
    zeta = np.zeros_like(u_data)
    for k in range(len(levels)):
        dv_dx = np.gradient(v_data[k], axis=1) / dx
        du_dy = np.gradient(u_data[k], axis=0) / dy
        zeta[k] = dv_dx - du_dy
        
    eta = zeta + f[None, :, :]
    P = -g * eta * dtheta_dp
    q_uvp = -P * 1e6
    return q_uvp

def plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-21T00:00'):
    """
    Recria a Figura 3: VPI (UVP) em coordenada isobárica, altura do geopotencial (m)
    e vetores de vento no nível de 400 hPa.
    Figura plana sem relevo sobreposto.
    """
    fig = plt.figure(figsize=(9, 7))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.8)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    level = 400
    levels_list = list(ds_pl.level.values)
    k400 = levels_list.index(level)
    
    q_uvp = calculate_ertel_vpi(ds_pl, date)
    q400 = q_uvp[k400]
    
    u = ds_pl['u'].sel(time=date, level=level).values
    v = ds_pl['v'].sel(time=date, level=level).values
    z = ds_pl['z'].sel(time=date, level=level).values / 9.80665 # Geopotencial em gpm
    
    lon, lat = np.meshgrid(ds_pl.longitude, ds_pl.latitude)
    
    # Preenchimento em cores da VPI ciclônica em UVP (valores > 0.4 UVP)
    cf = ax.contourf(lon, lat, q400, levels=np.linspace(0.4, 2.6, 12), cmap='YlOrRd',
                     transform=ccrs.PlateCarree(), extend='both')
    plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.06, label=r'Vorticidade Potencial Isentrópica - VPI em 400 hPa (UVP)')
    
    # Contorno da tropopausa dinâmica em 400 hPa (1.5 UVP) em linha vermelha espessa
    c_tropo = ax.contour(lon, lat, q400, levels=[1.5], colors='red', linewidths=2.0, transform=ccrs.PlateCarree())
    ax.clabel(c_tropo, inline=True, fontsize=8, fmt='Tropopausa (1.5 UVP)')
    
    # Geopotencial em linhas pretas
    cz = ax.contour(lon, lat, z, levels=np.arange(6800, 7600, 60), colors='black', linewidths=1.1, transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=7, fmt='%d')
    
    # Vetores de vento espaçados
    step = 4
    ax.quiver(lon[::step, ::step], lat[::step, ::step], u[::step, ::step], v[::step, ::step],
              transform=ccrs.PlateCarree(), scale=400, color='darkblue', width=0.002)
    
    ax.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
    plt.title(f'Figure 3: Isentropic Potential Vorticity (UVP), Height & Wind at 400 hPa - {date[:10]}', fontsize=10)
    plt.savefig(f'Figure_3_400hPa_{date[:10]}.png', dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura 3 (VPI de Ertel em 400 hPa) gerada para {date[:10]}: Figure_3_400hPa_{date[:10]}.png")

def plot_cross_section(ds_pl, ds_orog=None, lat_slice=-27.5, date='1995-12-22T00:00'):
    """
    Recria cortes verticais de temperatura potencial (isentrópicas),
    com a Cordilheira dos Andes indicada em marrom e máscara subterrânea.
    """
    fig, ax = plt.subplots(figsize=(10, 5.5))
    
    data = ds_pl.sel(time=date, latitude=lat_slice, method='nearest')
    lon = data.longitude.values
    levels = data.level.values
    t = data['t'].values.copy()
    
    # Temperatura potencial (theta)
    theta = t * (1000.0 / levels[:, None]) ** 0.286
    
    # Se houver dados de relevo/pressão de superfície, mascara abaixo do solo
    sp_hpa = None
    if ds_orog is not None:
        orog_data = ds_orog['sp'].sel(latitude=lat_slice, method='nearest')
        if 'valid_time' in orog_data.dims and len(orog_data.dims) > 1:
            orog_data = orog_data.isel(valid_time=0)
        sp_hpa = (orog_data / 100.0).values
        
        # Interpola para a mesma grade de longitude se necessário
        if len(sp_hpa) != len(lon):
            sp_hpa = np.interp(lon, ds_orog.longitude.values, sp_hpa)
            
        # Mascara a atmosfera subterrânea (onde p > sp)
        for i, p in enumerate(levels):
            theta[i, p > sp_hpa] = np.nan
    
    # Contornos de temperatura potencial (isentrópicas)
    c = ax.contour(lon, levels, theta, levels=np.arange(280, 380, 4), colors='crimson', linewidths=1.1)
    ax.clabel(c, inline=True, fontsize=8, fmt='%d K')
    
    # Desenha o perfil do relevo (Andes) em marrom
    if sp_hpa is not None:
        ax.fill_between(lon, sp_hpa, 1050, color='saddlebrown', alpha=0.95, zorder=5, label='Cordilheira dos Andes')
        ax.plot(lon, sp_hpa, color='black', linewidth=1.2, zorder=6)
        
        # Identificação dos Andes no pico do relevo
        andes_idx = np.argmin(sp_hpa)
        ax.text(lon[andes_idx], sp_hpa[andes_idx] + 80, 'Andes', color='white',
                fontweight='bold', fontsize=9, ha='center', zorder=7)
    
    ax.invert_yaxis()
    ax.set_yscale('log')
    ax.set_ylim(1050, 100)
    ax.set_yticks([1000, 850, 700, 500, 400, 300, 200, 100])
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.set_ylabel('Pressure (hPa)', fontweight='bold')
    ax.set_xlabel('Longitude (°W)', fontweight='bold')
    ax.set_title(f'Vertical Cross Section (Potential Temperature & Andes Relief) at {lat_slice}°S - {date[:10]}', fontsize=11)
    ax.legend(loc='lower right', framealpha=0.9)
    
    out_name = f'Cross_Section_{date[:10]}_{lat_slice}S.png'
    plt.savefig(out_name, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Corte vertical com relevo gerado: {out_name}")

def plot_figure_10_barotropic(ds_pl):
    """
    Recria a Figura 10 (plano limpo):
    (a) Parâmetro Qy = beta - d^2(u)/dy^2
    (b) Vento zonal médio u entre 300 e 100 hPa para 22-28/12/1995.
    """
    u_subset = ds_pl['u'].sel(time=slice('1995-12-22', '1995-12-28'), level=slice(100, 300))
    u_mean = u_subset.mean(dim=['time', 'level'])
    
    lats = u_mean.latitude.values
    lons = u_mean.longitude.values
    
    omega = 7.292115e-5
    a = 6.371e6
    phi = np.radians(lats)
    
    beta = (2.0 * omega * np.cos(phi)) / a
    dphi = np.radians(np.abs(np.gradient(lats)))
    dy = a * dphi
    
    du_dy = np.gradient(u_mean.values, axis=0) / dy[:, None]
    d2u_dy2 = np.gradient(du_dy, axis=0) / dy[:, None]
    
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
    print("Figura 10 (plano limpo) gerada: Figure_10_Barotropic_ERA5.png")

def main():
    ds_pl, ds_sfc, ds_orog = load_era5_data()
    if ds_pl is not None and ds_sfc is not None:
        print("\n--- Gerando Figuras com Relevo Apenas nos Perfis Verticais ---")
        plot_figure_6_slp_4panel(ds_sfc)
        plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-21T00:00')
        plot_figure_3_ipv_400hPa(ds_pl, date='1995-12-22T00:00')
        
        # Cortes verticais com relevo dos Andes em marrom
        plot_cross_section(ds_pl, ds_orog=ds_orog, lat_slice=-27.5, date='1995-12-21T00:00')
        plot_cross_section(ds_pl, ds_orog=ds_orog, lat_slice=-27.5, date='1995-12-22T00:00')
        plot_cross_section(ds_pl, ds_orog=ds_orog, lat_slice=-35.0, date='1995-12-20T00:00')
        
        plot_figure_10_barotropic(ds_pl)
        print("\nProcessamento concluído com sucesso!")

if __name__ == '__main__':
    main()
