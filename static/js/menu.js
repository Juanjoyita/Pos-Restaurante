// Scope: solo opera dentro de #lista-productos (el formulario de selección)
// No toca los div.pedido-row del card de pedido actual

const listaEl = document.getElementById("lista-productos");

function moneyCOP(n) {
  n = Math.round(n || 0);
  return "$" + n.toLocaleString("es-CO");
}

function calcular() {
  // SOLO los .item dentro del formulario de productos
  const items = listaEl ? listaEl.querySelectorAll(".item") : [];
  let total = 0;
  let count = 0;
  let resumen = [];

  items.forEach(row => {
    const precio = Number(row.dataset.precio || 0);
    const input = row.querySelector("input.qval");
    const qty = Number(input ? input.value : 0);

    if (qty > 0) {
      count += qty;
      total += precio * qty;
      const name = row.querySelector(".item-name")?.textContent?.trim() || "Producto";
      resumen.push(`${qty}× ${name}`);
    }
  });

  const countEl = document.getElementById("items-count");
  const totalEl = document.getElementById("total-val");
  const btn     = document.getElementById("btn-enviar");
  const hint    = document.getElementById("hint");
  const resumenEl = document.getElementById("resumen");

  if (countEl) countEl.textContent = String(count);
  if (totalEl) totalEl.textContent = moneyCOP(total);

  if (btn && hint) {
    if (count > 0) {
      btn.disabled = false;
      hint.textContent = "Listo para enviar ✅";
    } else {
      btn.disabled = true;
      hint.textContent = "Selecciona al menos 1 producto";
    }
  }

  if (resumenEl) {
    resumenEl.textContent = resumen.length ? "Resumen: " + resumen.join(" • ") : "";
  }
}

function cambiarQty(row, delta) {
  const input = row.querySelector("input.qval");
  if (!input) return;
  let qty = Number(input.value || 0);
  qty = Math.max(0, qty + delta);
  input.value = String(qty);
  calcular();
}

// Delegación de eventos: solo sobre lista-productos
if (listaEl) {
  listaEl.addEventListener("click", (e) => {
    const row = e.target.closest(".item");
    if (!row) return;
    if (e.target.classList.contains("mas"))   cambiarQty(row, +1);
    if (e.target.classList.contains("menos")) cambiarQty(row, -1);
  });
}

// Limpiar
document.getElementById("btn-limpiar")?.addEventListener("click", () => {
  if (listaEl) {
    listaEl.querySelectorAll("input.qval").forEach(i => i.value = "0");
  }
  calcular();
});

// Submit guard
document.getElementById("pedido-form")?.addEventListener("submit", (e) => {
  const count = Number(document.getElementById("items-count")?.textContent || 0);
  if (count <= 0) {
    e.preventDefault();
  }
});

// Inicializar
calcular();