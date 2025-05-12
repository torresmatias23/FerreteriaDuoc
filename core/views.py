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
                tipo_usuario = user_data.get("tipo_usuario", "").lower()

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
        seccion = request.POST["seccion"]
        precio = int(request.POST["precio"])
        imagen = request.POST["imagen"]

        db.collection("productos").add({
            "nombre": nombre,
            "descripcion": descripcion,
            "categoria": categoria,
            "seccion": seccion,
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
from firebase_admin import auth, _auth_utils  

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
                if tipo_usuario == "bodeguero":
                    return redirect("ordenes_bodega")
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

from django.views.decorators.http import require_POST

def usuarios(request):
    usuarios_completos = []

    try:
        page = auth.list_users()
        while page:
            for user in page.users:
                uid = user.uid
                email = user.email

                user_doc = db.collection("usuarios").document(uid).get()
                if user_doc.exists:
                    datos = user_doc.to_dict()
                    usuarios_completos.append({
                        "uid": uid,
                        "email": email,
                        "primer_nombre": datos.get("primer_nombre", ""),
                        "segundo_nombre": datos.get("segundo_nombre", ""),
                        "primer_apellido": datos.get("primer_apellido", ""),
                        "segundo_apellido": datos.get("segundo_apellido", ""),
                        "telefono": datos.get("telefono", ""),
                        "tipo_usuario": datos.get("tipo_usuario", "cliente"),
                    })
                else:
                    usuarios_completos.append({
                        "uid": uid,
                        "email": email,
                        "primer_nombre": "",
                        "segundo_nombre": "",
                        "primer_apellido": "",
                        "segundo_apellido": "",
                        "telefono": "",
                        "tipo_usuario": "cliente",
                    })

            if page.has_next_page():
                page = page.get_next_page()
            else:
                break
    except Exception as e:
        print("Error al obtener usuarios:", e)

    return render(request, "usuarios.html", {"usuarios": usuarios_completos})



@require_POST
def eliminar_usuario(request):
    uid = request.POST.get("uid")

    try:
        auth.delete_user(uid)
        db.collection("usuarios").document(uid).delete()
        messages.success(request, "Usuario eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar usuario: {str(e)}")

    return redirect("usuarios")

from django.views.decorators.http import require_http_methods

@require_http_methods(["POST"])
def editar_usuario(request):
    uid = request.POST.get("uid")
    primer_nombre = request.POST.get("primer_nombre")
    segundo_nombre = request.POST.get("segundo_nombre")
    primer_apellido = request.POST.get("primer_apellido")
    segundo_apellido = request.POST.get("segundo_apellido")
    telefono = request.POST.get("telefono")
    tipo_usuario = request.POST.get("tipo_usuario")  # <-- Añadido

    try:
        user_ref = db.collection("usuarios").document(uid)
        user_ref.update({
            "primer_nombre": primer_nombre,
            "segundo_nombre": segundo_nombre,
            "primer_apellido": primer_apellido,
            "segundo_apellido": segundo_apellido,
            "telefono": telefono,
            "tipo_usuario": tipo_usuario,  # <-- Añadido
        })
        messages.success(request, "Usuario actualizado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al editar usuario: {e}")

    return redirect("usuarios")

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

def perfil(request):
    nombre_usuario = ""
    apellido_usuario = ""
    segundo_apellido = ""
    telefono = ""
    tipo_usuario = ""
    email = ""

    try:
        uid = request.session.get("firebase_uid")
        if uid:
            user_ref = db.collection("usuarios").document(uid)

            # Si se envió el formulario
            if request.method == 'POST':
                nuevos_datos = {
                    "primer_nombre": request.POST.get("primer_nombre", ""),
                    "primer_apellido": request.POST.get("primer_apellido", ""),
                    "segundo_apellido": request.POST.get("segundo_apellido", ""),
                    "telefono": request.POST.get("telefono", ""),
                    "tipo_usuario": request.POST.get("tipo_usuario", ""),
                    "email": request.POST.get("email", "")
                }
                user_ref.update(nuevos_datos)

            user_doc = user_ref.get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                nombre_usuario = user_data.get("primer_nombre", "")
                apellido_usuario = user_data.get("primer_apellido", "").split(" ")[0]
                segundo_apellido = user_data.get("segundo_apellido", "")
                telefono = user_data.get("telefono", "")
                tipo_usuario = user_data.get("tipo_usuario", "")
                email = user_data.get("email", "")

    except Exception as e:
        print("Error al traer o actualizar datos del usuario:", e)

    return render(request, 'perfil.html', {
        'nombre_usuario': nombre_usuario,
        'apellido_usuario': apellido_usuario,
        'segundo_apellido': segundo_apellido,
        'telefono': telefono,
        'tipo_usuario': tipo_usuario,
        'email': email
    })

    print(">>> ENTRANDO A LA VISTA PERFIL <<<")

    nombre_usuario = ""
    apellido_usuario = ""
    segundo_apellido = ""
    telefono = ""
    tipo_usuario = ""
    email = ""

    try:
        uid = request.session.get("firebase_uid")
        print("UID en sesión:", uid)

        if uid:
            user_doc = db.collection("usuarios").document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                nombre_usuario = user_data.get("primer_nombre", "")
                apellido_usuario = user_data.get("primer_apellido", "").split(" ")[0]
                segundo_apellido = user_data.get("segundo_apellido", "")
                telefono = user_data.get("telefono", "")
                tipo_usuario = user_data.get("tipo_usuario", "")
                email = user_data.get("email", "")

    except Exception as e:
        print("Error al traer datos del usuario:", e)

    return render(request, 'perfil.html', {
        'nombre_usuario': nombre_usuario,
        'apellido_usuario': apellido_usuario,
        'segundo_apellido': segundo_apellido,
        'telefono': telefono,
        'tipo_usuario': tipo_usuario,
        'email': email
    })

    print(">>> ENTRANDO A LA VISTA PERFIL <<<")

    nombre_usuario = ""
    apellido_usuario = ""

    try:
        uid = request.session.get("firebase_uid")
        print("UID en sesión:", uid)

        if uid:
            user_doc = db.collection("usuarios").document(uid).get()
            if user_doc.exists:
                user_data = user_doc.to_dict()
                nombre_usuario = user_data.get("primer_nombre", "")
                apellido_usuario = user_data.get("primer_apellido", "").split(" ")[0]

    except Exception as e:
        print("Error al traer datos del usuario:", e)

    return render(request, 'perfil.html', {
        'nombre_usuario': nombre_usuario,
        'apellido_usuario': apellido_usuario
    })

def admin_productos(request):
    productos_completos = []

    try:
        docs = db.collection("productos").stream()
        for doc in docs:
            data = doc.to_dict()
            productos_completos.append({
                "uid": doc.id,
                "nombre": data.get("nombre", ""),
                "descripcion": data.get("descripcion", ""),
                "categoria": data.get("categoria", ""),
                "seccion": data.get("seccion", ""),
                "precio": data.get("precio", ""),
                "imagen": data.get("imagen", ""),
                "stock": data.get("stock", ""),
            })

    except Exception as e:
        print("Error al obtener productos:", e)

    return render(request, 'admin_productos.html', {
        'productos': productos_completos
    })
@require_http_methods(["POST"])
def editar_producto(request):
    uid = request.POST.get("uid")
    categoria = request.POST.get("categoria")
    descripcion = request.POST.get("descripcion")
    imagen = request.POST.get("imagen")
    nombre = request.POST.get("nombre")
    precio = request.POST.get("precio")
    seccion = request.POST.get("seccion")
    stock = request.POST.get("stock")

    try:
        prod_ref = db.collection("productos").document(uid)
        prod_ref.update({
            "categoria": categoria,
            "descripcion": descripcion,
            "imagen": imagen,
            "nombre": nombre,
            "precio": precio,
            "seccion": seccion,
            "stock": stock,
        })
        messages.success(request, "Producto actualizado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al editar producto: {e}")

    return redirect("admin_productos")

@require_POST
def eliminar_producto(request):
    uid = request.POST.get("uid")

    try:
        # Eliminar solo el documento del producto, no de usuarios
        db.collection("productos").document(uid).delete()
        messages.success(request, "Producto eliminado correctamente.")
    except Exception as e:
        messages.error(request, f"Error al eliminar el producto: {str(e)}")

    return redirect("admin_productos")

