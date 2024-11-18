import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pulp as pl

# Parámetros fijos
centros_distribucion = {"CD Lampa": 1, "ABCPACK": 2, "Egakat": 3}
capacidad_camion = 28
coste_por_camion = 70000
penalizacion_retraso = 70000
capacidad_horaria = 2
horarios = list(range(24))
dias = list(range(7))

# Título de la aplicación
st.title("Optimización de Despacho de Camiones")

# Entrada de datos
st.header("1. Introduce los datos necesarios")

# Input: Demanda diaria
st.subheader("Demanda diaria por pallets")
demanda_diaria_pallets = {}
for centro in centros_distribucion.keys():
    demanda_diaria_pallets[centro] = st.text_input(
        f"Demanda semanal para {centro} (separada por comas, ejemplo: 100,200,300,400,500,0,0):",
        placeholder="Introduce 7 valores separados por comas"
    )

# Input: Pallets pendientes
st.subheader("Pallets pendientes")
pallets_pendientes = {}
for centro in centros_distribucion.keys():
    pallets_pendientes[centro] = st.number_input(
        f"Pallets pendientes para {centro}:",
        min_value=0,
        step=1
    )

# Input: Horarios ocupados diarios
st.subheader("Horarios ocupados diarios")
horarios_ocupados_diarios = {}
for dia in dias:
    horarios_ocupados_diarios[dia] = st.text_input(
        f"Horarios ocupados para el día {['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'][dia]} (separados por comas):",
        placeholder="Ejemplo: 10,11,12"
    )

# Botón para ejecutar el modelo
if st.button("Ejecutar modelo de optimización"):
    try:
        # Procesar los inputs
        demanda_diaria_pallets = {k: list(map(int, v.split(','))) for k, v in demanda_diaria_pallets.items()}
        horarios_ocupados_diarios = {k: list(map(int, v.split(','))) if v else [] for k, v in horarios_ocupados_diarios.items()}
        
        # Crear el modelo
        modelo = pl.LpProblem("Optimización_Despacho_Camiones", pl.LpMinimize)
        x = pl.LpVariable.dicts("Camiones_pedidos", [(t, d) for t in horarios for d in dias], 0, None, pl.LpInteger)
        retraso = pl.LpVariable.dicts("Retraso", [(t, d) for t in horarios for d in dias], 0, None, pl.LpInteger)

        # Función objetivo
        modelo += pl.lpSum([penalizacion_retraso * retraso[(t, d)] for t in horarios for d in dias]) + \
                  pl.lpSum([coste_por_camion * x[(t, d)] for t in horarios for d in dias])

        # Restricciones
        for j in centros_distribucion:
            for d in dias:
                demanda = demanda_diaria_pallets[j][d] + (pallets_pendientes[j] if d == 0 else 0)
                modelo += pl.lpSum([x[(t, d)] * capacidad_camion for t in horarios]) >= demanda

        for d in dias:
            for t in horarios_ocupados_diarios[d]:
                modelo += x[(t, d)] == 0

        for d in dias:
            for t in horarios:
                modelo += x[(t, d)] <= capacidad_horaria

        # Resolver el modelo
        modelo.solve()

        # Generar el calendario
        calendario_camiones = pd.DataFrame(index=[f"{h}:00" for h in horarios],
                                           columns=["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"])
        for d in dias:
            for t in horarios:
                calendario_camiones.iloc[t, d] = x[(t, d)].varValue if x[(t, d)].varValue > 0 else 0

        # Visualización del gráfico
        st.header("2. Calendario de camiones")
        plt.figure(figsize=(10, 6))
        sns.heatmap(calendario_camiones.astype(float), annot=True, fmt=".0f", cmap="YlGnBu")
        plt.title("Calendario Semanal de Reserva de Camiones")
        plt.ylabel("Horas")
        plt.xlabel("Días de la Semana")
        st.pyplot(plt)

        # Descargar reporte
        st.header("3. Descarga el reporte de retrasos")
        retrasos_df = pd.DataFrame([(t, d, retraso[(t, d)].varValue) for t in horarios for d in dias],
                                   columns=["Hora", "Día", "Retraso"])
        retrasos_csv = retrasos_df.to_csv(index=False)
        st.download_button("Descargar reporte de retrasos", data=retrasos_csv, file_name="reporte_retrasos.csv")
    except Exception as e:
        st.error(f"Error: {e}")
