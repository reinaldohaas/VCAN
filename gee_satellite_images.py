import ee

def get_gee_satellite_data():
    """
    Exemplo de script para buscar imagens de satélite usando Google Earth Engine (GEE).
    Para imagens infravermelho (Figuras 1 e 8b) da década de 1990 (GOES-8).
    
    Atenção: É necessário autenticar primeiro rodando `earthengine authenticate` ou `ee.Authenticate()`.
    """
    try:
        # Inicializa com o seu projeto Google Cloud configurado
        ee.Initialize(project='labmit-ufsc-6aa9c')
    except Exception as e:
        print("Erro ao inicializar o Earth Engine. Por favor, rode 'earthengine authenticate' no seu terminal primeiro.")
        return

    # A coleção de imagens do GOES-8 no GEE. 
    # O GEE possui dados do NOAA CDR (Climate Data Record) como o GridSat-B1 (IR) que abrange o período.
    # Exemplo: NOAA/CDR/GRIDSAT-B1/V2
    
    dataset = ee.ImageCollection('NOAA/CDR/GRIDSAT-B1/V2') \
                .filterDate('1995-12-14', '1995-12-15')
                
    image = dataset.first()
    
    # Seleciona a banda do infravermelho (irwin_cdr)
    ir_band = image.select('irwin_cdr')
    
    # URL para baixar a imagem para visualização
    url = ir_band.getThumbURL({
        'min': 180,
        'max': 300,
        'dimensions': 800,
        'region': ee.Geometry.Rectangle([-90, -60, -30, 0]),
        'palette': ['white', 'black'] # Nuvem fria = branco, superfície quente = preto
    })
    
    print("URL da imagem de satélite (GridSat-B1 IR proxy para GOES-8):")
    print(url)
    print("Você pode baixar esta imagem para recriar as Figuras 1 e 8b.")

if __name__ == '__main__':
    get_gee_satellite_data()
