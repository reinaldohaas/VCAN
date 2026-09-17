import docx
from docx.shared import Inches, Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
import os

def create_rbmet_docx():
    doc = docx.Document()

    # 1. Configuração de Margens: 2.5 cm em todos os lados
    for section in doc.sections:
        section.top_margin = Cm(2.5)
        section.bottom_margin = Cm(2.5)
        section.left_margin = Cm(2.5)
        section.right_margin = Cm(2.5)
        
        # Ativa Numeração Contínua de Linhas para Peer Review
        sectPr = section._sectPr
        lnNumType = OxmlElement('w:lnNumType')
        lnNumType.set(qn('w:countBy'), '1')
        lnNumType.set(qn('w:restart'), 'continuous')
        sectPr.append(lnNumType)

    # 2. Configuração de Estilos e Fontes: Times New Roman 12 pt, Espaçamento 1.5
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0, 0, 0)
    normal_style.paragraph_format.line_spacing = 1.5
    normal_style.paragraph_format.space_after = Pt(6)
    normal_style.paragraph_format.space_before = Pt(0)

    # Helper para adicionar parágrafo padrão
    def add_p(text, bold=False, italic=False, align=WD_ALIGN_PARAGRAPH.JUSTIFY):
        p = doc.add_paragraph()
        p.alignment = align
        run = p.add_run(text)
        run.bold = bold
        run.italic = italic
        run.font.name = 'Times New Roman'
        run.font.size = Pt(12)
        return p

    # Helper para adicionar títulos de seção
    def add_heading(text, level=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(12)
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(text)
        run.bold = True
        run.font.name = 'Times New Roman'
        if level == 1:
            run.font.size = Pt(13)
        else:
            run.font.size = Pt(12)
        return p

    # Helper para adicionar figura com legenda
    def add_figure(img_path, caption_text, width_inches=6.0):
        if os.path.exists(img_path):
            p_img = doc.add_paragraph()
            p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_img.paragraph_format.space_before = Pt(8)
            p_img.paragraph_format.space_after = Pt(4)
            p_img.paragraph_format.keep_with_next = True
            run_img = p_img.add_run()
            run_img.add_picture(img_path, width=Inches(width_inches))

            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_before = Pt(2)
            p_cap.paragraph_format.space_after = Pt(12)
            run_cap = p_cap.add_run(caption_text)
            run_cap.font.name = 'Times New Roman'
            run_cap.font.size = Pt(10)
            run_cap.italic = True
        else:
            print(f"Aviso: Imagem não encontrada: {img_path}")

    # --- CABEÇALHO E TÍTULO ---
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_after = Pt(12)
    run_title = p_title.add_run("Analysis of the Evolution of the Upper Tropospheric Cyclonic Vortex of December 1995 over Southeastern South America Based on Isentropic Potential Vorticity")
    run_title.bold = True
    run_title.font.size = Pt(14)

    p_author = doc.add_paragraph()
    p_author.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_author.paragraph_format.space_after = Pt(18)
    run_author = p_author.add_run("Reinaldo Haas\nDepartment of Physics / Center for Physical and Mathematical Sciences\nFederal University of Santa Catarina (UFSC), Florianópolis - SC, Brazil\nContact: reinaldo.haas@ufsc.br")
    run_author.font.size = Pt(11)

    # --- ABSTRACT & KEYWORDS ---
    add_heading("ABSTRACT", level=1)
    add_p("During the last two weeks of December 1995, a synoptic baroclinic disturbance crossed the Andes Cordillera and evolved into a long-lived Upper Tropospheric Cyclonic Vortex (UTCV) that propagated anomalously northeastward along the southern and southeastern coast of Brazil. The system induced widespread extreme precipitation episodes, flash floods, and substantial socio-economic damage, including an extreme 24-hour rainfall of 411 mm recorded at the Epagri Itacorubi (Itacurubi) station in Florianópolis, Santa Catarina. In this study, the dynamic and thermodynamic lifecycle of the UTCV is investigated within the framework of Isentropic Potential Vorticity (IPV thinking; Hoskins et al., 1985) using the high-resolution ECMWF Reanalysis v5 (ERA5, 0.25° × 0.25°) and NOAA GridSat-B1 calibrated geostationary infrared observations. Our diagnostic results demonstrate that: (1) baroclinic coupling between an upper-level tropopause fold (q ≥ 1.5 UVP at 400 hPa) and a shallow boundary-layer cyclonic IPV anomaly dammed west of the Chilean coast pre-conditioned the initial intensification; (2) during Andean transit, the vortex axis tilted eastward before realigning vertically on the lee side into an equivalent barotropic column, inducing regional lee cyclogenesis associated with the Northwestern Argentine Low (BNOA; minimum sea level pressure of 989.6 hPa at 29.5°S, 66.5°W on 20/12 18 UTC); (3) upon reaching Southeastern South America (SESA), coastal re-intensification on 22/12 (peak 400 hPa IPV of 2.79 UVP) was maintained by low-level moisture convergence and an equivalent potential temperature (θe) tongue (341–343 K at 925 hPa), where negative IPV values associated with the tower reached the surface driven by a marked tendency of IPV concentration; and (4) the anomalous northeastward displacement from 35.5°S to 24.3°S between 21 and 28 December was dynamically sustained by upper-tropospheric barotropic instability across 300–100 hPa, where the meridional gradient of absolute vorticity Q_y = β - d²ū/dy² reversed sign (crossing zero at ~28.8°S), satisfying Kuo's necessary instability condition.")
    add_p("Keywords: Upper Tropospheric Cyclonic Vortex; IPV Thinking; Lee Cyclogenesis; Barotropic Instability; Flash Floods; ERA5.")

    # --- RESUMO & PALAVRAS-CHAVE ---
    add_heading("RESUMO", level=1)
    add_p("Durante as duas últimas semanas de dezembro de 1995, um distúrbio baroclínico de escala sinótica transpôs a Cordilheira dos Andes e evoluiu para um Vórtice Ciclônico de Altos Níveis (VCAN) de longa duração que se deslocou de forma anômala para nordeste ao longo do litoral Sul e Sudeste do Brasil. O sistema provocou episódios generalizados de precipitação extrema, inundações bruscas e severos prejuízos socioeconômicos, com precipitação pluviométrica recorde de 411 mm registrada na estação Itacorubi (Itacurubi) da Epagri em Florianópolis (SC). Neste trabalho, o ciclo de vida dinâmico e termodinâmico do VCAN é investigado sob o arcabouço da Vorticidade Potencial Isentrópica (pensamento VPI; Hoskins et al., 1985) utilizando a reanálise de alta resolução ECMWF ERA5 (0,25° × 0,25°) e observações infravermelhas calibradas do satélite geoestacionário NOAA GridSat-B1. Os resultados diagnósticos revelam que: (1) o acoplamento baroclínico entre uma dobra de tropopausa em altos níveis (q ≥ 1,5 UVP em 400 hPa) e uma anomalia rasa de VPI ciclônica na camada limite represada a oeste da costa chilena pré-condicionou a intensificação inicial; (2) durante a travessia andina, o eixo vertical do vórtice inclinou-se para leste antes de se realinhar verticalmente a sotavento em uma coluna barotrópica equivalente, induzindo ciclogênese a sotavento associada à Baixa do Noroeste Argentino (BNOA; pressão ao nível médio do mar de 989,6 hPa em 29,5°S, 66,5°W em 20/12 18 UTC); (3) ao alcançar o Sudeste da América do Sul (SESA), a reintensificação costeira em 22/12 (pico de VPI em 400 hPa de 2,79 UVP) foi sustentada pela convergência de umidade em baixos níveis e por uma língua de temperatura potencial equivalente (θe de 341–343 K em 925 hPa), na qual valores de VPI negativa associados à torre atingiram a superfície sob forte tendência de concentração da VPI; e (4) o deslocamento anômalo para nordeste de 35,5°S para 24,3°S entre 21 e 28 de dezembro foi sustentado dinamicamente por instabilidade barotrópica na alta troposfera entre 300 e 100 hPa, onde o gradiente meridional de vorticidade absoluta Q_y = β - d²ū/dy² inverteu de sinal (cruzando o zero em ~28,8°S), satisfazendo o critério necessário de instabilidade de Kuo.")
    add_p("Palavras-chave: Vórtice Ciclônico de Altos Níveis; Pensamento VPI; Ciclogênese a Sotavento; Instabilidade Barotrópica; Inundações Bruscas; ERA5.")

    # --- 1. INTRODUCTION ---
    add_heading("1. INTRODUCTION", level=1)
    add_p("Extratropical and subtropical cyclonic disturbances in the midlatitudes of the Southern Hemisphere exert a dominant control over synoptic weather patterns, precipitation distribution, and severe convective outbreaks (Bjerknes and Solberg, 1922; Charney, 1947; Eady, 1949). In South America, upper-tropospheric cut-off lows and Upper Tropospheric Cyclonic Vortices (UTCVs, commonly designated as VCANs in South American literature) represent high-impact synoptic phenomena capable of causing catastrophic flash floods, prolonged storm surges, and landslides (Gan and Rao, 1994; Reboita et al., 2009; Iwabe et al., 2010).")
    add_p("Historically, cyclone analysis relied heavily on multi-level isobaric charts and Sutcliffe-Trenberton quasi-geostrophic diagnostic equations. However, the formulation of Ertel's Potential Vorticity theorem (Ertel, 1942; Rossby, 1940) and its modern revitalization into Isentropic Potential Vorticity (IPV) by Hoskins et al. (1985) established the paradigm known as 'IPV thinking' (Thorpe, 1985; Davis and Emanuel, 1991). By consolidating dynamic vorticity and thermodynamic stratification into a single conserved tracer under adiabatic, frictionless conditions, IPV analysis offers an intuitive and invertible framework to examine tropopause folds, vortex-vortex interactions, and baroclinic amplification.")
    add_p("Between December 10 and 31, 1995, an exceptional UTCV developed over the southeastern Pacific, traversed the high topography of the Andes Cordillera, and produced an unusually persistent cyclonic disturbance over Southeastern South America (SESA). Rather than progressing eastward or southeastward toward the South Atlantic along standard storm tracks (Ambrizzi and Pezza, 1999), this system executed an anomalous northeastward trajectory spanning four Brazilian states (Rio Grande do Sul, Santa Catarina, Paraná, and São Paulo) and generated record-breaking rainfall episodes and flash floods, with 24-hour rainfall reaching 411 mm at the Epagri Itacorubi (Itacurubi) station in Florianópolis (Haas, 2002).")
    add_p("Despite the severity of this event, previous investigations lacked high-resolution reanalysis datasets to unravel the complex interaction between the Andes barrier, boundary-layer thermodynamics, and upper-level shear instability. In this paper, we employ the 0.25° ECMWF ERA5 reanalysis and NOAA GridSat-B1 calibrated geostationary observations to provide a rigorous, dynamically consistent diagnosis of the formation, Andean transit, coastal re-intensification, and anomalous northward displacement of this remarkable vortex.")

    # --- 2. LITERATURE REVIEW ---
    add_heading("2. LITERATURE REVIEW", level=1)
    add_p("Classical baroclinic instability theory demonstrates that cyclonic development requires vertical wind shear and an westward-tilted vertical axis with height (Charney, 1947; Eady, 1949). In the IPV conceptual framework, this configuration corresponds to an upper-tropospheric positive (cyclonic) IPV anomaly located upshear (west) of a low-level warm thermal disturbance (Hoskins et al., 1985; Hirschberg and Fritsch, 1991). The cyclonic circulation induced by the upper IPV anomaly advects warm, moist air poleward, creating an effective positive low-level IPV anomaly. In return, the low-level thermal perturbation induces cyclonic circulation aloft, reinforcing the upper vortex in a self-amplifying mutual feedback loop.")
    add_p("The massive barrier of the Andes Cordillera (mean elevation exceeding 4,000 m between 20°S and 35°S) drastically alters transient baroclinic waves entering South America (Gan and Rao, 1994; Seluchi and Saulo, 2012). Numerical sensitivity experiments by Orlanski et al. (1991) and Funatsu et al. (2004) showed that orographic vortex compression on the windward slope followed by rapid vertical stretching on the lee side triggers orographic lee cyclogenesis over western and central Argentina. This lee cyclogenesis frequently manifests through the amplification of the Northwestern Argentine Low (BNOA; Seluchi and Saulo, 2012), a thermal-orographic low centered east of the Andes.")
    add_p("Once displaced toward the subtropical South American coast, long-lived vortices can interact with maritime boundary-layer air masses. Reboita et al. (2009) and Iwabe et al. (2010) examined quasi-stationary cyclones off the southern coast of Brazil, highlighting the role of middle-tropospheric vorticity advection, warm thermal advection, and atmospheric blocking in impeding normal zonal evacuation. Furthermore, when horizontal wind shear is pronounced, the flow can satisfy Kuo's (1949) necessary condition for barotropic instability, allowing synoptic vortices to extract kinetic energy directly from the upper-tropospheric subtropical jet.")

    # --- 3. MATERIALS AND METHODS ---
    add_heading("3. MATERIALS AND METHODS", level=1)
    add_p("Atmospheric diagnostics were computed using the Fifth Generation ECMWF Atmospheric Reanalysis (ERA5; Hersbach et al., 2020). ERA5 data were acquired on a regular 0.25° × 0.25° horizontal grid spanning the domain 0°–60°S and 90°W–30°W at 6-hourly synoptic intervals (00, 06, 12, and 18 UTC) from December 10 to 31, 1995. The vertical domain comprises 12 standard isobaric levels: 1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, and 100 hPa. Surface parameters include mean sea level pressure (msl), 2-meter air temperature (t2m), sea surface temperature (sst), surface pressure (sp), and surface geopotential (z). To avoid fictitious isobaric extrapolation beneath the steep Andean orography, lower isobaric levels and vertical cross-sections were masked wherever pressure exceeded local surface pressure (p > sp).")
    add_p("Calibrated infrared (11 µm) window brightness temperatures from the GOES-8 geostationary satellite were obtained from the NOAA National Centers for Environmental Information (NCEI) GridSat-B1 climate data record (Knapp et al., 2011). Observational daily rainfall data for validation were obtained from the Santa Catarina State Agricultural Research and Rural Extension Enterprise (Epagri/Ciram) surface network, specifically station Itacorubi (Itacurubi) in Florianópolis, SC (Haas, 2002).")
    add_p("In hydrostatic pressure coordinates, Ertel's Potential Vorticity (Ertel, 1942) is formulated as:")
    add_p("P = -g (ζ_p + f) (∂θ / ∂p)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p("where g = 9.80665 m s⁻² is gravitational acceleration, f = 2Ω sin(φ) is the Coriolis parameter (Ω = 7.292115 × 10⁻⁵ rad s⁻¹), ζ_p = (∂v/∂x)_p - (∂u/∂y)_p is relative vorticity evaluated along isobaric surfaces, and θ = T (1000/p)^0.286 is potential temperature. In the Southern Hemisphere, where f < 0 and ∂θ/∂p < 0 in a statically stable atmosphere, Ertel PV values are algebraically negative. Following the Isentropic Potential Vorticity (IPV) framework (Hoskins et al., 1985) and Southern Hemisphere conventions in potential vorticity literature (Haas, 2002), we define cyclonic Isentropic Potential Vorticity as:")
    add_p("q ≡ -P × 10⁶  [PVU or UVP, 10⁻⁶ m² K kg⁻¹ s⁻¹]", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p("Under this sign convention, positive values (q > 0) unambiguously designate cyclonic vorticity in both hemispheres. Stratospheric air is demarcated by q ≥ 1.5 UVP, which defines the dynamical tropopause.")
    add_p("Equivalent potential temperature (θe) at lower tropospheric levels is computed using Bolton's (1980) formulation. To assess upper-level barotropic instability, the meridional gradient of absolute vorticity was evaluated from the layer-mean zonal wind (ū) between 300 and 100 hPa:")
    add_p("Q_y = β - (d²ū / dy²)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p("where β = (2Ω cos φ) / a and a = 6.371 × 10⁶ m. Kuo's (1949) theorem dictates that a change of sign of Q_y within the domain represents the necessary condition for barotropic instability.")

    # --- 4. RESULTS AND DISCUSSION ---
    add_heading("4. RESULTS AND DISCUSSION", level=1)

    add_heading("4.1 Vortex Genesis over the Southeastern Pacific", level=2)
    add_p("Between December 10 and 14, 1995, the synoptic precursor to the UTCV originated over the southeastern Pacific Ocean (40°–50°S, 100°–80°W). The vortex developed from the anticyclonic roll-up and equatorward fracture of a cold front whose polar segment advanced rapidly eastward while its subtropical branch remained retarded west of the coastline (Gan and Rao, 1994).")
    add_p("Calibrated GOES-8 infrared brightness temperatures from NOAA GridSat-B1 (Figure 1) capture the distinct morphological evolution of the vortex core. On December 14 at 18 UTC (Figure 1a), an incipient spiral of cyclonic cloudiness is centered near 32°S, 82°W. By December 19 at 18 UTC (Figure 1b), the system had evolved into a fully organized cut-off vortex centered near 35°S, 80°W, characterized by an expansive clear-sky eye indicative of strong upper-level subsidence and stratospheric intrusion.")
    add_figure("Figure_1_GOES8_IR.png", "Figure 1. Calibrated GOES-8 infrared (11 µm) brightness temperature (K) from the NOAA GridSat-B1 climate data record for: (a) 14/12/1995 18 UTC (incipient vortex formation over the southeastern Pacific); and (b) 19/12/1995 18 UTC (mature cut-off cyclonic vortex prior to Andean crossing). Arrows indicate the vortex core. Coastlines and international borders are shown in yellow.")

    add_heading("4.2 Pre-Andean Baroclinic Coupling", level=2)
    add_p("Prior to impinging upon the Andes Cordillera, the vortex experienced notable baroclinic amplification between December 17 and 19 over the eastern Pacific. Figure 2 presents a vertical cross-section along 35°S at 18 UTC on December 18, 1995, depicting cyclonic Isentropic Potential Vorticity (IPV, q, shaded) and isentropes (black contours).")
    add_p("The cross-section reveals an intense upper-tropospheric stratospheric extrusion (tropopause fold) characterized by q ≥ 1.5 UVP descending from the stratosphere down to the 400–500 hPa layer near 88°W, with peak core values reaching ~4.6 UVP. Downstream, along the Chilean coastal margin between 78°W and 74°W, a shallow boundary-layer cyclonic IPV anomaly (values up to ~1.0–1.2 UVP) is clearly evident below 850 hPa, dammed against the steep western flank of the Andes.")
    add_p("The upper-level cyclonic anomaly was positioned upshear (west) of the low-level coastal anomaly. This westward vertical tilt with height enabled mutual baroclinic amplification (Hoskins et al., 1985; Hirschberg and Fritsch, 1991). The cyclonic circulation associated with the descending tropopause fold induced warm, moist northerly advection along the coast, which intensified the low-level thermal and cyclonic anomaly, while the lower anomaly in turn enhanced poleward warm advection east of the upper trough. This mutual baroclinic coupling pre-conditioned the vortex into a robust coherent structure before it encountered the mountain barrier.")
    add_figure("Figure_2_Pacific_Pre_Andes_VPI.png", "Figure 2. Vertical cross-section along 35°S of Isentropic Potential Vorticity (IPV; q in UVP, shaded) and potential temperature (isentropes in black contours, interval 5 K) on 18/12/1995 at 18 UTC from ERA5 reanalysis. Shading highlights the upper-level tropopause fold (q ≥ 1.5 UVP) near 88°W and the shallow coastal IPV anomaly below 850 hPa dammed west of the Andes (~78°W). Topography is masked in gray below surface pressure.")

    add_heading("4.3 Andean Transit and Lee Cyclogenesis", level=2)
    add_p("Between December 20 and 22, the UTCV crossed the Andes Cordillera. The structural evolution of the vortex during mountain transit is illustrated by vertical cross-sections along 27.5°S at 20/12 00 UTC and 22/12 00 UTC (Figure 3).")
    add_p("On December 20 at 00 UTC (Figure 3a), as the system approached the mountain crest, the vertical axis of the vortex exhibited a pronounced westward tilt with height. The upper-tropospheric IPV anomaly (q > 2.0 UVP) remained centered west of 70°W between 400 and 250 hPa, while downstream at the surface, the initial stages of orographic vortex stretching were underway. By December 22 at 00 UTC (Figure 3b), following complete Andean crossing, the vortex axis transitioned into a nearly upright, equivalent barotropic vertical alignment between 62°W and 58°W, extending from the middle troposphere down to 850 hPa.")
    add_figure("Figure_3_Andes_CrossSection_Tilt.png", "Figure 3. Vertical cross-section along 27.5°S of Isentropic Potential Vorticity (IPV; q in UVP, shaded) and isentropes (black contours, interval 5 K) from ERA5 reanalysis for: (a) 20/12/1995 00 UTC (westward tilt during Andean approach); and (b) 22/12/1995 00 UTC (upright, equivalent barotropic alignment downstream of the Andes). The dashed red line marks the cyclonic vortex axis. Topography is masked in gray below surface pressure.")

    add_p("The corresponding surface pressure evolution during the lee cyclogenesis and post-Andean transition is documented in the synoptic and meso-alpha analysis of Mean Sea Level Pressure (SLP) from ERA5 (Figure 4). To resolve the intense pressure drop on the lee side of the Andes, Figure 4a displays a high-resolution regional zoom centered on Mendoza and the Cuyo region at 19 UTC on December 20, 1995, plotted with a refined contour interval of 2 hPa. The regional thermal-orographic Northwestern Argentine Low (BNOA; Seluchi and Saulo, 2012) intensified markedly east of the Andes, reaching a regional minimum of 988.9 hPa in Catamarca/La Rioja at 21 UTC on December 20 (989.6 hPa at 18 UTC; 29.5°S, 66.5°W). At the Mendoza station point (32.89°S, 68.84°W), hourly ERA5 diagnostics reveal that SLP reached a sharp trough minimum of 995.1 hPa at 19 UTC on December 20 (surface pressure sp = 914.5 hPa; red star in Figure 4a).")
    add_p("Figure 4b details the hourly SLP time series at Mendoza from December 18 to 22, 1995 (120 hourly steps). From an initial value of 1011.1 hPa on December 19 at 13 UTC, the pressure fell steadily to 998.1 hPa on December 20 at 13 UTC, yielding a maximum 24-hour pressure drop of 12.8 hPa. Over a 30-hour window, the pressure dropped by 15.9 hPa down to the 995.1 hPa trough minimum at 19 UTC on December 20. Following the cold frontal passage, pressure rebounded abruptly from 995.1 hPa to 1010.8 hPa by 05 UTC on December 21—a rapid post-frontal surge of +15.7 hPa in just 10 hours (+1.57 hPa h⁻¹). Notably, while this pressure drop was synoptically vigorous, it did not reach the classical meteorological bomb criterion of 24 hPa in 24 hours (Sanders and Gyakum, 1980), nor did it satisfy the latitude-adjusted bomb threshold at 33°S (~15.1 hPa/24 h; Bergeron value E = 12.8 / 15.1 = 0.85). Over the broader regional BNOA domain, however, the maximum 24-hour drop reached 17.6 hPa/24 h between 19/12 22 UTC and 20/12 22 UTC.")
    add_p("As the upper-level vortex tracked east of the Andes, a secondary surface low developed over Uruguay, reaching 1003.3 hPa on December 22 at 00 UTC (Figure 4c). Over subsequent days, this surface low gradually filled to 1008.0 hPa by December 25 (Figure 4d) and dissipated completely over the ocean by December 29, while the upper-level vortex remained remarkably active and dynamically coherent aloft.")
    add_figure("Figure_4_SLP_ERA5.png", "Figure 4. Mean Sea Level Pressure (SLP) analysis from ERA5: (a) Regional zoom on Mendoza and Cuyo at the time of lowest station pressure (20/12/1995 19 UTC), contoured every 2 hPa (986 to 1024 hPa), with the red star indicating Mendoza (minimum SLP of 995.1 hPa); (b) Hourly time series of SLP (hPa) at Mendoza (32.89°S, 68.84°W) from 18 to 22 December 1995, highlighting the 24-h drop of 12.8 hPa, 30-h drop of 15.9 hPa to the 995.1 hPa minimum, and the subsequent +15.7 hPa post-frontal surge; (c) Synoptic SLP on 22/12/1995 00 UTC (surface cyclone over Uruguay at 1003.3 hPa, 4 hPa contour interval); and (d) Synoptic SLP on 25/12/1995 00 UTC (decaying coastal trough, Uruguay low filled to 1008.0 hPa). In panels (a), (c), and (d), Andean topography above 2000 m is masked in gray.")

    add_heading("4.4 Coastal Re-intensification and Moisture Inflow over SESA", level=2)
    add_p("A central puzzle of the December 1995 UTCV was its prolonged vigor and devastating precipitation over Southeastern South America (SESA) despite the filling of the surface low. Figure 5 depicts the cyclonic Isentropic Potential Vorticity (IPV, q) and geopotential height at 400 hPa on December 22 at 00 UTC.")
    add_p("On December 22 at 00 UTC, the 400 hPa cyclonic vortex reached its peak intensity over SESA, with core IPV attaining 2.79 UVP centered at 31.5°S, 62.0°W. The dynamical tropopause (q = 1.5 UVP, bold red contour) extended across northern Argentina, Uruguay, and western Rio Grande do Sul, embedded within a closed cyclonic geopotential depression (minimum height ~7180 m). Cyclonic winds around the vortex periphery exceeded 35 m s⁻¹.")
    add_figure("Figure_5_400hPa_VPI_1995-12-22.png", "Figure 5. Isentropic Potential Vorticity (IPV; q in UVP, shaded) and geopotential height (black contours, interval 40 gpm) at 400 hPa on 22/12/1995 at 00 UTC from ERA5 reanalysis. The bold red line denotes the dynamic tropopause (q = 1.5 UVP). Vectors represent horizontal wind (m s⁻¹). Peak cyclonic IPV over SESA reaches 2.79 UVP.")

    add_p("The sustained convective activity and heavy precipitation along the Brazilian coast were governed by thermodynamic boundary-layer forcing. Figure 6 examines the lower-tropospheric structure at 925 hPa on December 23 at 00 UTC. An intense maritime tongue of high equivalent potential temperature (θe between 341 and 343 K; Figure 6b) was advected from the tropical Atlantic into the coastal sectors of Santa Catarina, Paraná, and Rio Grande do Sul by strong southeasterly/easterly maritime winds (10–15 m s⁻¹).")
    add_p("Under IPV theory, this high-θe maritime tongue acts dynamically as an effective positive lower-boundary IPV anomaly (Hoskins et al., 1985). As the upper-level vortex phased over this thermodynamic disturbance, negative IPV values associated with the cyclonic tower reached the surface. Rather than requiring a static pre-existing column, this vertical extension was governed by a strong tendency of IPV concentration driven by diabatic latent heat release and low-level mass convergence. The resulting deep vertical coupling sustained intense, quasi-stationary convective ascent along the coastal topography, triggering catastrophic localized rainfall episodes and flash floods, notably the record precipitation of 411 mm observed at the Epagri Itacorubi (Itacurubi) meteorological station in Florianópolis (Haas, 2002).")
    add_figure("Figure_6_SESA_Theta_e_925hPa.png", "Figure 6. Lower-tropospheric thermodynamic and dynamic forcing on 23/12/1995 at 00 UTC from ERA5 reanalysis: (a) 925 hPa Isentropic Potential Vorticity (IPV; q in UVP, shaded) with horizontal wind vectors (m s⁻¹) and overlaid 400 hPa IPV contours (dashed magenta, 1.5 and 2.0 UVP); (b) 925 hPa equivalent potential temperature (θe in K, shaded and black contours, interval 2 K) highlighting the warm/moist maritime plume (mean 341–343 K) advected into the subtropical coast.")

    add_heading("4.5 Anomalous Northeastward Trajectory and Barotropic Instability", level=2)
    add_p("From December 22 onwards, rather than following the climatological midlatitude path toward the east-southeast (Ambrizzi and Pezza, 1999), the UTCV underwent a sharp equatorward deflection, propagating slowly northeastward across southern Brazil toward the subtropics.")
    add_p("To examine the physical mechanism responsible for this unusual trajectory, barotropic instability diagnostics were computed across the upper-tropospheric jet layer (300–100 hPa layer mean, averaged between 70°W and 40°W). Figure 7 displays the 1D meridional profiles of zonal wind ū(y) and the absolute vorticity gradient Q_y(y) = β - d²ū/dy² on December 24 at 00 UTC, alongside the time-latitude Hovmöller evolution of Q_y from December 20 to 31.")
    add_p("On December 24 (Figure 7a,b), the subtropical jet was characterized by an intense westerly core (ū ~ 42 m s⁻¹) near 45°S and strong easterly/weak westerly flow to the north. This intense meridional horizontal wind shear created a pronounced local maximum in d²ū/dy² that overwhelmed planetary beta (β). Consequently, Q_y reversed sign, crossing zero at 28.8°S. According to Kuo (1949), the reversal of the meridional gradient of absolute vorticity within the fluid domain is the necessary condition for barotropic instability.")
    add_p("The Hovmöller diagram (Figure 7c) demonstrates that the condition Q_y ≤ 0 (demarcated by the bold black zero line) persisted continuously between 25°S and 32°S from December 21 to 28. Under barotropic instability, the synoptic perturbation extracts kinetic energy directly from the horizontal shear of the mean zonal jet. This energy extraction prevented the vortex from decaying rapidly as it propagated into the subtropics where planetary vorticity |f| diminishes, allowing the vortex to maintain its structural coherence.")
    add_figure("Figure_7_Barotropic_ERA5.png", "Figure 7. Upper-tropospheric barotropic instability diagnostics (300–100 hPa layer mean, 70°W–40°W) from ERA5 reanalysis: (a) Meridional profile of mean zonal wind ū (m s⁻¹) on 24/12/1995 00 UTC; (b) Meridional gradient of absolute vorticity Q_y = β - d²ū/dy² (10⁻¹¹ m⁻¹ s⁻¹) on 24/12/1995 00 UTC, showing sign reversal (zero crossing at 28.8°S); and (c) Time-latitude Hovmöller diagram of Q_y (10⁻¹¹ m⁻¹ s⁻¹) from 20 to 31 December 1995. The bold black line marks the zero contour (Q_y = 0), delineating the continuous fulfillment of Kuo's necessary instability condition.")

    add_p("The complete lifecycle trajectory of the vortex center was objectively tracked at 400 hPa using ERA5 reanalysis over 71 synoptic time steps (6-hourly intervals, December 14 at 06 UTC to December 31 at 18 UTC), as shown in Figure 8a. This comprehensive tracking spans over 17 days and reproduces the full 5-phase evolutionary lifecycle identified in Haas (2002): (1) Phase 1 — Pacific Genesis (14–17 Dec; open blue squares), initiating near 28.0°S, 103.8°W; (2) Phase 2 — Pre-Andean Baroclinic Intensification (18–20 Dec; solid blue circles), where the vortex amplified over the southeastern Pacific; (3) Phase 3 — Andean Crossing (20–21 Dec; open red circles), traversing the mountain barrier near 35.5°S, 69.0°W; (4) Phase 4 — Mature Phase and Anomalous Northeastward Trajectory over SESA (22–28 Dec; solid crimson squares), progressing northeastward across Argentina, Uruguay, Rio Grande do Sul, Santa Catarina, and Paraná to 24.25°S, 54.00°W; and (5) Phase 5 — Subtropical Decay and Atlantic Transition (28–31 Dec; open purple diamonds), drifting into the South Atlantic to 27.5°S, 43.8°W.")
    add_p("Figure 8b documents the co-evolution of the central geopotential anomaly (z₄₀₀', blue curve) and the maximum core cyclonic IPV (q, crimson curve) across all 71 time steps. The vortex maintained stratospheric IPV values (q > 1.5 UVP) continuously through Phases 2, 3, and 4, peaking at 5.66 UVP during post-Andean transition (21/12 12 UTC) and maintaining 2.79–3.37 UVP over SESA. Even during Phase 5, core IPV remained resilient (0.7–1.0 UVP), confirming that upper-level barotropic energy extraction sustained the cyclonic core long after surface cyclolysis.")
    add_figure("Figure_8_Northward_Trajectory_VPI.png", "Figure 8. Complete 5-phase lifecycle trajectory and intensity evolution of the UTCV at 400 hPa from ERA5 reanalysis (14 to 31 December 1995, 71 synoptic steps): (a) Trajectory of the vortex center across all five phases matching the doctoral thesis (Haas, 2002): Phase 1 (Pacific Genesis, 14–17 Dec, open squares), Phase 2 (Baroclinic Intensification, 18–20 Dec, solid circles), Phase 3 (Andean Crossing, 20–21 Dec, open red circles), Phase 4 (Mature SESA & anomalous NE trajectory, 22–28 Dec, solid crimson squares), and Phase 5 (Decay & Atlantic, 28–31 Dec, open purple diamonds); and (b) Temporal evolution of central geopotential anomaly z₄₀₀' (gpm, left axis, blue line) and core maximum cyclonic IPV (UVP, right axis, crimson line) across all 71 steps, with vertical lines demarcating the 5 lifecycle phases.")

    # --- 5. CONCLUSIONS ---
    add_heading("5. CONCLUSIONS", level=1)
    add_p("The extraordinary lifecycle, orographic transition, and anomalous northeastward propagation of the December 1995 Upper Tropospheric Cyclonic Vortex (UTCV) over Southeastern South America was comprehensively analyzed using the ERA5 reanalysis and NOAA GridSat-B1 satellite observations under the framework of Isentropic Potential Vorticity (IPV thinking). The principal conclusions are:")
    add_p("1. Baroclinic pre-conditioning over the Pacific: Before crossing the Andes, the descending stratospheric tropopause fold (q ≥ 1.5 UVP, core ~4.6 UVP at 400 hPa) coupled with a shallow boundary-layer cyclonic IPV anomaly dammed west of the Chilean coast (~78°W, below 850 hPa). The resulting westward vertical tilt facilitated mutual baroclinic amplification prior to mountain encounter.")
    add_p("2. Andean transit and lee cyclogenesis: Mountain transit induced severe vertical compression followed by lee stretching, causing the vortex axis to tilt eastward before recovering an upright equivalent barotropic column east of the Andes. This triggered intense regional lee cyclogenesis, with the thermal-orographic Northwestern Argentine Low (BNOA) reaching 988.9 hPa in Catamarca/La Rioja at 20/12 21 UTC (989.6 hPa at 18 UTC; 29.5°S, 66.5°W), and local sea level pressure at Mendoza dropping to a sharp trough minimum of 995.1 hPa on 20/12 19 UTC (with a 24-h drop of 12.8 hPa, 30-h drop of 15.9 hPa, and a rapid post-frontal rebound of +15.7 hPa in 10 h). While vigorous, the pressure fall at Mendoza did not reach the classical meteorological bomb criterion of 24 hPa in 24 hours.")
    add_p("3. Coastal re-intensification and IPV concentration over SESA: Upon reaching the subtropical coast on 22/12, 400 hPa cyclonic IPV reached a secondary peak of 2.79 UVP. Concurrently, maritime easterly flow advected a moist equivalent potential temperature tongue (θe = 341–343 K at 925 hPa) inland. Negative IPV values associated with the cyclonic tower reached the surface, governed by a marked tendency of IPV concentration under convective latent heating. This dynamic and thermodynamic coupling sustained persistent vertical motion, producing record-breaking precipitation of 411 mm recorded at the Epagri Itacorubi (Itacurubi) station in Florianópolis (Haas, 2002).")
    add_p("4. Full lifecycle and upper-level barotropic maintenance: The UTCV was tracked continuously across 71 synoptic steps (14 to 31 December 1995) spanning all 5 lifecycle phases from Pacific genesis to Atlantic dissipation as documented in Haas (2002). The unusual northeastward trajectory from 35.5°S to 24.3°S across SESA was dynamically governed by upper-tropospheric barotropic instability across 300–100 hPa. Strong horizontal wind shear in the northern flank of the jet caused the meridional gradient of absolute vorticity Q_y = β - d²ū/dy² to reverse sign (crossing zero at ~28.8°S), satisfying Kuo's necessary instability condition continuously between December 21 and 28. This enabled the vortex to extract kinetic energy from the mean jet, preserving its coherent structure during its subtropical transit.")

    # --- ACKNOWLEDGMENTS ---
    add_heading("ACKNOWLEDGMENTS", level=1)
    add_p("The author expresses sincere gratitude to the National Council for Scientific and Technological Development (CNPq - Conselho Nacional de Desenvolvimento Científico e Tecnológico) for financial and research support. Grateful acknowledgment is also extended to the European Centre for Medium-Range Weather Forecasts (ECMWF) for providing the ERA5 reanalysis data and to the NOAA National Centers for Environmental Information (NCEI) for the GridSat-B1 satellite records.")

    # --- REFERENCES ---
    add_heading("REFERENCES", level=1)
    refs = [
        "Ambrizzi, T.; Pezza, A. B. (1999). Cold waves and the propagation of extratropical cyclones and anticyclones in South America. Revista Geofísica, 51, 45-67.",
        "Bjerknes, J.; Solberg, H. (1922). Life cycles of cyclones and the polar front theory of atmospheric circulation. Geofysiske Publikasjoner, 3(1), 1-18.",
        "Bolton, D. (1980). The computation of equivalent potential temperature. Monthly Weather Review, 108(7), 1046-1053.",
        "Charney, J. G. (1947). The dynamics of long waves in a baroclinic westerly current. Journal of Meteorology, 4(5), 135-163.",
        "Davis, C. A.; Emanuel, K. A. (1991). Potential vorticity diagnostics of cyclogenesis. Monthly Weather Review, 119(8), 1929-1953.",
        "Eady, E. T. (1949). Long waves and cyclone waves. Tellus, 1(3), 33-52.",
        "Ertel, H. (1942). Ein neuer hydrodynamischer Wirbelsatz. Meteorologische Zeitschrift, 59, 277-281.",
        "Funatsu, B. M.; Gan, M. A.; Rao, V. B. (2004). A case study of orographic cyclogenesis over South America. Atmósfera, 17(2), 91-113.",
        "Gan, M. A.; Rao, V. B. (1994). The influence of the Andes Cordillera on transient disturbances. Monthly Weather Review, 122(6), 1141-1157.",
        "Haas, R. (2002). Simulações da chuva orográfica associada a um ciclone extratropical no litoral sul do Brasil. Tese de Doutorado, Instituto de Astronomia, Geofísica e Ciências Atmosféricas, Universidade de São Paulo (IAG/USP), 168 pp.",
        "Hersbach, H. et al. (2020). The ERA5 global reanalysis. Quarterly Journal of the Royal Meteorological Society, 146(730), 1999-2049.",
        "Hirschberg, P. A.; Fritsch, J. M. (1991). Tropopause undulations and the development of extratropical cyclones. Part II: Diagnostic analysis and conceptual model. Monthly Weather Review, 119(2), 518-550.",
        "Hoskins, B. J.; McIntyre, M. E.; Robertson, A. W. (1985). On the use and significance of isentropic potential vorticity maps. Quarterly Journal of the Royal Meteorological Society, 111(470), 877-946.",
        "Iwabe, C. M. N.; Reboita, M. S.; Camargo, R. (2010). Estudo de caso de uma situação atmosférica entre 12 a 19 de Setembro de 2008 similar à do Evento Catarina. Revista Brasileira de Meteorologia, 25(3), 369-386.",
        "Knapp, K. R.; Ansari, S.; Bain, C. L.; Bourassa, M. A.; Dickinson, M. J.; Khalid, A.; Levinson, D. H.; Bravo, N.; Magnusdottir, G. (2011). Globally gridded satellite observations for climate studies (GridSat-B1). Bulletin of the American Meteorological Society, 92(7), 893-907.",
        "Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. Journal of Meteorology, 6(2), 105-122.",
        "Orlanski, I.; Katzfey, J.; Menendez, C.; Marino, M. (1991). Simulation of an extratropical cyclone in the Southern Hemisphere: Model sensitivity. Journal of the Atmospheric Sciences, 48(21), 2293-2312.",
        "Reboita, M. S.; Iwabe, C. M. N.; da Rocha, R. P.; Ambrizzi, T. (2009). Análise de um ciclone semi-estacionário na costa sul do Brasil associado a bloqueio atmosférico. Revista Brasileira de Meteorologia, 24(4), 407-422.",
        "Rossby, C.-G. (1940). Planetary flow patterns in the atmosphere. Quarterly Journal of the Royal Meteorological Society, 66(Suppl.), 68-87.",
        "Sanders, F.; Gyakum, J. R. (1980). Synoptic-dynamic climatology of the 'bomb'. Monthly Weather Review, 108(10), 1589-1606.",
        "Seluchi, M. E.; Saulo, A. C. (2012). Baixa do Noroeste Argentino e Baixa do Chaco: características, processos e sua influência sobre o tempo na América do Sul. Revista Brasileira de Meteorologia, 27(1), 49-60.",
        "Thorpe, A. J. (1985). Diagnosis of balanced vortex structure using potential vorticity. Journal of the Atmospheric Sciences, 42(4), 397-406."
    ]
    for r in refs:
        p_ref = doc.add_paragraph()
        p_ref.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_after = Pt(4)
        run_ref = p_ref.add_run(r)
        run_ref.font.name = 'Times New Roman'
        run_ref.font.size = Pt(11)

    # Salva o arquivo final
    out_docx = "article_rbmet_english.docx"
    doc.save(out_docx)
    print(f"Documento DOCX formatado para RBMET gerado com sucesso: {out_docx}")

if __name__ == '__main__':
    create_rbmet_docx()

