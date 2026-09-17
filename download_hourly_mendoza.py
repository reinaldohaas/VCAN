import cdsapi

c = cdsapi.Client()

print("Requesting hourly ERA5 surface data for Mendoza/Cuyo region (18-22 Dec 1995)...")
c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'format': 'netcdf',
        'variable': [
            'mean_sea_level_pressure', 'surface_pressure', '2m_temperature'
        ],
        'year': '1995',
        'month': '12',
        'day': ['18', '19', '20', '21', '22'],
        'time': [f'{h:02d}:00' for h in range(24)],
        'area': [-25, -73, -38, -63],
    },
    'era5_hourly_mendoza_1995.nc'
)
print("Download completed: era5_hourly_mendoza_1995.nc")
