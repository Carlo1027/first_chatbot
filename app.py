# app.py
import streamlit as st
import google.generativeai as genai
import os # Para acceder a variables de entorno

# Configurar Gemini API Key
# En Streamlit Cloud, configurarás esta como una "Secret" llamada "GEMINI_API_KEY"
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

model = genai.GenerativeModel('models/gemini-1.5-flash-latest')

# Funciones del core (las que definiste en el Paso 2)
# Colócalas aquí dentro del mismo archivo app.py
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

import random

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

    # Extraer partes con parsing simple
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
            "respuesta_correcta": respuesta_correcta
        }
    except Exception as e:
        return None

def main():
    st.title("👨‍🏫 Mini-Módulo de Evaluación Formativa Adaptativa Asistida por IA para el curso Bases de Datos para Universitarios")
    st.markdown("¡Bienvenido! Estoy aquí para ayudarte con tus dudas de Bases de Datos")
    
    # Selectores para Tema y Nivel
    temas = ["Sistema de Gestión de Bases de Datos (DBMS)",
        "Lenguaje SQL",
        "Diseño de Bases de Datos",
        "Tipos de datos",
        "Seguridad de la base de datos",
        "Consultas SQL Básicas",
        "Consultas SQL Intermedias",
        "Consultas SQL Avanzadas",
        "Diseño de la base de datos",
        "Mantenimiento de la base de datos"
    ]
    nivel_estudiante = st.selectbox("Selecciona tu nivel actual:", ["Básico", "Intermedio", "Avanzado"])
    tema_seleccionado = st.selectbox("Selecciona un tema:", temas)
    
    # Opciones del chatbot
    opcion = st.radio("¿Qué quieres hacer hoy?",
                      ("Explicar un Concepto", "Proponer un Ejercicio", "Evaluar mi Respuesta a un Ejercicio", "Examen de Opción Múltiple"))
    
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
                st.session_state['current_exercise'] = ejercicio # Guardar el ejercicio para evaluación
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
                    for _ in range(10):
                        q = generar_ejercicio_opcion_multiple(tema_seleccionado, nivel_estudiante, preguntas_previas=st.session_state.exam_questions)
                        if q:
                            st.session_state.exam_questions.append(q)
                st.session_state.exam_started = True
                st.rerun()    
        else:
            idx = st.session_state.exam_index
            if idx < len(st.session_state.exam_questions):
                q = st.session_state.exam_questions[idx]
                st.subheader(f"Pregunta {idx + 1} de 10")
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
                        "feedback": feedback
                    })
                    st.session_state.exam_index += 1
                    st.rerun()
                    
                # Botón para reiniciar el examen en cualquier momento
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
                    st.markdown(f"---\n**Pregunta {i+1}:** {r['pregunta']}")
                    for clave, texto in r["opciones"].items():
                        prefijo = "✅" if clave == r["respuesta_correcta"] else "❌" if clave == r["seleccion"] else "•"
                        st.markdown(f"{prefijo} {clave}) {texto}")
    
                    st.markdown(f"**Tu respuesta:** {r['seleccion']} – {'Correcta ✅' if r['correcta'] else 'Incorrecta ❌'}")
    
                    if not r["correcta"] and r["feedback"]:
                        with st.expander("💡 Ver Feedback"):
                            st.markdown(r["feedback"])
    
                if st.button("Reiniciar Examen"):
                    for key in ["exam_started", "exam_index", "exam_questions", "exam_results"]:
                        del st.session_state[key]
                    st.rerun()

if __name__ == "__main__":
    main()
