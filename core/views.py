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
    productos = []
    nombre_usuario = ""
    apellido_usuario = ""

    try:
        # Obtener el UID guardado en sesión
        uid = request.session.get("firebase_uid")
        if uid:
            user_doc = db.collection("usuarios").document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                nombre_usuario = user_data.get("primer_nombre", "")
                apellido_usuario = user_data.get("primer_apellido", "").split(" ")[0]

        # Traer productos
        docs = db.collection("productos").stream()
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            productos.append(data)

    except Exception as e:
        print("Error al traer productos o datos del usuario:", e)

    return render(request, 'index.html', {
        'productos': productos,
        'nombre_usuario': nombre_usuario,
        'apellido_usuario': apellido_usuario
    })



def clientes_nuevos(request):
    users = []
    page = auth.list_users()
    while page: 
        for user in page.users:
            users.append({
                'uid': user.uid,
                'email': user.email
            })
        if page.has_next_page:
            page = page.get_next_page()
        else:
            break

    # Si quieres, puedes limitar a los últimos 5 registrados (Firebase no garantiza orden, pero tú podrías ordenar si tienes un campo fecha)
    users = users[:5]

    return render(request, 'dashboard_admin.html', {'users': users})


def productos(request):
    productos = []
    categorias = set()
    filtro_categoria = request.GET.get("categoria", "")

    try:
        docs = db.collection("productos").stream()
        for doc in docs:
            data = doc.to_dict()
            data["id"] = doc.id
            categorias.add(data["categoria"])
            if filtro_categoria == "" or data["categoria"] == filtro_categoria:
                productos.append(data)
    except Exception as e:
        print("Error:", e)

    return render(request, "productos.html", {
        "productos": productos,
        "categorias": sorted(categorias),
        "categoria_actual": filtro_categoria
    })


# DETALLE DE PRODUCTO
def detalle_producto(request, producto_id):
    try:
        doc = db.collection("productos").document(producto_id).get()
        if doc.exists:
            producto = doc.to_dict()
            producto["id"] = doc.id
            return render(request, "producto_detalle.html", {"producto": producto})
        else:
            return HttpResponse("Producto no encontrado", status=404)
    except Exception as e:
        return HttpResponse("Error al obtener producto: " + str(e), status=500)
# SUBIR NUEVO PRODUCTO
def subir_producto(request):
    if request.method == "POST":
        nombre = request.POST["nombre"]
        descripcion = request.POST["descripcion"]
        categoria = request.POST["categoria"]
        precio = int(request.POST["precio"])
        imagen = request.POST["imagen"]

        db.collection("productos").add({
            "nombre": nombre,
            "descripcion": descripcion,
            "categoria": categoria,
            "precio": precio,
            "imagen": imagen
        })

        return redirect("/productos/")

    return render(request, "subir_producto.html")

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
        # Datos del formulario
        email = request.POST["email"]
        password = request.POST["password"]
        primer_nombre = request.POST["primer_nombre"]
        segundo_nombre = request.POST.get("segundo_nombre", "")  # opcional
        primer_apellidos = request.POST["primer_apellido"]
        segundo_apellido = request.POST["segundo_apellido"]
        telefono = request.POST["telefono"]

        try:
            # Crear usuario en Firebase Authentication
            user = auth.create_user(email=email, password=password)
            uid = user.uid

            # Guardar información del usuario en Firestore
            db.collection("usuarios").document(uid).set({
                "email": email,
                "primer_nombre": primer_nombre,
                "segundo_nombre": segundo_nombre,
                "primer_apellido": primer_apellidos,
                "segundo_apellido": segundo_apellido,
                "telefono": telefono,
                "tipo_usuario": "cliente",
            })
            messages.success(request, "¡Registro exitoso!")
            return redirect('/login')
        except Exception as e:
            messages.error(request, f"Ocurrió un error al registrar: {str(e)}")

    return render(request, "registro.html")


def dashboard_admin(request):
    users = []
    try:
        page = auth.list_users()
        while page:
            for user in page.users:
                users.append({
                    'uid': user.uid,
                    'email': user.email
                })
            if page.has_next_page():
                page = page.get_next_page()
            else:
                break
        # Mostrar solo los últimos 5 (aunque Firebase no garantiza orden)
        users = users[:5]
    except Exception as e:
        print("Error al obtener usuarios:", e)

    return render(request, "dashboard_admin.html", {"users": users})



from django.contrib import messages
from firebase_admin import auth, _auth_utils  # Asegúrate de importar _auth_utils

def login_usuario(request): 
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]
        try:
            firebase_user = auth.get_user_by_email(email)

            uid = firebase_user.uid
            request.session["firebase_uid"] = uid

            # Obtener el tipo_usuario desde Firestore
            doc_ref = db.collection("usuarios").document(uid)
            doc = doc_ref.get()

            if doc.exists:
                datos_usuario = doc.to_dict()
                tipo_usuario = datos_usuario.get("tipo_usuario")

                # Crear el usuario en Django
                user, created = User.objects.get_or_create(username=uid, email=email)
                django_login(request, user)

                # Redirigir según tipo de usuario
                if tipo_usuario == "admin":
                    return redirect("dashboard_admin")  # usa el name del path
                else:
                    return redirect("home")
            else:
                messages.error(request, "No se encontró el usuario en la base de datos.")
        except auth.UserNotFoundError:
            messages.error(request, "El correo electrónico no está registrado.")
        except Exception as e:
            messages.error(request, f"Ocurrió un error al iniciar sesión: {str(e)}")

    return render(request, "login.html")


def logout_usuario(request):
    logout(request)
    return redirect("home")

def carrito(request):
    return render(request, 'carrito.html')

def checkout(request):
    return render(request, 'checkout.html')

def nosotros(request):
    return render(request, 'nosotros.html')

def ordenes_bodega(request):
    return render(request, 'ordenes_bodega.html')

def pagos(request):
    return render(request, 'pagos.html')

def pedidos(request):
    return render(request, 'pedidos.html')

def recuperar_contrasena(request):
    return render(request, 'recuperar_contrasena.html')

def reportes(request):
    return render(request, 'reportes.html')
