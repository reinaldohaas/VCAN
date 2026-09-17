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

def calculate_theta_e(t_k, rh_pct, p_hpa):
    """Calcula a temperatura potencial equivalente (Theta_e) via aproximação de Bolton (1980)"""
    # Pressão de vapor de saturação (hPa)
    es = 6.112 * np.exp((17.67 * (t_k - 273.15)) / (t_k - 29.65))
    e = (rh_pct / 100.0) * es
    w = 0.622 * e / (p_hpa - e)
    # Temperatura no LCL (K)
    tlcl = 56.0 + 1.0 / (1.0 / (t_k - 55.0) - np.log(np.maximum(rh_pct, 1.0) / 100.0) / 2840.0)
    theta = t_k * (1000.0 / p_hpa) ** (0.2854 * (1.0 - 0.28 * w))
    theta_e = theta * np.exp(((3376.0 / tlcl) - 2.54) * w * (1.0 + 0.81 * w))
    return theta_e

def calculate_vorticity(u, v, lats, lons):
    """Calcula a vorticidade relativa horizontal em coordenadas esféricas"""
    a = 6.371e6
    dphi = np.radians(np.abs(np.gradient(lats)))
    dlam = np.radians(np.abs(np.gradient(lons)))
    dx = a * np.cos(np.radians(lats[:, None])) * dlam[None, :]
    dy = a * dphi[:, None]
    
    dv_dx = np.gradient(v, axis=1) / dx
    du_dy = np.gradient(u, axis=0) / dy
    return dv_dx - du_dy

def plot_pacific_pre_andes_coupling(ds_pl):
    """
    Figura 1 de Prova: Acoplamento a Oeste dos Andes no Pacífico (19/12/1995 às 00Z).
    Mostra a anomalia ciclônica de 400 hPa e a anomalia ciclônica em baixos níveis (850 hPa).
    """
    date = '1995-12-19T00:00'
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    # 400 hPa (Altos níveis)
    z400 = ds_pl['z'].sel(time=date, level=400).values / 9.80665
    u400 = ds_pl['u'].sel(time=date, level=400).values
    v400 = ds_pl['v'].sel(time=date, level=400).values
    vort400 = calculate_vorticity(u400, v400, lats, lons)
    
    # 850 hPa (Baixos níveis)
    u850 = ds_pl['u'].sel(time=date, level=850).values
    v850 = ds_pl['v'].sel(time=date, level=850).values
    vort850 = calculate_vorticity(u850, v850, lats, lons)
    
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
    
    # No Hemisfério Sul, vorticidade ciclônica é negativa (< 0).
    # Plotamos vorticidade ciclônica de 850 hPa em preenchimento sombreado
    vort850_cyclonic = np.where(vort850 < -1e-5, -vort850 * 1e5, np.nan)
    c1 = ax.contourf(lon2d, lat2d, vort850_cyclonic, levels=np.linspace(1, 8, 8), cmap='YlOrRd',
                     transform=ccrs.PlateCarree(), extend='max', alpha=0.7)
    plt.colorbar(c1, ax=ax, orientation='horizontal', pad=0.06, label=r'Vorticidade Ciclônica em 850 hPa ($\times 10^{-5} \ \mathrm{s}^{-1}$)')
    
    # Geopotencial em 400 hPa em linhas azuis
    cz = ax.contour(lon2d, lat2d, z400, levels=np.arange(6800, 7500, 60), colors='blue', linewidths=1.5,
                    transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=8, fmt='%d m')
    
    # Anomalia de altos níveis (vorticidade ciclônica em 400 hPa) em linha tracejada preta
    c400 = ax.contour(lon2d, lat2d, -vort400 * 1e5, levels=[4, 6, 8, 10], colors='black', linewidths=1.8, linestyles='--',
                      transform=ccrs.PlateCarree())
    ax.clabel(c400, inline=True, fontsize=8, fmt='400hPa: %d')
    
    # Marcador da cordilheira e anomalia do Pacífico
    ax.plot([-70, -70], [-55, -15], color='brown', linewidth=3, linestyle='-', label='Andes (Eixo)', transform=ccrs.PlateCarree())
    
    ax.set_extent([-100, -55, -55, -20], crs=ccrs.PlateCarree())
    plt.title('Prova 1: Acoplamento Baroclínico no Pacífico (19/12/1995 00Z)\nLinhas Azuis: Geopotencial 400 hPa | Sombreado: Vorticidade Ciclônica 850 hPa | Tracejado: Vorticidade 400 hPa', fontsize=10)
    plt.legend(loc='lower left')
    out_fig = 'Proof_1_Pacific_Pre_Andes_Coupling.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura gerada: {out_fig}")

def plot_sesa_theta_e_anomaly(ds_pl):
    """
    Figura 2 de Prova: Campo de Theta_e em baixos níveis (925 hPa) no SESA e Litoral (23/12/1995 00Z)
    mostrando a língua de ar quente/úmido (alto Theta_e) e sua relação com o VCAN.
    """
    date = '1995-12-23T00:00'
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    lon2d, lat2d = np.meshgrid(lons, lats)
    
    t925 = ds_pl['t'].sel(time=date, level=925).values
    r925 = ds_pl['r'].sel(time=date, level=925).values
    z400 = ds_pl['z'].sel(time=date, level=400).values / 9.80665
    u925 = ds_pl['u'].sel(time=date, level=925).values
    v925 = ds_pl['v'].sel(time=date, level=925).values
    
    theta_e_925 = calculate_theta_e(t925, r925, 925.0)
    
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
    
    # Contorno colorido de Theta_e
    cf = ax.contourf(lon2d, lat2d, theta_e_925, levels=np.arange(315, 355, 2.5), cmap='Spectral_r',
                     transform=ccrs.PlateCarree(), extend='both')
    plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.06, label=r'$\theta_e$ em 925 hPa (K)')
    
    # Contornos de geopotencial em 400 hPa sobreposto
    cz = ax.contour(lon2d, lat2d, z400, levels=np.arange(6900, 7400, 50), colors='black', linewidths=1.2,
                    transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=8, fmt='%d m')
    
    # Vetores de vento em 925 hPa
    step = 4
    ax.quiver(lon2d[::step, ::step], lat2d[::step, ::step], u925[::step, ::step], v925[::step, ::step],
              transform=ccrs.PlateCarree(), scale=300, color='darkgreen', width=0.0025)
    
    ax.set_extent([-75, -35, -45, -15], crs=ccrs.PlateCarree())
    plt.title(r'Prova 2: Diagnóstico de $\theta_e$ em 925 hPa e VCAN em 400 hPa (23/12/1995 00Z)' + '\n' +
              r'Sombreado: $\theta_e$ (K) | Linhas Pretas: Geopotencial 400 hPa | Vetores: Vento em 925 hPa', fontsize=10)
    out_fig = 'Proof_2_SESA_Theta_e_925hPa.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura gerada: {out_fig}")

def plot_vcan_northward_intensification(ds_pl):
    """
    Figura 3 de Prova: Trajetória do VCAN para o norte e evolução da intensidade (21 a 28/12/1995).
    """
    times = ds_pl.time.sel(time=slice('1995-12-21', '1995-12-28')).values[::2] # a cada 12 horas
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    
    centers_lat = []
    centers_lon = []
    min_z400 = []
    max_cyclonic_vort = []
    dates_str = []
    
    for t in times:
        t_str = str(t)[:13]
        z = ds_pl['z'].sel(time=t, level=400).values / 9.80665
        u = ds_pl['u'].sel(time=t, level=400).values
        v = ds_pl['v'].sel(time=t, level=400).values
        vort = calculate_vorticity(u, v, lats, lons)
        
        # Procura o centro do VCAN na caixa do SESA [-70 a -40W, -45 a -20S]
        lat_mask = (lats >= -45) & (lats <= -20)
        lon_mask = (lons >= -70) & (lons <= -40)
        
        sub_z = z[np.ix_(lat_mask, lon_mask)]
        sub_vort = vort[np.ix_(lat_mask, lon_mask)]
        sub_lats = lats[lat_mask]
        sub_lons = lons[lon_mask]
        
        min_idx = np.unravel_index(np.argmin(sub_z), sub_z.shape)
        c_lat = sub_lats[min_idx[0]]
        c_lon = sub_lons[min_idx[1]]
        
        centers_lat.append(c_lat)
        centers_lon.append(c_lon)
        min_z400.append(sub_z[min_idx])
        max_cyclonic_vort.append(-sub_vort[min_idx] * 1e5)
        dates_str.append(t_str)
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Subplot 1: Mapa da Trajetória (deslocamento para o norte)
    ax1 = plt.subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    sc = ax1.scatter(centers_lon, centers_lat, c=range(len(centers_lon)), cmap='plasma', s=80, edgecolors='black',
                     zorder=5, transform=ccrs.PlateCarree())
    ax1.plot(centers_lon, centers_lat, color='black', linewidth=1.5, linestyle='--', transform=ccrs.PlateCarree())
    
    for i, (x, y, dt) in enumerate(zip(centers_lon, centers_lat, dates_str)):
        if i % 2 == 0:
            ax1.text(x + 0.6, y, dt[5:], fontsize=8, fontweight='bold', transform=ccrs.PlateCarree())
            
    ax1.set_extent([-70, -40, -42, -20], crs=ccrs.PlateCarree())
    ax1.set_title('(a) Trajetória do Centro do VCAN em 400 hPa\n(Deslocamento nítido para o Norte/Nordeste)', fontsize=10)
    
    # Subplot 2: Evolução temporal da intensidade (Geopotencial e Vorticidade Ciclônica)
    ax2 = plt.subplot(1, 2, 2)
    color = 'tab:blue'
    ax2.set_xlabel('Tempo (Data/Hora)', fontweight='bold')
    ax2.set_ylabel('Altura Geopotencial Mínima em 400 hPa (m)', color=color, fontweight='bold')
    ax2.plot(dates_str, min_z400, color=color, marker='o', linewidth=2, label='Geopotencial 400 hPa (m)')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.tick_params(axis='x', rotation=45)
    
    ax3 = ax2.twinx()
    color = 'tab:red'
    ax3.set_ylabel(r'Vorticidade Ciclônica Central ($\times 10^{-5} \ \mathrm{s}^{-1}$)', color=color, fontweight='bold')
    ax3.plot(dates_str, max_cyclonic_vort, color=color, marker='s', linestyle='--', linewidth=2, label='Vorticidade Ciclônica')
    ax3.tick_params(axis='y', labelcolor=color)
    
    plt.title('(b) Intensidade do VCAN durante a Trajetória para o Norte', fontsize=10)
    plt.tight_layout()
    out_fig = 'Proof_3_Northward_Trajectory_Intensification.png'
    plt.savefig(out_fig, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"Figura gerada: {out_fig}")

def main():
    ds_pl = load_data()
    print("Gerando Figuras de Prova Dinâmica...")
    plot_pacific_pre_andes_coupling(ds_pl)
    plot_sesa_theta_e_anomaly(ds_pl)
    plot_vcan_northward_intensification(ds_pl)
    print("Todas as figuras de prova foram geradas com sucesso!")

if __name__ == '__main__':
    main()
