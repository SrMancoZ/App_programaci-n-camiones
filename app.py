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

# Navegación entre versiones
st.title("Optimización de Despacho de Camiones")
opcion = st.radio("Selecciona la versión de la aplicación:", ["Semanal", "Diaria"])

# Versión diaria
if opcion == "Diaria":
    st.header("Optimización diaria")

    # Selección del día
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    dia_seleccionado = st.selectbox("Selecciona el día:", dias)
    dia_idx = dias.index(dia_seleccionado)

    # Entrada de demanda diaria
    st.subheader("Demanda diaria por pallets")
    demanda_diaria_pallets = {}
    for centro in centros_distribucion.keys():
        demanda_diaria_pallets[centro] = st.number_input(
            f"Demanda para {centro}:", min_value=0, step=1
        )

    # Entrada de horarios ocupados
    st.subheader("Horarios ocupados")
    horarios_ocupados = st.text_input(
        "Introduce los horarios ocupados (separados por comas, por ejemplo: 10,11,12):",
        placeholder="Ejemplo: 10,11,12"
    )
    horarios_ocupados = list(map(int, horarios_ocupados.split(','))) if horarios_ocupados else []

    # Botón para ejecutar el modelo
    if st.button("Ejecutar modelo de optimización"):
        try:
            # Crear el modelo
            modelo = pl.LpProblem("Optimización_Diaria", pl.LpMinimize)
            x = pl.LpVariable.dicts("Camiones_pedidos", horarios, 0, None, pl.LpInteger)
            retraso = pl.LpVariable.dicts("Retraso", horarios, 0, None, pl.LpInteger)

            # Función objetivo
            modelo += pl.lpSum([penalizacion_retraso * retraso[t] for t in horarios]) + \
                      pl.lpSum([coste_por_camion * x[t] for t in horarios])

            # Restricciones
            # 1. Cumplir con la demanda diaria de pallets
            for centro, pallets in demanda_diaria_pallets.items():
                modelo += pl.lpSum([x[t] * capacidad_camion for t in horarios]) >= pallets, \
                          f"Satisfacer_demanda_{centro}"

            # 2. Restricción de horarios ocupados
            for t in horarios_ocupados:
                modelo += x[t] == 0, f"Horario_ocupado_{t}"

            # 3. Restricción de capacidad por hora
            for t in horarios:
                modelo += x[t] <= capacidad_horaria, f"Capacidad_max_por_hora_{t}"

            # 4. Restricción de probabilidades de retraso
            prob_retraso = [0.5 if t % 2 == 0 else 0.2 for t in horarios]  # Ejemplo simple de probabilidad
            for t in horarios:
                modelo += retraso[t] >= prob_retraso[t] * x[t], f"Retraso_por_probabilidad_{t}"

            # Resolver el modelo
            modelo.solve()

            # Generar el calendario para el día
            calendario = pd.DataFrame(index=[f"{h}:00" for h in horarios],
                                       columns=["Camiones"])
            for t in horarios:
                calendario.iloc[t, 0] = x[t].varValue if x[t].varValue > 0 else 0

            # Visualización del gráfico
            st.subheader("Calendario de camiones")
            plt.figure(figsize=(10, 6))
            sns.heatmap(calendario.astype(float), annot=True, fmt=".0f", cmap="YlGnBu", cbar_kws={'label': 'Cantidad de Camiones'})
            plt.title(f"Calendario de Camiones - {dia_seleccionado}")
            plt.ylabel("Horas")
            plt.xlabel("Camiones")
            st.pyplot(plt)

            # Generar reporte de retrasos
            st.subheader("Reporte de retrasos")
            retrasos_df = pd.DataFrame({"Hora": [f"{h}:00" for h in horarios],
                                        "Retrasos": [retraso[t].varValue for t in horarios]})
            retrasos_csv = retrasos_df.to_csv(index=False)
            st.download_button("Descargar reporte de retrasos", data=retrasos_csv, file_name=f"retrasos_{dia_seleccionado}.csv")

        except Exception as e:
            st.error(f"Error: {e}")

# Versión semanal (placeholder para coexistencia)
if opcion == "Semanal":
    st.header("Optimización semanal")
    st.write("La versión semanal sigue disponible en esta misma aplicación.")
