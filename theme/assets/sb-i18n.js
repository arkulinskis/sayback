/* Sayback: English / Spanish for the member pages (client_code/i18n.py is the Python side).
   SB.tr(root, lang): every [data-t] element shows its English (kept in data-t-en) or the Spanish from SB_I18N;
   [data-ta="placeholder,aria-label"] does the same for attributes. Missing entries go to window.SB_MISSING. */
(function () {
  var SB = window.SB = window.SB || {};
  var KEY = 'sayback.lang';
  window.SB_MISSING = window.SB_MISSING || [];

  function norm(s) { return String(s || '').replace(/\s+/g, ' ').trim(); }
  function first() {
    try { var v = localStorage.getItem(KEY); if (v === 'en' || v === 'es') return v; } catch (e) {}
    return /^es\b/i.test(navigator.language || '') ? 'es' : 'en';
  }
  var current = first();

  SB.lang = function () { return current; };
  SB.setLang = function (v) {
    if (v !== 'en' && v !== 'es') return;
    current = v;
    try { localStorage.setItem(KEY, v); } catch (e) {}
    document.documentElement.setAttribute('lang', v);
  };
  SB.t = function (text) {
    var key = norm(text), pack = window.SB_I18N || {};
    if (current !== 'es') return text;
    if (Object.prototype.hasOwnProperty.call(pack, key)) return pack[key];
    if (window.SB_MISSING.indexOf(key) < 0) window.SB_MISSING.push(key);
    return text;
  };
  SB.tr = function (root, lang) {
    if (!root || !root.querySelectorAll) return;
    lang = lang || current;
    var els = Array.prototype.slice.call(root.querySelectorAll('[data-t]'));
    els.forEach(function (el) {
      if (!el.hasAttribute('data-t-en')) el.setAttribute('data-t-en', el.innerHTML);
      var en = el.getAttribute('data-t-en');
      var out = lang === 'es' ? SB.t(en) : en;
      if (lang === 'es' && out === en && current !== 'es') out = en;
      if (el.innerHTML !== out) el.innerHTML = out;
    });
    var withAttrs = Array.prototype.slice.call(root.querySelectorAll('[data-ta]'));
    withAttrs.forEach(function (el) {
      el.getAttribute('data-ta').split(',').forEach(function (name) {
        name = name.trim();
        var keep = 'data-ta-' + name;
        if (!el.hasAttribute(keep)) el.setAttribute(keep, el.getAttribute(name) || '');
        var en = el.getAttribute(keep);
        if (en) el.setAttribute(name, lang === 'es' ? SB.t(en) : en);
      });
    });
  };
})();

/* ---- the Spanish (key = the English text with spaces collapsed, exactly as written in the template) ---- */
window.SB_I18N = {
 "2,400 more phrases, up to fluent and local": "2.400 frases más, hasta hablar con soltura",
 "3,000 phrases across five levels": "3.000 frases en cinco niveles",
 "30 lessons × 45 minutes (22½ hours)": "30 lecciones de 45 minutos (22,5 horas)",
 "600 phrases in 30 real situations": "600 frases en 30 situaciones reales",
 "A gift": "Un regalo",
 "A taste: 3 of this lesson's 20 new phrases.": "Una muestra: 3 de las 20 frases nuevas de esta lección.",
 "About Sayback": "Qué es Sayback",
 "Account created. Check your email for a confirmation link, then sign in.": "Cuenta creada. Busca el enlace de confirmación en tu correo y luego entra.",
 "All 150 lessons × 45 minutes (112 hours)": "Las 150 lecciones de 45 minutos (112 horas)",
 "All 30 lessons of Level 1 are yours. Tomorrow's drive is lesson 2.": "Las 30 lecciones del nivel 1 son tuyas. El camino de mañana es la lección 2.",
 "Almost there": "Casi listo",
 "An account with that email already exists. Try signing in.": "Ya hay una cuenta con ese correo. Prueba a entrar.",
 "Appearance": "Apariencia",
 "At least 8 characters": "Al menos 8 caracteres",
 "Auto": "Automático",
 "Back 10 seconds": "Atrás 10 segundos",
 "Back to sign in": "Volver a entrar",
 "Back to the library": "Volver a la biblioteca",
 "Best value": "La mejor opción",
 "Car mode": "Modo carro",
 "Complete course · Levels 1 to 5": "Curso completo · Niveles 1 a 5",
 "Continue with Google": "Continuar con Google",
 "Course": "Curso",
 "Courses": "Cursos",
 "Create account": "Crear cuenta",
 "Create your free account": "Crea tu cuenta gratis",
 "Culture moment": "Momento cultural",
 "Dark": "Oscuro",
 "Do the first five lessons, out loud. If you can't greet someone, order a coffee and ask for directions, write to us within the guarantee period for a full refund. No forms, no questions.": "Haz las primeras cinco lecciones, en voz alta. Si no puedes saludar, pedir un café y preguntar una dirección, escríbenos dentro del plazo de la garantía y te devolvemos todo. Sin formularios, sin preguntas.",
 "Done": "Hecha",
 "Done. Mark as not done": "Hecha. Marcar como pendiente",
 "Download the MP3": "Descargar el MP3",
 "Download the transcript": "Descargar la transcripción",
 "Email": "Correo",
 "Email me a reset link": "Envíame un enlace para cambiarla",
 "Every level is unlocked. Your next lesson is waiting in the library.": "Todos los niveles están abiertos. Tu próxima lección te espera en la biblioteca.",
 "Exit car mode": "Salir del modo carro",
 "Follow your device, or pick one.": "Sigue a tu dispositivo, o elige uno.",
 "Forgot your password?": "¿Olvidaste tu contraseña?",
 "Forward 10 seconds": "Adelante 10 segundos",
 "Free": "Gratis",
 "Get Level 1": "Quiero el nivel 1",
 "Get Levels 2 to 5": "Quiero los niveles 2 a 5",
 "Get the complete course": "Quiero el curso completo",
 "Good afternoon": "Buenas tardes",
 "Good evening": "Buenas noches",
 "Good morning": "Buenos días",
 "Google sign-in was cancelled.": "Se canceló la entrada con Google.",
 "Great": "Perfecto",
 "Here's a taste: the first 3 of its 20 new phrases. Pay once and every lesson in the level is yours to keep.": "Aquí tienes una muestra: las 3 primeras de sus 20 frases nuevas. Pagas una vez y todas las lecciones del nivel son tuyas.",
 "Hide": "Ocultar",
 "How we greet you": "Cómo te saludamos",
 "If that email has an account, a reset link is on its way.": "Si ese correo tiene una cuenta, el enlace ya va en camino.",
 "In your library": "En tu biblioteca",
 "Intro": "Introducción",
 "Language": "Idioma",
 "Language of the app": "Idioma de la app",
 "Learn English": "Aprender inglés",
 "Learn Spanish": "Aprender español",
 "Less than buying the levels one by one": "Menos que comprar los niveles uno por uno",
 "Lesson 1 is already yours. Leave your email and we'll write once, the day the full course is ready, with an early-listener price.": "La lección 1 ya es tuya. Déjanos tu correo y te escribiremos una sola vez, el día que el curso completo esté listo, con un precio para los primeros.",
 "Lesson 1 is free. Unlock Level 1 for the other 29.": "La lección 1 es gratis. Desbloquea el nivel 1 para las otras 29.",
 "Lesson 1 is yours, all 45 minutes. It takes a few seconds.": "La lección 1 es tuya, los 45 minutos. Tarda unos segundos.",
 "Lesson done. Well spoken!": "Lección terminada. ¡Bien dicho!",
 "Lesson {n}": "Lección {n}",
 "Lessons": "Lecciones",
 "Lessons unlock the moment you pay, in the app and as MP3s.": "Las lecciones se abren en cuanto pagas, en la app y como MP3.",
 "Level 1": "Nivel 1",
 "Level 1 · First Steps": "Nivel 1 · Primeros pasos",
 "Level {n}": "Nivel {n}",
 "Levels 1 to 5": "Niveles 1 a 5",
 "Levels 2 to 5": "Niveles 2 a 5",
 "Levels 2 to 5: 120 more lessons (90 hours)": "Niveles 2 a 5: 120 lecciones más (90 horas)",
 "Library": "Biblioteca",
 "Light": "Claro",
 "Listen free": "Escucha gratis",
 "Listen to lesson 1 free": "Escucha la lección 1 gratis",
 "Locked": "Bloqueada",
 "Locked. Lesson titles are here so you can see what's coming.": "Bloqueado. Ves los títulos para saber lo que viene.",
 "Main": "Principal",
 "Make your free account first. It takes a few seconds.": "Primero crea tu cuenta gratis. Tarda unos segundos.",
 "Mark as done": "Marcar como hecha",
 "Marked as done": "Marcada como hecha",
 "Marked as not done": "Marcada como pendiente",
 "Next lesson": "Siguiente lección",
 "Next up: {title}. Unlock Level 1 to keep going tomorrow morning.": "Lo que sigue: {title}. Desbloquea el nivel 1 para seguir mañana temprano.",
 "Not now": "Ahora no",
 "Not sure yet? Make a free account and the whole of lesson 1 is yours.": "¿Aún no te decides? Crea una cuenta gratis y la lección 1 completa es tuya.",
 "Nothing bought yet. Lesson 1 of each course is free with your account.": "Todavía no compraste nada. La lección 1 de cada curso es gratis con tu cuenta.",
 "One payment. No subscription, nothing to cancel.": "Un solo pago. Sin suscripción, nada que cancelar.",
 "Open your library": "Abre tu biblioteca",
 "Paid": "Pagado",
 "Part {n} of 3": "Parte {n} de 3",
 "Password": "Contraseña",
 "Pause": "Pausa",
 "Pay once. Keep every lesson. Listen anywhere.": "Pagas una vez. Te quedas con todas las lecciones. Escúchalas donde sea.",
 "Pep talk": "Ánimo",
 "Phrase sheet and full transcript for each lesson": "Hoja de frases y transcripción de cada lección",
 "Picking up where you stopped, at {t}.": "Sigues donde te quedaste, en {t}.",
 "Play": "Reproducir",
 "Play in the app or download the MP3s": "Escúchalas en la app o descarga los MP3",
 "Play lesson": "Escuchar la lección",
 "Play my next lesson": "Escuchar mi próxima lección",
 "Please choose a password of at least 8 characters.": "Elige una contraseña de al menos 8 caracteres.",
 "Please choose a stronger password.": "Elige una contraseña más segura.",
 "Please confirm your email first. Check your inbox for the link.": "Primero confirma tu correo. Busca el enlace en tu bandeja de entrada.",
 "Please enter a valid email address.": "Escribe un correo válido.",
 "Please enter your password.": "Escribe tu contraseña.",
 "Please tell us your name.": "Dinos tu nombre, por favor.",
 "Please use at least 2 characters for your name.": "Usa al menos 2 letras para tu nombre.",
 "Position in the lesson": "Posición en la lección",
 "Previous lesson": "Lección anterior",
 "Prices": "Precios",
 "Privacy &amp; Terms": "Privacidad y condiciones",
 "Privacy &amp; Terms, and your data": "Privacidad, condiciones y tus datos",
 "Quiz yourself": "Ponte a prueba",
 "Read them after the lesson, not while driving. Quiz yourself hides the answers: say them out loud, then tap to check.": "Léelas después de la lección, no mientras manejas. «Ponte a prueba» oculta las respuestas: dilas en voz alta y toca para comprobar.",
 "Ready": "Lista",
 "Refunded": "Reembolsado",
 "Regional accents and slang in Level 5": "Acentos y expresiones de cada región en el nivel 5",
 "Reset your password": "Cambia tu contraseña",
 "Resume at {t}": "Seguir en {t}",
 "Sales open very soon. The buttons put you on the list for opening day, with an early-listener price.": "La venta abre muy pronto. Los botones te apuntan en la lista para el día de apertura, con un precio para los primeros.",
 "Save": "Guardar",
 "Saved": "Guardado",
 "Sayback opens for sale very soon": "Sayback sale a la venta muy pronto",
 "Secure checkout by Stripe. We never see your card.": "Pago seguro con Stripe. Nunca vemos tu tarjeta.",
 "See the courses": "Ver los cursos",
 "Send the link": "Enviar el enlace",
 "Show": "Ver",
 "Show all answers": "Ver todas las respuestas",
 "Sign in": "Entrar",
 "Sign in or create an account": "Entra o crea una cuenta",
 "Sign in to pick up where you stopped.": "Entra para seguir donde te quedaste.",
 "Sign out": "Cerrar sesión",
 "Signed out. See you soon!": "Sesión cerrada. ¡Hasta pronto!",
 "Speak a new language in the minutes you already have.": "Habla un idioma nuevo en los minutos que ya tienes.",
 "Speak or it's free.": "Hablas o es gratis.",
 "Speed": "Velocidad",
 "Stripe has your payment. This usually takes a few seconds.": "Stripe ya tiene tu pago. Normalmente tarda unos segundos.",
 "Submit feedback": "Enviar comentarios",
 "Take it with you": "Llévatela",
 "Tap anywhere big to play or pause. Eyes on the road.": "Toca el botón grande para pausar o seguir. La vista en el camino.",
 "Tell me when it opens": "Avísame cuando abra",
 "That didn't work.": "Eso no funcionó.",
 "That email and password don't match.": "Ese correo y esa contraseña no coinciden.",
 "That email doesn't look right. Check it and try again.": "Ese correo no parece correcto. Revísalo y vuelve a intentarlo.",
 "That isn't something we sell.": "Eso no es algo que vendamos.",
 "That lesson doesn't exist.": "Esa lección no existe.",
 "That page is for admins only.": "Esa página es solo para administradores.",
 "That was the free lesson. Unlock Level 1 and tomorrow's drive is lesson 2.": "Esa era la lección gratis. Desbloquea el nivel 1 y el camino de mañana será la lección 2.",
 "That was the very last lesson. You did it: the whole course, out loud.": "Esa fue la última lección. Lo lograste: el curso entero, en voz alta.",
 "That's a lot of sign-ups from one browser. Please try again later.": "Son muchos registros desde un mismo navegador. Vuelve a intentarlo más tarde.",
 "That's about 112 hours of speaking out loud. Pick any lesson to keep it fresh, or try the other direction with a friend.": "Son unas 112 horas hablando en voz alta. Elige cualquier lección para mantenerlo fresco, o prueba el otro sentido con un amigo.",
 "The last two weeks. A day counts once you've listened for a minute.": "Las últimas dos semanas. Un día cuenta en cuanto escuchas un minuto.",
 "The lesson audio didn't load. Check your connection, then press play again.": "El audio de la lección no cargó. Revisa tu conexión y vuelve a darle play.",
 "The lessons are being uploaded. Try again a little later: your place in the course is saved.": "Estamos subiendo las lecciones. Vuelve a intentarlo un poco más tarde: tu lugar en el curso está guardado.",
 "There's no such course.": "Ese curso no existe.",
 "This account is disabled.": "Esta cuenta está desactivada.",
 "This lesson is in Levels 2 to 5": "Esta lección está en los niveles 2 a 5",
 "This lesson is locked.": "Esta lección está bloqueada.",
 "This lesson's audio is on its way": "El audio de esta lección está en camino",
 "Today's new phrases": "Las frases nuevas de hoy",
 "Tomorrow: {title}. Sleep on today's phrases; that's when they set.": "Mañana: {title}. Duerme con las frases de hoy: es cuando se fijan.",
 "Too many wrong attempts. Wait a while, or reset your password.": "Demasiados intentos fallidos. Espera un rato o cambia tu contraseña.",
 "Unlock Level 1 to hear this lesson": "Desbloquea el nivel 1 para escuchar esta lección",
 "Unlock the rest of the course": "Desbloquea el resto del curso",
 "Unlocking your lessons": "Abriendo tus lecciones",
 "Upgrade · Levels 2 to 5": "Ampliación · Niveles 2 a 5",
 "We only use it for this one message. You can ask us to remove it any time.": "Solo lo usamos para ese mensaje. Puedes pedirnos que lo borremos cuando quieras.",
 "We'll email you a link to choose a new one.": "Te enviaremos un enlace para elegir una nueva.",
 "We'll email you a link to choose a new password.": "Te enviaremos un enlace para elegir una contraseña nueva.",
 "We'll write once, the day it opens. Until then, lesson 1 is waiting in your library.": "Te escribiremos una vez, el día que abra. Mientras tanto, la lección 1 te espera en tu biblioteca.",
 "Welcome back": "Hola de nuevo",
 "Welcome back!": "¡Qué bueno verte de nuevo!",
 "Welcome to Sayback!": "¡Bienvenido a Sayback!",
 "Wrap-up": "Cierre",
 "You": "Tú",
 "You already own this. It's in your library.": "Ya lo tienes. Está en tu biblioteca.",
 "You finished all 150 lessons.": "Terminaste las 150 lecciones.",
 "You picked this one": "Elegiste esta",
 "You're in. Welcome to Sayback.": "Ya estás dentro. Bienvenido a Sayback.",
 "You're on the list": "Ya estás en la lista",
 "You've heard the free lesson. Ready for the rest?": "Ya escuchaste la lección gratis. ¿Listo para el resto?",
 "Your Level 1 progress carries straight on": "Sigues justo donde vas en el nivel 1",
 "Your account": "Tu cuenta",
 "Your courses": "Tus cursos",
 "Your email": "Tu correo",
 "Your library": "Tu biblioteca",
 "Your name": "Tu nombre",
 "Your payment went through, but the unlock is taking longer than usual. It will appear in your library shortly. If it hasn't within an hour, write to arkvital@outlook.com and we'll sort it out the same day.": "Tu pago se hizo, pero la apertura está tardando más de lo normal. Aparecerá en tu biblioteca en breve. Si no aparece en una hora, escribe a arkvital@outlook.com y lo resolvemos el mismo día.",
 "a man says": "lo dice un hombre",
 "a woman says": "lo dice una mujer",
 "day streak": "días seguidos",
 "days": "días",
 "lessons done": "lecciones hechas",
 "member since": "miembro desde",
 "one time, yours to keep": "pago único, tuyo para siempre",
 "or": "o",
 "stolen minutes this week": "minutos robados esta semana",
 "tap to show the answer": "toca para ver la respuesta",
 "{done} of {count} done": "{done} de {count} hechas",
 "{n} of 150 lessons done": "{n} de 150 lecciones hechas",
 "{pct}% heard": "{pct}% escuchada"
};
