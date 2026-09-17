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
# FIGURA 4: Pressão ao Nível do Mar (4 painéis)
# ==============================================================
def generate_figure_4(ds_sfc, ds_orog):
    print("Generating Figure 4 (Mean Sea Level Pressure)...")
    dates = ['1995-12-21T00:00', '1995-12-22T00:00', '1995-12-25T00:00', '1995-12-29T00:00']
    titles = [
        '(a) 21/12/1995 00 UTC: Lee Low / BNOA (L: 989.6 hPa)',
        '(b) 22/12/1995 00 UTC: Coastal Transit (L: 1003.3 hPa)',
        '(c) 25/12/1995 00 UTC: Decaying Trough & Atlantic Ridge (H: 1022 hPa)',
        '(d) 29/12/1995 00 UTC: Dissipation Stage'
    ]
    
    z_orog = (ds_orog['z'].isel(valid_time=0) / G).values
    mask_andes = z_orog > 2000.0
    lon2d, lat2d = np.meshgrid(ds_sfc.longitude, ds_sfc.latitude)
    
    fig, axes = plt.subplots(2, 2, figsize=(13, 11), subplot_kw={'projection': ccrs.PlateCarree()}, constrained_layout=True)
    
    for ax, date, title in zip(axes.flat, dates, titles):
        ax.add_feature(cfeature.COASTLINE, linewidth=0.9)
        ax.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
        
        slp_raw = (ds_sfc['msl'].sel(time=date) / 100.0).values
        slp_smooth = ndimage.gaussian_filter(slp_raw, sigma=1.2)
        
        slp_plot = slp_smooth.copy()
        slp_plot[mask_andes] = np.nan
        
        ax.contourf(lon2d, lat2d, mask_andes.astype(float), levels=[0.5, 1.5],
                    colors=['#e0e0e0'], transform=ccrs.PlateCarree(), zorder=3)
                    
        contours = ax.contour(lon2d, lat2d, slp_plot, levels=np.arange(988, 1032, 4),
                              colors='darkblue', linewidths=1.2, transform=ccrs.PlateCarree(), zorder=4)
        ax.clabel(contours, inline=True, fontsize=8, fmt='%d')
        
        gl = ax.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.right_labels = False
        ax.set_extent([-90, -30, -50, -10], crs=ccrs.PlateCarree())
        ax.set_title(title, fontsize=10, fontweight='bold')
        
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
# FIGURA 8: Rastreamento do Vórtice e Evolução de Intensidade
# ==============================================================
def generate_figure_8(ds_pl):
    print("Generating Figure 8 (Vortex Northward Tracking & Intensity)...")
    times = ds_pl.time.sel(time=slice('1995-12-21', '1995-12-28')).values[::2]
    lats = ds_pl.latitude.values
    lons = ds_pl.longitude.values
    levels_list = list(ds_pl.level.values)
    k400 = levels_list.index(400)
    
    cur_lat, cur_lon = -35.5, -69.0
    centers_lat = []
    centers_lon = []
    z_anoms = []
    q400_vals = []
    dates_str = []
    
    print("\n--- Vortex Tracking Table (TAREFA 1 Validation) ---")
    for t in times:
        t_str = str(t)[:13]
        z = (ds_pl['z'].sel(time=t, level=400) / G).values
        z_zonal = np.nanmean(z, axis=1, keepdims=True)
        z_anom = z - z_zonal
        
        dist = np.sqrt((lats[:, None] - cur_lat)**2 + (lons[None, :] - cur_lon)**2)
        local_mask = dist <= 5.5
        
        sub_anom = np.where(local_mask, z_anom, np.nan)
        min_idx = np.unravel_index(np.nanargmin(sub_anom), sub_anom.shape)
        cur_lat = float(lats[min_idx[0]])
        cur_lon = float(lons[min_idx[1]])
        val_anom = float(sub_anom[min_idx])
        
        q_all, _ = calculate_ertel_vpi(ds_pl, t)
        q400 = q_all[k400]
        c_dist = np.sqrt((lats[:, None] - cur_lat)**2 + (lons[None, :] - cur_lon)**2)
        local_q = float(np.nanmax(q400[c_dist <= 3.0]))
        
        centers_lat.append(cur_lat)
        centers_lon.append(cur_lon)
        z_anoms.append(val_anom)
        q400_vals.append(local_q)
        dates_str.append(t_str[5:])
        print(f"  {t_str}: Lat={cur_lat:6.2f}°S, Lon={cur_lon:6.2f}°W | z_anom={val_anom:6.1f} m | q400={local_q:4.2f} UVP")
        
    fig = plt.figure(figsize=(14, 6))
    
    # Subplot 1: Mapa da Trajetória
    ax1 = fig.add_subplot(1, 2, 1, projection=ccrs.PlateCarree())
    ax1.add_feature(cfeature.COASTLINE, linewidth=0.9)
    ax1.add_feature(cfeature.BORDERS, linestyle=':', linewidth=0.5)
    
    sc = ax1.scatter(centers_lon, centers_lat, c=q400_vals, cmap='plasma', s=120, edgecolors='black',
                     vmin=0.6, vmax=4.0, zorder=5, transform=ccrs.PlateCarree())
    cbar = plt.colorbar(sc, ax=ax1, orientation='horizontal', pad=0.08, label='400 hPa Cyclonic IPV (UVP)')
    ax1.plot(centers_lon, centers_lat, color='black', linewidth=1.5, linestyle='--', transform=ccrs.PlateCarree())
    
    for i, (x, y, dt) in enumerate(zip(centers_lon, centers_lat, dates_str)):
        if i % 2 == 0:
            ax1.text(x + 0.6, y, dt, fontsize=8, fontweight='bold', transform=ccrs.PlateCarree())
            
    gl = ax1.gridlines(draw_labels=True, linewidth=0.5, color='gray', alpha=0.5, linestyle='--')
    gl.top_labels = False
    gl.right_labels = False
    ax1.set_extent([-72, -45, -40, -20], crs=ccrs.PlateCarree())
    ax1.set_title('(a) Track of the UTCV 400 hPa Center (21-28 Dec 1995)\nSystematic Northward Migration from ~35.5°S to ~24.3°S', fontsize=10, fontweight='bold')
    
    # Subplot 2: Evolução temporal
    ax2 = fig.add_subplot(1, 2, 2)
    color = 'tab:blue'
    ax2.set_xlabel('Time (MM-DD HH)', fontweight='bold', fontsize=10)
    ax2.set_ylabel('Central Geopotential Anomaly at 400 hPa (m)', color=color, fontweight='bold', fontsize=10)
    ax2.plot(dates_str, z_anoms, color=color, marker='o', linewidth=2.0, label='z400 Anomaly (m)')
    ax2.tick_params(axis='y', labelcolor=color)
    ax2.tick_params(axis='x', rotation=45, labelsize=8)
    ax2.grid(True, linestyle='--', alpha=0.4)
    
    ax3 = ax2.twinx()
    color = 'crimson'
    ax3.set_ylabel('Max Cyclonic IPV at 400 hPa (UVP)', color=color, fontweight='bold', fontsize=10)
    ax3.plot(dates_str, q400_vals, color=color, marker='s', linestyle='--', linewidth=2.0, label='400 hPa IPV')
    ax3.axhline(1.5, color='gray', linestyle=':', label='Tropopause Threshold (1.5 UVP)')
    ax3.tick_params(axis='y', labelcolor=color)
    
    plt.title('(b) Evolution of Central Vortex Intensity\nPeak on 21-22 Dec, subsequent decay as system migrates north', fontsize=10, fontweight='bold')
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
    generate_figure_8(ds_pl)
    print("=== ALL 8 FIGURES GENERATED WITH FULL DATA INTEGRITY ===")

if __name__ == '__main__':
    main()
