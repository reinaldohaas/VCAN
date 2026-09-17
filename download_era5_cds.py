import cdsapi
import os

def download_era5():
    """
    Script para baixar os dados do ERA5 (Copernicus Climate Data Store)
    necessários para recriar as figuras do artigo sobre o VCAN (Dez/1995).
    
    Atenção: É necessário ter o cdsapi configurado (~/.cdsapirc).
    """
    c = cdsapi.Client()
    
    # Baixando variáveis em níveis de pressão (Necessário para VPI, perfis e Qy)
    # Níveis típicos para VPI: 1000 a 10 hPa (selecionamos os principais)
    print("Baixando dados do ERA5 em níveis de pressão...")
    c.retrieve(
        'reanalysis-era5-pressure-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': [
                'geopotential', 'temperature', 'u_component_of_wind',
                'v_component_of_wind', 'relative_vorticity'
            ],
            'pressure_level': [
                '100', '150', '200', '250', '300', '400', '500',
                '600', '700', '850', '925', '1000',
            ],
            'year': '1995',
            'month': '12',
            'day': [
                '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'
            ],
            'time': [
                '00:00', '06:00', '12:00', '18:00',
            ],
            'area': [
                0, -90, -60, -30, # Norte, Oeste, Sul, Leste
            ],
        },
        'era5_pressure_levels_vcan_1995.nc')
        
    print("Baixando dados do ERA5 em superfície...")
    c.retrieve(
        'reanalysis-era5-single-levels',
        {
            'product_type': 'reanalysis',
            'format': 'netcdf',
            'variable': [
                'mean_sea_level_pressure', '2m_temperature',
                'sea_surface_temperature'
            ],
            'year': '1995',
            'month': '12',
            'day': [
                '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20',
                '21', '22', '23', '24', '25', '26', '27', '28', '29', '30', '31'
            ],
            'time': [
                '00:00', '06:00', '12:00', '18:00',
            ],
            'area': [
                0, -90, -60, -30,
            ],
        },
        'era5_surface_vcan_1995.nc')

if __name__ == '__main__':
    download_era5()
