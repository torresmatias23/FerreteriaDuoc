document.addEventListener('DOMContentLoaded', function () {


  // Agregar evento a todos los botones "Agregar a carrito"
  document.querySelectorAll('.btn-cart').forEach(function (button) {
    button.addEventListener('click', function (e) {
      e.preventDefault();

      const productCard = button.closest('.product-item');
      const nombre = productCard.querySelector('h3').innerText;
      const precio = parseFloat(productCard.querySelector('.text-dark').innerText.replace('$', ''));
      const cantidad = parseInt(productCard.querySelector('.quantity').value);



      fetch('/agregar-carrito/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({ nombre, precio: precio, cantidad })
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          actualizarCarrito(data.carrito);
        }
      });
    });
  });

    // Cargar el carrito cuando se abre el menú lateral
  const offcanvasCart = document.getElementById('offcanvasCart');
  if (offcanvasCart) {
    offcanvasCart.addEventListener('show.bs.offcanvas', function () {
      fetch('/obtener-carrito/')
        .then(response => response.json())
        .then(data => {
          actualizarCarrito(data.carrito);
        });
    });
  }
});

// Actualiza visualmente el carrito
function actualizarCarrito(carrito) {
  const lista = document.querySelector('.offcanvas-body ul');
  const totalElemento = document.getElementById('total-carrito');
  const cantidadProductos = document.getElementById('cantidad-productos');

  lista.innerHTML = '';
  let total = 0;

  carrito.forEach(item => {
    const li = document.createElement('li');
    li.className = "list-group-item d-flex justify-content-between lh-sm";
    li.innerHTML = `
      <div>
        <h6 class="my-0">${item.nombre}</h6>
        <small>${item.cantidad} x $${item.precio.toFixed(2)}</small>
      </div>
      <span>$${(item.cantidad * item.precio).toFixed(2)}</span>
      <button class="btn btn-danger btn-sm ms-2 btn-eliminar" data-producto-nombre="${item.nombre}">Eliminar</button>
    `;
    lista.appendChild(li);
    total += item.cantidad * item.precio;
  });

  totalElemento.innerText = `$${total.toFixed(2)}`;
  cantidadProductos.innerText = carrito.length;

  // Agregar evento de eliminación de producto
  document.querySelectorAll('.btn-eliminar').forEach(function (button) {
    button.addEventListener('click', function (e) {
      const productoNombre = button.getAttribute('data-producto-nombre');
      
      fetch(`/eliminar-carrito/${productoNombre}/`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': getCookie('csrftoken')
        }
      })
      .then(response => response.json())
      .then(data => {
        if (data.success) {
          actualizarCarrito(data.carrito);  // Actualiza la vista del carrito
        }
      });
    });
  });
}

// Función para obtener el CSRF token de la cookie
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}
