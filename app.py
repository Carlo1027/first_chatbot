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

def main():
    st.title("👨‍🏫 Chatbot de Bases de Datos para Universitarios")
    st.markdown("¡Bienvenido! Estoy aquí para ayudarte con tus dudas de Bases de Datos")
    
    # Selectores para Tema y Nivel
    temas = ["Introducción a las Bases de Datos",
        "Modelo Relacional y Normalización",
        "SQL - Nivel Básico",
        "SQL - Nivel Intermedio",
        "SQL - Nivel Avanzado",
        "Administración de Bases de Datos",
        "Modelado de Datos y Herramientas",
        "Proyecto Final o Caso Práctico",
        "Temas Complementarios"
    ]
    nivel_estudiante = st.selectbox("Selecciona tu nivel actual:", ["Básico", "Intermedio", "Avanzado"])
    tema_seleccionado = st.selectbox("Selecciona un tema:", temas)
    
    # Opciones del chatbot
    opcion = st.radio("¿Qué quieres hacer hoy?",
                      ("Explicar un Concepto", "Proponer un Ejercicio", "Evaluar mi Respuesta a un Ejercicio", "Simular un Examen"))
    
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

    elif opcion == "Simular un Examen":
        st.header("📝 Examen de Bases de Datos")
    
        if 'exam_started' not in st.session_state:
            st.session_state.exam_started = False
            st.session_state.exam_index = 0
            st.session_state.exam_questions = []
            st.session_state.exam_user_answers = []
            st.session_state.exam_results = []
    
        if not st.session_state.exam_started:
            if st.button("Comenzar Examen"):
                with st.spinner("Generando preguntas del examen..."):
                    for _ in range(10):
                        pregunta = generar_ejercicio(tema_seleccionado, nivel_estudiante)
                        st.session_state.exam_questions.append(pregunta)
                st.session_state.exam_started = True
                st.rerun()()
    
        else:
            index = st.session_state.exam_index
            if index < 10:
                st.subheader(f"Pregunta {index + 1} de 10")
                st.write(st.session_state.exam_questions[index])
                respuesta = st.text_area("Tu respuesta:", key=f"respuesta_{index}")
                if st.button("Enviar Respuesta", key=f"enviar_{index}"):
                    with st.spinner("Evaluando..."):
                        feedback = evaluar_respuesta_y_dar_feedback(
                            st.session_state.exam_questions[index], respuesta
                        )
                        es_correcta = "correcta" in feedback.lower()
                        st.session_state.exam_user_answers.append(respuesta)
                        st.session_state.exam_results.append({
                            "pregunta": st.session_state.exam_questions[index],
                            "respuesta": respuesta,
                            "correcta": es_correcta,
                            "feedback": feedback
                        })
                        st.session_state.exam_index += 1
                        st.rerun()()
            else:
                st.success("¡Examen terminado!")
                total_correctas = sum(1 for r in st.session_state.exam_results if r["correcta"])
                st.markdown(f"### Resultado: {total_correctas} / 10 respuestas correctas")
                for i, r in enumerate(st.session_state.exam_results):
                    st.markdown(f"---\n**Pregunta {i+1}:**\n{r['pregunta']}")
                    st.markdown(f"**Tu Respuesta:** {r['respuesta']}")
                    st.markdown(f"**Correcta:** {'✅ Sí' if r['correcta'] else '❌ No'}")
                    with st.expander("Ver Feedback"):
                        st.markdown(r["feedback"])
    
                if st.button("Reiniciar Examen"):
                    for key in ["exam_started", "exam_index", "exam_questions", "exam_user_answers", "exam_results"]:
                        del st.session_state[key]
                    st.rerun()()


if __name__ == "__main__":
    main()
