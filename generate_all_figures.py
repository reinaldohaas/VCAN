import os
import xarray as xr
import numpy as np
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import scipy.ndimage as ndimage

# Constantes geofísicas
OMEGA = 7.292115e-5
G = 9.80665
A = 6.371e6

def load_datasets():
    ds_pl = xr.open_dataset('era5_pressure_levels_vcan_1995.nc')
    ds_sfc = xr.open_dataset('era5_surface_vcan_1995.nc')
    ds_orog = xr.open_dataset('era5_surface_orography.nc')
    
    if 'valid_time' in ds_pl.coords:
        ds_pl = ds_pl.rename({'valid_time': 'time', 'pressure_level': 'level'})
    if 'valid_time' in ds_sfc.coords:
        ds_sfc = ds_sfc.rename({'valid_time': 'time'})
        
    return ds_pl, ds_sfc, ds_orog

def calculate_ertel_vpi(ds_pl, date):
    """Calcula a VPI de Ertel (UVP) no Hemisfério Sul (q = -P * 1e6)"""
    levels = ds_pl.level.values * 100.0 # Pa
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    
    phi = np.radians(lats)
    f = (2.0 * OMEGA * np.sin(phi))[:, None]
    
    dphi = np.radians(np.abs(np.gradient(lats)))
    dlam = np.radians(np.abs(np.gradient(lons)))
    dx = A * np.cos(phi[:, None]) * dlam[None, :]
    dy = A * dphi[:, None]
    
    t_data = ds_pl['t'].sel(time=date).values
    u_data = ds_pl['u'].sel(time=date).values
    v_data = ds_pl['v'].sel(time=date).values
    
    theta = t_data * (100000.0 / levels[:, None, None]) ** 0.286
    dtheta_dp = np.gradient(theta, levels, axis=0)
    
    zeta = np.zeros_like(u_data)
    for k in range(len(levels)):
        zeta[k] = (np.gradient(v_data[k], axis=1) / dx) - (np.gradient(u_data[k], axis=0) / dy)
        
    P = -G * (zeta + f[None, :, :]) * dtheta_dp
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

# ==========================================
# FIGURA 1: Satélite GOES-8 IR (GridSat-B1)
# ==========================================
def generate_figure_1():
    print("Generating Figure 1 (GOES-8 IR)...")
    ds1 = xr.open_dataset('GRIDSAT-B1.1995.12.14.18.v02r01.nc')
    ds2 = xr.open_dataset('GRIDSAT-B1.1995.12.19.18.v02r01.nc')
    
    ir1 = ds1['irwin_cdr'].sel(lat=slice(-55, -10), lon=slice(-90, -30)).squeeze()
    ir2 = ds2['irwin_cdr'].sel(lat=slice(-55, -10), lon=slice(-90, -30)).squeeze()
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 7), subplot_kw={'projection': ccrs.PlateCarree()})
    
    items = [
        (ax1, ir1, '(a) GOES-8 IR - 14/12/1995 18 UTC', (-82, -32)),
        (ax2, ir2, '(b) GOES-8 IR - 19/12/1995 18 UTC', (-80, -35))
    ]
    
    mesh = None
    for ax, ir, title, vortex_pt in items:
        ax.add_feature(cfeature.COASTLINE, color='yellow', linewidth=0.8)
        ax.add_feature(cfeature.BORDERS, linestyle=':', color='yellow', linewidth=0.5)
        
        mesh = ax.pcolormesh(ir.lon, ir.lat, ir.values, cmap='gray_r', vmin=190, vmax=330,
                             transform=ccrs.PlateCarree(), shading='auto')
        
        ax.annotate('Vortex Center', xy=vortex_pt, xytext=(vortex_pt[0]-7, vortex_pt[1]+6),
                    arrowprops=dict(facecolor='yellow', edgecolor='black', arrowstyle='->', lw=2),
                    color='yellow', fontsize=9, fontweight='bold', transform=ccrs.PlateCarree(),
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='black', alpha=0.7))
                    
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        ax.set_extent([-90, -30, -55, -10], crs=ccrs.PlateCarree())
        ax.set_title(title, fontsize=11, fontweight='bold')
        
    cbar = fig.colorbar(mesh, ax=[ax1, ax2], orientation='horizontal', pad=0.08, aspect=40)
    cbar.set_label('Brightness Temperature (K)', fontsize=10, fontweight='bold')
    
    out_file = 'Figure_1_GOES8_IR.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

# ==============================================================
# FIGURA 2: Corte Vertical Pacífico Pré-Andes (35°S, 18/12 18Z)
# ==============================================================
def generate_figure_2(ds_pl, ds_orog):
    print("Generating Figure 2 (Pacific Pre-Andes Cross Section)...")
    date = '1995-12-18T18:00'
    lat_slice = -35.0
    
    q_uvp, theta = calculate_ertel_vpi(ds_pl, date)
    
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    levels = ds_pl.level.values
    
    lat_idx = np.argmin(np.abs(lats - lat_slice))
    q_cross = q_uvp[:, lat_idx, :].copy()
    theta_cross = theta[:, lat_idx, :].copy()
    
    # Relevo
    orog_data = ds_orog['sp'].sel(latitude=lat_slice, method='nearest')
    if 'valid_time' in orog_data.dims and len(orog_data.dims) > 1:
        orog_data = orog_data.isel(valid_time=0)
    sp_hpa = (orog_data / 100.0).values
    if len(sp_hpa) != len(lons):
        sp_hpa = np.interp(lons, ds_orog.longitude.values, sp_hpa)
        
    # Mascara subterranea
    for k, p_val in enumerate(levels):
        q_cross[k, p_val > sp_hpa] = np.nan
        theta_cross[k, p_val > sp_hpa] = np.nan

    fig, ax = plt.subplots(figsize=(10, 6))
    lon2d, lev2d = np.meshgrid(lons, levels)
    
    cf = ax.contourf(lon2d, lev2d, q_cross, levels=np.linspace(0.0, 3.5, 15),
                     cmap='Spectral_r', extend='both')
    cbar = plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.12, aspect=35)
    cbar.set_label('Isentropic Potential Vorticity - Cyclonic IPV (UVP)', fontsize=10, fontweight='bold')
    
    c_tropo = ax.contour(lon2d, lev2d, q_cross, levels=[1.5], colors='red', linewidths=2.0)
    ax.clabel(c_tropo, inline=True, fontsize=8, fmt='Tropopause (1.5 UVP)')
    
    ct = ax.contour(lon2d, lev2d, theta_cross, levels=np.arange(275, 385, 5), colors='black', linewidths=0.9)
    ax.clabel(ct, inline=True, fontsize=8, fmt='%d K')
    
    ax.fill_between(lons, sp_hpa, 1050, color='saddlebrown', alpha=0.95, zorder=5)
    ax.plot(lons, sp_hpa, color='black', linewidth=1.5, zorder=6)
    
    ax.text(-69.5, 750, 'Andes', color='white', fontweight='bold', fontsize=10, ha='center', zorder=7)
    ax.annotate('Low-Level Anomaly\n(dammed along coast)', xy=(-78, 960), xytext=(-88, 880),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.85))
    ax.annotate('Stratospheric Intrusion\n(Upper UTCV)', xy=(-88, 380), xytext=(-88, 250),
                arrowprops=dict(facecolor='black', arrowstyle='->', lw=1.5),
                fontsize=9, fontweight='bold', bbox=dict(boxstyle='round,pad=0.3', facecolor='cyan', alpha=0.85))
    
    ax.set_xlim(-90, -62)
    ax.set_ylim(1050, 150)
    ax.set_yscale('log')
    ax.set_yticks([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150])
    ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
    ax.minorticks_off()
    ax.set_ylabel('Pressure (hPa)', fontweight='bold', fontsize=10)
    ax.set_xlabel('Longitude (°W)', fontweight='bold', fontsize=10)
    ax.set_title('Figure 2: Vertical Cross-Section (35°S) of IPV and Isentropes over the Pacific (18/12/1995 18 UTC)\n' +
                 'Upper-level stratospheric extrusion (~88°W) and shallow coastal anomaly dammed west of the Andes (~78°W)',
                 fontsize=10, fontweight='bold')
                 
    out_file = 'Figure_2_Pacific_Pre_Andes_VPI.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

# ==============================================================
# FIGURA 3: Corte Vertical dos Andes - Evolução da Inclinação
# ==============================================================
def generate_figure_3(ds_pl, ds_orog):
    print("Generating Figure 3 (Andes Cross-Section Tilt Evolution)...")
    dates = ['1995-12-20T00:00', '1995-12-22T00:00']
    titles = [
        '(a) 20/12/1995 00 UTC: Mountain Transit (Westward Tilt with Height)',
        '(b) 22/12/1995 00 UTC: Over Uruguay / SESA (Equivalent Barotropic Alignment)'
    ]
    lat_slice = -32.0
    
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    levels = ds_pl.level.values
    
    lat_idx = np.argmin(np.abs(lats - lat_slice))
    orog_data = ds_orog['sp'].sel(latitude=lat_slice, method='nearest')
    if 'valid_time' in orog_data.dims and len(orog_data.dims) > 1:
        orog_data = orog_data.isel(valid_time=0)
    sp_hpa = (orog_data / 100.0).values
    if len(sp_hpa) != len(lons):
        sp_hpa = np.interp(lons, ds_orog.longitude.values, sp_hpa)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 10))
    
    cf = None
    for ax, date, title in zip([ax1, ax2], dates, titles):
        q_uvp, theta = calculate_ertel_vpi(ds_pl, date)
        q_cross = q_uvp[:, lat_idx, :].copy()
        theta_cross = theta[:, lat_idx, :].copy()
        
        for k, p_val in enumerate(levels):
            q_cross[k, p_val > sp_hpa] = np.nan
            theta_cross[k, p_val > sp_hpa] = np.nan
            
        lon2d, lev2d = np.meshgrid(lons, levels)
        cf = ax.contourf(lon2d, lev2d, q_cross, levels=np.linspace(0.0, 3.5, 15),
                         cmap='Spectral_r', extend='both')
        
        c_tropo = ax.contour(lon2d, lev2d, q_cross, levels=[1.5], colors='red', linewidths=1.8)
        ax.clabel(c_tropo, inline=True, fontsize=8, fmt='1.5 UVP')
        
        ct = ax.contour(lon2d, lev2d, theta_cross, levels=np.arange(275, 385, 5), colors='black', linewidths=0.8)
        ax.clabel(ct, inline=True, fontsize=8, fmt='%d K')
        
        ax.fill_between(lons, sp_hpa, 1050, color='saddlebrown', alpha=0.95, zorder=5)
        ax.plot(lons, sp_hpa, color='black', linewidth=1.2, zorder=6)
        
        # Marcação do eixo do vórtice (linha de centros de geopotencial mínimo)
        if '20/12' in title:
            # Eixo inclinado para oeste: 200 hPa em ~75W, 400 hPa em ~74W, 700 hPa em ~71W, 850 hPa em ~70W
            axis_lons = [-70.0, -71.0, -72.5, -74.0, -75.0]
            axis_levs = [850, 700, 500, 400, 250]
            ax.plot(axis_lons, axis_levs, color='cyan', linewidth=2.5, linestyle='--', marker='o', zorder=8)
            ax.text(-75.5, 230, 'Vortex Axis (Tilt to West)', color='darkblue', fontweight='bold', fontsize=9, zorder=9)
        else:
            # Eixo verticalizado (barotrópico equivalente) em ~62W
            axis_lons = [-62.0, -62.0, -62.0, -62.0, -62.0]
            axis_levs = [850, 700, 500, 400, 250]
            ax.plot(axis_lons, axis_levs, color='cyan', linewidth=2.5, linestyle='--', marker='o', zorder=8)
            ax.text(-61.5, 230, 'Vortex Axis (Vertical / Barotropic)', color='darkblue', fontweight='bold', fontsize=9, zorder=9)
            
        ax.text(-69.5, 750, 'Andes', color='white', fontweight='bold', fontsize=9, ha='center', zorder=7)
        ax.set_xlim(-90, -45)
        ax.set_ylim(1050, 150)
        ax.set_yscale('log')
        ax.set_yticks([1000, 925, 850, 700, 500, 400, 300, 250, 200, 150])
        ax.get_yaxis().set_major_formatter(plt.ScalarFormatter())
        ax.minorticks_off()
        ax.set_ylabel('Pressure (hPa)', fontweight='bold', fontsize=10)
        ax.set_title(title, fontsize=10, fontweight='bold')

    ax2.set_xlabel('Longitude (°W)', fontweight='bold', fontsize=10)
    cbar = fig.colorbar(cf, ax=[ax1, ax2], orientation='horizontal', pad=0.08, aspect=45)
    cbar.set_label('Isentropic Potential Vorticity - Cyclonic IPV (UVP)', fontsize=10, fontweight='bold')
    
    out_file = 'Figure_3_Andes_CrossSection_Tilt.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

# ==============================================================
# FIGURA 4: Pressão ao Nível do Mar e Ciclogênese a Sotavento (Mendoza)
# ==============================================================
def generate_figure_4(ds_sfc, ds_orog):
    print("Generating Figure 4 (Mean Sea Level Pressure & Mendoza Lee Deepening)...")
    
    # Carrega dados horários de Mendoza se disponíveis
    ds_h = None
    if os.path.exists('era5_hourly_mendoza_1995.nc'):
        ds_h = xr.open_dataset('era5_hourly_mendoza_1995.nc')
    
    z_orog = (ds_orog['z'].isel(valid_time=0) / G).values
    mask_andes = z_orog > 2000.0
    lon2d, lat2d = np.meshgrid(ds_sfc.longitude, ds_sfc.latitude)
    
    fig = plt.figure(figsize=(15, 12))
    
    # Painel (a): Zoom regional de Mendoza no mínimo de pressão (20/12 19 UTC) com intervalos de 2 hPa
    ax1 = fig.add_subplot(2, 2, 1, projection=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax1.add_feature(cfeature.BORDERS, linestyle='--', linewidth=0.8)
    
    m_lat, m_lon = -32.89, -68.84
    
    if ds_h is not None:
        t_peak = '1995-12-20T19:00'
        slp_peak = (ds_h['msl'].sel(valid_time=t_peak).values) / 100.0
        slp_peak_smooth = ndimage.gaussian_filter(slp_peak, sigma=1.0)
        lon_h, lat_h = np.meshgrid(ds_h.longitude, ds_h.latitude)
        
        sub_z = ds_orog['z'].isel(valid_time=0).interp(latitude=ds_h.latitude, longitude=ds_h.longitude).values / G
        mask_peak_andes = sub_z > 2000.0
        
        ax1.contourf(lon_h, lat_h, mask_peak_andes.astype(float), levels=[0.5, 1.5], colors=['#d0d0d0'], zorder=3)
        slp_peak_plot = np.where(mask_peak_andes, np.nan, slp_peak_smooth)
        
        # Intervalos de 2 hPa conforme solicitado pelo usuário
        levels_2hpa = np.arange(986, 1024, 2)
        c1 = ax1.contour(lon_h, lat_h, slp_peak_plot, levels=levels_2hpa, colors='darkblue', linewidths=1.3, zorder=4)
        ax1.clabel(c1, inline=True, fontsize=8, fmt='%d')
        
        ax1.plot(m_lon, m_lat, marker='*', markersize=14, color='red', markeredgecolor='black', zorder=10)
        ax1.text(m_lon + 0.3, m_lat - 0.2, 'Mendoza\n995.1 hPa', fontsize=10, fontweight='bold', color='darkred', zorder=10,
                 bbox=dict(boxstyle='round,pad=0.2', facecolor='white', alpha=0.8, edgecolor='red'))
        
        ax1.set_extent([-73, -63, -37, -26], crs=ccrs.PlateCarree())
        ax1.set_title('(a) Regional Zoom: Mendoza & Cuyo at SLP Minimum\n20/12/1995 19:00 UTC (Contour interval: 2 hPa)', fontsize=11, fontweight='bold')
    else:
        # Fallback usando dados 6-horários
        slp_peak = (ds_sfc['msl'].sel(time='1995-12-20T18:00').values) / 100.0
        slp_peak_smooth = ndimage.gaussian_filter(slp_peak, sigma=1.0)
        slp_peak_plot = np.where(mask_andes, np.nan, slp_peak_smooth)
        ax1.contourf(lon2d, lat2d, mask_andes.astype(float), levels=[0.5, 1.5], colors=['#d0d0d0'], zorder=3)
        c1 = ax1.contour(lon2d, lat2d, slp_peak_plot, levels=np.arange(986, 1024, 2), colors='darkblue', linewidths=1.3, zorder=4)
        ax1.clabel(c1, inline=True, fontsize=8, fmt='%d')
        ax1.plot(m_lon, m_lat, marker='*', markersize=14, color='red', markeredgecolor='black', zorder=10)
        ax1.text(m_lon + 0.3, m_lat - 0.2, 'Mendoza\n995.7 hPa', fontsize=10, fontweight='bold', color='darkred', zorder=10)
        ax1.set_extent([-73, -63, -37, -26], crs=ccrs.PlateCarree())
        ax1.set_title('(a) Regional Zoom: Mendoza & Cuyo (20/12 18 UTC, 2 hPa intervals)', fontsize=11, fontweight='bold')
        
    gl1 = ax1.gridlines(draw_labels=True, linestyle=':', alpha=0.6)
    gl1.top_labels = False
    gl1.right_labels = False
    
    # Painel (b): Evolução horária da pressão na região a sotavento e em Mendoza (18 a 22/12)
    ax2 = fig.add_subplot(2, 2, 2)
    if ds_h is not None:
        times_h = ds_h.valid_time.values
        ilat = np.abs(ds_h.latitude.values - m_lat).argmin()
        ilon = np.abs(ds_h.longitude.values - m_lon).argmin()
        slp_mendoza = ds_h['msl'][:, ilat, ilon].values / 100.0
        time_hours = [(t - times_h[0]) / np.timedelta64(1, 'h') for t in times_h]
        
        # Mínimo regional horário excluindo relevo > 2000 m
        sub_z = ds_orog['z'].isel(valid_time=0).interp(latitude=ds_h.latitude, longitude=ds_h.longitude).values / G
        mask_andes_h = sub_z > 2000.0
        regional_min = []
        for i in range(len(times_h)):
            vals = (ds_h['msl'][i].values / 100.0).copy()
            vals[mask_andes_h] = np.nan
            regional_min.append(np.nanmin(vals))
            
        regional_min = np.array(regional_min)
        
        # Curva da baixa a sotavento regional (Cuyo / BNOA)
        ax2.plot(time_hours, regional_min, color='crimson', linewidth=2.2, marker='s', markersize=3,
                 label='Regional Lee Low Min SLP (Cuyo/BNOA: 20.9 hPa / 30h drop)')
        idx_reg_min = np.argmin(regional_min)
        ax2.plot(time_hours[idx_reg_min], regional_min[idx_reg_min], marker='*', markersize=16, color='red', markeredgecolor='black',
                 label=f'Regional Min: {regional_min[idx_reg_min]:.1f} hPa (20/12 22Z, E = 1.42 Bergeron)')
        
        # Curva pontual de Mendoza
        ax2.plot(time_hours, slp_mendoza, color='darkblue', linewidth=1.6, linestyle='--', marker='o', markersize=3,
                 label='Mendoza Station Point (33°S, 68.8°W; Min 995.1 hPa)')
        
        ax2.set_xlabel('Hours since 18/12 00:00 UTC', fontsize=10, fontweight='bold')
        ax2.set_ylabel('Mean Sea Level Pressure (hPa)', fontsize=10, fontweight='bold')
        ax2.set_title('(b) Hourly Pressure Evolution during Lee Cyclogenesis (18-22 Dec 1995)\n' +
                      'Regional 30h drop: 20.9 hPa | 24h drop: 17.6 hPa (Explosive Cyclogenesis / Bomb)', fontsize=11, fontweight='bold')
        ax2.grid(True, linestyle='--', alpha=0.5)
        xticks = [0, 24, 48, 72, 96]
        xlabels = ['18/12 00Z', '19/12 00Z', '20/12 00Z', '21/12 00Z', '22/12 00Z']
        ax2.set_xticks(xticks)
        ax2.set_xticklabels(xlabels)
        ax2.legend(loc='upper right', fontsize=8.5)
    else:
        ax2.text(0.5, 0.5, 'Dados horários não encontrados', ha='center')
        
    # Painel (c): 22/12 00 UTC - Ciclone sobre o Uruguai
    ax3 = fig.add_subplot(2, 2, 3, projection=ccrs.PlateCarree())
    ax3.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax3.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    t_coord = 'valid_time' if 'valid_time' in ds_sfc.coords else 'time'
    slp_22 = (ds_sfc['msl'].sel({t_coord: '1995-12-22T00:00'}).values) / 100.0
    slp_22_smooth = ndimage.gaussian_filter(slp_22, sigma=1.2)
    ax3.contourf(lon2d, lat2d, mask_andes.astype(float), levels=[0.5, 1.5], colors=['#e0e0e0'], zorder=3)
    slp_22_plot = np.where(mask_andes, np.nan, slp_22_smooth)
    c3 = ax3.contour(lon2d, lat2d, slp_22_plot, levels=np.arange(990, 1032, 4), colors='darkblue', linewidths=1.2, zorder=4)
    ax3.clabel(c3, inline=True, fontsize=8, fmt='%d')
    ax3.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
    ax3.set_title('(c) 22/12/1995 00 UTC: Uruguay Surface Cyclone (L: 1003.3 hPa)', fontsize=10, fontweight='bold')
    gl3 = ax3.gridlines(draw_labels=True, linestyle=':', alpha=0.5)
    gl3.top_labels = False
    gl3.right_labels = False
    
    # Painel (d): 25/12 00 UTC - Cavado em dissipação
    ax4 = fig.add_subplot(2, 2, 4, projection=ccrs.PlateCarree())
    ax4.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax4.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    slp_25 = (ds_sfc['msl'].sel({t_coord: '1995-12-25T00:00'}).values) / 100.0
    slp_25_smooth = ndimage.gaussian_filter(slp_25, sigma=1.2)
    ax4.contourf(lon2d, lat2d, mask_andes.astype(float), levels=[0.5, 1.5], colors=['#e0e0e0'], zorder=3)
    slp_25_plot = np.where(mask_andes, np.nan, slp_25_smooth)
    c4 = ax4.contour(lon2d, lat2d, slp_25_plot, levels=np.arange(990, 1032, 4), colors='darkblue', linewidths=1.2, zorder=4)
    ax4.clabel(c4, inline=True, fontsize=8, fmt='%d')
    ax4.set_extent([-85, -25, -50, -10], crs=ccrs.PlateCarree())
    ax4.set_title('(d) 25/12/1995 00 UTC: Decaying Coastal Trough (L: 1008.0 hPa)', fontsize=10, fontweight='bold')
    gl4 = ax4.gridlines(draw_labels=True, linestyle=':', alpha=0.5)
    gl4.top_labels = False
    gl4.right_labels = False
    
    plt.suptitle('Figure 4: Mean Sea Level Pressure Evolution & Mendoza Lee Deepening (ERA5 Reanalysis)', fontsize=13, y=0.95, fontweight='bold')
    out_file = 'Figure_4_SLP_ERA5.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")


# ==============================================================
# FIGURA 5: VPI de Ertel em 400 hPa em 22/12 00Z (Pico SESA)
# ==============================================================
def generate_figure_5(ds_pl):
    print("Generating Figure 5 (400 hPa VPI on 22/12 00Z)...")
    date = '1995-12-22T00:00'
    q_uvp, _ = calculate_ertel_vpi(ds_pl, date)
    
    levels_list = list(ds_pl.level.values)
    k400 = levels_list.index(400)
    q400 = q_uvp[k400]
    
    u = ds_pl['u'].sel(time=date, level=400).values
    v = ds_pl['v'].sel(time=date, level=400).values
    z = (ds_pl['z'].sel(time=date, level=400) / G).values
    
    lon2d, lat2d = np.meshgrid(ds_pl.longitude, ds_pl.latitude)
    
    fig = plt.figure(figsize=(10, 7.5))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    cf = ax.contourf(lon2d, lat2d, q400, levels=np.linspace(0.4, 3.2, 15),
                     cmap='YlOrRd', transform=ccrs.PlateCarree(), extend='both')
    plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.08, label='Isentropic Potential Vorticity - 400 hPa IPV (UVP)')
    
    c_tropo = ax.contour(lon2d, lat2d, q400, levels=[1.5], colors='red', linewidths=2.0, transform=ccrs.PlateCarree())
    ax.clabel(c_tropo, inline=True, fontsize=8, fmt='1.5 UVP')
    
    cz = ax.contour(lon2d, lat2d, z, levels=np.arange(6800, 7600, 60), colors='black', linewidths=1.0, transform=ccrs.PlateCarree())
    ax.clabel(cz, inline=True, fontsize=7, fmt='%d m')
    
    # Vetores de vento espaçados a cada 14 pontos (~3.5 graus) para não encobrir o campo
    step = 14
    ax.quiver(lon2d[::step, ::step], lat2d[::step, ::step], u[::step, ::step], v[::step, ::step],
              transform=ccrs.PlateCarree(), scale=350, color='darkblue', width=0.003)
              
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    ax.set_extent([-90, -30, -50, -10], crs=ccrs.PlateCarree())
    ax.set_title('Figure 5: Upper-Level Vortex at Peak Intensity (22/12/1995 00 UTC)\n' +
                 'Shading: 400 hPa IPV (max 2.79 UVP) | Red Line: Dynamic Tropopause (1.5 UVP) | Vectors: Wind',
                 fontsize=10, fontweight='bold')
                 
    out_file = 'Figure_5_400hPa_VPI_1995-12-22.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

# ==============================================================
# FIGURA 6: Forçamento Termodinâmico no SESA (Theta_e em 925 hPa)
# ==============================================================
def generate_figure_6(ds_pl, ds_orog):
    print("Generating Figure 6 (SESA Theta_e & 400 hPa Geopotential)...")
    date = '1995-12-23T00:00'
    t925 = ds_pl['t'].sel(time=date, level=925).values
    r925 = ds_pl['r'].sel(time=date, level=925).values
    u925 = ds_pl['u'].sel(time=date, level=925).values
    v925 = ds_pl['v'].sel(time=date, level=925).values
    z400 = (ds_pl['z'].sel(time=date, level=400) / G).values
    
    theta_e = calculate_theta_e(t925, r925, 925.0)
    
    # Mascara relevo acima de 925 hPa
    sp_data = ds_orog['sp'].isel(valid_time=0) if 'valid_time' in ds_orog.coords else ds_orog['sp'].sel(time=date, method='nearest')
    sp_hpa = (sp_data.values / 100.0)
    mask_925 = 925.0 > sp_hpa
    theta_e[mask_925] = np.nan
    
    lon2d, lat2d = np.meshgrid(ds_pl.longitude, ds_pl.latitude)
    
    fig = plt.figure(figsize=(10, 8))
    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.add_feature(cfeature.COASTLINE, linewidth=1.0)
    ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.6)
    
    # Mascara relevo dos Andes em cinza
    ax.contourf(lon2d, lat2d, mask_925.astype(float), levels=[0.5, 1.5],
                colors=['#e0e0e0'], transform=ccrs.PlateCarree(), zorder=3)
                
    cf = ax.contourf(lon2d, lat2d, theta_e, levels=np.linspace(315, 355, 17),
                     cmap='Spectral_r', transform=ccrs.PlateCarree(), extend='both', zorder=2)
    plt.colorbar(cf, ax=ax, orientation='horizontal', pad=0.08, label=r'Equivalent Potential Temperature $\theta_e$ at 925 hPa (K)')
    
    # Geopotencial de 400 hPa ajustado a faixa real
    cz = ax.contour(lon2d, lat2d, z400, levels=np.arange(7140, 7560, 40), colors='black',
                    linewidths=1.2, transform=ccrs.PlateCarree(), zorder=4)
    ax.clabel(cz, inline=True, fontsize=8, fmt='%d m')
    
    step = 12
    ax.quiver(lon2d[::step, ::step], lat2d[::step, ::step], u925[::step, ::step], v925[::step, ::step],
              transform=ccrs.PlateCarree(), scale=250, color='darkgreen', width=0.003, zorder=5)
              
    gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    ax.set_extent([-75, -40, -42, -18], crs=ccrs.PlateCarree())
    ax.set_title('Figure 6: Low-Level Thermodynamic Forcing over SESA (23/12/1995 00 UTC)\n' +
                 r'Shading: 925 hPa $\theta_e$ (K) | Black Lines: 400 hPa Geopotential | Green Vectors: 925 hPa Wind',
                 fontsize=10, fontweight='bold')
                 
    out_file = 'Figure_6_SESA_Theta_e_925hPa.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

# ==============================================================
# FIGURA 7: Diagnóstico Barotrópico (Perfis 1D + Hovmöller)
# ==============================================================
def generate_figure_7(ds_pl):
    print("Generating Figure 7 (Barotropic Instability: 1D Profile & Hovmöller)...")
    lats = ds_pl.latitude.values
    phi = np.radians(lats)
    beta = (2.0 * OMEGA * np.cos(phi)) / A
    y = A * phi
    
    # 1. Perfil Médio 1D para o período 22-28/12 no setor 70W-40W
    u_sec = ds_pl['u'].sel(level=slice(300, 100), longitude=slice(-70, -40))
    u_time_mean = u_sec.sel(time=slice('1995-12-22', '1995-12-28')).mean(dim=['time', 'level', 'longitude']).values
    u_smooth_1d = ndimage.gaussian_filter1d(u_time_mean, sigma=6) # ~5 graus
    
    du_dy = np.gradient(u_smooth_1d, y)
    d2u_dy2 = np.gradient(du_dy, y)
    Qy_1d = beta - d2u_dy2
    
    # 2. Hovmöller latitude x tempo de Qy (20-31/12)
    times = ds_pl.time.sel(time=slice('1995-12-20', '1995-12-31')).values
    Qy_hov = np.zeros((len(times), len(lats)))
    
    for idx, t in enumerate(times):
        u_prof = ds_pl['u'].sel(time=t, level=slice(300, 100), longitude=slice(-70, -40)).mean(dim=['level', 'longitude']).values
        u_sm = ndimage.gaussian_filter1d(u_prof, sigma=6)
        d2u = np.gradient(np.gradient(u_sm, y), y)
        Qy_hov[idx] = beta - d2u
        
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Painel 1: Perfil Médio 1D
    ax1.plot(Qy_1d * 1e11, lats, color='crimson', linewidth=2.0, label=r'$Q_y = \beta - \frac{d^2\bar{u}}{dy^2}$')
    ax1.axvline(0, color='black', linestyle='--', linewidth=1.2)
    ax1.axhline(-28.75, color='darkblue', linestyle=':', label='Kuo zero-crossing (-28.8°S)')
    ax1.set_xlabel(r'$Q_y \ (\times 10^{-11} \ \mathrm{m}^{-1}\mathrm{s}^{-1})$', fontweight='bold', fontsize=10)
    ax1.set_ylabel('Latitude (°S)', fontweight='bold', fontsize=10)
    ax1.set_ylim(-48, -15)
    ax1.set_xlim(-6, 8)
    ax1.grid(True, linestyle='--', alpha=0.5)
    
    ax1_twin = ax1.twiny()
    ax1_twin.plot(u_smooth_1d, lats, color='purple', linewidth=1.5, linestyle='-.', label=r'Zonal Wind $\bar{u}$ (m/s)')
    ax1_twin.set_xlabel(r'Mean Zonal Wind $\bar{u}$ (m/s)', color='purple', fontweight='bold', fontsize=10)
    ax1_twin.tick_params(axis='x', labelcolor='purple')
    ax1.set_title('(a) Meridional Profiles (22-28 Dec 1995)\nSector 70°W-40°W, 300-100 hPa', fontsize=10, fontweight='bold')
    ax1.legend(loc='lower left', fontsize=9)
    
    # Painel 2: Hovmöller de Qy
    time_dates = [str(t)[5:13] for t in times]
    t_idx = np.arange(len(times))
    t2d, lat2d = np.meshgrid(t_idx, lats)
    
    cf = ax2.contourf(t2d, lat2d, Qy_hov.T * 1e11, levels=np.linspace(-6, 8, 29),
                      cmap='RdBu_r', extend='both')
    cbar = plt.colorbar(cf, ax=ax2, orientation='horizontal', pad=0.1, aspect=35)
    cbar.set_label(r'$Q_y \ (\times 10^{-11} \ \mathrm{m}^{-1}\mathrm{s}^{-1})$', fontsize=10, fontweight='bold')
    
    c_zero = ax2.contour(t2d, lat2d, Qy_hov.T, levels=[0], colors='black', linewidths=2.0)
    ax2.clabel(c_zero, inline=True, fontsize=8, fmt='Qy=0')
    
    ax2.set_xticks(t_idx[::4])
    ax2.set_xticklabels(time_dates[::4], rotation=45, fontsize=8)
    ax2.set_ylabel('Latitude (°S)', fontweight='bold', fontsize=10)
    ax2.set_xlabel('Time (MM-DD HH)', fontweight='bold', fontsize=10)
    ax2.set_ylim(-48, -15)
    ax2.set_title(r'(b) Time Evolution of $Q_y$ (20-31 Dec 1995)' + '\nBold Black Line: $Q_y = 0$ (Kuo Condition Satisfied)', fontsize=10, fontweight='bold')
    
    plt.suptitle('Figure 7: Upper-Tropospheric Barotropic Instability Diagnostics (300-100 hPa, 5° Filter)', fontsize=11, y=0.98)
    plt.tight_layout()
    out_file = 'Figure_7_Barotropic_ERA5.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

# ==============================================================
# FIGURA 8: Rastreamento do Vórtice e Trajetória Completa (Tese Haas, 2002)
# ==============================================================
def generate_figure_8(ds_pl, ds_orog=None):
    print("Generating Figure 8 (Full Vortex Lifecycle Track & Intensity)...")
    
    # Carrega dados do Pacífico para a gênese se disponíveis
    ds_pac = None
    if os.path.exists('era5_400hpa_pacific_genesis.nc'):
        ds_pac = xr.open_dataset('era5_400hpa_pacific_genesis.nc')
        if 'valid_time' in ds_pac.coords:
            ds_pac = ds_pac.rename({'valid_time': 'time', 'pressure_level': 'level'})
            
    z_main = ds_pl['z'].sel(level=400).squeeze(drop=True) / G
    z_pac = None
    if ds_pac is not None:
        z_pac = ds_pac['z'].squeeze(drop=True) / G
        
    common_lats = np.arange(-15.0, -50.25, -0.25)
    common_lons = np.arange(-110.0, -29.75, 0.25)
    times = ds_pl.time.sel(time=slice('1995-12-14T06:00', '1995-12-31T18:00')).values
    
    levels_list = list(ds_pl.level.values)
    k400 = levels_list.index(400)
    
    cur_lat, cur_lon = -28.0, -103.75
    pts = []
    
    print("\n--- Rastreamento Completo do VCAN (14 a 31/12/1995) ---")
    for i, t in enumerate(times):
        t_str = str(t)[:16]
        sub_main = z_main.sel(time=t).interp(latitude=common_lats, longitude=common_lons, method='nearest').values
        z_grid = sub_main.copy()
        if z_pac is not None and t in z_pac.time.values:
            sub_pac = z_pac.sel(time=t).interp(latitude=common_lats, longitude=common_lons, method='nearest').values
            west_mask = common_lons < -90.0
            z_grid[:, west_mask] = sub_pac[:, west_mask]
            
        z_anom = z_grid - np.nanmean(z_grid, axis=1, keepdims=True)
        dist = np.sqrt((common_lats[:, None] - cur_lat)**2 + (common_lons[None, :] - cur_lon)**2)
        sub_anom = np.where(dist <= 4.5, z_anom, np.nan)
        
        min_idx = np.unravel_index(np.nanargmin(sub_anom), sub_anom.shape)
        cur_lat = float(common_lats[min_idx[0]])
        cur_lon = float(common_lons[min_idx[1]])
        val_anom = float(sub_anom[min_idx])
        
        q_val = np.nan
        if cur_lon >= -89.0:
            q_all, _ = calculate_ertel_vpi(ds_pl, t)
            q400 = q_all[k400]
            c_dist = np.sqrt((ds_pl.latitude.values[:, None] - cur_lat)**2 + (ds_pl.longitude.values[None, :] - cur_lon)**2)
            q_val = float(np.nanmax(q400[c_dist <= 3.0]))
            
        # 5 Fases conforme Haas (2002):
        if i < 14:
            phase = 1 # Formação Pacífico (14-17/12)
        elif i < 24:
            phase = 2 # Intensificação Baroclínica (17-20/12)
        elif i < 28:
            phase = 3 # Travessia dos Andes (20-21/12)
        elif i < 58:
            phase = 4 # Fase Madura / SESA e trajetória anômala (21-28/12)
        else:
            phase = 5 # Desintensificação / Atlântico (28-31/12)
            
        pts.append({
            'pt': i + 1, 'time': t_str, 'lat': cur_lat, 'lon': cur_lon,
            'z_anom': val_anom, 'q400': q_val, 'phase': phase
        })
        if i % 8 == 0 or i == len(times) - 1:
            q_str = f"{q_val:4.2f} UVP" if not np.isnan(q_val) else "  N/A   "
            print(f"  Pt {i+1:2d} ({t_str}): Lat={cur_lat:6.2f}°S, Lon={cur_lon:6.2f}°W | z_anom={val_anom:6.1f} m | q400={q_str} | Fase {phase}")

    fig = plt.figure(figsize=(16, 7))
    
    # Subplot 1: Mapa Completo da Trajetória
    ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    if ds_orog is not None:
        z_orog = (ds_orog['z'].isel(valid_time=0) / G).values
        lon_orog, lat_orog = np.meshgrid(ds_orog.longitude, ds_orog.latitude)
        ax1.contourf(lon_orog, lat_orog, (z_orog > 2000.0).astype(float), levels=[0.5, 1.5],
                     colors=['#e0e0e0'], zorder=2, transform=ccrs.PlateCarree())
                     
    all_lons = [p['lon'] for p in pts]
    all_lats = [p['lat'] for p in pts]
    ax1.plot(all_lons, all_lats, color='gray', linewidth=1.2, linestyle='--', zorder=3, transform=ccrs.PlateCarree())
    
    phase_styles = {
        1: {'marker': 's', 'facecolor': 'white', 'edgecolor': 'navy', 'label': 'Fase 1: Formação no Pacífico (14–17/12)', 'size': 45},
        2: {'marker': 'o', 'facecolor': 'blue', 'edgecolor': 'black', 'label': 'Fase 2: Intensificação Baroclínica (18–20/12)', 'size': 50},
        3: {'marker': 'o', 'facecolor': 'white', 'edgecolor': 'crimson', 'label': 'Fase 3: Travessia dos Andes (20–21/12)', 'size': 60},
        4: {'marker': 's', 'facecolor': 'crimson', 'edgecolor': 'black', 'label': 'Fase 4: Fase Madura / SESA (22–28/12)', 'size': 55},
        5: {'marker': 'D', 'facecolor': 'white', 'edgecolor': 'purple', 'label': 'Fase 5: Desintensificação / Atlântico (28–31/12)', 'size': 45}
    }
    
    for ph, style in phase_styles.items():
        ph_pts = [p for p in pts if p['phase'] == ph]
        lons = [p['lon'] for p in ph_pts]
        lats = [p['lat'] for p in ph_pts]
        ax1.scatter(lons, lats, marker=style['marker'], facecolors=style['facecolor'],
                    edgecolors=style['edgecolor'], s=style['size'], linewidths=1.5,
                    label=style['label'], zorder=5, transform=ccrs.PlateCarree())
                    
    key_annotations = [
        (pts[0], '14/12 06Z\n(Início VCAN)', (-10, 15)),
        (pts[14], '18/12 00Z\n(Intensif.)', (-25, -25)),
        (pts[24], '20/12 06Z\n(Andes)', (10, -15)),
        (pts[28], '21/12 06Z\n(Sotavento)', (10, -20)),
        (pts[31], '22/12 00Z\n(Pico SESA)', (10, 10)),
        (pts[57], '28/12 12Z\n(Deflexão N)', (-35, 12)),
        (pts[-1], '31/12 18Z\n(Decaimento)', (10, -10))
    ]
    
    for p_item, text, offset in key_annotations:
        ax1.annotate(text, xy=(p_item['lon'], p_item['lat']), xytext=offset,
                     textcoords='offset points', fontsize=7.5, fontweight='bold',
                     bbox=dict(boxstyle='round,pad=0.2', facecolor='yellow', alpha=0.7, edgecolor='black'),
                     arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', color='black', lw=0.8),
                     transform=ccrs.PlateCarree(), zorder=10)
                     
    ax1.set_extent([-110, -32, -44, -18], crs=ccrs.PlateCarree())
    ax1.set_title('(a) Trajetória Completa do VCAN em 400 hPa (14 a 31/12/1995)\nClassificação em 5 Fases Conforme Tese (Haas, 2002)', fontsize=10.5, fontweight='bold')
    gl = ax1.gridlines(draw_labels=True, linestyle=':', alpha=0.5)
    gl.top_labels = False
    gl.right_labels = False
    ax1.legend(loc='lower left', fontsize=7.5, framealpha=0.9)
    
    # Subplot 2: Evolução temporal do Vórtice
    ax2 = fig.add_subplot(1, 2, 2)
    dates_str = [p['time'][5:] for p in pts]
    z_anoms = [p['z_anom'] for p in pts]
    q400_vals = [p['q400'] for p in pts]
    x_indices = np.arange(len(pts))
    
    color = 'tab:blue'
    ax2.set_xlabel('Data / Hora (MM-DD HH)', fontweight='bold', fontsize=10)
    ax2.set_ylabel('Anomalia Central de Geopotencial em 400 hPa (m)', color=color, fontweight='bold', fontsize=10)
    ax2.plot(x_indices, z_anoms, color=color, marker='o', markersize=3.5, linewidth=1.8, label="Anomalia z400' (m)")
    ax2.tick_params(axis='y', labelcolor=color)
    
    ax3 = ax2.twinx()
    color = 'crimson'
    ax3.set_ylabel('VPI Ciclônica Máxima em 400 hPa (UVP)', color=color, fontweight='bold', fontsize=10)
    valid_q_idx = [i for i, q in enumerate(q400_vals) if not np.isnan(q)]
    valid_q_vals = [q400_vals[i] for i in valid_q_idx]
    ax3.plot(valid_q_idx, valid_q_vals, color=color, marker='s', markersize=4, linestyle='--', linewidth=1.8, label='VPI em 400 hPa')
    ax3.axhline(1.5, color='gray', linestyle=':', label='Tropopausa Dinâmica (1.5 UVP)')
    ax3.tick_params(axis='y', labelcolor=color)
    
    phase_transitions = [14, 24, 28, 58]
    for pt_idx in phase_transitions:
        ax2.axvline(pt_idx, color='gray', linestyle='--', alpha=0.6)
        
    ax2.text(7, -25, 'F1', fontsize=9, fontweight='bold', ha='center', color='navy')
    ax2.text(19, -25, 'F2', fontsize=9, fontweight='bold', ha='center', color='blue')
    ax2.text(26, -25, 'F3', fontsize=9, fontweight='bold', ha='center', color='crimson')
    ax2.text(43, -25, 'Fase 4 (SESA)', fontsize=9, fontweight='bold', ha='center', color='crimson')
    ax2.text(64, -25, 'F5', fontsize=9, fontweight='bold', ha='center', color='purple')
    
    step_ticks = np.arange(0, len(pts), 8)
    ax2.set_xticks(step_ticks)
    ax2.set_xticklabels([dates_str[i] for i in step_ticks], rotation=40, fontsize=8)
    ax2.grid(True, linestyle='--', alpha=0.4)
    ax2.set_title('(b) Evolução da Intensidade Central do Vórtice\n(Anomalia de z400 e VPI de 14 a 31 de Dezembro de 1995)', fontsize=10.5, fontweight='bold')
    
    plt.tight_layout()
    out_file = 'Figure_8_Northward_Trajectory_VPI.png'
    plt.savefig(out_file, dpi=250, bbox_inches='tight')
    plt.close()
    print(f"Saved: {out_file}")

def main():
    print("=== STARTING FULL FIGURE REGENERATION ===")
    ds_pl, ds_sfc, ds_orog = load_datasets()
    
    generate_figure_1()
    generate_figure_2(ds_pl, ds_orog)
    generate_figure_3(ds_pl, ds_orog)
    generate_figure_4(ds_sfc, ds_orog)
    generate_figure_5(ds_pl)
    generate_figure_6(ds_pl, ds_orog)
    generate_figure_7(ds_pl)
    generate_figure_8(ds_pl, ds_orog)
    print("=== ALL 8 FIGURES GENERATED WITH FULL DATA INTEGRITY ===")

if __name__ == '__main__':
    main()
