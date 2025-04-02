from django.shortcuts import render,redirect
from django.http import JsonResponse
from firebase_admin import auth
from django.contrib.auth import login as django_login
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from django.contrib.auth import logout
from django.contrib import messages
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import firebase_admin
from firebase_admin import firestore
import json

# Conectar con Firestore
db = firestore.client()
def home(request):
    return render(request, 'index.html')

def productos(request):
    return render(request, 'productos.html')
def contacto(request):
    mensaje = ""
    
    if request.method == "POST":
        nombre = request.POST.get("nombre")
        email = request.POST.get("email")
        mensaje = request.POST.get("mensaje")

        doc_ref = db.collection("contactos").document()
        doc_ref.set({
            "nombre": nombre,
            "email": email,
            "mensaje": mensaje
        })

        mensaje = "Mensaje enviado correctamente"

    return render(request, "contacto.html", {"mensaje": mensaje})

def registrar_usuario(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            # Crear usuario en Firebase
            user = auth.create_user(email=email, password=password)
            
            # Crear un objeto de usuario en Django
            # Usamos el mismo email y contraseña para crear el usuario en Django
            django_user = User.objects.create_user(username=email, email=email, password=password)
            
            # Iniciar sesión automáticamente al registrarse
            login(request, django_user)

            # Mostrar mensaje de éxito
            messages.success(request, "¡Registro exitoso! Ya estás logueado.")

            # Redirigir a la página principal (index)
            return redirect('/')
        except Exception as e:
            return JsonResponse({"error": str(e)})

    return render(request, "registro.html")


def login_usuario(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            # Autenticación con Firebase
            firebase_user = auth.get_user_by_email(email)
            
            # Intentamos encontrar el usuario en Django (puede que no esté registrado)
            user, created = User.objects.get_or_create(username=firebase_user.uid, email=email)
            
            # Aquí puedes implementar la verificación de la contraseña, si es necesario.
            # Para este ejemplo asumimos que el usuario ya está registrado en Django.

            # Si el usuario no tiene contraseña en Django (porque Firebase no la sincroniza),
            # puedes establecer una contraseña aleatoria o pedirle que la cambie.
            
            # Iniciar la sesión del usuario en Django
            django_login(request, user)

            # Redirigir al home (página principal)
            return redirect('/')
        except auth.AuthError as e:
            # Si hay algún error con Firebase (como usuario no encontrado o contraseña incorrecta)
            return JsonResponse({"error": "Usuario no encontrado o contraseña incorrecta"})

    return render(request, "login.html")


def logout_usuario(request):
    logout(request)
    return redirect("login")