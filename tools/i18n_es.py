"""The Spanish for the member pages. Edit here, then run:

    python tools/i18n_es.py        (writes window.SB_I18N in theme/assets/sb-i18n.js, then checks nothing is missing)

Keys are the English exactly as the templates and the Python have them (spaces collapsed). Placeholders in braces
({n}, {t}, {title} ...) stay as they are. Tone: warm, "tú", neutral Latin-American Spanish (carro, manejar).
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

ES = {
    # waitlist
    "Sayback opens for sale very soon": "Sayback sale a la venta muy pronto",
    "Lesson 1 is already yours. Leave your email and we'll write once, the day the full course is ready, with an early-listener price.":
        "La lección 1 ya es tuya. Déjanos tu correo y te escribiremos una sola vez, el día que el curso completo esté listo, con un precio para los primeros.",
    "Your email": "Tu correo",
    "We only use it for this one message. You can ask us to remove it any time.":
        "Solo lo usamos para ese mensaje. Puedes pedirnos que lo borremos cuando quieras.",
    "You're on the list": "Ya estás en la lista",
    "We'll write once, the day it opens. Until then, lesson 1 is waiting in your library.":
        "Te escribiremos una vez, el día que abra. Mientras tanto, la lección 1 te espera en tu biblioteca.",
    "Not now": "Ahora no", "Tell me when it opens": "Avísame cuando abra", "Great": "Perfecto",
    # tiles, levels, phrases
    "Done": "Hecha", "{pct}% heard": "{pct}% escuchada", "Locked": "Bloqueada", "Free": "Gratis", "Ready": "Lista",
    "Level {n}": "Nivel {n}", "Lesson {n}": "Lección {n}",
    "a woman says": "lo dice una mujer", "a man says": "lo dice un hombre", "tap to show the answer": "toca para ver la respuesta",
    # offers
    "one time, yours to keep": "pago único, tuyo para siempre", "Best value": "La mejor opción", "You picked this one": "Elegiste esta",
    "Level 1 · First Steps": "Nivel 1 · Primeros pasos", "Complete course · Levels 1 to 5": "Curso completo · Niveles 1 a 5",
    "Upgrade · Levels 2 to 5": "Ampliación · Niveles 2 a 5", "Get Level 1": "Quiero el nivel 1",
    "Get the complete course": "Quiero el curso completo", "Get Levels 2 to 5": "Quiero los niveles 2 a 5",
    "30 lessons × 45 minutes (22½ hours)": "30 lecciones de 45 minutos (22,5 horas)",
    "600 phrases in 30 real situations": "600 frases en 30 situaciones reales",
    "Phrase sheet and full transcript for each lesson": "Hoja de frases y transcripción de cada lección",
    "Play in the app or download the MP3s": "Escúchalas en la app o descarga los MP3",
    "All 150 lessons × 45 minutes (112 hours)": "Las 150 lecciones de 45 minutos (112 horas)",
    "3,000 phrases across five levels": "3.000 frases en cinco niveles",
    "Regional accents and slang in Level 5": "Acentos y expresiones de cada región en el nivel 5",
    "Less than buying the levels one by one": "Menos que comprar los niveles uno por uno",
    "Levels 2 to 5: 120 more lessons (90 hours)": "Niveles 2 a 5: 120 lecciones más (90 horas)",
    "2,400 more phrases, up to fluent and local": "2.400 frases más, hasta hablar con soltura",
    "Your Level 1 progress carries straight on": "Sigues justo donde vas en el nivel 1",
    "In your library": "En tu biblioteca",
    "Paid": "Pagado", "A gift": "Un regalo", "Refunded": "Reembolsado",
    "Level 1": "Nivel 1", "Levels 1 to 5": "Niveles 1 a 5", "Levels 2 to 5": "Niveles 2 a 5",
    # frame
    "Signed out. See you soon!": "Sesión cerrada. ¡Hasta pronto!", "Sign in": "Entrar", "Listen free": "Escucha gratis",
    "Your library": "Tu biblioteca", "Your account": "Tu cuenta", "Appearance": "Apariencia", "Auto": "Automático",
    "Light": "Claro", "Dark": "Oscuro", "Submit feedback": "Enviar comentarios", "Privacy &amp; Terms": "Privacidad y condiciones",
    "Sign out": "Cerrar sesión", "Speak a new language in the minutes you already have.": "Habla un idioma nuevo en los minutos que ya tienes.",
    "Prices": "Precios", "You": "Tú", "Main": "Principal", "Library": "Biblioteca", "Courses": "Cursos",
    "That page is for admins only.": "Esa página es solo para administradores.",
    # sign in
    "Continue with Google": "Continuar con Google", "At least 8 characters": "Al menos 8 caracteres", "Show": "Ver", "Hide": "Ocultar",
    "Welcome to Sayback!": "¡Bienvenido a Sayback!", "Welcome back!": "¡Qué bueno verte de nuevo!", "Welcome back": "Hola de nuevo",
    "Sign in to pick up where you stopped.": "Entra para seguir donde te quedaste.",
    "Create your free account": "Crea tu cuenta gratis",
    "Lesson 1 is yours, all 45 minutes. It takes a few seconds.": "La lección 1 es tuya, los 45 minutos. Tarda unos segundos.",
    "Create account": "Crear cuenta", "Reset your password": "Cambia tu contraseña",
    "We'll email you a link to choose a new password.": "Te enviaremos un enlace para elegir una contraseña nueva.",
    "Send the link": "Enviar el enlace", "Your name": "Tu nombre", "Email": "Correo", "Password": "Contraseña", "or": "o",
    "Forgot your password?": "¿Olvidaste tu contraseña?", "Back to sign in": "Volver a entrar", "About Sayback": "Qué es Sayback",
    "Sign in or create an account": "Entra o crea una cuenta",
    "Make your free account first. It takes a few seconds.": "Primero crea tu cuenta gratis. Tarda unos segundos.",
    # buy
    "Pay once. Keep every lesson. Listen anywhere.": "Pagas una vez. Te quedas con todas las lecciones. Escúchalas donde sea.",
    "Sales open very soon. The buttons put you on the list for opening day, with an early-listener price.":
        "La venta abre muy pronto. Los botones te apuntan en la lista para el día de apertura, con un precio para los primeros.",
    "Learn Spanish": "Aprender español", "Learn English": "Aprender inglés", "Course": "Curso", "days": "días",
    "Speak or it's free.": "Hablas o es gratis.",
    "Do the first five lessons, out loud. If you can't greet someone, order a coffee and ask for directions, write to us within the guarantee period for a full refund. No forms, no questions.":
        "Haz las primeras cinco lecciones, en voz alta. Si no puedes saludar, pedir un café y preguntar una dirección, escríbenos dentro del plazo de la garantía y te devolvemos todo. Sin formularios, sin preguntas.",
    "Secure checkout by Stripe. We never see your card.": "Pago seguro con Stripe. Nunca vemos tu tarjeta.",
    "One payment. No subscription, nothing to cancel.": "Un solo pago. Sin suscripción, nada que cancelar.",
    "Lessons unlock the moment you pay, in the app and as MP3s.": "Las lecciones se abren en cuanto pagas, en la app y como MP3.",
    "Not sure yet? Make a free account and the whole of lesson 1 is yours.": "¿Aún no te decides? Crea una cuenta gratis y la lección 1 completa es tuya.",
    "Listen to lesson 1 free": "Escucha la lección 1 gratis", "See the courses": "Ver los cursos", "Open your library": "Abre tu biblioteca",
    # lesson
    "Unlock Level 1 to hear this lesson": "Desbloquea el nivel 1 para escuchar esta lección",
    "This lesson is in Levels 2 to 5": "Esta lección está en los niveles 2 a 5",
    "Here's a taste: the first 3 of its 20 new phrases. Pay once and every lesson in the level is yours to keep.":
        "Aquí tienes una muestra: las 3 primeras de sus 20 frases nuevas. Pagas una vez y todas las lecciones del nivel son tuyas.",
    "Picking up where you stopped, at {t}.": "Sigues donde te quedaste, en {t}.",
    "A taste: 3 of this lesson's 20 new phrases.": "Una muestra: 3 de las 20 frases nuevas de esta lección.",
    "Read them after the lesson, not while driving. Quiz yourself hides the answers: say them out loud, then tap to check.":
        "Léelas después de la lección, no mientras manejas. «Ponte a prueba» oculta las respuestas: dilas en voz alta y toca para comprobar.",
    "Quiz yourself": "Ponte a prueba", "Show all answers": "Ver todas las respuestas", "Next lesson": "Siguiente lección",
    "Previous lesson": "Lección anterior", "Done. Mark as not done": "Hecha. Marcar como pendiente", "Mark as done": "Marcar como hecha",
    "Marked as done": "Marcada como hecha", "Marked as not done": "Marcada como pendiente",
    "The lesson audio didn't load. Check your connection, then press play again.":
        "El audio de la lección no cargó. Revisa tu conexión y vuelve a darle play.",
    "Tomorrow: {title}. Sleep on today's phrases; that's when they set.":
        "Mañana: {title}. Duerme con las frases de hoy: es cuando se fijan.",
    "That was the free lesson. Unlock Level 1 and tomorrow's drive is lesson 2.":
        "Esa era la lección gratis. Desbloquea el nivel 1 y el camino de mañana será la lección 2.",
    "That was the very last lesson. You did it: the whole course, out loud.":
        "Esa fue la última lección. Lo lograste: el curso entero, en voz alta.",
    "Play": "Reproducir", "Pause": "Pausa", "Back 10 seconds": "Atrás 10 segundos", "Forward 10 seconds": "Adelante 10 segundos",
    "Position in the lesson": "Posición en la lección", "Intro": "Introducción", "Part {n} of 3": "Parte {n} de 3",
    "Pep talk": "Ánimo", "Wrap-up": "Cierre", "Car mode": "Modo carro", "Exit car mode": "Salir del modo carro", "Speed": "Velocidad",
    "Tap anywhere big to play or pause. Eyes on the road.": "Toca el botón grande para pausar o seguir. La vista en el camino.",
    "This lesson's audio is on its way": "El audio de esta lección está en camino",
    "The lessons are being uploaded. Try again a little later: your place in the course is saved.":
        "Estamos subiendo las lecciones. Vuelve a intentarlo un poco más tarde: tu lugar en el curso está guardado.",
    "Lesson done. Well spoken!": "Lección terminada. ¡Bien dicho!", "Back to the library": "Volver a la biblioteca",
    "Today's new phrases": "Las frases nuevas de hoy", "Culture moment": "Momento cultural", "Take it with you": "Llévatela",
    "Download the MP3": "Descargar el MP3", "Download the transcript": "Descargar la transcripción", "Lessons": "Lecciones",
    # library
    "Good morning": "Buenos días", "Good afternoon": "Buenas tardes", "Good evening": "Buenas noches",
    "{n} of 150 lessons done": "{n} de 150 lecciones hechas",
    "You've heard the free lesson. Ready for the rest?": "Ya escuchaste la lección gratis. ¿Listo para el resto?",
    "Next up: {title}. Unlock Level 1 to keep going tomorrow morning.":
        "Lo que sigue: {title}. Desbloquea el nivel 1 para seguir mañana temprano.",
    "Resume at {t}": "Seguir en {t}", "Play lesson": "Escuchar la lección", "{done} of {count} done": "{done} de {count} hechas",
    "Lesson 1 is free. Unlock Level 1 for the other 29.": "La lección 1 es gratis. Desbloquea el nivel 1 para las otras 29.",
    "Locked. Lesson titles are here so you can see what's coming.": "Bloqueado. Ves los títulos para saber lo que viene.",
    "You finished all 150 lessons.": "Terminaste las 150 lecciones.",
    "That's about 112 hours of speaking out loud. Pick any lesson to keep it fresh, or try the other direction with a friend.":
        "Son unas 112 horas hablando en voz alta. Elige cualquier lección para mantenerlo fresco, o prueba el otro sentido con un amigo.",
    "stolen minutes this week": "minutos robados esta semana", "day streak": "días seguidos", "lessons done": "lecciones hechas",
    "The last two weeks. A day counts once you've listened for a minute.":
        "Las últimas dos semanas. Un día cuenta en cuanto escuchas un minuto.",
    "Unlock the rest of the course": "Desbloquea el resto del curso",
    # profile
    "Save": "Guardar", "Saved": "Guardado", "Email me a reset link": "Envíame un enlace para cambiarla", "member since": "miembro desde",
    "Please tell us your name.": "Dinos tu nombre, por favor.", "Your courses": "Tus cursos",
    "Nothing bought yet. Lesson 1 of each course is free with your account.":
        "Todavía no compraste nada. La lección 1 de cada curso es gratis con tu cuenta.",
    "How we greet you": "Cómo te saludamos", "Language of the app": "Idioma de la app", "Language": "Idioma",
    "Follow your device, or pick one.": "Sigue a tu dispositivo, o elige uno.",
    "We'll email you a link to choose a new one.": "Te enviaremos un enlace para elegir una nueva.",
    "Privacy &amp; Terms, and your data": "Privacidad, condiciones y tus datos",
    # thanks
    "Unlocking your lessons": "Abriendo tus lecciones",
    "Stripe has your payment. This usually takes a few seconds.": "Stripe ya tiene tu pago. Normalmente tarda unos segundos.",
    "Almost there": "Casi listo",
    "Your payment went through, but the unlock is taking longer than usual. It will appear in your library shortly. If it hasn't within an hour, write to arkvital@outlook.com and we'll sort it out the same day.":
        "Tu pago se hizo, pero la apertura está tardando más de lo normal. Aparecerá en tu biblioteca en breve. Si no aparece en una hora, escribe a arkvital@outlook.com y lo resolvemos el mismo día.",
    "You're in. Welcome to Sayback.": "Ya estás dentro. Bienvenido a Sayback.",
    "Every level is unlocked. Your next lesson is waiting in the library.": "Todos los niveles están abiertos. Tu próxima lección te espera en la biblioteca.",
    "All 30 lessons of Level 1 are yours. Tomorrow's drive is lesson 2.": "Las 30 lecciones del nivel 1 son tuyas. El camino de mañana es la lección 2.",
    "Play my next lesson": "Escuchar mi próxima lección",
    # server messages
    "This lesson is locked.": "Esta lección está bloqueada.",
    "You already own this. It's in your library.": "Ya lo tienes. Está en tu biblioteca.",
    "That isn't something we sell.": "Eso no es algo que vendamos.",
    "That email doesn't look right. Check it and try again.": "Ese correo no parece correcto. Revísalo y vuelve a intentarlo.",
    "There's no such course.": "Ese curso no existe.",
    "That's a lot of sign-ups from one browser. Please try again later.": "Son muchos registros desde un mismo navegador. Vuelve a intentarlo más tarde.",
    "That lesson doesn't exist.": "Esa lección no existe.",
    "Please use at least 2 characters for your name.": "Usa al menos 2 letras para tu nombre.",
    "That didn't work.": "Eso no funcionó.",
    "An account with that email already exists. Try signing in.": "Ya hay una cuenta con ese correo. Prueba a entrar.",
    "Please confirm your email first. Check your inbox for the link.": "Primero confirma tu correo. Busca el enlace en tu bandeja de entrada.",
    "This account is disabled.": "Esta cuenta está desactivada.",
    "Too many wrong attempts. Wait a while, or reset your password.": "Demasiados intentos fallidos. Espera un rato o cambia tu contraseña.",
    "That email and password don't match.": "Ese correo y esa contraseña no coinciden.",
    "Please choose a stronger password.": "Elige una contraseña más segura.",
    "Account created. Check your email for a confirmation link, then sign in.": "Cuenta creada. Busca el enlace de confirmación en tu correo y luego entra.",
    "If that email has an account, a reset link is on its way.": "Si ese correo tiene una cuenta, el enlace ya va en camino.",
    "Google sign-in was cancelled.": "Se canceló la entrada con Google.",
    "Please enter a valid email address.": "Escribe un correo válido.",
    "Please choose a password of at least 8 characters.": "Elige una contraseña de al menos 8 caracteres.",
    "Please enter your password.": "Escribe tu contraseña.",
}


def main():
    f = ROOT / "theme" / "assets" / "sb-i18n.js"
    js = f.read_text(encoding="utf-8")
    head = js.split("window.SB_I18N = ", 1)[0]
    body = json.dumps(dict(sorted(ES.items())), ensure_ascii=False, indent=1)
    f.write_bytes((head + "window.SB_I18N = " + body + ";\n").encode("utf-8"))
    print("wrote %d entries" % len(ES))
    sys.exit(subprocess.call([sys.executable, str(ROOT / "tools" / "i18n_keys.py")]))


if __name__ == "__main__":
    main()
