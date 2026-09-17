import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

def load_data():
    ds_pl = xr.open_dataset('era5_pressure_levels_vcan_1995.nc')
    if 'valid_time' in ds_pl.coords:
        ds_pl = ds_pl.rename({'valid_time': 'time', 'pressure_level': 'level'})
    return ds_pl

def calculate_ertel_vpi(ds_pl, date):
    """
    Calcula a Vorticidade Potencial Isentrópica (VPI de Ertel na aproximação hidrostática).
    Convenção para o Hemisfério Sul (Notas de Aula Prof. Reinaldo Haas):
        P = -g * (zeta + f) * dtheta/dp
        q = -P * 1e6 (em UVP, onde q > 0 representa VPI ciclônica / estratosférica)
    """
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
    
    t_data = ds_pl['t'].sel(time=date).values # (level, lat, lon)
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
    
    # q ciclonica no HS em UVP
    q_uvp = -P * 1e6
    return q_uvp, theta

def calculate_theta_e(t_k, rh_pct, p_hpa):
    """Calcula a temperatura potencial equivalente (Theta_e) via Bolton (1980)"""
    es = 6.112 * np.exp((17.67 * (t_k - 273.15)) / (t_k - 29.65))
    e = (rh_pct / 100.0) * es
    w = 0.622 * e / (p_hpa - e)
    tlcl = 56.0 + 1.0 / (1.0 / (t_k - 55.0) - np.log(np.maximum(rh_pct, 1.0) / 100.0) / 2840.0)
    theta = t_k * (1000.0 / p_hpa) ** (0.2854 * (1.0 - 0.28 * w))
    theta_e = theta * np.exp(((3376.0 / tlcl) - 2.54) * w * (1.0 + 0.81 * w))
    return theta_e

def plot_pacific_pre_andes_vpi(ds_pl):
    """
    Figura 1 de Prova: Anomalia de VPI a Oeste dos Andes no Pacífico (19/12/1995 00Z).
    Mostra a anomalia ciclônica de VPI em 850 hPa e a anomalia de VPI em 400 hPa.
    """
    date = '1995-12-19T00:00'
    q_uvp, _ = calculate_ertel_vpi(ds_pl, date)
    
    levels_list = list(ds_pl.level.values)
    k400 = levels_list.index(400)
    k850 = levels_list.index(850)
    
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    z400 = ds_pl['z'].sel(time=date, level=400).values / 9.80665
    
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
    
    # VPI em 850 hPa: valores ciclônicos (> 0.5 UVP)
    q850 = q_uvp[k850]
    c1 = ax.contourf(lon2d, lat2d, q850, levels=np.linspace(0.5, 3.0, 11), cmap='YlOrRd',
                     transform=ccrs.PlateCarree(), extend='both', alpha=0.8)
    plt.colorbar(c1, ax=ax, orientation='horizontal', pad=0.06, label=r'VPI Ciclônica em 850 hPa (UVP)')
    
    # Geopotencial em 400 hPa em linhas azuis
    cz = ax.contour(lon2d, lat2d, z400, levels=np.arange(6800, 7500, 60), colors='blue', linewidths=1.5,
                    transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=8, fmt='%d m')
    
    # Anomalia de VPI em 400 hPa (contornos pretos tracejados indicando ar estratosférico >= 1.5 UVP)
    q400 = q_uvp[k400]
    c400 = ax.contour(lon2d, lat2d, q400, levels=[1.2, 1.5, 2.0, 2.5], colors='black', linewidths=1.8, linestyles='--',
                      transform=ccrs.PlateCarree())
    ax.clabel(c400, inline=True, fontsize=8, fmt='400hPa: %.1f')
    
    # Eixo da Cordilheira dos Andes
    ax.plot([-70, -70], [-55, -15], color='saddlebrown', linewidth=3.5, label='Cordilheira dos Andes', transform=ccrs.PlateCarree())
    
    ax.set_extent([-100, -55, -55, -20], crs=ccrs.PlateCarree())
    plt.title('Prova 1: Acoplamento de VPI no Pacífico pré-Andes (19/12/1995 00Z)\n' +
              r'Sombreado: VPI em 850 hPa (UVP) | Linhas Pretas Tracejadas: VPI em 400 hPa (UVP) | Linhas Azuis: Geopotencial 400 hPa', fontsize=10)
    plt.legend(loc='lower left')
    out_fig = 'Proof_1_Pacific_Pre_Andes_VPI.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura de VPI do Pacífico gerada: {out_fig}")

def plot_sesa_vpi_and_theta_e(ds_pl):
    """
    Figura 2 de Prova: Campo de VPI em 925 hPa e Theta_e em baixos níveis (23/12/1995 00Z).
    """
    date = '1995-12-23T00:00'
    q_uvp, _ = calculate_ertel_vpi(ds_pl, date)
    
    levels_list = list(ds_pl.level.values)
    k925 = levels_list.index(925)
    k400 = levels_list.index(400)
    
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    t925 = ds_pl['t'].sel(time=date, level=925).values
    r925 = ds_pl['r'].sel(time=date, level=925).values
    z400 = ds_pl['z'].sel(time=date, level=400).values / 9.80665
    
    theta_e_925 = calculate_theta_e(t925, r925, 925.0)
    q925 = q_uvp[k925]
    q400 = q_uvp[k400]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 7), subplot_kw={'projection': ccrs.PlateCarree()})
    
    # Painel 1: VPI em 925 hPa (Baixos níveis) e VPI em 400 hPa (Torre de VPI)
    ax1.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
    
    c1 = ax1.contourf(lon2d, lat2d, q925, levels=np.linspace(0.4, 2.5, 11), cmap='YlOrRd',
                      transform=ccrs.PlateCarree(), extend='both')
    plt.colorbar(c1, ax=ax1, orientation='horizontal', pad=0.08, label=r'VPI Ciclônica em 925 hPa (UVP)')
    
    # Contorno de VPI em 400 hPa (> 1.5 UVP - tropopausa rebaixada)
    c_top = ax1.contour(lon2d, lat2d, q400, levels=[1.2, 1.5, 2.0], colors='black', linewidths=1.8,
                        transform=ccrs.PlateCarree())
    ax1.clabel(c_top, inline=True, fontsize=8, fmt='400hPa: %.1f')
    
    ax1.set_extent([-75, -35, -45, -15], crs=ccrs.PlateCarree())
    ax1.set_title('(a) VPI em 925 hPa e Torre de VPI (400 hPa)\n(Sobreposição vertical no litoral do SESA)', fontsize=10)
    
    # Painel 2: Theta_e em 925 hPa
    ax2.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax2.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
    
    c2 = ax2.contourf(lon2d, lat2d, theta_e_925, levels=np.arange(315, 355, 2.5), cmap='Spectral_r',
                      transform=ccrs.PlateCarree(), extend='both')
    plt.colorbar(c2, ax=ax2, orientation='horizontal', pad=0.08, label=r'$\theta_e$ em 925 hPa (K)')
    
    cz = ax2.contour(lon2d, lat2d, z400, levels=np.arange(6900, 7400, 50), colors='black', linewidths=1.2,
                     transform=ccrs.PlateCarree())
    ax2.clabel(cz, inline=True, fontsize=8, fmt='%d m')
    
    ax2.set_extent([-75, -35, -45, -15], crs=ccrs.PlateCarree())
    ax2.set_title(r'(b) $\theta_e$ em 925 hPa e Geopotencial 400 hPa' + '\n(Língua quente/úmida costeira alimentando o sistema)', fontsize=10)
    
    plt.suptitle('Prova 2: Diagnóstico de VPI e Termodinâmica de Superfície no SESA (23/12/1995 00Z)', fontsize=12, y=0.98)
    out_fig = 'Proof_2_SESA_VPI_and_Theta_e.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura de VPI e Theta_e gerada: {out_fig}")

def plot_vcan_northward_vpi_evolution(ds_pl):
    """
    Figura 3 de Prova: Evolução da VPI em 400 hPa durante a trajetória para o Norte (21 a 28/12/1995).
    """
    times = ds_pl.time.sel(time=slice('1995-12-21', '1995-12-28')).values[::2] # a cada 12h
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    levels_list = list(ds_pl.level.values)
    k400 = levels_list.index(400)
    
    centers_lat = []
    centers_lon = []
    max_vpi_400 = []
    min_z400 = []
    dates_str = []
    
    for t in times:
        t_str = str(t)[:13]
        q_uvp, _ = calculate_ertel_vpi(ds_pl, t)
        q400 = q_uvp[k400]
        z400 = ds_pl['z'].sel(time=t, level=400).values / 9.80665
        
        # Caixa SESA
        lat_mask = (lats >= -45) & (lats <= -20)
        lon_mask = (lons >= -70) & (lons <= -40)
        
        sub_z = z400[np.ix_(lat_mask, lon_mask)]
        sub_q = q400[np.ix_(lat_mask, lon_mask)]
        sub_lats = lats[lat_mask]
        sub_lons = lons[lon_mask]
        
        # O centro do vórtice é o mínimo de geopotencial / máximo de VPI
        min_idx = np.unravel_index(np.argmin(sub_z), sub_z.shape)
        c_lat = sub_lats[min_idx[0]]
        c_lon = sub_lons[min_idx[1]]
        
        # Máximo de VPI próximo ao centro (raio de 3 graus)
        dist = np.sqrt((sub_lats[:, None] - c_lat)**2 + (sub_lons[None, :] - c_lon)**2)
        local_q = np.nanmax(sub_q[dist < 3.5])
        
        centers_lat.append(c_lat)
        centers_lon.append(c_lon)
        min_z400.append(sub_z[min_idx])
        max_vpi_400.append(local_q)
        dates_str.append(t_str)
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Subplot 1: Trajetória com cores indicando a intensidade de VPI
    ax1 = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    sc = ax1.scatter(centers_lon, centers_lat, c=max_vpi_400, cmap='YlOrRd', s=120, edgecolors='black',
                     vmin=1.2, vmax=2.5, zorder=5, transform=ccrs.PlateCarree())
    plt.colorbar(sc, ax=ax1, orientation='horizontal', pad=0.08, label='VPI Ciclônica Máxima em 400 hPa (UVP)')
    ax1.plot(centers_lon, centers_lat, color='black', linewidth=1.5, linestyle='--', transform=ccrs.PlateCarree())
    
    for i, (x, y, dt) in enumerate(zip(centers_lon, centers_lat, dates_str)):
        if i % 2 == 0:
            ax1.text(x + 0.6, y, dt[5:], fontsize=8, fontweight='bold', transform=ccrs.PlateCarree())
            
    ax1.set_extent([-70, -40, -42, -20], crs=ccrs.PlateCarree())
    ax1.set_title('(a) Trajetória do VCAN para o Norte colorida por VPI\n(Mantém VPI estratosférica > 1.5 UVP)', fontsize=10)
    
    # Subplot 2: Série temporal de VPI e Geopotencial
    ax2 = plt.subplot(1, 2, 2)
    color = 'crimson'
    ax2.set_xlabel('Tempo (Data/Hora)', fontweight='bold')
    ax2.set_ylabel('VPI Máxima em 400 hPa (UVP)', color=color, fontweight='bold')
    ax2.plot(dates_str, max_vpi_400, color=color, marker='s', linewidth=2.2, label='VPI 400 hPa (UVP)')
    ax2.axhline(1.5, color='gray', linestyle=':', label='Limiar Estratosférico (1.5 UVP)')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.tick_params(axis='x', rotation=45)
    ax2.set_ylim(1.0, 2.8)
    
    ax3 = ax2.twinx()
    color = 'tab:blue'
    ax3.set_ylabel('Geopotencial Mínimo em 400 hPa (m)', color=color, fontweight='bold')
    ax3.plot(dates_str, min_z400, color=color, marker='o', linewidth=2, linestyle='--', label='Geopotencial 400 hPa (m)')
    ax3.tick_params(axis='y', labelcolor=color)
    
    plt.title('(b) Manutenção da Anomalia de VPI durante o Deslocamento para o Norte', fontsize=10)
    plt.tight_layout()
    out_fig = 'Proof_3_Northward_VPI_Evolution.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura de evolução temporal da VPI gerada: {out_fig}")

def main():
    ds_pl = load_data()
    print("--- Gerando Figuras com VPI de Ertel (UVP) ---")
    plot_pacific_pre_andes_vpi(ds_pl)
    plot_sesa_vpi_and_theta_e(ds_pl)
    plot_vcan_northward_vpi_evolution(ds_pl)
    print("Todas as figuras em VPI foram geradas com sucesso!")

if __name__ == '__main__':
    main()
