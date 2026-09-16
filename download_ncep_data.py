import os
import xarray as xr
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np

# Definindo o período e a região de interesse para o VCAN de dez/1995
# A região analisada no artigo abrange a América do Sul
lon_slice = slice(270, 330) # 90W a 30W
lat_slice = slice(0, -60)   # 0 a 60S
time_slice = slice('1995-12-10', '1995-12-31')

def download_and_subset_ncep(variable, level_type='pressure'):
    """
    Baixa os dados do NCEP/NCAR Reanalysis via OPeNDAP para a região e período necessários.
    """
    print(f"Baixando dados para a variável: {variable}")
    if level_type == 'pressure':
        url = f"https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/pressure/{variable}.1995.nc"
    else:
        url = f"https://psl.noaa.gov/thredds/dodsC/Datasets/ncep.reanalysis.dailyavgs/surface/{variable}.1995.nc"
    
    try:
        ds = xr.open_dataset(url)
        # Recortando tempo e espaço
        ds_subset = ds.sel(time=time_slice, lon=lon_slice, lat=lat_slice)
        
        # Salvando os dados localmente
        out_file = f"{variable}_1995_subset.nc"
        ds_subset.to_netcdf(out_file)
        print(f"Dados salvos em {out_file}")
        return ds_subset
    except Exception as e:
        print(f"Erro ao baixar {variable}: {e}")
        return None

def main():
    # 1. Download de variáveis essenciais para cálculo de VPI (Vorticidade Potencial Isentrópica)
    # Variáveis: Vento zonal (uwnd), Vento meridional (vwnd), Temperatura (air), Geopotencial (hgt)
    # E para superfície: Pressão ao nível do mar (slp)
    vars_pl = ['uwnd', 'vwnd', 'air', 'hgt']
    
    for var in vars_pl:
        download_and_subset_ncep(var, 'pressure')
        
    download_and_subset_ncep('slp', 'surface')
    
    print("Processo concluído. Os dados foram recortados para a região do VCAN e salvos em arquivos NetCDF.")

if __name__ == "__main__":
    main()
