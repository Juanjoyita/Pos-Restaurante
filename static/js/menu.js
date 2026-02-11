function moneyCOP(n){
  n = Math.round(n || 0);
  return "$" + n.toLocaleString("es-CO");
}

function calcular(){
  const items = document.querySelectorAll(".item");
  let total = 0;
  let count = 0;
  let resumen = [];

  items.forEach(row => {
    const precio = Number(row.dataset.precio || 0);
    const input = row.querySelector("input.qval");
    const qty = Number(input.value || 0);

    if(qty > 0){
      count += qty;
      total += precio * qty;

      const name = row.querySelector(".item-name")?.textContent?.trim() || "Producto";
      resumen.push(`${qty}x ${name}`);
    }
  });

  document.getElementById("items-count").textContent = String(count);
  document.getElementById("total-val").textContent = moneyCOP(total);

  const btn = document.getElementById("btn-enviar");
  const hint = document.getElementById("hint");
  if(count > 0){
    btn.disabled = false;
    hint.textContent = "Listo para enviar ✅";
  }else{
    btn.disabled = true;
    hint.textContent = "Selecciona al menos 1 producto";
  }

  const resumenEl = document.getElementById("resumen");
  resumenEl.textContent = resumen.length ? ("Resumen: " + resumen.join(" • ")) : "";
}

function cambiarQty(row, delta){
  const input = row.querySelector("input.qval");
  let qty = Number(input.value || 0);
  qty = Math.max(0, qty + delta);
  input.value = String(qty);
  calcular();
}

document.addEventListener("click", (e) => {
  const row = e.target.closest(".item");
  if(!row) return;

  if(e.target.classList.contains("mas")){
    cambiarQty(row, +1);
  }
  if(e.target.classList.contains("menos")){
    cambiarQty(row, -1);
  }
});

document.getElementById("btn-limpiar")?.addEventListener("click", () => {
  document.querySelectorAll("input.qval").forEach(i => i.value = "0");
  calcular();
});

document.getElementById("pedido-form")?.addEventListener("submit", (e) => {
  // pequeña confirmación rápida
  const count = Number(document.getElementById("items-count").textContent || 0);
  if(count <= 0){
    e.preventDefault();
    return;
  }
  // si quieres confirmación:
  // if(!confirm("¿Enviar pedido?")) e.preventDefault();
});

calcular();
