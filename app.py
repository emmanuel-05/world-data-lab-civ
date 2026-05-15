import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import sys
import os

# Ajouter le dossier src au PATH pour pouvoir importer utils
sys.path.append(os.path.abspath("src"))
import utils

# Configuration de la page
st.set_page_config(
    page_title="Dashboard Emploi Jeune CIV | World Data Lab",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Style CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-family: 'Inter', sans-serif;
        color: #2c3e50;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .metric-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #00cc96;
    }
    .metric-label {
        font-size: 1.1rem;
        color: #7f8c8d;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------------
# CHARGEMENT DES DONNÉES
# -------------------------------------------------------------------
@st.cache_data
def load_data():
    dfs_raw = utils.load_all_data()
    dfs_civ = utils.filter_civ(dfs_raw)
    dfs_harmonized = utils.harmonize_gender(dfs_civ)
    
    # Séparation par tranches d'âge
    dfs_strict = utils.filter_youth(dfs_harmonized, max_age=24)
    dfs_large = utils.filter_youth(dfs_harmonized, max_age=35)
    
    # Données externes
    df_external = utils.load_external_data()
    df_demo = df_external["demographics"]
    
    return dfs_strict, dfs_large, df_demo

dfs_strict, dfs_large, df_demo = load_data()

# -------------------------------------------------------------------
# SIDEBAR
# -------------------------------------------------------------------

st.sidebar.title("World Data Lab")
st.sidebar.markdown("### Hackathon - Emploi des Jeunes")

menu = st.sidebar.radio(
    "Navigation",
    ["Accueil & Contexte", "Analyse Exploratoire", "Projections (2035)"]
)

# -------------------------------------------------------------------
# PAGE 1 : ACCUEIL
# -------------------------------------------------------------------
if menu == "Accueil & Contexte":
    st.markdown('<h1 class="main-header">L\'Emploi des Jeunes en Côte d\'Ivoire</h1>', unsafe_allow_html=True)
    st.markdown("""
    Bienvenue sur le tableau de bord interactif du projet **World Data Lab**.
    Cette application présente l'analyse approfondie du marché du travail des jeunes en Côte d'Ivoire, 
    ainsi que les projections jusqu'en 2035.
    
    ### Notre Mission
    Comprendre les dynamiques structurelles de l'emploi (notamment l'écart de genre et la prépondérance de l'informel) 
    pour proposer des solutions technologiques ciblées.
    
    ### Les deux définitions de la Jeunesse
    - **15-24 ans (ILO)** : La période critique de transition école-emploi.
    - **15-35 ans (AYEC)** : La jeunesse élargie, pour analyser la stabilisation professionnelle.
    """)
    
    st.info("Utilisez le menu de gauche pour naviguer à travers les différentes analyses.")

# -------------------------------------------------------------------
# PAGE 2 : ANALYSE EXPLORATOIRE
# -------------------------------------------------------------------
elif menu == "Analyse Exploratoire":
    st.markdown('<h1 class="main-header">Analyse Exploratoire (EDA)</h1>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["Informel vs Formel", "Éducation", "Urbain vs Rural"])
    
    with tab1:
        st.subheader("La dynamique d'insertion : L'hégémonie de l'informel")
        tranche = st.radio("Sélectionnez la tranche d'âge", ["15-24 ans", "15-35 ans"])
        
        df_target = dfs_strict["formality"] if tranche == "15-24 ans" else dfs_large["formality"]
        latest_yr = df_target['year'].max()
        df_latest = df_target[df_target['year'] == latest_yr]
        df_form = df_latest.groupby(['gender', 'formality'])['population'].sum().reset_index()
        total = df_form.groupby("gender")["population"].transform("sum")
        df_form["pct"] = (df_form["population"] / total * 100).round(1)
        
        fig1 = px.bar(
            df_form, x="gender", y="pct", color="formality",
            barmode="stack", text="pct",
            color_discrete_map={"Formal": "#636efa", "Informal": "#ef553b"},
            labels={"pct": "Proportion (%)", "gender": "Genre", "formality": "Statut"}
        )
        fig1.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        st.plotly_chart(fig1, use_container_width=True)
        
        st.write("""
        **Constat :** Plus de 95% des jeunes travailleurs ivoiriens évoluent dans l'informel. 
        Le passage à l'âge adulte (15-35 ans) permet une timide percée vers le secteur formel, 
        mais cette évolution est nettement moins favorable aux femmes.
        """)
        
    with tab2:
        st.subheader("Inactivité par niveau d'éducation (15-24 ans)")
        df_in = dfs_strict["inactive"]
        latest_yr = df_in['year'].max()
        df_latest = df_in[df_in['year'] == latest_yr]
        
        # Le taux NEET est donné par neet_fc
        df_in_rate = df_latest.groupby(['edu_ilo', 'gender'])['neet_fc'].mean().reset_index()
        df_in_rate['inactivity_rate'] = (df_in_rate['neet_fc'] * 100).round(1)
        
        fig2 = px.bar(
            df_in_rate, x="edu_ilo", y="inactivity_rate", color="gender",
            barmode="group", text="inactivity_rate",
            color_discrete_map={"Male": "#636efa", "Female": "#ef553b"},
            labels={"inactivity_rate": "Taux d'inactivité (%)", "edu_ilo": "Niveau d'éducation"}
        )
        fig2.update_traces(texttemplate="%{text}%", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)
        st.write("**Le paradoxe du diplôme** : L'inactivité culmine chez les diplômés du secondaire (Upper secondary).")

    with tab3:
        st.subheader("Répartition Géographique de l'Emploi")
        tranche_geo = st.radio("Tranche d'âge", ["15-24 ans", "15-35 ans"], key="geo")
        df_target_geo = dfs_strict["employed_ur"] if tranche_geo == "15-24 ans" else dfs_large["employed_ur"]
        
        latest_yr_geo = df_target_geo['year'].max()
        df_latest_geo = df_target_geo[df_target_geo['year'] == latest_yr_geo]
        df_geo = df_latest_geo.groupby(['geo', 'gender'])['pop_emp_geo'].sum().reset_index()
        total_par_genre = df_geo.groupby('gender')['pop_emp_geo'].transform('sum')
        df_geo['pct'] = (df_geo['pop_emp_geo'] / total_par_genre * 100).round(1)
        
        fig3 = px.bar(
            df_geo, x="gender", y="pct", color="geo", barmode="stack", text="pct",
            color_discrete_map={"urban": "#636efa", "rural": "#00cc96"},
            labels={"pct": "Proportion (%)", "gender": "Genre", "geo": "Zone"}
        )
        fig3.update_traces(texttemplate="%{text:.1f}%", textposition="inside")
        st.plotly_chart(fig3, use_container_width=True)
        st.write("Les villes demeurent les pôles d'attraction majeurs à la sortie du système scolaire.")

# -------------------------------------------------------------------
# PAGE 3 : PROJECTIONS
# -------------------------------------------------------------------
elif menu == "Projections (2035)":
    st.markdown('<h1 class="main-header">Projections et Impact (2025-2035)</h1>', unsafe_allow_html=True)
    
    # Régression pour obtenir df_proj (Simulé d'après l'analyse)
    df_neet_hist = dfs_strict["inactive"].groupby('year')['neet_fc'].mean().reset_index()
    from sklearn.linear_model import LinearRegression
    model = LinearRegression().fit(df_neet_hist[['year']].values, df_neet_hist['neet_fc'].values)
    
    years_future = np.arange(2025, 2036).reshape(-1, 1)
    preds = model.predict(years_future)
    
    df_proj = pd.DataFrame({
        'year': years_future.flatten(),
        'rate_baseline': preds,
        'rate_opti': preds * 0.85
    })
    
    df_impact = df_proj.merge(df_demo[['year', 'pop_15plus']], on='year')
    df_impact['neet_count_baseline'] = df_impact['rate_baseline'] * df_impact['pop_15plus']
    df_impact['neet_count_opti'] = df_impact['rate_opti'] * df_impact['pop_15plus']
    df_impact['jeunes_sauves'] = df_impact['neet_count_baseline'] - df_impact['neet_count_opti']
    
    jeunes_sauves_2035 = df_impact.iloc[-1]['jeunes_sauves'] / 1e6
    
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Jeunes réintégrés en 2035 (Scénario Optimiste)</div>
        <div class="metric-value">{jeunes_sauves_2035:.2f} Millions</div>
    </div>
    <br>
    """, unsafe_allow_html=True)
    
    df_plot = df_impact.melt(
        id_vars='year',
        value_vars=['neet_count_opti', 'jeunes_sauves'],
        var_name='Scenario', value_name='Nombre'
    )
    df_plot['Scenario'] = df_plot['Scenario'].map({
        'neet_count_opti': 'Jeunes NEET restants',
        'jeunes_sauves':   'Jeunes réintégrés (-15%)'
    })
    
    fig_impact = px.area(
        df_plot, x='year', y='Nombre', color='Scenario',
        color_discrete_map={'Jeunes NEET restants': '#ef553b', 'Jeunes réintégrés (-15%)': '#00cc96'},
    )
    fig_impact.update_layout(yaxis_tickformat=",", margin=dict(t=20))
    st.plotly_chart(fig_impact, use_container_width=True)
    
    st.write("""
    **Le Paradoxe Démographique** : Même avec un taux NEET en baisse, 
    la croissance démographique fait que le nombre absolu de jeunes en difficulté continue d'augmenter 
    dans le scénario de référence. L'innovation technologique permet de forcer la trajectoire 
    vers le scénario optimiste.
    """)
