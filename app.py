# Author: Carlo Castro
import streamlit as st
import google.generativeai as genai
import os
import random
import pandas as pd
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from textwrap import wrap

# Configurar Gemini API Key como secreto
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

def explicar_concepto(tema):
    prompt = f"""Eres un tutor de Bases de Datos. Explica el concepto de {tema} de forma clara, concisa y paso a paso, como si se lo explicaras a un estudiante universitario. Incluye ejemplos si es pertinente."""
    response = model.generate_content(prompt)
    return response.text

def generar_ejercicio(tema, nivel):
    prompt = f"""Eres un tutor de Bases de Datos. Crea un problema nuevo y original sobre {tema} para un estudiante de nivel {nivel}. Asegúrate de que el problema sea relevante para el tema y el nivel de dificultad. No incluyas la solución."""
    response = model.generate_content(prompt)
    return response.text

def evaluar_respuesta_y_dar_feedback(ejercicio, respuesta_estudiante):
    prompt = f"""Eres un tutor de Bases de Datos. Tu tarea es evaluar la respuesta de un estudiante a un problema y proporcionar retroalimentación detallada.
        Problema:
        {ejercicio}

        Respuesta del estudiante:
        {respuesta_estudiante}

        Por favor, sigue estos pasos:
        1.  Primero, indica si la respuesta del estudiante es correcta o incorrecta.
        2.  Si es incorrecta, explica *por qué* es incorrecta, señalando los errores conceptuales o de cálculo.
        3.  Luego, proporciona la solución *completa y detallada* paso a paso del ejercicio original.
        4.  Usa formato Markdown para una mejor lectura (por ejemplo, listas numeradas para pasos).
    """
    response = model.generate_content(prompt)
    return response.text

def generar_ejercicio_opcion_multiple(tema, nivel, preguntas_previas=None):
    historial = ""
    if preguntas_previas:
        historial = "\nEstas son preguntas que ya se han hecho. No las repitas:\n" + "\n".join(
            [f"- {p['pregunta']}" for p in preguntas_previas if p.get("pregunta")]
        )

    prompt = f"""
        Eres un tutor de Bases de Datos. Debes tener un tópico asociado a esta unidad del curso: {tema}. Crea una pregunta tipo examen de opción múltiple sobre algún tópico dentro de la unidad {tema} para un estudiante de nivel {nivel}.
        Debes retornar:

        1. El enunciado de la pregunta.
        2. Cuatro opciones (A, B, C, D).
        3. Indicar cuál es la opción correcta (por ejemplo, "A").
        4. {historial}

        Usa este formato:
        Pregunta: ...
        Opciones:
        A) ...
        B) ...
        C) ...
        D) ...
        Respuesta correcta: X
    """
    response = model.generate_content(prompt)
    texto = response.text.strip()

    try:
        pregunta = texto.split("Pregunta:")[1].split("Opciones:")[0].strip()
        opciones_raw = texto.split("Opciones:")[1].split("Respuesta correcta:")[0].strip()
        respuesta_correcta = texto.split("Respuesta correcta:")[1].strip()

        opciones = {}
        for linea in opciones_raw.splitlines():
            if ")" in linea:
                clave, valor = linea.split(")", 1)
                opciones[clave.strip()] = valor.strip()

        return {
            "pregunta": pregunta,
            "opciones": opciones,
            "respuesta_correcta": respuesta_correcta,
            "nivel": nivel
        }
    except Exception:
        return None

def generar_pdf(nombre_estudiante, correo_estudiante, exam_results, puntaje):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - inch

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Resultado del Examen – {nombre_estudiante} - {correo_estudiante}")
    y -= 30
    c.setFont("Helvetica", 12)
    c.drawString(50, y, f"Puntaje final: {puntaje}")
    y -= 40

    for i, r in enumerate(exam_results):
        pregunta = r['pregunta']
        opciones = r['opciones']
        seleccion = r['seleccion']
        correcta = r['respuesta_correcta']
        nivel = r['nivel']
        estado = "✅" if r['correcta'] else "❌"

        if y < 150:
            c.showPage()
            y = height - inch

        c.setFont("Helvetica-Bold", 12)
        wrapped_pregunta = wrap(f"{i+1}. {pregunta} (Nivel: {nivel})", width=90)
        for line in wrapped_pregunta:
            c.drawString(50, y, line)
            y -= 15

        c.setFont("Helvetica", 11)
        for clave in ['A', 'B', 'C', 'D']:
            if clave in opciones:
                texto = opciones[clave]
                wrapped_opcion = wrap(f"{clave}) {texto}", width=80)
                for linea in wrapped_opcion:
                    c.drawString(70, y, linea)
                    y -= 13

        c.drawString(70, y, f"Tu respuesta: {seleccion}    | Correcta: {correcta}    {estado}")
        y -= 25

    c.save()
    buffer.seek(0)
    return buffer

def main():
    st.title("👨‍🏫 Mini-Módulo de Evaluación Formativa Adaptativa Asistida por IA para el curso Bases de Datos para Universitarios")
    st.markdown("¡Bienvenido! Estoy aquí para ayudarte con tus dudas de Bases de Datos")

    temas = [
        "Sistema de Gestión de Bases de Datos (DBMS)",
        "Lenguaje SQL",
        "Diseño de Bases de Datos",
        "Tipos de datos",
        "Seguridad de la base de datos",
        "Consultas SQL Básicas",
        "Optimización y buenas prácticas SQL",
        "Diseño de la base de datos",
        "Mantenimiento de la base de datos",
        "Administración de base de datos"
    ]
    nivel_estudiante = st.selectbox("Selecciona tu nivel actual:", ["Básico", "Intermedio", "Avanzado", "Examen real"])
    tema_seleccionado = st.selectbox("Selecciona un tema:", temas)

    opcion = st.radio("¿Qué quieres hacer hoy?", ("Explicar un Concepto", "Proponer un Ejercicio", "Evaluar mi Respuesta a un Ejercicio", "Examen de Opción Múltiple"))

    if opcion == "Explicar un Concepto":
        st.header(f"Explicación de {tema_seleccionado}")
        if st.button("Obtener Explicación"):
            with st.spinner("Generando explicación..."):
                explicacion = explicar_concepto(tema_seleccionado)
                st.write(explicacion)

    elif opcion == "Proponer un Ejercicio":
        st.header(f"Ejercicio de {tema_seleccionado} (Nivel {nivel_estudiante})")
        if st.button("Generar Ejercicio"):
            with st.spinner("Generando ejercicio..."):
                ejercicio = generar_ejercicio(tema_seleccionado, nivel_estudiante)
                st.session_state['current_exercise'] = ejercicio
                st.write(ejercicio)
                st.info("Ahora puedes ir a 'Evaluar mi Respuesta' para obtener retroalimentación.")

    elif opcion == "Evaluar mi Respuesta a un Ejercicio":
        st.header("Evaluar mi Respuesta")
        if 'current_exercise' in st.session_state and st.session_state['current_exercise']:
            st.write("**Ejercicio Actual:**")
            st.write(st.session_state['current_exercise'])
            respuesta_estudiante = st.text_area("Escribe aquí tu respuesta:")
            if st.button("Evaluar"):
                if respuesta_estudiante:
                    with st.spinner("Evaluando y generando feedback..."):
                        feedback = evaluar_respuesta_y_dar_feedback(st.session_state['current_exercise'], respuesta_estudiante)
                        st.write(feedback)
                else:
                    st.warning("Por favor, escribe tu respuesta para evaluar.")
        else:
            st.info("Primero genera un ejercicio en la sección 'Proponer un Ejercicio'.")

    elif opcion == "Examen de Opción Múltiple":
        st.header("📝 Examen de Opción Múltiple")

        if 'exam_started' not in st.session_state:
            st.session_state.exam_started = False
            st.session_state.exam_index = 0
            st.session_state.exam_questions = []
            st.session_state.exam_results = []

        if not st.session_state.exam_started:
            if st.button("Comenzar Examen"):
                with st.spinner("Generando preguntas..."):
                    niveles_posibles = ["Básico", "Intermedio", "Avanzado"] if nivel_estudiante == "Examen real" else [nivel_estudiante]
                    for _ in range(10):
                        nivel_random = random.choice(niveles_posibles)
                        q = generar_ejercicio_opcion_multiple(tema_seleccionado, nivel_random, preguntas_previas=st.session_state.exam_questions)
                        if q:
                            st.session_state.exam_questions.append(q)
                st.session_state.exam_started = True
                st.rerun()
        else:
            idx = st.session_state.exam_index
            if idx < len(st.session_state.exam_questions):
                q = st.session_state.exam_questions[idx]
                st.subheader(f"Pregunta {idx + 1} de 10 – Nivel: {q.get('nivel', 'N/A')}")
                st.write(q["pregunta"])
                opciones = list(q["opciones"].items())
                seleccion = st.radio("Selecciona una opción:", [f"{k}) {v}" for k, v in opciones], key=f"preg_{idx}")

                if st.button("Responder", key=f"btn_{idx}"):
                    respuesta_usuario = seleccion.split(")")[0]
                    correcta = respuesta_usuario == q["respuesta_correcta"]

                    feedback = ""
                    if not correcta:
                        ejercicio_texto = f"{q['pregunta']}\nOpciones:\n" + "\n".join([f"{k}) {v}" for k, v in q["opciones"].items()])
                        respuesta_estudiante = f"{respuesta_usuario}) {q['opciones'][respuesta_usuario]}"
                        feedback = evaluar_respuesta_y_dar_feedback(ejercicio_texto, respuesta_estudiante)

                    st.session_state.exam_results.append({
                        "pregunta": q["pregunta"],
                        "seleccion": respuesta_usuario,
                        "correcta": correcta,
                        "respuesta_correcta": q["respuesta_correcta"],
                        "opciones": q["opciones"],
                        "feedback": feedback,
                        "nivel": q.get("nivel")
                    })
                    st.session_state.exam_index += 1
                    st.rerun()

                st.divider()
                if st.button("🔄 Reiniciar Examen"):
                    for key in ["exam_started", "exam_index", "exam_questions", "exam_results"]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()
            else:
                st.success("¡Examen finalizado!")
                total = len(st.session_state.exam_results)
                correctas = sum(1 for r in st.session_state.exam_results if r["correcta"])
                st.markdown(f"### ✅ Resultado final: {correctas} / {total} correctas")              

                for i, r in enumerate(st.session_state.exam_results):
                    st.markdown(f"---\n**Pregunta {i+1} (Nivel: {r['nivel']}):** {r['pregunta']}")
                    for clave, texto in r["opciones"].items():
                        prefijo = "✅" if clave == r["respuesta_correcta"] else "❌" if clave == r["seleccion"] else "•"
                        st.markdown(f"{prefijo} {clave}) {texto}")

                    st.markdown(f"**Tu respuesta:** {r['seleccion']} – {'Correcta ✅' if r['correcta'] else 'Incorrecta ❌'}")

                    if not r["correcta"] and r["feedback"]:
                        with st.expander("💡 Ver Feedback"):
                            st.markdown(r["feedback"])

                # --- Formulario para exportar resultados ---
                st.markdown("### 📄 Descargar Resultados del Examen")
                
                nombre_estudiante = st.text_input("🧑‍🎓 Tu nombre", key="nombre_resultado")
                correo_estudiante = st.text_input("📧 Tu correo", key="correo_resultado")
                
                if nombre_estudiante and correo_estudiante:
                    df_resultados = pd.DataFrame([
                        {
                            "Pregunta": r["pregunta"],
                            "Nivel": r["nivel"],
                            "Tu respuesta": r["seleccion"],
                            "Respuesta correcta": r["respuesta_correcta"],
                            "¿Correcta?": "Sí" if r["correcta"] else "No"
                        }
                        for r in st.session_state.exam_results
                    ])
                    df_resultados.loc[len(df_resultados.index)] = {
                        "Pregunta": "PUNTAJE FINAL",
                        "Nivel": "",
                        "Tu respuesta": "",
                        "Respuesta correcta": "",
                        "¿Correcta?": f"{correctas} de {total}"
                    }
                
                    excel_output = BytesIO()
                    with pd.ExcelWriter(excel_output, engine='xlsxwriter') as writer:
                        df_resultados.to_excel(writer, index=False, sheet_name='Resultados')
                    excel_output.seek(0)
                
                    st.download_button(
                        label="📥 Descargar Resultados en Excel",
                        data=excel_output,
                        file_name=f"Resultados_{nombre_estudiante.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("Completa tu nombre y correo para activar la descarga en formato excel.")

                if nombre_estudiante and correo_estudiante:
                    if st.button("📥 Generar y Descargar PDF"):
                        pdf_bytes = generar_pdf(nombre_estudiante, correo_estudiante, st.session_state.exam_results, f"{correctas} / {total}")
                        st.download_button(
                            label="Descargar PDF",
                            data=pdf_bytes,
                            file_name=f"Resultados_{nombre_estudiante.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
                else:
                    st.info("Completa tu nombre y correo para habilitar la descarga en formato PDF.")               

                # --- Botón para reiniciar resultado ---
                if st.button("Reiniciar Examen"):
                    for key in ["exam_started", "exam_index", "exam_questions", "exam_results"]:
                        del st.session_state[key]
                    st.rerun()

if __name__ == "__main__":
    main()
