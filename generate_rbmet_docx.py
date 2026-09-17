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
    add_p("During the last two weeks of December 1995, a baroclinic system crossed the Andes Cordillera and moved slowly northeastward over the southern and southeastern coast of Brazil as an Upper Tropospheric Cyclonic Vortex (UTCV). The system triggered extreme precipitation events, flash floods, and severe socio-economic impacts. In this study, the anomalous trajectory, intensification, and decay mechanisms of the UTCV are investigated under the framework of Isentropic Potential Vorticity (IPV thinking) using high-resolution ERA5 reanalysis and satellite observations. It is demonstrated that baroclinic instability with a low-level IPV anomaly dammed west of the Andes was critical during initial formation. Orographic vortex stretching induced explosive lee cyclogenesis over western Argentina, causing the vortex to verticalize into an equivalent barotropic structure. Over Southeastern South America (SESA), interaction with a coastal equivalent potential temperature (θe) anomaly re-intensified the system, establishing a deep tropospheric IPV tower. Finally, the anomalous northeastward trajectory was driven by barotropic instability in upper levels where Kuo's necessary condition (Qy changing sign) was satisfied, assisted by a horizontal quarter-wavelength interaction with a secondary IPV anomaly over Paraná and a dipole blocking pattern over the Atlantic.")
    add_p("Keywords: Upper Tropospheric Cyclonic Vortex; IPV Thinking; Lee Cyclogenesis; Barotropic Instability; Flash Floods.")

    # --- RESUMO & PALAVRAS-CHAVE ---
    add_heading("RESUMO", level=1)
    add_p("Durante as duas últimas semanas de dezembro de 1995, um sistema baroclínico cruzou a Cordilheira dos Andes e deslocou-se lentamente para nordeste ao longo do litoral Sul e Sudeste do Brasil como um Vórtice Ciclônico de Altos Níveis (VCAN). O sistema produziu chuvas torrenciais, inundações bruscas e severos danos materiais e humanos. Neste estudo, a trajetória anômala e os processos de intensificação e decaimento do sistema são investigados com base no conceito de Vorticidade Potencial Isentrópica (VPI de Ertel) utilizando dados da reanálise ERA5 e observações de satélite. Demonstra-se que a instabilidade baroclínica acoplada a uma anomalia de VPI em baixos níveis represada a oeste dos Andes desempenhou papel primordial na fase inicial. O estiramento orográfico de vórtice induziu ciclogênese explosiva a sotavento no norte da Argentina, transformando o sistema em uma estrutura barotrópica equivalente. Sobre o Sudeste da América do Sul (SESA), a interação com um distúrbio costeiro de temperatura potencial equivalente (θe) amplificou a torre de VPI até a superfície. A trajetória anômala para nordeste decorreu da satisfação do critério de instabilidade barotrópica de Kuo (inversão do sinal de Qy nos níveis do jato), conjugada ao acoplamento horizontal em λ/4 com uma anomalia secundária de VPI sobre o Paraná e a um bloqueio tipo dipolo no Atlântico.")
    add_p("Palavras-chave: Vórtice Ciclônico de Altos Níveis; Pensamento VPI; Ciclogênese a Sotavento; Instabilidade Barotrópica; Inundações Bruscas.")

    # --- 1. INTRODUCTION ---
    add_heading("1. INTRODUCTION", level=1)
    add_p("The study of atmospheric dynamics responsible for the development and lifecycle of cyclonic systems in the midlatitudes and subtropics of the Southern Hemisphere is of paramount meteorological importance (Bjerknes and Solberg, 1922; Charney, 1947). In South America, upper-tropospheric cut-off lows and Upper Tropospheric Cyclonic Vortices (UTCVs, or VCANs in Portuguese) frequently modulate convective activity, severe weather outbreaks, and prolonged flood episodes.")
    add_p("Equally important, the Ertel Potential Vorticity (PV) theorem (Ertel, 1942; Rossby, 1940) provides an elegant, conserved tracer for adiabatic and frictionless flows. The revitalized formulation of Isentropic Potential Vorticity (IPV) by Hoskins et al. (1985) founded the 'IPV thinking' methodology (Thorpe, 1985). By combining thermal stratification (static stability) and absolute vorticity into a single invertible scalar, IPV analysis enables direct physical insight into vortex-vortex interactions, tropopause folds, and cyclogenesis without requiring multiple isobaric levels.")
    add_p("In this work, the IPV framework is applied to reconstruct the entire lifecycle of the catastrophic UTCV event of December 10–31, 1995 over Southeastern South America (SESA). This system exhibited extraordinary longevity, an anomalous northeastward path across four Brazilian states, and produced record-breaking rainfall exceeding 400 mm in Santa Catarina. Using the state-of-the-art ECMWF ERA5 reanalysis and NOAA geostationary satellite records, we explain the physical mechanisms governing its formation, orographic transit, coastal intensification, and unusual propagation.")

    # --- 2. LITERATURE REVIEW ---
    add_heading("2. LITERATURE REVIEW", level=1)
    add_p("Classical baroclinic instability theory establishes that cyclogenesis requires vertical wind shear and an westward-tilted vertical axis (Charney, 1947; Eady, 1949). In the IPV framework, this corresponds to an upper-level cyclonic IPV anomaly located a quarter-wavelength (λ/4) upshear of a low-level warm thermal anomaly (Hoskins et al., 1985). Under this favorable mutual phasing, the upper and lower anomalies amplify each other continuously.")
    add_p("The Andes Cordillera represents a formidable meridional barrier that profoundly modifies transient systems traversing South America (Gan and Rao, 1994; Seluchi and Saulo, 2012). While numerical experiments by Orlanski et al. (1991) indicated that downstream cyclogenesis can occur even in idealized flat topography, realistic simulations demonstrate that orographic vortex stretching on the lee side triggers intense cyclogenesis over western Argentina and Uruguay (Funatsu et al., 2004).")
    add_p("Furthermore, Reboita et al. (2009) and Iwabe et al. (2010) examined stationary cyclones on the southern coast of Brazil and highlighted the role of dipole blocking patterns and warm air advection in preventing downstream eastward evacuation. In the present study, we expand upon these foundations to explain how upper-level barotropic instability (Kuo, 1949) and horizontal IPV phasing sustain long-lived systems with anomalous northward tracks.")

    # --- 3. MATERIALS AND METHODS ---
    add_heading("3. MATERIALS AND METHODS", level=1)
    add_p("High-resolution Fifth Generation ECMWF Reanalysis (ERA5; Hersbach et al., 2020) data were utilized spanning December 10 to 31, 1995. The dataset comprises 12 vertical isobaric levels (1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, and 100 hPa) with a spatial resolution of 0.25° × 0.25° at 6-hourly synoptic intervals (00, 06, 12, and 18 UTC). Single-level variables include mean sea level pressure (msl), 2-meter temperature (t2m), and surface pressure (sp).")
    add_p("Calibrated infrared (IR, 11 µm) observations from the GOES-8 geostationary satellite were obtained from the NOAA National Centers for Environmental Information (NCEI) GridSat-B1 climate data record at 18 UTC.")
    add_p("In hydrostatic isobaric coordinates, Ertel's Isentropic Potential Vorticity (IPV) is evaluated as:")
    add_p("P = -g (ζ_p + f) (∂θ / ∂p)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p("where g = 9.80665 m s⁻² is gravitational acceleration, f = 2Ω sin(φ) is the Coriolis parameter, ζ_p is relative vorticity on isobaric surfaces, and θ = T(1000/p)^0.286 is potential temperature. In the Southern Hemisphere, where f < 0 and ∂θ/∂p < 0, Ertel PV values are algebraically negative. Following the Southern Hemisphere convention (Haas, 2002; slide notes), we define the cyclonic IPV as:")
    add_p("q ≡ -P × 10⁶  [PVU or UVP, 10⁻⁶ m² K kg⁻¹ s⁻¹]", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p("Under this convention, q > 0 consistently designates cyclonic, stratospheric air in both hemispheres. Stratospheric air is defined by q ≥ 1.5 UVP (the dynamic tropopause).")
    add_p("Equivalent potential temperature (θe) at lower levels is calculated using Bolton's (1980) formulation. Barotropic instability is evaluated through the meridional gradient of absolute vorticity:")
    add_p("Q_y = β - (d²ū / dy²)", bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    add_p("where ū is the layer-mean zonal wind between 300 and 100 hPa and β = 2Ω cos(φ)/a. According to Kuo (1949), a sign change of Q_y within the domain is the necessary condition for barotropic instability.")

    # --- 4. RESULTS AND DISCUSSION ---
    add_heading("4. RESULTS AND DISCUSSION", level=1)

    add_heading("4.1 UTCV Formation Stage over the Pacific", level=2)
    add_p("The initial formation occurred between December 10 and 14, 1995 over the southeastern Pacific Ocean. The vortex originated from the equatorial fracturing of a cold front whose polar segment propagated faster than its subtropical extension (Gan and Rao, 1994). Satellite imagery from GOES-8 (Figure 1) confirms the presence of a well-defined cyclonic swirl with minimal cloudiness in its core on December 14 and 19 at 18 UTC.")
    add_figure("Figure_1_GOES8_IR.png", "Figure 1. GOES-8 infrared (11 µm) brightness temperature from NOAA GridSat-B1 for (a) 14/12/1995 18Z (initial vortex roll-up over the Pacific) and (b) 19/12/1995 18Z (mature vortex prior to Andean crossing). Source: NOAA/NCEI.")

    add_heading("4.2 Pre-Andes Baroclinic Intensification", level=2)
    add_p("Between December 18 and 20, the upper-level IPV anomaly experienced rapid intensification over the Pacific. Diagnostic analysis reveals that this deepening was driven by coupling with a pre-existing shallow boundary-layer cyclonic IPV anomaly near the surface (below 850 hPa, at 1000–925 hPa), dammed along the Chilean coastline near 80°W–75°W, 35°S (Figure 2).")
    add_p("As documented in the vertical cross-section across 35°S (Figure 2), the upper-level stratospheric IPV anomaly at 400 hPa (VCAN tropopause fold, q >= 1.5 UVP) was positioned approximately a quarter-wavelength (λ/4) upshear (west, ~88°W) of the low-level cyclonic center (~78°W). This vertical phase locking produced mutual baroclinic amplification (Hirschberg and Fritsch, 1991; Hoskins et al., 1985), priming the system before it reached the high topography of the Andes.")
    add_figure("Proof_1_Pacific_Pre_Andes_VPI.png", "Figure 2. Vertical cross-section A (35°S) of Ertel Isentropic Potential Vorticity (q in UVP, shaded) and potential temperature (isentropes in black, K) across the southeastern Pacific and Andes Cordillera on 18/12/1995 at 18 UTC. Note the shallow boundary-layer cyclonic IPV anomaly below 850 hPa dammed along the Chilean coast (~78°W) phased in a quarter-wavelength (λ/4) with the upper-level tropopause fold (~88°W, 400 hPa). The brown polygon delineates the Andes Cordillera topography masked below surface pressure. Source: ERA5 Reanalysis.")

    add_heading("4.3 Lee Cyclogenesis and Orographic Transition", level=2)
    add_p("On December 20–21, 1995, the vortex crossed the high topography of the Andes. Vertical cross-sections (Figure 3) demonstrate that the vertical axis of the vortex tilted eastward during mountain transit, recovering vertical alignment on the lee side to form an equivalent barotropic column.")
    add_p("At 00 UTC on December 21, explosive lee cyclogenesis occurred over Mendoza, Argentina (Figure 4a). Surface pressure fell 19 hPa in 30 hours to 994 hPa, satisfying the 'meteorological bomb' criterion (Sanders and Gyakum, 1980). This intense drop resulted from the hydrostatic superposition of the warm stratospheric air column within the folded tropopause and intense diurnal continental surface heating.")
    add_figure("Cross_Section_1995-12-21_-27.5S.png", "Figure 3. Vertical cross-section of potential temperature (isentropes in crimson, K) along 27.5°S on 21/12/1995 at 00 UTC. The brown polygon delineates the Andes Cordillera topography masked below surface pressure. Source: ERA5 Reanalysis.")
    add_figure("Figure_6_SLP_ERA5.png", "Figure 4. Mean Sea Level Pressure (hPa) from ERA5 reanalysis showing key stages: (a) 21/12/1995 00Z (explosive lee cyclogenesis over Mendoza), (b) 22/12/1995 00Z (re-intensification over Uruguay), (c) 25/12/1995 00Z (mature coastal cyclone), and (d) 29/12/1995 00Z (decay phase). Source: ERA5 Reanalysis.")

    add_heading("4.4 Mature Phase and Coastal Re-intensification over SESA", level=2)
    add_p("Upon entering Uruguay and Rio Grande do Sul on December 22–23, the vortex underwent a secondary intensification, dropping central pressure to 1000 hPa. In upper levels (Figure 5), an intense cyclonic IPV anomaly exceeding 2.2 UVP was established at 400 hPa.")
    add_p("Simultaneously, strong easterly/northeasterly low-level winds advected maritime tropical air with equivalent potential temperature (θe) exceeding 345 K over the coastal zone of Santa Catarina and Rio Grande do Sul (Figure 6). Under IPV theory, this high-θe surface tongue acts as a positive low-level IPV anomaly. Phased with the upper-level vortex, it constructed a continuous tropospheric IPV tower that anchored torrential rainfall (e.g., 411 mm in Florianópolis).")
    add_figure("Figure_3_400hPa_1995-12-21.png", "Figure 5. Ertel Isentropic Potential Vorticity (q, UVP) at 400 hPa on 21/12/1995 at 00 UTC. Shading: cyclonic IPV (UVP). Thick red contour: dynamic tropopause (1.5 UVP). Black contours: 400 hPa geopotential height (m). Blue vectors: horizontal wind. Source: ERA5 Reanalysis.")
    add_figure("Proof_2_SESA_VPI_and_Theta_e.png", "Figure 6. Diagnostic proof of coastal thermodynamic forcing on 23/12/1995 at 00 UTC: (a) Low-level 925 hPa IPV overlaid with 400 hPa IPV tower contours; (b) Equivalent potential temperature (θe in K) in 925 hPa showing the maritime warm/moist plume advected into the cyclone core. Source: ERA5 Reanalysis.")

    add_heading("4.5 Anomalous Northeastward Trajectory and Barotropic Instability", level=2)
    add_p("From December 22 onwards, the UTCV deviated from the standard eastward/southeastward trajectory and propagated slowly northeastward across Santa Catarina, Paraná, and São Paulo (Figure 7a).")
    add_p("This anomalous track is explained by upper-level barotropic instability. Figure 7 demonstrates that between 300 and 100 hPa, extreme meridional shear in the zonal wind caused the absolute vorticity gradient Q_y = β - d²ū/dy² to reverse sign exactly across the latitude of deflection (~25–30°S). Satisfying Kuo's (1949) condition, the vortex extracted kinetic energy from the mean jet, maintaining high cyclonic IPV (> 1.6–2.0 UVP; Figure 8) despite moving toward lower latitudes where planetary vorticity |f| decreases.")
    add_p("This process was further assisted by horizontal quarter-wavelength (λ/4) phase locking with a secondary IPV anomaly over Paraná, as well as steering from an offshore dipole blocking anticyclone.")
    add_figure("Figure_10_Barotropic_ERA5.png", "Figure 7. Barotropic instability diagnostics averaged between 300 and 100 hPa for December 22–28, 1995: (a) Absolute vorticity gradient Q_y = β - d²ū/dy² (x 10⁻¹¹ m⁻¹ s⁻¹), with the bold black line denoting the zero contour (Q_y = 0, Kuo's necessary condition satisfied across the deflection zone); (b) Mean zonal wind ū (m s⁻¹). Source: ERA5 Reanalysis.")
    add_figure("Proof_3_Northward_VPI_Evolution.png", "Figure 8. Verification of northward propagation and vortex vigor (21–28/12/1995): (a) Track of the 400 hPa center colored by maximum cyclonic IPV; (b) Time series of 400 hPa central geopotential height and maximum IPV, proving sustained stratospheric values (> 1.5 UVP). Source: ERA5 Reanalysis.")

    # --- 5. CONCLUSIONS ---
    add_heading("5. CONCLUSIONS", level=1)
    add_p("The lifecycle of the December 1995 UTCV over Southeastern South America was investigated through the lens of Isentropic Potential Vorticity (IPV thinking). The key findings are summarized as follows:")
    add_p("1. Baroclinic pre-conditioning occurred over the southeastern Pacific Ocean due to vertical phase coupling (λ/4) between the descending stratospheric PV anomaly and a boundary-layer cyclonic IPV anomaly dammed west of the Andes.")
    add_p("2. Andean mountain transit induced severe vertical compression and downstream stretching, triggering explosive lee cyclogenesis over western Argentina (994 hPa at Mendoza) through the superposition of a warm tropopause fold and diurnal surface heating.")
    add_p("3. Coastal re-intensification over SESA was sustained by an equivalent potential temperature (θe) tongue (> 345 K) fed by easterly maritime advection, forming a vertical IPV tower.")
    add_p("4. The anomalous northeastward displacement across southern and southeastern Brazil was governed by upper-tropospheric barotropic instability (reversal of Kuo's parameter Q_y), horizontal λ/4 vortex interaction, and offshore dipole blocking.")

    # --- ACKNOWLEDGMENTS ---
    add_heading("ACKNOWLEDGMENTS", level=1)
    add_p("The author expresses sincere gratitude to the National Council for Scientific and Technological Development (CNPq - Conselho Nacional de Desenvolvimento Científico e Tecnológico) for financial and research support. Thanks are also extended to the European Centre for Medium-Range Weather Forecasts (ECMWF) for the ERA5 reanalysis and to the NOAA National Centers for Environmental Information (NCEI) for the GridSat-B1 satellite records.")

    # --- REFERENCES ---
    add_heading("REFERENCES", level=1)
    refs = [
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
        "Kuo, H. L. (1949). Dynamic instability of two-dimensional nondivergent flow in a barotropic atmosphere. Journal of Meteorology, 6(2), 105-122.",
        "Orlanski, I.; Katzfey, J.; Menendez, C.; Marino, M. (1991). Simulation of an extratropical cyclone in the Southern Hemisphere: Model sensitivity. Journal of the Atmospheric Sciences, 48(21), 2293-2312.",
        "Reboita, M. S.; Iwabe, C. M. N.; da Rocha, R. P.; Ambrizzi, T. (2009). Análise de um ciclone semi-estacionário na costa sul do Brasil associado a bloqueio atmosférico. Revista Brasileira de Meteorologia, 24(4), 407-422.",
        "Rossby, C.-G. (1940). Planetary flow patterns in the atmosphere. Quarterly Journal of the Royal Meteorological Society, 66(Suppl.), 68-87.",
        "Sanders, F.; Gyakum, J. R. (1980). Synoptic-dynamic climatology of the 'bomb'. Monthly Weather Review, 108(10), 1589-1606.",
        "Seluchi, M. E.; Saulo, A. C. (2012). Baixa do Noroeste Argentino e Baixa do Chaco: características, processos e sua influência sobre o tempo na América do Sul. Revista Brasileira de Meteorologia, 27(1), 49-60.",
        "Thorpe, A. J. (1985). Diagnosis of balanced vortex structure using potential vorticity. Journal of the Atmospheric Sciences, 42(4), 397-406.",
        "Uccellini, L. W.; Keyser, D.; Brill, K. F.; Wash, C. H. (1985). The Presidents' Day cyclone of 18-19 February 1979: Influence of upstream trough amplification and a tropopause fold. Monthly Weather Review, 113(6), 962-988."
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
